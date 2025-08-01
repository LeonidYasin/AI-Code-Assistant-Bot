# Вклад в проект

Спасибо за интерес к участию в проекте! Вот несколько рекомендаций, которые помогут вам внести свой вклад.

## Как внести вклад

1. **Сообщите об ошибке**
   - Проверьте, не сообщали ли о такой ошибке ранее
   - Опишите проблему как можно подробнее
   - Укажите шаги для воспроизведения ошибки
   - Укажите версию Python и используемые зависимости

2. **Предложите улучшение**
   - Опишите предлагаемое улучшение
   - Объясните, почему это улучшение будет полезно
   - Укажите, является ли это новым функционалом или изменением существующего

3. **Отправьте Pull Request**
   - Создайте форк репозитория
   - Создайте ветку для вашей функции/исправления
   - Сделайте коммит с понятными сообщениями
   - Отправьте Pull Request с описанием изменений

## Требования к коду

- Код должен соответствовать стилю, определенному в `.pre-commit-config.yaml`
- Все новые функции должны быть покрыты тестами
- Документируйте публичные API и сложные участки кода
- Обновляйте документацию при изменении функционала

## Процесс разработки

1. Установите зависимости для разработки:
   ```bash
   pip install -r requirements-dev.txt
   pre-commit install
   ```

2. Создайте ветку для вашего изменения:
   ```bash
   git checkout -b feature/feature-name
   # или
   git checkout -b bugfix/issue-description
   ```

3. Внесите изменения и протестируйте их:
   ```bash
   # Запуск тестов
   pytest
   
   # Проверка стиля кода
   black .
   isort .
   flake8
   mypy .
   ```

4. Сделайте коммит с понятным сообщением:
   ```bash
   git add .
   git commit -m "Краткое описание изменений"
   ```

5. Отправьте изменения в ваш форк и создайте Pull Request

## Кодекс поведения

Этот проект придерживается [Кодекса поведения участников с открытым исходным кодом](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
Участвуя в этом проекте, вы соглашаетесь соблюдать его условия.
