"""Gemini/OpenAI solo redactan. Los hechos salen de las fichas."""

from __future__ import annotations

import asyncio
import logging
import unicodedata

import httpx

from config import settings

logger = logging.getLogger(__name__)

_GEMINI_MODELS = (
    "gemini-3.6-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash",
)
_FAIL = "Tuve un problema para generar la respuesta."
_GEMINI_SECONDS = 12


def fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def is_sendable(text: str) -> bool:
    raw = (text or "").strip()
    if len(raw) < 8:
        return False
    blob = fold(raw)
    if raw.lower().lstrip().startswith("rules"):
        return False
    if "hechos:" in blob or "system_instruction" in blob:
        return False
    if len(raw.split()) >= 5 and not raw.endswith((".", "?", "!", "…")):
        return False
    return True


async def reply_to(
    user_text: str,
    history: list[dict] | None = None,
    extra_context: str = "",
) -> str:
    mode = settings.ai_mode.strip().lower()
    if mode == "echo":
        return f"ENTRENARIA recibió: {user_text}"
    if mode in {"openai", "gemini"}:
        if _use_gemini():
            try:
                text = await asyncio.wait_for(
                    _gemini_reply(user_text, history or [], extra_context),
                    timeout=_GEMINI_SECONDS,
                )
            except asyncio.TimeoutError:
                logger.warning("Gemini tardó más de %ss; uso plantilla", _GEMINI_SECONDS)
                return _FAIL
            if not is_sendable(text):
                return _FAIL
            return text
        return await _openai_reply(user_text, history or [], extra_context)
    raise ValueError(f"AI_MODE desconocido: {settings.ai_mode}")


def _use_gemini() -> bool:
    base = settings.openai_base_url.lower()
    model = settings.openai_model.lower()
    return "generativelanguage.googleapis.com" in base or model.startswith("gemini")


def _system_prompt(extra_context: str) -> str:
    if not extra_context.strip():
        return settings.ai_system_prompt
    return f"{settings.ai_system_prompt}\n\n{extra_context}"


def _history(turns: list[dict]) -> list[dict]:
    clean = []
    for turn in turns[-12:]:
        text = str(turn.get("text") or "")
        if turn.get("role") == "assistant" and not is_sendable(text):
            continue
        clean.append(turn)
    return clean


async def _openai_reply(user_text: str, history: list[dict], extra_context: str) -> str:
    if not settings.openai_api_key:
        return "Falta OPENAI_API_KEY en el archivo .env"
    url = settings.openai_base_url.rstrip("/") + "/chat/completions"
    messages = [{"role": "system", "content": _system_prompt(extra_context)}]
    for turn in _history(history):
        role = "assistant" if turn.get("role") == "assistant" else "user"
        messages.append({"role": role, "content": turn.get("text", "")})
    messages.append({"role": "user", "content": user_text})
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.openai_model,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 180,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            logger.error("AI request failed: %s %s", response.status_code, response.text[:500])
            return _FAIL
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


def _visible_text(response) -> str:
    try:
        text = (response.text or "").strip()
        if text:
            return text
    except Exception:
        pass
    chunks: list[str] = []
    for cand in getattr(response, "candidates", None) or []:
        content = getattr(cand, "content", None)
        for part in getattr(content, "parts", None) or []:
            if getattr(part, "thought", False):
                continue
            piece = getattr(part, "text", None)
            if piece:
                chunks.append(piece)
    return "".join(chunks).strip()


def _gemini_configs(types, instruction: str):
    configs = []
    thinking = getattr(types, "ThinkingConfig", None)
    afc = types.AutomaticFunctionCallingConfig(disable=True)
    if thinking is not None:
        try:
            configs.append(
                types.GenerateContentConfig(
                    system_instruction=instruction,
                    temperature=0.4,
                    max_output_tokens=400,
                    thinking_config=thinking(thinking_budget=0),
                    automatic_function_calling=afc,
                )
            )
        except Exception:
            pass
    configs.append(
        types.GenerateContentConfig(
            system_instruction=instruction,
            temperature=0.4,
            max_output_tokens=400,
            automatic_function_calling=afc,
        )
    )
    configs.append(
        types.GenerateContentConfig(
            system_instruction=instruction,
            temperature=0.4,
            max_output_tokens=400,
        )
    )
    return configs


async def _gemini_reply(user_text: str, history: list[dict], extra_context: str) -> str:
    if not settings.openai_api_key:
        return "Falta OPENAI_API_KEY en el archivo .env"

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.openai_api_key)
    preferred = settings.openai_model.strip()
    instruction = _system_prompt(extra_context)
    contents: list[types.Content] = []
    for turn in _history(history):
        role = "model" if turn.get("role") == "assistant" else "user"
        contents.append(
            types.Content(role=role, parts=[types.Part(text=turn.get("text", ""))])
        )
    contents.append(types.Content(role="user", parts=[types.Part(text=user_text)]))

    last_error = ""
    models = []
    if preferred:
        models.append(preferred)
    for name in _GEMINI_MODELS:
        if name not in models:
            models.append(name)

    raw_configs = _gemini_configs(types, instruction)
    for model in models:
        for config in raw_configs:
            try:
                response = await client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                text = _visible_text(response)
                if text:
                    logger.info("Gemini OK with model %s", model)
                    return text
            except Exception as exc:
                last_error = str(exc)[:400]
                logger.warning("Gemini model %s failed: %s", model, last_error)
                continue

    logger.error("Gemini SDK failed: %s", last_error)
    return _FAIL
