"""OpenAI-backed structured LLM client with deterministic fallback support."""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from backend.config import settings

ModelT = TypeVar("ModelT", bound=BaseModel)
FallbackFn = Callable[[str, str], Awaitable[dict[str, Any]]]


class LLMClient:
    def __init__(self) -> None:
        self.use_llm = settings.USE_LLM
        self.provider = settings.LLM_PROVIDER.lower().strip()
        self.model = settings.LLM_MODEL
        self.disable_reason: str | None = None
        self.base_url = settings.LLM_BASE_URL
        if self.provider == "groq" and not self.base_url:
            self.base_url = "https://api.groq.com/openai/v1"

        if settings.LLM_API_KEY:
            self.api_key = settings.LLM_API_KEY
        elif self.provider == "groq":
            self.api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        else:
            self.api_key = settings.OPENAI_API_KEY
        self._fallbacks: Dict[type[BaseModel], FallbackFn] = {}
        self._client = None
        if self.use_llm:
            try:
                from openai import AsyncOpenAI
            except ModuleNotFoundError:
                self.use_llm = False
                self.disable_reason = "openai package is not installed in the running Python environment"
            else:
                if self.base_url:
                    self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
                else:
                    self._client = AsyncOpenAI(api_key=self.api_key)

    def register_fallback(self, model: type[BaseModel], fallback_fn: FallbackFn) -> None:
        self._fallbacks[model] = fallback_fn

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[ModelT],
        temperature: Optional[float] = None,
    ) -> ModelT:
        fallback_fn = self._fallbacks.get(response_model)

        if not self.use_llm:
            if not fallback_fn:
                raise RuntimeError(f"LLM disabled and no fallback registered for {response_model.__name__}")
            fallback_payload = await fallback_fn(system_prompt, user_prompt)
            return response_model.model_validate(fallback_payload)

        if not self.api_key:
            if fallback_fn:
                fallback_payload = await fallback_fn(system_prompt, user_prompt)
                return response_model.model_validate(fallback_payload)
            raise RuntimeError(
                "LLM API key is missing. Set LLM_API_KEY, or set GROQ_API_KEY/OPENAI_API_KEY based on LLM_PROVIDER."
            )

        try:
            completion = await self._client.beta.chat.completions.parse(
                model=self.model,
                temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=response_model,
            )
            parsed = completion.choices[0].message.parsed
            if parsed is None:
                raise RuntimeError("LLM response did not contain valid parsed structured data")
            return parsed
        except ValidationError:
            raise
        except Exception as exc:
            # Provider-compatible JSON mode fallback for endpoints that don't support beta.parse.
            try:
                completion = await self._client.chat.completions.create(
                    model=self.model,
                    temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                content = completion.choices[0].message.content
                if not content:
                    raise RuntimeError("LLM JSON response content is empty")
                payload = json.loads(content)
                return response_model.model_validate(payload)
            except Exception:
                pass
            if fallback_fn:
                fallback_payload = await fallback_fn(system_prompt, user_prompt)
                return response_model.model_validate(fallback_payload)
            raise RuntimeError(f"Structured generation failed: {exc}") from exc
