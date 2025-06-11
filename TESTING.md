# Руководство по тестированию

## Содержание
1. [Общие принципы](#общие-принципы)
2. [Принципы тестирования](#принципы-тестирования)
3. [Структура тестов](#структура-тестов)
4. [Запуск тестов](#запуск-тестов)
5. [Написание тестов](#написание-тестов)
6. [Тестирование команд](#тестирование-команд)
7. [Интеграционное тестирование](#интеграционное-тестирование)
8. [Лучшие практики](#лучшие-практики)
9. [CI/CD](#ci-cd)

## Общие принципы

1. **Централизованное тестирование**:
   - Все тесты выполняются через `main.py`
   - Тестируется готовый функционал, а не отдельные компоненты
   - Проверяется корректность работы всей системы в сборе

2. **Черный ящик**:
   - Тестируем систему как черный ящик
   - Не делаем предположений о внутренней реализации
   - Проверяем только входные и выходные данные

## Принципы тестирования

1. **End-to-End подход**:
   - Каждый тест проверяет полный сценарий работы
   - Включает инициализацию, выполнение команды и проверку результата
   - Минимизирует моки и стабы

2. **Изоляция тестов**:
   - Каждый тест должен быть независим
   - Тесты не должны влиять друг на друга
   - Используем временные файлы и каталоги

3. **Воспроизводимость**:
   - Тесты должны давать одинаковый результат при каждом запуске
   - Избегаем недетерминированного поведения
   - Используем фиксированные данные для тестирования

## Структура тестов

```
tests/
├── commands/               # Тесты команд
│   ├── test_help.py        # Тесты справки
│   ├── test_project.py     # Тесты работы с проектами
│   └── test_analyze.py     # Тесты анализа кода
├── fixtures/               # Фикстуры и тестовые данные
│   ├── test_projects/      # Тестовые проекты
│   └── configs/            # Конфигурации для тестов
└── conftest.py             # Фикстуры и хелперы
```

## Запуск тестов

### Установка зависимостей для тестирования
```bash
pip install -r requirements-test.txt
```

### Запуск всех тестов
```bash
python -m pytest tests/
```

### Запуск тестов конкретной команды
```bash
python -m pytest tests/commands/test_help.py -v
```

### Запуск с логированием
```bash
python -m pytest tests/ -v --log-cli-level=INFO
```

### Пример тестового сценария
```bash
# Создаем тестовый проект
python main.py project create test_project

# Запускаем анализ
python main.py analyze_project

# Проверяем результат
python -m pytest tests/commands/test_analyze.py -v
```

## Написание тестов

### Основной принцип
Все тесты выполняются исключительно через вызов `main.py` с соответствующими аргументами командной строки. Никакие внутренние функции или классы не тестируются напрямую.

### Пример теста команды help
```bash
# Тест основной справки
python main.py help

# Проверяем, что вывод содержит основные разделы
if ! python main.py help | grep -q "Доступные команды"; then
    echo "Ошибка: не найден раздел 'Доступные команды'"
    exit 1
fi

# Тест справки по конкретной команде
if ! python main.py help project | grep -q "project create"; then
    echo "Ошибка: не найдена команда 'project create' в справке"
    exit 1
fi
```

### Проверка кодов возврата
```bash
# Успешное выполнение
python main.py help
echo $?  # Должно быть 0

# Ошибка при несуществующей команде
python main.py несуществующая_команда
echo $?  # Должно быть не 0
```

## Тестирование команд

### Общий подход
1. Каждая команда тестируется через вызов `main.py`
2. Проверяются:
   - Код возврата (0 при успехе, не 0 при ошибке)
   - Вывод в stdout/stderr
   - Изменения в файловой системе
   - Сообщения об ошибках

### Пример теста команды проекта
```bash
# Создаем временный каталог для теста
TEST_DIR="/tmp/bot_test_$(date +%s)"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR" || exit 1

# Тест создания проекта
if ! python /path/to/main.py project create test_project_123; then
    echo "Ошибка при создании проекта"
    exit 1
fi

# Проверяем, что проект создан
if [ ! -d "test_project_123" ]; then
    echo "Ошибка: директория проекта не создана"
    exit 1
fi

# Проверяем список проектов
if ! python /path/to/main.py project list | grep -q "test_project_123"; then
    echo "Ошибка: проект не найден в списке"
    exit 1
fi

# Удаляем временный каталог
cd /tmp && rm -rf "$TEST_DIR"
```

## Интеграционное тестирование

### Полные сценарии
Тестирование полных сценариев работы с ботом через командную строку.

### Пример: Полный цикл анализа проекта
```bash
#!/bin/bash
set -e  # Выход при первой ошибке

# Создаем временный каталог для теста
TEST_DIR="/tmp/bot_test_$(date +%s)"
PROJECT_NAME="analysis_test"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR" || exit 1

# 1. Создаем проект
if ! python /path/to/main.py project create "$PROJECT_NAME"; then
    echo "Ошибка при создании проекта"
    exit 1
fi

# 2. Переключаемся на проект
if ! python /path/to/main.py project switch "$PROJECT_NAME" | grep -q "активный проект"; then
    echo "Ошибка при переключении на проект"
    exit 1
fi

# 3. Создаем тестовый Python-файл
cat > "$PROJECT_NAME/main.py" << 'EOF'
def hello():
    return "Hello, World!"
EOF

# 4. Запускаем анализ
if ! OUTPUT=$(python /path/to/main.py analyze_project); then
    echo "Ошибка при анализе проекта"
    echo "Вывод: $OUTPUT"
    exit 1
fi

# 5. Проверяем результаты анализа
if ! echo "$OUTPUT" | grep -q "python"; then
    echo "Ошибка: не найден Python в выводе анализа"
    exit 1
fi

if ! echo "$OUTPUT" | grep -q "main.py"; then
    echo "Ошибка: не найден main.py в выводе анализа"
    exit 1
fi

# 6. Проверяем наличие рекомендаций
if ! echo "$OUTPUT" | grep -q "рекомендации"; then
    echo "Ошибка: не найдены рекомендации в выводе анализа"
    exit 1
fi

# Очистка
cd /tmp && rm -rf "$TEST_DIR"
echo "Тест пройден успешно"
```

## Тестирование с внешними зависимостями

### Использование тестовых конфигураций
1. Создаем тестовый конфиг в `tests/fixtures/configs/test_config.ini`
2. Указываем тестовые API ключи и настройки
3. Используем флаг `--config` для указания конфига

### Пример теста с конфигурацией
```python
def test_with_custom_config(tmp_path):
    """Тест с использованием тестовой конфигурации."""
    # Создаем тестовый конфиг
    config_path = tmp_path / "test_config.ini"
    config_path.write_text(
        "[api]\n"
        "api_key = test_key_123\n"
        "model = test-model\n"
    )
    
    # Запускаем команду с тестовым конфигом
    result = subprocess.run(
        ['python', 'main.py', '--config', str(config_path), 'analyze', 'print(1)'],
        cwd=tmp_path,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "анализ завершен" in result.stdout.lower()
```

### Моки для тестирования
В редких случаях, когда нужно замокать внешние вызовы:

1. Создаем скрипт-обертку, который подменяет реальные вызовы
2. Используем переменные окружения для переключения на тестовый режим
3. Пример:

```python
# test_wrapper.py
import os
import sys
from unittest.mock import patch

def run_with_mocks():
    """Запуск main.py с подмененными зависимостями."""
    with patch('requests.post') as mock_post:
        # Настраиваем мок для внешнего API
        mock_post.return_value.json.return_value = {"result": "test response"}
        mock_post.return_value.status_code = 200
        
        # Запускаем основной скрипт
        from main import main
        return main()

if __name__ == "__main__":
    sys.exit(run_with_mocks())
```

## Лучшие практики

### 1. Организация тестов
- Группируйте тесты по функциональности
- Используйте описательные имена тестов
- Следуйте соглашению об именовании: `test_<команда>_<сценарий>_<ожидаемый_результат>`

### 2. Надежность тестов
- Используйте `tmp_path` для изоляции тестов
- Очищайте ресурсы после тестов
- Проверяйте коды возврата и вывод команд

### 3. Читаемость
- Добавляйте комментарии к сложным проверкам
- Разделяйте тесты на логические блоки с комментариями
- Используйте константы для повторяющихся значений

### 4. Производительность
- Избегайте избыточных операций ввода-вывода
- Используйте фикстуры для настройки тестового окружения
- Группируйте связанные проверки в одном тесте

### 5. Обработка ошибок
- Проверяйте сообщения об ошибках
- Тестируйте граничные случаи
- Проверяйте корректность завершения при ошибках

## CI/CD

### GitHub Actions
Пример конфигурации `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest --cov=bot --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## CI/CD

### GitHub Actions
Пример конфигурации для автоматического тестирования:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v
      env:
        # Тестовые переменные окружения
        TEST_MODE: "true"
```

### Локальный pre-commit хук
Добавьте в `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Запуск тестов перед коммитом
if ! python -m pytest tests/ -k "not slow"; then
    echo "Тесты не пройдены, коммит отменен"
    exit 1
fi

exit 0
```

Не забудьте сделать файл исполняемым:
```bash
chmod +x .git/hooks/pre-commit
```

## Полезные ссылки
- [Документация pytest](https://docs.pytest.org/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

## Примеры

### Тест обработчика команды
```python
@pytest.mark.asyncio
async def test_analyze_project_command():
    """Тест команды анализа проекта."""
    update = MockUpdate(text="/analyze_project")
    context = MockContext()
    
    # Настройка моков
    context.bot_data = {
        'project_manager': Mock(),
        'llm_client': Mock()
    }
    
    # Вызов обработчика
    from bot.handlers import nlp_processor
    await nlp_processor.handle_analyze_project(update, context)
    
    # Проверки
    assert update.message.reply_text.called
    response = update.message.reply_text.call_args[0][0]
    assert "анализ проекта" in response.lower()
```

### Тест с параметрами
```python
@pytest.mark.parametrize("input_data,expected", [
    ("test.py", "python"),
    ("test.js", "javascript"),
    ("test.txt", "unknown"),
])
def test_detect_file_type(input_data, expected):
    """Параметризованный тест определения типа файла."""
    assert detect_file_type(input_data) == expected
```
