from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.config import AIEndpointConfig, Settings
from app.services.ai.prompts import EXERCISE_SYSTEM, SCENARIO_SYSTEM


class AIProviderError(Exception):
    pass


def extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise AIProviderError(f"Invalid JSON from AI: {e}") from e


class OpenAICompatibleProvider:
    def __init__(self, config: AIEndpointConfig, *, http_proxy: str | None = None):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key
        self.model = config.model
        self.http_proxy = http_proxy

    def _http_client(self) -> httpx.AsyncClient:
        timeout = httpx.Timeout(self.config.timeout_seconds, connect=min(self.config.timeout_seconds, 10.0))
        kwargs: dict[str, object] = {"timeout": timeout}
        if self.http_proxy:
            kwargs["proxy"] = self.http_proxy
        return httpx.AsyncClient(**kwargs)

    async def _post(self, client: httpx.AsyncClient, url: str, **kwargs: Any) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await client.post(url, **kwargs)
                if response.status_code not in {408, 429, 500, 502, 503, 504}:
                    return response
                last_error = AIProviderError(
                    f"AI upstream temporarily unavailable: {response.status_code} {response.text[:500]}"
                )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
            if attempt < self.config.max_retries:
                await asyncio.sleep(0.5 * (2**attempt))
        if isinstance(last_error, AIProviderError):
            raise last_error
        if isinstance(last_error, httpx.TimeoutException):
            raise AIProviderError(f"AI request timed out after {self.config.timeout_seconds:g}s") from last_error
        raise AIProviderError(f"AI request failed: {last_error}") from last_error

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise AIProviderError("AI API key is not configured")
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        schema_hint: str,
        *,
        task: str = "generic",
    ) -> dict[str, Any]:
        if task == "scenario":
            system_content = f"{SCENARIO_SYSTEM}\nSchema: {schema_hint}"
        elif task == "exercise":
            system_content = f"{EXERCISE_SYSTEM}\nSchema: {schema_hint}"
        elif task == "translate":
            from app.services.ai.prompts import TRANSLATION_SYSTEM

            system_content = f"{TRANSLATION_SYSTEM}\nSchema: {schema_hint}"
        elif task == "writing_sample":
            from app.services.ai.prompts import WRITING_SAMPLE_SYSTEM

            system_content = f"{WRITING_SAMPLE_SYSTEM}\nSchema: {schema_hint}"
        else:
            system_content = (
                "You must respond with valid JSON only, no markdown. "
                f"Use exactly these field names from the schema. Schema: {schema_hint}"
            )
        system_msg = {"role": "system", "content": system_content}
        base_payload = {
            "model": self.model,
            "messages": [system_msg, *messages],
            "temperature": 0.7,
        }
        async with self._http_client() as client:
            payload_with_json = {**base_payload, "response_format": {"type": "json_object"}}
            resp = await self._post(
                client,
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload_with_json,
            )
            if resp.status_code != 200:
                resp = await self._post(
                    client,
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=base_payload,
                )
            if resp.status_code != 200:
                raise AIProviderError(f"LLM request failed: {resp.status_code} {resp.text}")
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return extract_json(content)

    async def chat_text(self, messages: list[dict[str, str]]) -> str:
        payload = {"model": self.model, "messages": messages, "temperature": 0.5}
        async with self._http_client() as client:
            resp = await self._post(client, f"{self.base_url}/chat/completions", headers=self._headers(), json=payload)
            if resp.status_code != 200:
                raise AIProviderError(f"LLM request failed: {resp.status_code} {resp.text}")
            return resp.json()["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        payload = {"model": self.model, "messages": messages, "temperature": 0.5, "stream": True}
        yielded = False
        try:
            async with self._http_client() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        raise AIProviderError(f"LLM stream failed: {resp.status_code} {body.decode()}")
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yielded = True
                            yield content
        except AIProviderError:
            yielded = False
        except Exception:
            yielded = False

        if not yielded:
            text = await self.chat_text(messages)
            for char in text:
                yield char

    async def text_to_speech(self, text: str, voice: str | None = None) -> bytes:
        voice_name = voice or self.config.voice or "alloy"
        payload = {"model": self.model, "input": text[:4096], "voice": voice_name}
        async with self._http_client() as client:
            resp = await self._post(
                client,
                f"{self.base_url}/audio/speech",
                headers={**self._headers(), "Accept": "audio/mpeg"},
                json=payload,
            )
            if resp.status_code != 200:
                raise AIProviderError(f"TTS request failed: {resp.status_code} {resp.text}")
            return resp.content

    async def speech_to_text(self, audio: bytes, filename: str = "audio.webm") -> str:
        mime = "application/octet-stream"
        lower = filename.lower()
        if lower.endswith(".webm"):
            mime = "audio/webm"
        elif lower.endswith(".wav"):
            mime = "audio/wav"
        elif lower.endswith(".mp3"):
            mime = "audio/mpeg"
        elif lower.endswith(".m4a"):
            mime = "audio/mp4"

        async with self._http_client() as client:
            try:
                resp = await self._post(
                    client,
                    f"{self.base_url}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data={"model": self.model},
                    files={"file": (filename, audio, mime)},
                )
            except Exception as exc:
                raise AIProviderError(f"STT request error: {exc}") from exc
            if resp.status_code != 200:
                raise AIProviderError(f"STT request failed: {resp.status_code} {resp.text}")
            try:
                data = resp.json()
            except json.JSONDecodeError as exc:
                raise AIProviderError(f"STT invalid response: {resp.text[:200]}") from exc
            text = data.get("text")
            if text is None:
                raise AIProviderError(f"STT response missing text: {data}")
            return str(text)


class MockAIProvider:
    """For tests and offline development without API key."""

    _THEME_META: dict[str, dict[str, str]] = {
        "travel": {
            "title": "A Day at the Airport",
            "summary_zh": "莎拉在机场确认行程并办理登机手续。",
            "fun_fact": "The word 'airport' combines 'air' and 'port', originally meaning a port for aircraft.",
            "opener": "Sarah arrived early at the airport to review her travel plans.",
        },
        "campus": {
            "title": "A Busy Semester on Campus",
            "summary_zh": "大学生在校园里平衡课程、作业与图书馆学习。",
            "fun_fact": "The word 'campus' comes from Latin, meaning an open field.",
            "opener": "Tom spent the afternoon on campus preparing for his next lecture.",
        },
        "business": {
            "title": "The Quarterly Business Review",
            "summary_zh": "团队在会议上讨论合同、提案、预算与晋升安排。",
            "fun_fact": "The word 'negotiate' comes from Latin negotiari, meaning to do business.",
            "opener": "The team gathered in the conference room for an important client review.",
        },
        "health": {
            "title": "A Visit to the Clinic",
            "summary_zh": "患者向医生描述症状并讨论治疗方案。",
            "fun_fact": "The word 'diagnosis' comes from Greek, meaning to distinguish or discern.",
            "opener": "Emma visited the hospital after noticing several worrying symptoms.",
        },
        "technology": {
            "title": "Launching the New Platform",
            "summary_zh": "工程师讨论软件更新、网络安全与数据库迁移。",
            "fun_fact": "The word 'algorithm' is derived from the name of Persian mathematician al-Khwarizmi.",
            "opener": "The product team met to plan a major update to their digital platform.",
        },
        "environment": {
            "title": "Protecting the Local Ecosystem",
            "summary_zh": "志愿者讨论污染、气候与可持续能源保护。",
            "fun_fact": "The word 'recycle' literally means to cycle again.",
            "opener": "Local volunteers organized a campaign to protect wildlife and reduce waste.",
        },
        "culture": {
            "title": "An Evening at the Museum",
            "summary_zh": "参观者在博物馆欣赏文学、雕塑与传统展览。",
            "fun_fact": "The word 'museum' comes from Greek, meaning a place dedicated to the Muses.",
            "opener": "Visitors gathered at the museum for a special exhibition on classic literature.",
        },
        "daily": {
            "title": "A Busy Day at Home",
            "summary_zh": "日常生活中处理家务、购物与社区事务。",
            "fun_fact": "The word 'routine' comes from French route, meaning a regular path.",
            "opener": "Lisa started her morning with a simple household routine.",
        },
        "food": {
            "title": "Dinner at a Local Restaurant",
            "summary_zh": "朋友们讨论食谱、营养与日常饮食习惯。",
            "fun_fact": "The word 'appetite' comes from Latin appetitus, meaning desire.",
            "opener": "The friends met to plan a healthy menu for the weekend gathering.",
        },
        "sports": {
            "title": "Training for the Championship",
            "summary_zh": "运动员为比赛训练并讨论健康与恢复。",
            "fun_fact": "The word 'champion' originally referred to a warrior who fought in single combat.",
            "opener": "The team gathered early to review their training plan before the big competition.",
        },
        "social": {
            "title": "Reconnecting with Old Friends",
            "summary_zh": "朋友们交流情感、尊重与沟通方式。",
            "fun_fact": "The word 'sympathy' comes from Greek, meaning feeling with someone.",
            "opener": "They met at a cafe to talk honestly about friendship and community support.",
        },
        "news": {
            "title": "Breaking News in the Headlines",
            "summary_zh": "记者报道政策辩论与公共议题。",
            "fun_fact": "The word 'journalist' comes from French journal, meaning a daily record.",
            "opener": "Editors gathered to discuss how to report the latest political campaign.",
        },
        "psychology": {
            "title": "Managing Stress and Anxiety",
            "summary_zh": "咨询师帮助来访者理解情绪、压力与心理健康。",
            "fun_fact": "The word 'psychology' comes from Greek psyche (soul) and logos (study).",
            "opener": "During the session, they discussed how anxiety can affect daily thoughts and habits.",
        },
        "science": {
            "title": "Designing a Research Experiment",
            "summary_zh": "科研团队提出假设、收集证据并分析实验结果。",
            "fun_fact": "The word 'hypothesis' comes from Greek, meaning a foundation or supposition.",
            "opener": "The researchers met to review their hypothesis before starting the next experiment.",
        },
    }

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        schema_hint: str,
        *,
        task: str = "generic",
    ) -> dict[str, Any]:
        if task == "exercise":
            return await self._mock_exercises()
        if task == "writing_sample":
            return await self._mock_writing_sample(messages)
        if task == "translate":
            return await self._mock_translation(messages)
        return await self._mock_scenario(messages)

    @classmethod
    def _parse_scenario_request(cls, messages: list[dict[str, str]]) -> dict[str, Any]:
        theme = "daily"
        target_words: list[str] = []
        scenario_type = "narrative"
        for msg in messages:
            if msg.get("role") != "user":
                continue
            for line in msg.get("content", "").splitlines():
                stripped = line.strip()
                if stripped.startswith("Theme:"):
                    theme = stripped.split(":", 1)[1].strip().lower() or theme
                elif stripped.startswith("Target words"):
                    part = stripped.split(":", 1)[1].strip()
                    target_words = [word.strip() for word in part.split(",") if word.strip()]
                elif stripped.startswith("Type:"):
                    scenario_type = stripped.split(":", 1)[1].split(".", 1)[0].strip().lower() or scenario_type
        if not target_words:
            target_words = ["plan", "practice", "learn", "improve", "focus"]
        return {
            "theme": theme,
            "words": target_words,
            "scenario_type": scenario_type,
        }

    @classmethod
    def _build_mock_passage(cls, theme: str, words: list[str]) -> tuple[str, list[dict[str, str]]]:
        meta = cls._THEME_META.get(theme, cls._THEME_META["daily"])
        sentences = [meta["opener"]]
        word_usage: list[dict[str, str]] = []
        for word in words:
            sentence = f"As the discussion continued, everyone focused on how {word} shaped the outcome."
            sentences.append(sentence)
            word_usage.append({"word": word, "sentence": sentence, "meaning_zh": word})
        return " ".join(sentences), word_usage

    async def _mock_scenario(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        req = self._parse_scenario_request(messages)
        theme = req["theme"]
        words = req["words"]
        meta = self._THEME_META.get(theme, self._THEME_META["daily"])
        passage, word_usage = self._build_mock_passage(theme, words)
        dialogue = []
        if req["scenario_type"] == "dialogue":
            lead_word = words[0]
            dialogue = [
                {"speaker": "Alex", "text": f"Let's start by discussing {lead_word}."},
                {"speaker": "Jordan", "text": f"Good idea. {lead_word} is central to our plan today."},
                {"speaker": "Alex", "text": f"We should also cover {words[1] if len(words) > 1 else 'the next step'}."},
            ]
        passage_zh = meta["summary_zh"]
        if word_usage:
            passage_zh += " " + " ".join(
                f"讨论中，大家关注到了关键词「{item['word']}」。"
                for item in word_usage[:6]
            )
        return {
            "title": meta["title"],
            "theme": theme,
            "passage": passage,
            "dialogue": dialogue,
            "word_usage": word_usage,
            "summary_zh": meta["summary_zh"],
            "passage_zh": passage_zh,
            "fun_fact": meta["fun_fact"],
        }

    @classmethod
    def _parse_target_words(cls, messages: list[dict[str, str]]) -> list[str]:
        for msg in messages:
            if msg.get("role") != "user":
                continue
            for line in msg.get("content", "").splitlines():
                stripped = line.strip()
                if stripped.startswith("Target words"):
                    part = stripped.split(":", 1)[1].strip()
                    return [word.strip() for word in part.split(",") if word.strip()]
        return ["plan", "practice", "learn", "improve", "focus"]

    async def _mock_writing_sample(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        import random

        words = self._parse_target_words(messages)
        regenerate = any("REGENERATION request" in msg.get("content", "") for msg in messages)
        templates = [
            (
                "During my first semester on campus, I decided to enroll in a faculty-led seminar. "
                "We discussed how to choose a thesis topic and manage tuition costs. "
                "The professor encouraged us to review every syllabus carefully and ask questions early. "
                "By the end of the week, I felt more confident about academic planning.",
                "在我大学第一个学期，我决定报名参加由 faculty 主持的研讨课。"
                "我们讨论了如何选择 thesis 题目以及如何规划 tuition 开支。"
                "教授鼓励我们认真研读每份 syllabus 并尽早提问。"
                "到周末时，我对学业规划更有信心了。",
            ),
            (
                "Before paying tuition, I met with a faculty advisor to plan my thesis. "
                "She explained how to enroll in research workshops and balance workload across the semester. "
                "We mapped deadlines on a calendar and listed resources that would support my writing. "
                "The conversation helped me start the term with a clearer goal.",
                "在缴纳 tuition 之前，我与 faculty 导师会面，规划我的 thesis。"
                "她说明了如何 enroll 参加研究 workshop，并在整个 semester 内平衡学习负担。"
                "我们在日历上标注截止日期，并列出了有助于写作的资源。"
                "这次谈话让我以更清晰的目标开启新学期。",
            ),
            (
                "At the start of the semester, our class debated how thesis research shapes career choices. "
                "Some students worried about tuition, while others asked how to enroll in advanced labs. "
                "The faculty host shared examples from alumni who turned small projects into strong portfolios. "
                "It reminded us that steady practice matters more than perfect first drafts.",
                "学期初，我们班讨论了 thesis 研究如何影响职业选择。"
                "有同学担心 tuition，也有同学询问如何 enroll 进入高阶实验课。"
                "faculty 主持人分享了校友将小型项目做成优秀 portfolio 的例子。"
                "这提醒我们，持续练习比追求一次写完美更重要。",
            ),
        ]
        if regenerate:
            sample_en, sample_zh = random.choice(templates)
        else:
            sample_en, sample_zh = templates[0]
        return {"sample_en": sample_en, "sample_zh": sample_zh}

    async def _mock_translation(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        passage = ""
        for msg in messages:
            if msg.get("role") != "user":
                continue
            content = msg.get("content", "")
            if "Passage:" in content:
                passage = content.split("Passage:", 1)[1].split("\n\nDialogue", 1)[0].strip()
                break
        return {
            "passage_zh": f"【译文】{passage[:200]}" if passage else "暂无译文",
            "dialogue_zh": [],
        }

    async def _mock_exercises(self) -> dict[str, Any]:
        return {
            "exercises": [
                {
                    "type": "single_choice",
                    "question": "What is the main theme of the passage?",
                    "options": [
                        {"label": "A", "text": "Travel planning"},
                        {"label": "B", "text": "Job interview"},
                        {"label": "C", "text": "Campus life"},
                        {"label": "D", "text": "Shopping"},
                    ],
                    "correct_label": "A",
                    "explanation": "The passage focuses on travel planning.",
                },
                {
                    "type": "fill_blank",
                    "passage_with_blanks": "They decided to ___ the trip carefully.",
                    "blanks": [{"index": 0, "hint": "v.", "answer": "plan", "accept": ["plan", "planned"]}],
                    "explanation": "Plan fits the context.",
                },
            ]
        }

    async def chat_text(self, messages: list[dict[str, str]]) -> str:
        user_msgs = [m["content"] for m in messages if m["role"] == "user"]
        last = user_msgs[-1] if user_msgs else ""
        if "Start the role-play" in last:
            return (
                "Good morning! Welcome to the airport check-in desk. "
                "May I help you with your reservation today? (您好，请问需要办理什么？)"
            )
        if any("\u4e00" <= c <= "\u9fff" for c in last):
            return (
                "I understand. Try saying: \"I'd like to check my schedule, please.\" "
                "Could you tell me your flight number?"
            )
        return (
            "That's helpful, thank you. Could you tell me more about your travel plans? "
            "We should confirm your schedule and luggage details."
        )

    async def chat_stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        text = await self.chat_text(messages)
        for char in text:
            yield char
            await asyncio.sleep(0.015)

    async def text_to_speech(self, text: str, voice: str | None = None) -> bytes:
        return b""

    async def speech_to_text(self, audio: bytes, filename: str = "audio.webm") -> str:
        return "They decided to plan the trip carefully."


def _provider_from_config(
    config: AIEndpointConfig,
    *,
    http_proxy: str | None = None,
) -> OpenAICompatibleProvider | None:
    if config.is_configured:
        return OpenAICompatibleProvider(config, http_proxy=http_proxy)
    return None


def get_llm_provider(settings: Settings) -> OpenAICompatibleProvider | MockAIProvider:
    if settings.testing:
        return MockAIProvider()
    proxy = settings.ai_http_proxy.strip() or None
    provider = _provider_from_config(settings.llm_config(), http_proxy=proxy)
    return provider or MockAIProvider()


def get_stt_provider(settings: Settings) -> OpenAICompatibleProvider | None:
    proxy = settings.ai_stt_http_proxy.strip() or settings.ai_http_proxy.strip() or None
    return _provider_from_config(settings.stt_config(), http_proxy=proxy)


def get_tts_provider(settings: Settings) -> OpenAICompatibleProvider | None:
    return _provider_from_config(settings.tts_config())


def get_ai_provider(settings: Settings) -> OpenAICompatibleProvider | MockAIProvider:
    """Backward-compatible alias for LLM provider."""
    return get_llm_provider(settings)
