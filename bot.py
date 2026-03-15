import json
import random
import asyncio
from pathlib import Path

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ────────────────────────────────────────────────
# Константы и файлы
# ────────────────────────────────────────────────

WORDS_FILE = "words.json"
USERS_FILE = "users.json"


def load_words() -> list:
    if not Path(WORDS_FILE).is_file():
        print(f"Файл {WORDS_FILE} не найден")
        return []
    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_users() -> dict:
    if not Path(USERS_FILE).is_file():
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(data: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


all_words = load_words()
users_data = load_users()


# ────────────────────────────────────────────────
# Вспомогательные функции
# ────────────────────────────────────────────────

async def send_new_words(update: Update, uid: str):
    level = users_data[uid].get("level")
    if not level:
        await update.message.reply_text("Сначала выбери уровень! 🎯")
        return

    available = [
        w for w in all_words
        if w.get("level") == level
        and w["word"] not in users_data[uid]["shown"]
        and w["word"] not in users_data[uid]["learned"]
    ]

    if not available:
        await update.message.reply_text("Слова закончились! 🎉")
        return

    new_words = random.sample(available, min(3, len(available)))
    users_data[uid]["shown"] = [w["word"] for w in new_words]
    save_users(users_data)

    text = "Новые слова:\n\n" + "\n".join(
        f"{w['word']} ({w.get('translation', '?')})" for w in new_words
    )

    buttons = [
        [KeyboardButton("Выучил(а)✅"), KeyboardButton("Примеры🤓")],
        [KeyboardButton("Сменить уровень🔄"), KeyboardButton("Новые слова📕")],
    ]

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )


async def send_examples(update: Update, uid: str):
    shown = users_data[uid]["shown"]
    words = [w for w in all_words if w["word"] in shown]

    if not words:
        await update.message.reply_text("Нет активных слов для примеров.")
        return

    text = "Примеры:\n\n"
    MAX = 3800

    for w in words:
        text += f"{w['word']} ({w.get('translation', '?')}):\n"
        if "examples" in w:
            for ex in w["examples"]:
                de = ex.get("de", "").strip()
                ru = ex.get("ru", "").strip()
                if de and ru:
                    block = f"{de}\n{ru}\n\n"
                    if len(text) + len(block) > MAX:
                        await update.message.reply_text(text)
                        text = ""
                    text += block

    if text.strip():
        await update.message.reply_text(text)


async def send_motivation(context: ContextTypes.DEFAULT_TYPE):
    msgs = [

            "📚 Время учить новые слова! Ты сможешь! 💪",
            "🧠 Прокачай мозг с тремя новыми словами! 🚀",
            "✨ Немного знаний каждый день — и ты гений завтра! 🌟",
            "🌱 Каждое новое слово — это шаг к свободному немецкому! 💚",
            "⏰ Не откладывай на завтра то, что можно выучить сегодня! 🔥",
            "Ты уже круче, чем вчера — продолжай! 🚀",
            "Слова не ждут — они ждут именно тебя! 📖",
            "Маленькие победы каждый день = огромный прогресс! 🏆",
            "Твой мозг любит вызовы — дай ему немецкие слова! 🧠💥",
            "Ещё 3 слова сегодня — и ты на голову выше! 😎",
            "Учи с удовольствием — и немецкий сам придёт к тебе! ☀️",
            "Ты не учишь язык — ты его завоёвываешь! ⚔️📚",
            "Каждое слово — это новая дверь в мир. Открывай! 🚪✨",
            "Не жди мотивации — создавай её сам(а)! 💪🔥",
            "Ты уже на пути к мечте — не останавливайся! 🌟",
    ]

    for uid_str, data in users_data.items():
        if data.get("notifications"):
            try:
                await context.bot.send_message(int(uid_str), random.choice(msgs))
            except Exception as e:
                print(f"Ошибка уведомления {uid_str}: {e}")


