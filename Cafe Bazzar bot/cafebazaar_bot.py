import re
import telebot
from cafebazaar_api import get_app_info_from_url
import time, datetime

# Replace 'YOUR_BOT_TOKEN' with your actual Telegram Bot API token
BOT_TOKEN = '6484393153:AAGeXQkqhLScCusUktmzyS6vOyhSkgfRojQ'

bot = telebot.TeleBot(BOT_TOKEN)

# Dictionary to store last message timestamps for each user
last_message_time = {}

# Time threshold in seconds
TIME_THRESHOLD = 3

def is_spam(chat_id, message_text):
    current_time = datetime.datetime.now()
    
    if chat_id in last_message_time:
        time_diff = (current_time - last_message_time[chat_id]).seconds
        if time_diff < TIME_THRESHOLD:
            return True
    
    last_message_time[chat_id] = current_time
    return False

def is_message_new(message):
    # Get the current time when the bot receives the message
    current_time = int(time.time())

    # Get the message timestamp
    message_timestamp = message.date

    # Set a threshold time difference (e.g., 5 minutes) for messages to be considered "new"
    time_threshold = 300

    # Calculate the time difference between the current time and the message timestamp
    time_diff = current_time - message_timestamp

    # Return True if the message is "new" (within the time threshold), otherwise False
    return time_diff <= time_threshold

@bot.message_handler(commands=['start'])
def start_command(message):
    welcome_message = (
        "به ربات Cafe Bazaar خوش آمدید!\n"
        "برای دریافت اطلاعات و لینک دانلود اپلیکیشن Cafe Bazaar، لینک مورد نظر را ارسال کنید."
    )
    bot.reply_to(message, welcome_message)


@bot.message_handler(func=lambda message: is_message_new(message))
def handle_message(message):
    user_id = message.from_user.id
    message_text = message.text

    if is_spam(user_id, message_text):
        bot.send_message(user_id, "Warning: Your messages seem like spam.")
    else:
            try:
                url = message.text
                if re.match(r"^https?://cafebazaar\.ir/.*$", url):
                    app_info = get_app_info_from_url(url)
                    description = app_info['description']

                    response = (
                        f"*نام اپلیکیشن*: {app_info['app_name']}\n"
                        f"*امتیاز*: {app_info['average_rate']}\n"
                        f"*دسته‌بندی*: {app_info['category']}\n"
                        f"*تعداد نصب*: {app_info['install_count_range']}\n"
                        f"*حجم فایل*: {app_info['file_size']:.2f} مگابایت\n"
                        f"*نسخه*: {app_info['version_code']}"
                    )

                    # Create an inline keyboard with a button for the download link
                    keyboard = telebot.types.InlineKeyboardMarkup()
                    download_button = telebot.types.InlineKeyboardButton(text="دانلود", url=app_info['download_link'])
                    keyboard.add(download_button)

                    # Send the response with the inline keyboard
                    bot.reply_to(message, response, parse_mode="Markdown", reply_markup=keyboard)
                else:
                    bot.reply_to(message, "لطفاً یک لینک معتبر از Cafe Bazaar وارد کنید.")

            except Exception as e:
                error_message = "هنگام پردازش لینک خطایی رخ داده است. لطفاً بعداً دوباره تلاش کنید."
                bot.reply_to(message, error_message)
                print("Error:", str(e))

        


bot.polling()