import telebot
from telebot import types
import time
import json
import requests

# ========================
# CONFIG
# ========================
BOT_TOKEN = "8490643516:AAFlTEA7Uk4-4IFZ6qW-twFFFajKlchb5ms"
OWNER_ID = 8554393063

API_FILE = "apis.json"
bot = telebot.TeleBot(BOT_TOKEN)

user_temp = {}
uid_queue = []

# ========================
# LOAD / SAVE APIs
# ========================
def load_apis():
    try:
        with open(API_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_apis(apis):
    with open(API_FILE, "w") as f:
        json.dump(apis, f, indent=4)

# ========================
# START BOT
# ========================
@bot.message_handler(commands=["start"])
def start(message):

    if message.chat.id != OWNER_ID:
        bot.reply_to(message, "❌ You are not the owner!")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Add UID", "Add API", "Delete API")
    bot.send_message(message.chat.id, "👋 Welcome Owner!", reply_markup=markup)


# ========================
# ADD UID FLOW
# ========================
@bot.message_handler(func=lambda m: m.text in ["Add UID", "➕ Add New UID"])
def add_uid(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("IND", "BD")

    bot.send_message(message.chat.id, "Select Server:", reply_markup=markup)
    bot.register_next_step_handler(message, select_server)


def select_server(message):

    if message.text not in ["IND", "BD"]:
        bot.send_message(message.chat.id, "❌ Choose IND or BD")
        return

    user_temp[message.chat.id] = {"server": message.text}

    bot.send_message(message.chat.id, "Enter UID:")
    bot.register_next_step_handler(message, enter_uid)


def enter_uid(message):

    user_temp[message.chat.id]["uid"] = message.text

    bot.send_message(message.chat.id, "Kitni baar hit karna hai? (Example: 1 / 5 / 10)")
    bot.register_next_step_handler(message, enter_hit)


def enter_hit(message):

    try:
        hits = int(message.text)
    except:
        bot.send_message(message.chat.id, "❌ Valid number enter karo.")
        return

    data = user_temp[message.chat.id]
    server = data["server"]
    uid = data["uid"]

    uid_queue.append({
        "server": server,
        "uid": uid,
        "hits": hits
    })

    bot.send_message(
        message.chat.id,
        f"🆗 Added to Queue:\nUID: {uid}\nServer: {server}\nHits: {hits}"
    )

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Add New UID")
    bot.send_message(message.chat.id, "Add more UIDs if needed:", reply_markup=markup)

    if len(uid_queue) == 1:
        process_next(message)


# ========================
# PROCESS NEXT UID
# ========================
def process_next(message):

    if not uid_queue:
        bot.send_message(message.chat.id, "🎉 All UID Completed!")
        return

    current = uid_queue[0]
    server = current["server"]
    uid = current["uid"]
    hits = current["hits"]

    apis = load_apis()
    if not apis:
        bot.send_message(message.chat.id, "❌ No APIs added!")
        return

    bot.send_message(
        message.chat.id,
        f"🔥 Starting UID: {uid}\nServer: {server}\nHits: {hits}"
    )

    total_stats = {}

    for api in apis:
        total_stats[api] = {"level": None, "likes": None, "success": 0}

    for round_no in range(1, hits + 1):

        for api in apis:

            full_url = api.replace("<server>", server).replace("<uid>", uid)

            try:
                response = requests.get(full_url, timeout=10)

                try:
                    data = response.json()

                    if "success" in data and "level" in data and "likes" in data:
                        total_stats[api]["level"] = data["level"]
                        total_stats[api]["likes"] = data["likes"]
                        total_stats[api]["success"] += data["success"]

                except:
                    pass

            except:
                pass

        bot.send_message(message.chat.id, f"Round {round_no} completed. ⏳ Wait 30 sec…")
        time.sleep(30)

    final_text = (
        f"🔥 UID: {uid}\n"
        f"🌍 Server: {server}\n"
        f"🔁 Hits: {hits}\n"
        f"=======================\n\n"
    )

    for api, stat in total_stats.items():

        succ = stat["success"]
        succ_text = f"{succ//1000}k" if succ >= 1000 else str(succ)

        final_text += (
            f"🔗 API: {api}\n"
            f"⭐ Level: {stat['level']}\n"
            f"👍 Likes: {stat['likes']}\n"
            f"🏆 Total Success: {succ_text}\n\n"
        )

    bot.send_message(message.chat.id, final_text)

    uid_queue.pop(0)

    if uid_queue:
        bot.send_message(message.chat.id, "➡ Starting Next UID…")
        process_next(message)
    else:
        bot.send_message(message.chat.id, "🎉 All UIDs Completed!")


# ========================
# ADD API
# ========================
@bot.message_handler(func=lambda m: m.text == "Add API")
def add_api(message):

    bot.send_message(
        message.chat.id,
        "Send API like:\nhttps://your-api.vercel.app/<server>/<uid>"
    )
    bot.register_next_step_handler(message, save_api)


def save_api(message):

    api = message.text
    apis = load_apis()
    apis.append(api)
    save_apis(apis)

    bot.send_message(message.chat.id, "✅ API Added!")


# ========================
# DELETE API
# ========================
@bot.message_handler(func=lambda m: m.text == "Delete API")
def delete_api_menu(message):

    apis = load_apis()
    if not apis:
        bot.send_message(message.chat.id, "❌ No APIs added yet.")
        return

    text = "🗑 Select API Number to Delete:\n\n"
    for i, api in enumerate(apis, start=1):
        text += f"{i}. {api}\n"

    bot.send_message(message.chat.id, text)
    bot.send_message(message.chat.id, "➡ Send API number to delete")

    bot.register_next_step_handler(message, delete_api_process)


def delete_api_process(message):

    try:
        num = int(message.text)
    except:
        bot.send_message(message.chat.id, "❌ Invalid number.")
        return

    apis = load_apis()

    if num < 1 or num > len(apis):
        bot.send_message(message.chat.id, "❌ Number out of range.")
        return

    deleted = apis.pop(num - 1)
    save_apis(apis)

    bot.send_message(message.chat.id, f"🗑 Deleted API:\n{deleted}")


# ========================
# START BOT
# ========================
print("Bot Running…")
bot.polling(none_stop=True)
