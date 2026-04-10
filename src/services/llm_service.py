from google import genai
import json
import logging
from ..config import Config


class LLMService:
    def __init__(self):
        self.model_id = "gemini-3.1-flash-lite-preview"
        self.client = genai.Client(api_key=Config.GEMINI_KEY)

    def parse_logs_with_dates(self, text: str):
        prompt = f"""
        Ты — аналитик данных. Перед тобой лог сообщений из чата общежития в формате "[ГГГГ-ММ-ДД ЧЧ:ММ:СС] Текст".
        Твоя задача: вычленить комнаты, которые заступили на дежурство, и указать ДАТУ этого события из лога.

        ПРАВИЛА:
        1. Если комнаты дежурят вместе (напр. "302 и 303"), верни ТОЛЬКО ПЕРВУЮ (302).
        2. Извлеки дату из квадратных скобок лога (напр. 2026-04-08).
        3. Если в тексте жалобы, запиши их в 'notes'.
        4. ИГНОРИРУЙ сообщения про "завтра" (даже если там есть дата в скобках, это лишь время отправки).
        5. Если в комнату не зашли/закрыто или написано "нет/нету" про комнату — ИГНОРИРУЙ её.
        6. Сообщения, где нет номеров комнат, игнорируй.

        Верни ТОЛЬКО JSON список объектов:
        [
          {{"room": 101, "date": "2026-04-08", "notes": ""}},
          {{"room": 205, "date": "2026-04-07", "notes": "грязная плита"}}
        ]

        ТЕКСТ ЛОГА:
        {text}
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            if not response.text:
                return []

            clean_json = response.text.strip()
            if clean_json.startswith("```"):
                clean_json = clean_json.split("```json")[-1].split("```")[0].strip()

            return json.loads(clean_json)
        except Exception as e:
            logging.error(f"LLM Parsing Error: {e}")
            return []
