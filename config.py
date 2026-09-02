from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ROOT / ".env", extra="ignore")

    ai_mode: str = "openai"
    openai_api_key: str = ""
    openai_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    openai_model: str = "gemini-3.6-flash"
    ai_system_prompt: str = (
        "Sos empleado de mostrador de una repuestera. "
        "Argentino informal, de vos. Los HECHOS de la ficha mandan. "
        "No inventes piezas, marcas ni códigos. "
        "Respondé solo el mensaje al cliente, completo."
    )


settings = Settings()
