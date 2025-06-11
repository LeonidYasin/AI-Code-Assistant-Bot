#!/usr/bin/env python3
import asyncio
import os
import sys
import time
import logging
import aiohttp
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"Загружены переменные из файла: {env_path}")
else:
    print(f"Внимание: Файл {env_path} не найден. Используются системные переменные окружения.")
    load_dotenv()

# Настройка кодировки консоли для Windows
import sys
import io

# Устанавливаем UTF-8 кодировку для вывода в консоль
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)  # Используем stdout с правильной кодировкой
    ]
)
logger = logging.getLogger(__name__)

class TelegramDebugger:
    def __init__(self, token: str, chat_id: int):
        """Инициализация отладчика
        
        Args:
            token: Токен бота от @BotFather
            chat_id: ID чата, куда отправлять сообщения
        """
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.session = None
        self.last_update_id = 0  # Для отслеживания последнего полученного обновления
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Завершение работы с сессией"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, params: dict = None) -> dict:
        """Выполнение HTTP-запроса к API Telegram
        
        Args:
            method: Название метода API
            params: Параметры запроса
            
        Returns:
            dict: Ответ от API или None в случае ошибки
        """
        if not self.session:
            raise RuntimeError("Сессия не инициализирована. Используйте контекстный менеджер 'async with'")
            
        url = f"{self.base_url}/{method}"
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        return data.get('result')
                    else:
                        logger.error(f"Ошибка API: {data.get('description')}")
                else:
                    logger.error(f"Ошибка HTTP {response.status}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            return None
    
    async def send_command(self, command: str) -> bool:
        """Отправка команды боту
        
        Args:
            command: Команда для отправки (например, "/start" или "Привет")
            
        Returns:
            bool: True, если команда отправлена успешно, иначе False
        """
        try:
            print(f"\n{'='*50}")
            print(f"ОТПРАВКА КОМАНДЫ: {command}")
            print(f"{'='*50}")
            
            # Отправляем команду
            result = await self._make_request(
                "sendMessage",
                params={"chat_id": self.chat_id, "text": command}
            )
            
            if result:
                message_id = result.get('message_id')
                logger.info(f"Команда отправлена (ID: {message_id}): {command}")
                return True
            else:
                logger.error("Не удалось отправить команду")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при отправке команды: {e}")
            return False
    
    def __init__(self, token: str, chat_id: int):
        """Инициализация отладчика
        
        Args:
            token: Токен бота от @BotFather
            chat_id: ID чата, куда отправлять сообщения
        """
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.session = None
        self.last_update_id = 0  # Для отслеживания последнего полученного обновления
        
    async def get_chat_history(self, limit: int = 5) -> list:
        """Получение новых сообщений из чата
        
        Args:
            limit: Максимальное количество сообщений для получения
            
        Returns:
            list: Список обновлений или пустой список в случае ошибки
        """
        try:
            params = {
                "timeout": 1,
                "limit": limit,
                "allowed_updates": ["message"]  # Нас интересуют только сообщения
            }
            
            # Если у нас есть последний ID обновления, запрашиваем только новые
            if self.last_update_id > 0:
                params["offset"] = self.last_update_id + 1
            
            result = await self._make_request("getUpdates", params=params)
            
            if result:
                # Обновляем последний ID обновления
                self.last_update_id = max(update['update_id'] for update in result)
                
            return result or []
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории чата: {e}")
            return []
    
    async def wait_for_bot_response(self, command: str, timeout: int = 10) -> bool:
        """Ожидание ответа от бота на команду
        
        Args:
            command: Отправленная команда
            timeout: Максимальное время ожидания в секундах
            
        Returns:
            bool: True, если получен ответ, иначе False
        """
        print(f"\nОжидаю ответ на команду: {command}")
        print(f"Таймаут: {timeout} сек...")
        
        start_time = time.time()
        
        # Сначала делаем небольшую задержку, чтобы дать боту время на обработку команды
        await asyncio.sleep(1)
        
        while (time.time() - start_time) < timeout:
            try:
                # Получаем новые обновления
                updates = await self.get_chat_history(5)
                
                if updates:
                    # Ищем ответ бота
                    for update in updates:
                        if 'message' in update and 'text' in update['message']:
                            msg = update['message']
                            
                            # Пропускаем сообщения от пользователя (нас самих)
                            if 'from' in msg and 'is_bot' in msg['from'] and not msg['from']['is_bot']:
                                continue
                                
                            # Выводим ответ от бота
                            print(f"\n✅ Получен ответ от бота:")
                            print(f"   Текст: {msg.get('text', '(нет текста)')}")
                            
                            # Если есть кнопки, выводим их
                            if 'reply_markup' in msg and 'inline_keyboard' in msg['reply_markup']:
                                print("   Кнопки:")
                                for row in msg['reply_markup']['inline_keyboard']:
                                    for btn in row:
                                        print(f"   - {btn.get('text', 'Без текста')}")
                            
                            return True
                
                # Небольшая задержка перед следующим запросом
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка при ожидании ответа: {e}")
                await asyncio.sleep(1)
        
        print("❌ Таймаут ожидания ответа истек")
        return False
    
    async def run_commands_sequentially(self, commands: List[str], delay: float = 2.0) -> bool:
        """Последовательный запуск команд с ожиданием ответа
        
        Args:
            commands: Список команд для отправки
            delay: Задержка между командами в секундах
            
        Returns:
            bool: True, если все команды выполнены успешно, иначе False
        """
        all_success = True
        
        for i, cmd in enumerate(commands, 1):
            print(f"\n{'='*50}")
            print(f"КОМАНДА {i}/{len(commands)}: {cmd}")
            print(f"{'='*50}")
            
            # Отправляем команду
            success = await self.send_command(cmd)
            
            if not success:
                print(f"❌ Не удалось отправить команду: {cmd}")
                all_success = False
            else:
                print(f"✅ Команда отправлена: {cmd}")
                
                # Ждем ответа от бота
                response_received = await self.wait_for_bot_response(cmd)
                if not response_received:
                    print(f"⚠️ Не удалось получить ответ на команду: {cmd}")
                    all_success = False
            
            # Задержка перед следующей командой
            if i < len(commands):
                print(f"\nПауза {delay} сек. перед следующей командой...")
                await asyncio.sleep(delay)
        
        return all_success

async def main():
    # Загружаем токен бота из переменных окружения
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Не задан TELEGRAM_BOT_TOKEN в переменных окружения")
        print("Проверьте наличие переменной TELEGRAM_BOT_TOKEN в файле .env")
        return
    
    # ID чата, куда отправлять команды
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        logger.error("Не задан TELEGRAM_CHAT_ID в переменных окружения")
        print("Проверьте наличие переменной TELEGRAM_CHAT_ID в файле .env")
        print("Вы можете получить его, отправив сообщение боту @userinfobot в Telegram")
        return
    
    try:
        chat_id = int(chat_id)
    except ValueError:
        logger.error("TELEGRAM_CHAT_ID должен быть числом")
        return
    
    # Пример набора команд для отладки
    test_commands = [
        "/start",
        "/help",
        "/test",
        "Привет! Что ты умеешь?",
        "/project list"
    ]
    
    print("\n" + "="*50)
    print("ТЕСТИРОВАНИЕ ТЕЛЕГРАМ БОТА")
    print("-"*50)
    print(f"Бот: {token[:10]}...")
    print(f"Чат ID: {chat_id}")
    print("-"*50)
    print("Будут выполнены команды:")
    for i, cmd in enumerate(test_commands, 1):
        print(f"{i}. {cmd}")
    print("="*50 + "\n")
    
    print("Начинаю последовательное тестирование команд...")
    print("Будут выводиться подробные логи выполнения.")
    print("-"*50 + "\n")
    
    # Используем контекстный менеджер для управления сессией
    async with TelegramDebugger(token=token, chat_id=chat_id) as debugger:
        try:
            # Запускаем тестовые команды последовательно
            success = await debugger.run_commands_sequentially(test_commands, delay=2.0)
            
            if success:
                print("\n" + "="*50)
                print("✅ ВСЕ ТЕСТЫ УСПЕШНО ЗАВЕРШЕНЫ")
                print("="*50 + "\n")
            else:
                print("\n" + "="*50)
                print("❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
                print("="*50 + "\n")
                
        except Exception as e:
            logger.error(f"Критическая ошибка при выполнении тестов: {e}")
            print("\n" + "="*50)
            print("❌ ТЕСТИРОВАНИЕ АВАРИЙНО ЗАВЕРШЕНО")
            print(f"Ошибка: {e}")
            print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
