import logging
import re
from datetime import datetime, date
from sqlalchemy.orm import Session
from ..models.db_models import Room, CleaningLog
from .llm_service import LLMService
from .cleaning_service import CleaningService
from ..config import Config

logger = logging.getLogger(__name__)

class DailySyncService:
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()
        self.cleaning_service = CleaningService(db)

    async def sync_today_messages(self, bot_manager):
        """Синхронизирует сообщения за сегодняшний день"""
        today = date.today()
        messages = []
        
        logger.info(f"Начинаю синхронизацию сообщений за {today}")
        
        try:
            # Получаем сообщения за сегодня
            async for msg in bot_manager.app.get_chat_history(Config.CHAT_ID, limit=200):
                # Проверяем, что сообщение за сегодня
                if msg.date.date() != today:
                    break
                    
                if not msg.text:
                    continue
                    
                text = msg.text.strip()
                
                # Пропускаем команды и служебные сообщения
                if text.startswith('/') or text.startswith('.'):
                    continue
                if text.startswith('Очередь на '):
                    continue
                    
                # Добавляем сообщение с временной меткой
                date_str = msg.date.strftime('%Y-%m-%d %H:%M:%S')
                for line in text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('Очередь на '):
                        continue
                    if re.match(r'^\d+\.\s', line) and 'была:' in line:
                        continue
                    messages.append(f"[{date_str}] {line}")
            
            if not messages:
                logger.info("Сообщений за сегодня не найдено")
                return 0
                
            logger.info(f"Найдено {len(messages)} сообщений за сегодня, обрабатываю через LLM...")
            
            # Обрабатываем сообщения через LLM батчами
            batch_size = 15
            total_saved = 0
            total_updated = 0
            total_skipped = 0
            
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                parsed = self.llm.parse_logs_with_dates("\n".join(batch))
                
                if not parsed:
                    logger.warning(f"Батч {i // batch_size + 1}: LLM не нашёл дежурств")
                    continue
                    
                batch_saved = 0
                batch_updated = 0
                batch_skipped = 0
                
                for entry in parsed:
                    result = self.cleaning_service.save_duty(entry['room'], entry['date'], entry['notes'])
                    if result:
                        if result['action'] == 'created':
                            batch_saved += 1
                            logger.info(f"  ✓ Создана запись: комната {result['room']}, дата {result['date']}, заметка: {result['notes']}")
                        elif result['action'] == 'updated':
                            batch_updated += 1
                            logger.info(f"  ↻ Обновлена запись: комната {result['room']}, {result['old_date']} → {result['new_date']}, заметка: {result['notes']}")
                        elif result['action'] == 'skipped':
                            batch_skipped += 1
                            logger.info(f"  ⊘ Пропущена запись: комната {result['room']}, дата {result['date']} (причина: {result['reason']})")
                        
                total_saved += batch_saved
                total_updated += batch_updated
                total_skipped += batch_skipped
                
                logger.info(f"Батч {i // batch_size + 1}: обработано {len(parsed)}, создано {batch_saved}, обновлено {batch_updated}, пропущено {batch_skipped}")
            
            logger.info(f"Ежедневная синхронизация завершена: создано {total_saved}, обновлено {total_updated}, пропущено {total_skipped} записей")
            return total_saved + total_updated
            
        except Exception as e:
            logger.error(f"Ошибка при ежедневной синхронизации: {e}")
            raise