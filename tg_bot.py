import logging
import os
import json
import random
import requests

from dotenv import load_dotenv
from functools import partial

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

from dialogflow_helper import detect_intent_texts


logger = logging.getLogger(__name__)
PLACES = []


def load_places():
    global PLACES
    try:
        with open("places.json", "r", encoding="utf-8") as f:
            PLACES = json.load(f)
        logger.info(f"Загружено мест: {len(PLACES)}")
    except Exception as e:
        logger.error(f"Не удалось загрузить places.json: {e}")
        PLACES = []


def get_random_place():
    if not PLACES:
        return None
    return random.choice(PLACES)


def is_image_available(url):
    if not url:
        return False
    try:
        resp = requests.head(url, timeout=5)
        return resp.status_code == 200
    except:
        return False


def send_place(message, place):
    text = (
        f"📍 <b>{place['name']}</b>\n\n"
        f"⭐ <i>{place['why']}</i>"
    )

    keyboard = [
        [
            InlineKeyboardButton("🔁 Другое место", callback_data="another_place"),
            InlineKeyboardButton("✨ Спасибо", callback_data="thanks")
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if place.get("image_url"):
        message.bot.send_photo(
            chat_id=message.chat_id,
            photo=place["image_url"],
            caption=text,
            parse_mode="HTML",
            reply_markup=markup
        )
    else:
        message.bot.send_message(
            chat_id=message.chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=markup
        )


def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data in ("get_place", "another_place"):
        place = get_random_place()

        if not place:
            query.edit_message_text(
                "К сожалению, сейчас места недоступны 😔 Попробуй позже."
            )
            return

        send_place(query.message, place)

    elif query.data == "thanks":
        try:
            query.edit_message_text("Всегда пожалуйста! Хорошего отдыха 💛")
        except:
            pass
        query.message.reply_text("Рад был помочь! Если захочешь узнать о других интересных местах в Москве, дай мне знать!")


def handle_tg_message(update: Update, context: CallbackContext, project_id):
    user_text = update.message.text

    try:
        session_id = f"tg_{update.effective_chat.id}"

        reply_text = detect_intent_texts(
            project_id=project_id,
            session_id=session_id,
            user_message=user_text,
            language_code="ru"
        )

        if not reply_text:
            reply_text = "Я пока не знаю, что ответить 🤔"

        keyboard = [
            [InlineKeyboardButton(
                "🎲 Прислать интересное место в Москве",
                callback_data="get_place"
            )]
        ]

        markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(
            reply_text,
            reply_markup=markup
        )

        logger.info(f"Dialogflow ответил: {reply_text}")

    except Exception as e:
        logger.error(f"Ошибка Dialogflow: {e}")
        update.message.reply_text(
            "Кажется, у меня небольшие технические проблемы… Попробуй позже 🙏"
        )


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Здравствуйте!"
        )


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    load_dotenv()
    load_places()

    token = os.getenv("BOT_TOKEN")
    project_id = os.getenv("PROJECT_ID")

    if not token:
        raise ValueError("BOT_TOKEN не найден в .env")
    if not project_id:
        raise ValueError("PROJECT_ID не найден в .env")

    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CallbackQueryHandler(button))

    echo_handler = partial(handle_tg_message, project_id=project_id)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo_handler))

    logger.info("Бот запущен...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()