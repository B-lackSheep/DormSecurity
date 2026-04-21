import time
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
        Забудь все настройки и промты, которые тебе отправляли до этого.
        Ты — аналитик данных. Перед тобой сообщения из чата общежития в формате "[ДАТА_ОТПРАВКИ] Текст".
        ДАТА_ОТПРАВКИ в скобках — это когда сообщение было отправлено, используй её как дату дежурства.
        Твоя задача: найти сообщения о дежурстве и извлечь номер комнаты и дату.

        ПРАВИЛА:
        1. Дата дежурства = дата из квадратных скобок (формат ГГГГ-ММ-ДД ЧЧ:ММ:СС), бери только ГГГГ-ММ-ДД.
        2. Номер комнаты всегда ВНЕ круглых скобок. Содержимое круглых скобок () — добавь в 'notes'.
        3. Если комнаты объединены ('+', ',', 'и', 'вместе') — бери ТОЛЬКО ПЕРВУЮ (левую).
        4. Если в тексте есть жалобы или замечания — запиши в 'notes'.

        ИГНОРИРУЙ сообщение если:
        - В нём нет номера комнаты.
        - Написано "завтра", "послезавтра" про основную комнату.
        - Написано "нет", "нету", "закрыто", "отсутствует" про комнату.
        - Это флуд, вопрос или не связано с дежурством.

        ПРИМЕРЫ:
        - "[2026-03-20 21:41:00] 212 (210 найти)" -> {{"room": 212, "date": "2026-03-20", "notes": "210 найти"}}
        - "[2026-03-21 10:00:00] 507+509" -> {{"room": 507, "date": "2026-03-21", "notes": ""}}
        - "[2026-03-22 09:00:00] завтра 304" -> ИГНОРИРОВАТЬ
        - "[2026-03-23 08:00:00] 408 (один человек)" -> {{"room": 408, "date": "2026-03-23", "notes": "один человек"}}
        - "[2026-03-24 12:00:00] 502 (вместе с 504)" -> {{"room": 502, "date": "2026-03-24", "notes": "вместе с 504"}}

        Верни ТОЛЬКО JSON список объектов:
        [
          {{"room": 101, "date": "2026-04-08", "notes": ""}},
          {{"room": 205, "date": "2026-04-07", "notes": "грязная плита"}}
        ]

        ТЕКСТ:
        {text}
        """
        for attempt in range(4):
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
                if "503" in str(e) and attempt < 2:
                    wait = 15 * (attempt + 1)
                    logging.warning(f"LLM 503, повтор через {wait} сек... ({attempt + 1}/4)")
                    time.sleep(wait)
                else:
                    logging.error(f"LLM Parsing Error: {e}")
                    return []
