#!/usr/bin/env python3
"""
Интерактивный AI чат для CLI
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

from core.ai.ai_router import ask

class AIChat:
    def __init__(self, model: str = "hf_deepseek"):
        self.model = model
        self.conversation_history = []
        self.commands = {
            "/help": self.show_help,
            "/clear": self.clear_history,
            "/history": self.show_history,
            "/model": self.switch_model,
            "/analyze": self.analyze_file,
            "/exit": self.exit_chat,
            "/quit": self.exit_chat
        }
        
    def show_help(self):
        """Показать справку по командам"""
        print("\n🤖 AI Assistant - Доступные команды:")
        print("=" * 40)
        print("/help     - Показать эту справку")
        print("/clear    - Очистить историю разговора")
        print("/history  - Показать историю разговора") 
        print("/model    - Переключить AI модель")
        print("/analyze <file> - Анализировать файл")
        print("/exit     - Выйти из чата")
        print("/quit     - Выйти из чата")
        print("=" * 40)
        print("Просто введите ваш вопрос для общения с AI")
        
    def clear_history(self):
        """Очистить историю разговора"""
        self.conversation_history = []
        print("✅ История разговора очищена")
        
    def show_history(self):
        """Показать историю разговора"""
        if not self.conversation_history:
            print("📝 История разговора пуста")
            return
            
        print("\n📝 История разговора:")
        print("=" * 50)
        for i, msg in enumerate(self.conversation_history, 1):
            role = "🧑 Вы" if msg["role"] == "user" else "🤖 AI"
            print(f"{i}. {role}: {msg['content'][:100]}...")
        print("=" * 50)
        
    def switch_model(self, model_name: str = None):
        """Переключить AI модель"""
        if not model_name:
            print("Доступные модели:")
            print("- hf_deepseek (DeepSeek - бесплатный)")
            print("- kimi (Kimi - быстрый)")
            print("- gigachat (GigaChat)")
            print("\nИспользование: /model <имя_модели>")
            return
            
        if model_name in ["hf_deepseek", "kimi", "gigachat"]:
            self.model = model_name
            os.environ["PROVIDER"] = model_name
            print(f"✅ Переключено на модель: {model_name}")
        else:
            print(f"❌ Неизвестная модель: {model_name}")
            
    async def analyze_file(self, file_path: str = None):
        """Анализировать файл"""
        if not file_path:
            print("❌ Укажите путь к файлу: /analyze <file_path>")
            return
            
        try:
            if not os.path.exists(file_path):
                print(f"❌ Файл не найден: {file_path}")
                return
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            print(f"🔍 Анализирую файл: {file_path}")
            
            messages = [{"role": "user", "content": f"Проанализируй код из файла {file_path}:\n\n{content}"}]
            result = await ask(messages)
            
            print("\n" + "="*50)
            print("📊 АНАЛИЗ ФАЙЛА:")
            print("="*50)
            print(result)
            print("="*50)
            
        except Exception as e:
            print(f"❌ Ошибка при анализе файла: {e}")
            
    def exit_chat(self):
        """Выйти из чата"""
        print("👋 До свидания!")
        sys.exit(0)
        
    async def process_command(self, user_input: str):
        """Обработать команду пользователя"""
        parts = user_input.strip().split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if command in self.commands:
            if command == "/analyze":
                await self.analyze_file(args[0] if args else None)
            elif command == "/model":
                self.switch_model(args[0] if args else None)
            else:
                self.commands[command]()
            return True
        return False
        
    async def chat_with_ai(self, user_message: str):
        """Общение с AI"""
        try:
            # Добавляем сообщение пользователя в историю
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Ограничиваем историю последними 10 сообщениями
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
                
            print("🤖 AI думает...")
            
            # Отправляем запрос к AI
            result = await ask(self.conversation_history)
            
            # Добавляем ответ AI в историю
            self.conversation_history.append({"role": "assistant", "content": result})
            
            print(f"\n🤖 AI ({self.model}):")
            print("-" * 40)
            print(result)
            print("-" * 40)
            
        except Exception as e:
            print(f"❌ Ошибка при общении с AI: {e}")
            print("💡 Проверьте настройки API ключей в .env файле")
            
    async def run(self):
        """Запустить интерактивный чат"""
        os.environ["PROVIDER"] = self.model
        
        print("🤖 AI Code Assistant - Интерактивный чат")
        print("=" * 50)
        print(f"Модель: {self.model}")
        print("Введите /help для справки или /exit для выхода")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n🧑 Вы: ").strip()
                
                if not user_input:
                    continue
                    
                # Проверяем, это команда или обычное сообщение
                if user_input.startswith('/'):
                    await self.process_command(user_input)
                else:
                    await self.chat_with_ai(user_input)
                    
            except KeyboardInterrupt:
                print("\n👋 До свидания!")
                break
            except EOFError:
                print("\n👋 До свидания!")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")

def main():
    """Главная функция"""
    model = "hf_deepseek"
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--model", "-m"] and len(sys.argv) > 2:
            model = sys.argv[2]
        elif sys.argv[1] in ["--help", "-h"]:
            print("Использование: python3 ai_chat.py [--model MODEL]")
            print("Доступные модели: hf_deepseek, kimi, gigachat")
            return
            
    chat = AIChat(model)
    asyncio.run(chat.run())

if __name__ == "__main__":
    main()