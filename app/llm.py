import json
import re
from typing import Any

from huggingface_hub import InferenceClient

from app.config import settings


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("Model response did not contain JSON.")

    return json.loads(match.group(0))


class HFLLM:
    def __init__(self) -> None:
        self.enabled = bool(settings.huggingface_api_token)
        self.client = None

        if self.enabled:
            self.client = InferenceClient(
                model=settings.hf_model,
                token=settings.huggingface_api_token,
            )

    def json_response(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not self.enabled or self.client is None:
            raise RuntimeError("Hugging Face API is not configured.")

        response = self.client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=700,
            temperature=0.1,
        )

        content = response.choices[0].message.content
        return _extract_json(content)


llm = HFLLM()
