# test_basic_commands.ps1
# Тестирование базовых команд бота

# Функция для вывода ошибки
function Write-Error {
    param([string]$Message)
    Write-Host "[ОШИБКА] $Message" -ForegroundColor Red
    exit 1
}

# Функция для вывода успеха
function Write-Success {
    param([string]$Message)
    Write-Host "[УСПЕХ] $Message" -ForegroundColor Green
}

# Проверка наличия main.py
if (-not (Test-Path "main.py")) {
    Write-Error "Файл main.py не найден в текущей директории"
}

# Создаем временный каталог для тестов
$TestDir = "$env:TEMP\bot_test_$(Get-Date -Format "yyyyMMdd_HHmmss")
$ProjectName = "test_project_$(Get-Date -Format "yyyyMMdd_HHmmss")

Write-Host "Создаем тестовое окружение в $TestDir"
New-Item -ItemType Directory -Path $TestDir -Force | Out-Null
Push-Location $TestDir

try {
    # 1. Тестируем команду help
    Write-Host "`n=== Тестируем help ===" -ForegroundColor Cyan
    $helpOutput = python ..\main.py help 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Команда help завершилась с ошибкой"
    }
    Write-Success "Команда help выполнена успешно"

    # 2. Тестируем создание проекта
    Write-Host "`n=== Тестируем создание проекта ===" -ForegroundColor Cyan
    $createOutput = python ..\main.py project create $ProjectName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Не удалось создать проект"
    }
    
    if (-not (Test-Path $ProjectName)) {
        Write-Error "Директория проекта не была создана"
    }
    Write-Success "Проект $ProjectName успешно создан"

    # 3. Тестируем переключение на проект
    Write-Host "`n=== Тестируем переключение на проект ===" -ForegroundColor Cyan
    $switchOutput = python ..\main.py project switch $ProjectName 2>&1
    if ($LASTEXITCODE -ne 0 -or $switchOutput -notmatch "активный проект") {
        Write-Error "Не удалось переключиться на проект"
    }
    Write-Success "Успешно переключились на проект $ProjectName"

    # 4. Создаем тестовый файл для анализа
    Write-Host "`n=== Подготавливаем тестовый файл ===" -ForegroundColor Cyan
    $testFilePath = "$TestDir\$ProjectName\test_script.py"
    @'
def hello():
    """Тестовая функция"""
    return "Hello, World!"

if __name__ == "__main__":
    print(hello())
'@ | Out-File -FilePath $testFilePath -Encoding utf8
    
    if (-not (Test-Path $testFilePath)) {
        Write-Error "Не удалось создать тестовый файл"
    }
    Write-Success "Создан тестовый файл"

    # 5. Тестируем анализ файла
    Write-Host "`n=== Тестируем анализ файла ===" -ForegroundColor Cyan
    $analysisOutput = python ..\main.py analyze "$ProjectName\test_script.py" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Анализ файла завершился с ошибкой"
    }

    # Проверяем ключевые слова в выводе
    $keywords = @("анализ", "функция", "код")
    foreach ($keyword in $keywords) {
        if ($analysisOutput -notmatch $keyword) {
            Write-Error "В выводе анализа не найдено ключевое слово: $keyword"
        }
    }
    Write-Success "Анализ файла выполнен успешно"

    # 6. Тестируем анализ проекта
    Write-Host "`n=== Тестируем анализ проекта ===" -ForegroundColor Cyan
    $projectAnalysis = python ..\main.py analyze_project 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Анализ проекта завершился с ошибкой"
    }

    # Проверяем ключевые слова в выводе
    $keywords = @("анализ", "файл", "рекомендации")
    foreach ($keyword in $keywords) {
        if ($projectAnalysis -notmatch $keyword) {
            Write-Error "В выводе анализа проекта не найдено ключевое слово: $keyword"
        }
    }
    Write-Success "Анализ проекта выполнен успешно"

    # 7. Тестируем отображение информации о проекте
    Write-Host "`n=== Тестируем отображение информации о проекте ===" -ForegroundColor Cyan
    $infoOutput = python ..\main.py project info 2>&1
    if ($LASTEXITCODE -ne 0 -or $infoOutput -notmatch "Информация о проекте") {
        Write-Error "Не удалось получить информацию о проекте"
    }
    Write-Success "Информация о проекте отображена успешно"

    # 8. Тестируем обработку ошибок
    Write-Host "`n=== Тестируем обработку ошибок ===" -ForegroundColor Cyan

    # Несуществующая команда
    $errorOutput = python ..\main.py несуществующая_команда 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Error "Несуществующая команда должна завершаться с ошибкой"
    }
    Write-Success "Обработка несуществующей команды работает корректно"

    # Создание существующего проекта
    $errorOutput = python ..\main.py project create $ProjectName 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Error "Повторное создание проекта должно завершаться с ошибкой"
    }
    Write-Success "Обработка дублирующегося проекта работает корректно"

    Write-Host "`n=== Завершение тестирования ===" -ForegroundColor Green
    Write-Success "Тестирование завершено успешно! Все тесты пройдены."
}
finally {
    # Возвращаемся в исходную директорию
    Pop-Location
    
    # Удаляем временную директорию
    if (Test-Path $TestDir) {
        Remove-Item -Path $TestDir -Recurse -Force
    }
}
