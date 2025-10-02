# Ты не один (You're Not Alone)

Telegram-бот для поиска собеседников по интересам и жизненным ситуациям с поддержкой peer-to-peer диалогов.

## 🎯 Описание

Сервис для анонимного общения один-на-один с людьми, пережившими похожий опыт. Платформа помогает найти поддержку от тех, кто понимает вашу ситуацию.

### Основные возможности

- 🔍 **Умный матчинг** — подбор собеседников по общим темам и часовому поясу
- 🎭 **Анонимность** — общение под псевдонимом без раскрытия личных данных
- 🤖 **AI-подсказки** — помощь в эмпатичном общении (опционально)
- ⭐ **Чаевые** — возможность отблагодарить собеседника через Telegram Stars
- 🛡️ **Безопасность** — система жалоб, модерация и ссылки на профессиональную помощь

## 🏗️ Архитектура

### Стек технологий

- **Backend:** Python 3.12, FastAPI, aiogram 3.x
- **База данных:** PostgreSQL 18
- **Кэш/Очередь:** Redis 7.4
- **ORM:** SQLAlchemy 2.x + Alembic
- **Платежи:** Telegram Stars (XTR)
- **AI:** OpenAI API (опционально)
- **Деплой:** Docker, Docker Compose

### Структура проекта

```
├── apps/
│   ├── api/              # FastAPI приложение
│   ├── bot/              # Telegram бот
│   ├── ai_coach/         # AI сервис подсказок
│   └── workers/          # Фоновые воркеры
├── core/                 # Базовые модули
├── models/               # SQLAlchemy модели
├── migrations/           # Alembic миграции
├── deploy/               # Docker файлы
└── tests/                # Тесты
```

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Python 3.12+ (для локальной разработки)
- Токен Telegram бота от [@BotFather](https://t.me/BotFather)

### Установка

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd NotAlone
   ```

2. **Создайте файл окружения:**
   ```bash
   cp .env.example .env
   ```

3. **Настройте переменные в `.env`:**
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   PUBLIC_BASE_URL=https://your-domain.com
   SECRET_KEY=your_secret_key_here
   ```

4. **Запустите сервисы:**
   ```bash
   make up
   ```

5. **Примените миграции:**
   ```bash
   make migrate
   ```

## 📝 Команды разработки

```bash
make help          # Показать все доступные команды
make up            # Запустить все сервисы
make down          # Остановить все сервисы
make logs          # Показать логи
make migrate       # Применить миграции
make migrate-create # Создать новую миграцию
make fmt           # Форматировать код
make lint          # Проверить код линтерами
make test          # Запустить тесты
```

## 🔧 Разработка

### Локальная разработка без Docker

1. **Установите зависимости:**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Запустите PostgreSQL и Redis:**
   ```bash
   docker compose -f deploy/compose.yml up db redis -d
   ```

3. **Запустите API:**
   ```bash
   make dev-api
   ```

4. **Запустите бота (в другом терминале):**
   ```bash
   make dev-bot
   ```

### Создание миграции

```bash
make migrate-create
# Введите описание миграции
```

### Форматирование и линтинг

```bash
make fmt   # Автоформатирование кода
make lint  # Проверка кода
```

## 🗄️ База данных

### Основные модели

- **User** — пользователи с анонимными профилями
- **Topic** — темы для обсуждения
- **Match** — матчи между пользователями
- **ChatSession** — сессии диалогов
- **Tip** — чаевые через Telegram Stars
- **AiHint** — AI подсказки для общения

### Схема миграций

Миграции управляются через Alembic:
```bash
alembic upgrade head      # Применить все миграции
alembic downgrade -1      # Откатить последнюю миграцию
alembic history           # История миграций
```

## 🤖 Telegram Bot

### Основные команды

- `/start` — начать работу с ботом
- `/profile` — настроить профиль
- `/find` — найти собеседника
- `/tips` — оставить чаевые
- `/help` — помощь и правила

### Webhooks

Бот работает через webhooks. Убедитесь, что:
- У вас есть публичный домен с HTTPS
- Webhook URL указан в `PUBLIC_BASE_URL`

## 🔐 Безопасность

### Анонимность

- Никакие персональные данные не собираются
- Общение под псевдонимами
- Минимизация PII в логах

### Модерация

- Система жалоб и блокировок
- Safety флаги для токсичного контента
- Ссылки на профессиональную помощь

## 💳 Платежи

Платежи реализованы через **Telegram Stars (XTR)**:
- Цифровые чаевые собеседникам
- Автоматический учет комиссий
- Прозрачная система расчетов

## 🧪 Тестирование

```bash
make test              # Запустить все тесты
pytest tests/unit      # Только unit-тесты
pytest tests/integration  # Только integration-тесты
```

## 📊 Мониторинг

### Health Checks

- `GET /health` — общий статус
- `GET /health/db` — статус базы данных
- `GET /health/redis` — статус Redis

### Логи

```bash
make logs          # Все логи
make logs-api      # Логи API
make logs-bot      # Логи бота
make logs-worker   # Логи воркера
```

## 🚢 Деплой

### Production готовность

Для продакшена рекомендуется:
1. Использовать managed PostgreSQL (Neon, Supabase)
2. Использовать managed Redis (Upstash, Redis Cloud)
3. Настроить HTTPS с валидным сертификатом
4. Настроить мониторинг (Prometheus, Grafana)
5. Настроить логирование (Loki, ELK)

### Docker деплой

```bash
docker compose -f deploy/compose.yml up -d --build
```

## 📋 TODO

- [ ] Реализовать логику матчинга
- [ ] Добавить AI интеграцию
- [ ] Настроить Telegram Stars платежи
- [ ] Добавить систему рейтингов
- [ ] Реализовать модерацию
- [ ] Добавить метрики и аналитику

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку для фичи (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Запушьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

MIT License

## 📞 Контакты

Для вопросов и предложений: [sammuti.com](https://sammuti.com)

---

⚠️ **Важно:** Это не замена профессиональной психологической помощи. При серьезных проблемах обращайтесь к специалистам.