# ────────────────────────────────────────────────
# Хендлеры
# ────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in users_data:
        users_data[uid] = {
            "shown": [],
            "learned": [],
            "level": None,
            "notifications": False
        }
        save_users(users_data)

    # Основная клавиатура с уровнями + уведомлениями
    buttons = [
        [KeyboardButton("A1 🟢"), KeyboardButton("A2 🔵")],
        [KeyboardButton("B1 🟡"), KeyboardButton("B2 🟠")],
        [KeyboardButton("Уведомления включить 🔔"), KeyboardButton("Уведомления выключить 🔔")],
    ]

    await update.message.reply_text(
        "Привет! 😎\nВыбери уровень или настрой уведомления:",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    text = update.message.text.strip()

    # Защита структуры пользователя
    if uid not in users_data:
        users_data[uid] = {
            "shown": [],
            "learned": [],
            "level": None,
            "notifications": False
        }
    else:
        user = users_data[uid]
        user.setdefault("shown", [])
        user.setdefault("learned", [])
        user.setdefault("level", None)
        user.setdefault("notifications", False)

    save_users(users_data)

    levels = ["A1 🟢", "A2 🔵", "B1 🟡", "B2 🟠"]

    if text in levels:
        level_short = text.split()[0]
        users_data[uid]["level"] = level_short
        users_data[uid]["shown"] = []
        save_users(users_data)
        await update.message.reply_text(f"Выбран уровень {level_short}! 🚀")
        await send_new_words(update, uid)
        return

    # ─── Обработка уведомлений ───────────────────────────────
    if text == "Уведомления включить 🔔":
        if not users_data[uid]["notifications"]:
            users_data[uid]["notifications"] = True
            save_users(users_data)
            await update.message.reply_text("Уведомления включены 🔔✅")
        else:
            await update.message.reply_text("Уведомления уже включены 🔔")

        return

    if text == "Уведомления выключить 🔔":
        if users_data[uid]["notifications"]:
            users_data[uid]["notifications"] = False
            save_users(users_data)
            await update.message.reply_text("Уведомления выключены 🔔❌")
        else:
            await update.message.reply_text("Уведомления уже выключены 🔔")

        return
    # ──────────────────────────────────────────────────────────

    if text in ("Старт🏁", "Новые слова📕"):
        await send_new_words(update, uid)

    elif text == "Выучил(а)✅":
        added = 0
        for w in users_data[uid]["shown"]:
            if w not in users_data[uid]["learned"]:
                users_data[uid]["learned"].append(w)
                added += 1
        save_users(users_data)

        msg = "Отлично! ✅" + ("\n(большинство уже выучено)" if added == 0 else "")
        await update.message.reply_text(msg)
        await send_new_words(update, uid)

    elif text == "Примеры🤓":
        await send_examples(update, uid)

    elif text == "Сменить уровень🔄":
        buttons = [
            [KeyboardButton("A1 🟢"), KeyboardButton("A2 🔵")],
            [KeyboardButton("B1 🟡"), KeyboardButton("B2 🟠")],
            [KeyboardButton("Уведомления включить 🔔"), KeyboardButton("Уведомления выключить 🔔")],
        ]
        await update.message.reply_text(
            "Выбери новый уровень или уведомления:",
            reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
        )


# ────────────────────────────────────────────────
# Запуск
# ────────────────────────────────────────────────

async def main():
    TOKEN = "8746968281:AAGvdzb6CxoflimDPDLFlRiS5zAR-Aso2tE"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if app.job_queue:
        app.job_queue.run_repeating(send_motivation, interval=21600, first=30)
    else:
        print("JobQueue не установлен. Установите: pip install \"python-telegram-bot[job-queue]\"")

    print("Бот запускается... 🚀")

    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    print("Бот работает...  Ctrl+C — остановка")

    try:
        await asyncio.sleep(float('inf'))
    except asyncio.CancelledError:
        pass

    print("Остановка...")
    await app.updater.stop()
    await app.stop()
    await app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
    except Exception as e:
        print("Ошибка:", e)
        raise