# Команда Лайна — Telegram Бот для бронювання ігрових слотів

Бот для групового чату, який дозволяє бронювати слоти на ігрові сесії PUBG на вихідні.

## Можливості

- Бронювання слотів на PUBG (4 гравці)
- Автоматичне відкриття бронювання щочетверга о 18:00
- Автоматичне закриття щонеділі о 23:00
- Черга очікування (waitlist) з автоматичним просуванням
- Розрахунок оптимального часу для всіх гравців
- Нагадування за годину до гри
- Статистика гравців

## Команди

| Команда | Опис |
|---------|------|
| `/book` | Інтерактивне меню бронювання |
| `/book pubg sat 18:00-22:00` | Швидке бронювання |
| `/cancel` | Скасувати бронювання (меню) |
| `/cancel pubg sat` | Швидке скасування |
| `/status` | Показати поточні бронювання |
| `/mystats` | Ваша статистика |
| `/stats` | Статистика групи |
| `/help` | Довідка |
| `/chatid` | Показати ID чату |

## Локальний запуск

1. Створіть віртуальне середовище:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

2. Встановіть залежності:
```bash
pip install -r requirements.txt
```

3. Створіть `.env` файл:
```bash
cp .env.example .env
```

4. Відредагуйте `.env`:
```
BOT_TOKEN=your_bot_token_from_botfather
DATABASE_URL=sqlite+aiosqlite:///./bot.db
CHAT_ID=your_chat_id
TIMEZONE=Europe/Warsaw
```

5. Запустіть бота:
```bash
python3 -m bot.main
```

## Деплой на Railway

1. Створіть акаунт на [railway.app](https://railway.app)

2. Створіть новий проект

3. Додайте PostgreSQL плагін

4. Підключіть GitHub репозиторій

5. Додайте змінні середовища:
   - `BOT_TOKEN` — токен від @BotFather
   - `DATABASE_URL` — автоматично від Railway (замініть `postgresql://` на `postgresql+asyncpg://`)
   - `CHAT_ID` — ID вашого чату (дізнатись через `/chatid`)
   - `TIMEZONE` — Europe/Warsaw

6. Deploy!

## Отримання токена бота

1. Напишіть [@BotFather](https://t.me/BotFather) в Telegram
2. Надішліть `/newbot`
3. Введіть назву та username бота
4. Скопіюйте токен

## Отримання Chat ID

1. Додайте бота в групу
2. Надішліть команду `/chatid`
3. Скопіюйте ID

## Структура проекту

```
komanda-telegram/
├── bot/
│   ├── main.py              # Точка входу
│   ├── config.py            # Конфігурація
│   ├── handlers/            # Обробники команд
│   ├── keyboards/           # Inline клавіатури
│   ├── services/            # Бізнес-логіка
│   ├── database/            # Моделі та репозиторії
│   └── utils/               # Утиліти
├── alembic/                 # Міграції БД
├── requirements.txt
├── Procfile                 # Для Railway
└── railway.toml
```
