# Доменный слой TraveleBot

Этот модуль содержит основные бизнес-модели и интерфейсы согласно принципам "Чистой архитектуры".

## Структура

### models.py
Содержит основные доменные модели:
- `TravelCategory` - перечисление категорий путешествий
- `UserAnswer` - ответ пользователя на вопрос
- `TravelRequest` - запрос на планирование путешествия
- `TravelRecommendation` - рекомендация путешествия
- Исключения доменного слоя

### interfaces.py
Определяет интерфейсы для внешних зависимостей:
- `ITravelRecommendationService` - сервис рекомендаций
- `IUserStateRepository` - репозиторий состояний пользователей
- `IAnalyticsService` - сервис аналитики
- `INotificationService` - сервис уведомлений

### constants.py
Константы доменного слоя:
- Маппинг категорий на названия
- Обязательные вопросы для каждой категории
- Лимиты валидации

## Принципы

1. **Независимость от фреймворков** - доменный слой не зависит от aiogram или других внешних библиотек
2. **Инверсия зависимостей** - зависимости определены через интерфейсы
3. **Чистота бизнес-логики** - вся бизнес-логика инкапсулирована в доменных моделях

## Пример использования

```python
from bot.domain.models import TravelRequest, TravelCategory

# Создание запроса
request = TravelRequest(
    user_id=123,
    category=TravelCategory.FAMILY,
    answers={}
)

# Добавление ответа
request.add_answer("family_size", "2+1", "2 взрослых + 1 ребенок")

# Проверка завершенности
required_questions = ["family_size", "travel_time", "priority"]
is_complete = request.is_complete(required_questions)
```
