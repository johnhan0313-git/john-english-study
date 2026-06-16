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
    def __init__(self, config: AIEndpointConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key
        self.model = config.model

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
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload_with_json = {**base_payload, "response_format": {"type": "json_object"}}
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload_with_json,
            )
            if resp.status_code != 200:
                resp = await client.post(
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
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=self._headers(), json=payload)
            if resp.status_code != 200:
                raise AIProviderError(f"LLM request failed: {resp.status_code} {resp.text}")
            return resp.json()["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        payload = {"model": self.model, "messages": messages, "temperature": 0.5, "stream": True}
        yielded = False
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
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

        if not yielded:
            text = await self.chat_text(messages)
            for char in text:
                yield char

    async def text_to_speech(self, text: str, voice: str | None = None) -> bytes:
        voice_name = voice or self.config.voice or "alloy"
        payload = {"model": self.model, "input": text[:4096], "voice": voice_name}
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/audio/speech",
                headers={**self._headers(), "Accept": "audio/mpeg"},
                json=payload,
            )
            if resp.status_code != 200:
                raise AIProviderError(f"TTS request failed: {resp.status_code} {resp.text}")
            return resp.content

    async def speech_to_text(self, audio: bytes, filename: str = "audio.webm") -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"model": self.model},
                files={"file": (filename, audio, "application/octet-stream")},
            )
            if resp.status_code != 200:
                raise AIProviderError(f"STT request failed: {resp.status_code} {resp.text}")
            return resp.json()["text"]


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
        return {
            "title": meta["title"],
            "theme": theme,
            "passage": passage,
            "dialogue": dialogue,
            "word_usage": word_usage,
            "summary_zh": meta["summary_zh"],
            "fun_fact": meta["fun_fact"],
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


def _provider_from_config(config: AIEndpointConfig) -> OpenAICompatibleProvider | None:
    if config.is_configured:
        return OpenAICompatibleProvider(config)
    return None


def get_llm_provider(settings: Settings) -> OpenAICompatibleProvider | MockAIProvider:
    if settings.testing:
        return MockAIProvider()
    provider = _provider_from_config(settings.llm_config())
    return provider or MockAIProvider()


def get_stt_provider(settings: Settings) -> OpenAICompatibleProvider | None:
    return _provider_from_config(settings.stt_config())


def get_tts_provider(settings: Settings) -> OpenAICompatibleProvider | None:
    return _provider_from_config(settings.tts_config())


def get_ai_provider(settings: Settings) -> OpenAICompatibleProvider | MockAIProvider:
    """Backward-compatible alias for LLM provider."""
    return get_llm_provider(settings)
