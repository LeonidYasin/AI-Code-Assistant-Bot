#!/bin/bash
# test_basic_commands.sh
# Тестирование базовых команд бота

set -e  # Выход при первой ошибке

# Функция для вывода ошибки
error() {
    echo -e "\033[0;31m[ОШИБКА]\033[0m $1"
    exit 1
}

# Функция для вывода успеха
success() {
    echo -e "\033[0;32m[УСПЕХ]\033[0m $1"
}

# Проверка наличия main.py
if [ ! -f "main.py" ]; then
    error "Файл main.py не найден в текущей директории"
fi

# Создаем временный каталог для тестов
TEST_DIR="/tmp/bot_test_$(date +%s)"
PROJECT_NAME="test_project_$(date +%s)"
echo "Создаем тестовое окружение в $TEST_DIR"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR" || exit 1

# 1. Тестируем команду help
echo -e "\n=== Тестируем help ==="
if ! python ../main.py help >/dev/null; then
    error "Команда help завершилась с ошибкой"
fi
success "Команда help выполнена успешно"

# 2. Тестируем создание проекта
echo -e "\n=== Тестируем создание проекта ==="
if ! python ../main.py project create "$PROJECT_NAME" >/dev/null; then
    error "Не удалось создать проект"
fi

if [ ! -d "$PROJECT_NAME" ]; then
    error "Директория проекта не была создана"
fi
success "Проект $PROJECT_NAME успешно создан"

# 3. Тестируем переключение на проект
echo -e "\n=== Тестируем переключение на проект ==="
if ! python ../main.py project switch "$PROJECT_NAME" | grep -q "активный проект"; then
    error "Не удалось переключиться на проект"
fi
success "Успешно переключились на проект $PROJECT_NAME"

# 4. Создаем тестовый файл для анализа
echo -e "\n=== Подготавливаем тестовый файл ==="
cat > "$PROJECT_NAME/test_script.py" << 'EOF'
def hello():
    """Тестовая функция"""
    return "Hello, World!"

if __name__ == "__main__":
    print(hello())
EOF
success "Создан тестовый файл"

# 5. Тестируем анализ файла
echo -e "\n=== Тестируем анализ файла ==="
ANALYSIS_OUTPUT=$(python ../main.py analyze "$PROJECT_NAME/test_script.py")
if [ $? -ne 0 ]; then
    error "Анализ файла завершился с ошибкой"
fi

# Проверяем ключевые слова в выводе
for keyword in "анализ" "функция" "код"; do
    if ! echo "$ANALYSIS_OUTPUT" | grep -qi "$keyword"; then
        error "В выводе анализа не найдено ключевое слово: $keyword"
    fi
done
success "Анализ файла выполнен успешно"

# 6. Тестируем анализ проекта
echo -e "\n=== Тестируем анализ проекта ==="
PROJECT_ANALYSIS=$(python ../main.py analyze_project)
if [ $? -ne 0 ]; then
    error "Анализ проекта завершился с ошибкой"
fi

# Проверяем ключевые слова в выводе
for keyword in "анализ" "файл" "рекомендации"; do
    if ! echo "$PROJECT_ANALYSIS" | grep -qi "$keyword"; then
        error "В выводе анализа проекта не найдено ключевое слово: $keyword"
    fi
done
success "Анализ проекта выполнен успешно"

# 7. Тестируем отображение информации о проекте
echo -e "\n=== Тестируем отображение информации о проекте ==="
if ! python ../main.py project info | grep -q "Информация о проекте"; then
    error "Не удалось получить информацию о проекте"
fi
success "Информация о проекте отображена успешно"

# 8. Тестируем обработку ошибок
echo -e "\n=== Тестируем обработку ошибок ==="

# Несуществующая команда
if python ../main.py несуществующая_команда 2>/dev/null; then
    error "Несуществующая команда должна завершаться с ошибкой"
fi
success "Обработка несуществующей команды работает корректно"

# Создание существующего проекта
if python ../main.py project create "$PROJECT_NAME" 2>/dev/null; then
    error "Повторное создание проекта должно завершаться с ошибкой"
fi
success "Обработка дублирующегося проекта работает корректно"

# Очистка
echo -e "\n=== Завершение тестирования ==="
cd ..
rm -rf "$TEST_DIR"
success "Тестирование завершено успешно! Все тесты пройдены."
