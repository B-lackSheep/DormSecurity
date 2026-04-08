import google.generativeai as genai
import json
import logging
from ..config import Config

genai.configure(api_key=Config.GEMINI_KEY)


class LLMService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def parse_daily_logs(self, text: str):
        prompt = f"""
        Ты — парсер дежурств. На основе текста сообщений выдели комнаты, которые заступили на дежурство сегодня.

        ПРАВИЛА:
        1. Если комнаты дежурят вместе (напр. "503 и 504"), верни ТОЛЬКО ПЕРВУЮ (503). Вторая остается без даты.
        2. Все слова в строке после назначенной комнаты запиши в 'notes'.
        3. Информация о комнатах может быть как в виде одного сообщения, так и в виде нескольких.
        4. Сообщения без номеров комнат ИГНОРИРУЙ.

        Верни ТОЛЬКО JSON список объектов:
        [{"room": 306, "notes": ""}, {"room": 407, "notes": "оставили мусор"}, {"room": 507, "notes": "и 510"}]

        ТЕКСТ:
        {text}
        """
        try:
            response = self.model.generate_content(prompt)
            clean_json = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(clean_json)
        except Exception as e:
            logging.error(f"LLM Parsing Error: {e}")
            return []
