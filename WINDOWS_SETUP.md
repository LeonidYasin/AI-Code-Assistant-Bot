# 🪟 AI Code Assistant - Инструкция для Windows

## 🚀 Быстрый запуск в Windows

### 1. Проверьте установку Python

```cmd
python --version
```
Должно показать версию Python 3.9+

### 2. Установите зависимости

```cmd
pip install -r requirements.txt
```

### 3. Запуск команд

**Используйте `python` (НЕ `python3`) в Windows:**

```cmd
# ✅ ПРАВИЛЬНО для Windows:
python main.py --help
python main.py project list
python main.py chat
python ai_chat.py

# ❌ НЕ РАБОТАЕТ в Windows:
python3 main.py --help
```

### 4. Быстрые команды через run.bat

```cmd
# Справка
run.bat help

# Список проектов
run.bat project list

# AI чат
run.bat chat

# Анализ файла
run.bat analyze main.py
```

## 🔧 Настройка AI моделей

### Создайте .env файл:

```cmd
copy .env.example .env
notepad .env
```

### Добавьте API ключи:

**DeepSeek (бесплатная):**
```
PROVIDER=hf_deepseek
HF_TOKEN=hf_ваш_токен_сюда
```

**Получить токен:** https://huggingface.co/settings/tokens

**Kimi (быстрая):**
```
PROVIDER=kimi  
KIMI_API_KEY=sk-ваш_ключ_сюда
```

**GigaChat (российская):**
```
PROVIDER=gigachat
GIGACHAT_API_KEY=ваш_ключ_сюда
```

## 🧪 Тестирование

```cmd
# Проверка базового функционала
python main.py --help
python main.py project list
python main.py file list

# С API ключами
python main.py chat
python main.py analyze main.py
```

## 🆘 Решение проблем Windows

### "python не является внутренней или внешней командой"
```cmd
# Установите Python с python.org
# Убедитесь что галочка "Add to PATH" отмечена
```

### "No module named 'core'"
```cmd
# Убедитесь что вы в правильной директории
cd C:\Projects\AI-Code-Assistant-Bot
python main.py --help
```

### Проблемы с кодировкой
```cmd
# Установите кодировку UTF-8
chcp 65001
python main.py --help
```

## 📋 Готовые команды для Windows

```cmd
REM Быстрая проверка
python main.py --help

REM Управление проектами  
python main.py project list
python main.py project create test_project

REM Работа с файлами
python main.py file list
python main.py file view README.md

REM AI функции (требуют API ключи)
python main.py chat
python main.py analyze main.py

REM Через batch файл
run.bat chat
run.bat project list
```

**🎯 Теперь все должно работать в Windows!**