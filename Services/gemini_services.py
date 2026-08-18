# Services/gemini_services.py
import time
from typing import Iterable

from google import genai
from google.genai import types


class GeminiService:
    # Pass config / system instruction lewat parameter
    def __init__(
        self,
        api_key: str,
        model_name: str,
        system_instruction: str,
        fallback_models: Iterable[str] | None = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        if not api_key:
            raise ValueError("API Key tidak boleh kosong!")

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.fallback_models = [
            model.strip() for model in (fallback_models or []) if model and model.strip()
        ]
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _is_retryable_error(self, message: str) -> bool:
        msg = message.lower()
        retryable_keywords = [
            "503",
            "429",
            "unavailable",
            "high demand",
            "temporarily",
            "resource exhausted",
            "rate limit",
            "try again later",
            "overloaded",
        ]
        return any(keyword in msg for keyword in retryable_keywords)

    def _generate_with_model(self, model_name: str, file_bytes: bytes, mime_type: str):
        return self.client.models.generate_content(
            model=model_name,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                "Tolong rekap dokumen ini sesuai aturan yang berlaku."
            ],
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.1
            )
        )

    def extract_invoice_data(self, file_bytes: bytes, mime_type: str = "application/pdf") -> str:
        models_to_try = [self.model_name] + self.fallback_models
        last_error = None

        for model_name in models_to_try:
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = self._generate_with_model(model_name, file_bytes, mime_type)
                    return response.text
                except Exception as e:
                    last_error = e
                    error_message = str(e)

                    if attempt < self.max_retries and self._is_retryable_error(error_message):
                        time.sleep(self.retry_delay * attempt)
                        continue

                    break

            if model_name != models_to_try[-1]:
                continue

        raise RuntimeError(
            f"Gagal memproses dokumen via Gemini API setelah mencoba model: {', '.join(models_to_try)}. "
            f"Error terakhir: {last_error}"
        )