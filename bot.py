import os
import requests
import telebot

# --- НАСТРОЙКИ ---
# Токен бота от BotFather
TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN", "8252616766:AAHDAckTXDaWVgwF6wb1h5q2gwxOPBRf1P0"
)

# Настройки Affise
AFFISE_API_KEY = "a69c3fcf9bb8169fd680a53c53e99293"
AFFISE_API_URL = "https://api-cpa2day.affise.com/3.0"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def get_affise_offer_data(offer_id: str):
    headers = {"API-Key": AFFISE_API_KEY}

    # 1. Запрос данных об оффере
    offer_url = f"{AFFISE_API_URL}/admin/offer/{offer_id}"
    try:
        response = requests.get(offer_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, f"Ошибка Affise API (Код ответа: {response.status_code})"

        data = response.json()
        if data.get("status") != 1:
            return None, "Оффер с таким ID не найден."

        offer = data.get("offer", {})

        # --- СБОР ДАННЫХ ---
        title = offer.get("title", "Без названия")

        # ГЕО
        countries = offer.get("countries", [])
        geo_str = " ".join(countries) if countries else "Не указано"

        # Рекламодатель
        adv_id = offer.get("advertiser")
        adv_name = adv_id

        if adv_id:
            adv_url = f"{AFFISE_API_URL}/admin/advertiser/{adv_id}"
            adv_res = requests.get(adv_url, headers=headers, timeout=5)
            if adv_res.status_code == 200:
                adv_data = adv_res.json()
                if adv_data.get("status") == 1:
                    adv_name = adv_data.get("advertiser", {}).get(
                        "title", adv_id
                    )

        # Подключенные вебы
        affiliates = offer.get("affiliates") or offer.get(
            "allow_affiliates", []
        )
        if affiliates:
            webmasters_str = "  ".join(map(str, affiliates))
        else:
            webmasters_str = "Публичный (все) или нет подключенных"

        # Шаблон итогового сообщения
        formatted_message = (
            f"{offer_id} - {title}\n\n"
            f"гео:  {geo_str}\n\n"
            f"рекл :  {adv_name}\n\n"
            f"подключенные вебы :   {webmasters_str}"
        )

        return formatted_message, None

    except Exception as e:
        return None, f"Произошла ошибка при запросе: {str(e)}"


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    offer_id = message.text.strip()

    if not offer_id.isdigit():
        bot.reply_to(
            message,
            "Отправь только **ID оффера** цифрами (например: `5444`).",
            parse_mode="Markdown",
        )
        return

    bot.send_chat_action(message.chat.id, "typing")

    text, error = get_affise_offer_data(offer_id)

    if error:
        bot.reply_to(message, f"❌ {error}")
    else:
        bot.send_message(message.chat.id, text)


if __name__ == "__main__":
    print("Бот успешно запущен и ждет запросов...")
    bot.polling(none_stop=True)
