from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.config import Settings
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
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.ai_base_url.rstrip("/")
        self.api_key = settings.ai_api_key
        self.model = settings.ai_model

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

    async def text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        payload = {"model": self.settings.ai_tts_model, "input": text[:4096], "voice": voice}
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
                data={"model": self.settings.ai_stt_model},
                files={"file": (filename, audio, "application/octet-stream")},
            )
            if resp.status_code != 200:
                raise AIProviderError(f"STT request failed: {resp.status_code} {resp.text}")
            return resp.json()["text"]


class MockAIProvider:
    """For tests and offline development without API key."""

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        schema_hint: str,
        *,
        task: str = "generic",
    ) -> dict[str, Any]:
        if task == "exercise":
            return await self._mock_exercises()
        return await self._mock_scenario()

    async def _mock_scenario(self) -> dict[str, Any]:
        return {
            "title": "A Day at the Airport",
            "theme": "travel",
            "passage": (
                "Sarah arrived at the airport early to check her schedule and confirm her reservation. "
                "She needed to negotiate with the agent about her luggage allowance before boarding."
            ),
            "dialogue": [
                {"speaker": "Sarah", "text": "Excuse me, could you help me with my reservation?"},
                {"speaker": "Agent", "text": "Of course. Let me check your schedule and luggage details."},
            ],
            "word_usage": [
                {"word": "schedule", "sentence": "She checked her schedule.", "meaning_zh": "日程"},
                {"word": "reservation", "sentence": "Confirm her reservation.", "meaning_zh": "预订"},
                {"word": "negotiate", "sentence": "Negotiate about luggage.", "meaning_zh": "协商"},
            ],
            "summary_zh": "莎拉在机场办理登机手续并协商行李额度。",
            "fun_fact": "The word 'airport' combines 'air' and 'port', originally meaning a port for aircraft.",
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
        return "Good writing overall. Consider using more target vocabulary."

    async def text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        return b""

    async def speech_to_text(self, audio: bytes, filename: str = "audio.webm") -> str:
        return "They decided to plan the trip carefully."


def get_ai_provider(settings: Settings) -> OpenAICompatibleProvider | MockAIProvider:
    if settings.ai_api_key:
        return OpenAICompatibleProvider(settings)
    return MockAIProvider()
