import telebot
from telebot import types
import sqlite3
from os import path
import datetime

bot = telebot.TeleBot("7137374641:AAHuBp-BIcG6QiIaS7pDkCLzPG-UCjlAZao")

con = sqlite3.connect("trash_search_db.sql", check_same_thread=False)
cur = con.cursor()


def check_fine(message):
    fine = cur.execute("""SELECT fine FROM Users WHERE tg_id=(?)""", (message.from_user.id,)).fetchone()
    fine = int(str(fine)[1:-2])
    if fine >= 5:
        bot.send_message(message.chat.id, "Вы заблокированы")
        return True


@bot.message_handler(commands=["start"])
def start(message):
    tg_id = cur.execute("""SELECT tg_id FROM Users WHERE tg_id=(?)""", (message.from_user.id,)).fetchall()
    if not tg_id:
        result = cur.execute("""INSERT INTO Users(tg_id) VALUES(?)""", (message.from_user.id,))
    if not check_fine(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Конечно!"))
        bot.send_message(message.chat.id,
                         f"Здравствуйте, {message.from_user.first_name}, желаете ли вы начать помогать городу?",
                         reply_markup=markup)
        bot.register_next_step_handler(message, main_menu)
        con.commit()


def stats(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = types.InlineKeyboardButton(text="Назад🔙")
    markup.add(back_button)
    trash_count = str(
        cur.execute("""SELECT count_trash FROM Users WHERE tg_id=(?)""", (message.from_user.id,)).fetchone())[1:-2]
    fine = str(cur.execute("""SELECT fine FROM Users WHERE tg_id=(?)""", (message.from_user.id,)).fetchone())[1:-2]
    bot.send_message(message.chat.id, f"""Вот ваша статистика, {message.from_user.first_name}:
    Запросов принято: {trash_count}
    Штрафов: {fine}""", reply_markup=markup)


def main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    go_button = types.KeyboardButton(text="Помочь городу🌳")
    stat_button = types.KeyboardButton(text="Моя статистика📊")
    markup.add(go_button, stat_button)
    bot.send_message(message.chat.id, "Это главное меню. Отсюда вы можете отправить заявку или посмотреть статистику.",
                     reply_markup=markup)


def yes(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    back = types.KeyboardButton(text="Отмена❌")
    markup.add(back)
    bot.send_message(message.chat.id, "Сначала отправьте фото неубранной мусорки", reply_markup=markup)


def write_coord(longitude, latitude):
    with open("all_coordinates.txt", "a") as file:
        file.write(f" {str(longitude)} {str(latitude)} {datetime.datetime.now()}\n")


@bot.message_handler(content_types=["location"])
def check_geo(message):
    if not check_fine(message):
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        back = types.KeyboardButton(text="Отмена❌")
        markup.add(back)
        bot.send_message(message.chat.id,
                         f"Геолокация принята! Ваша заявка отправлена! Можете проверить её на сайте: https://moosly.pythonanywhere.com/")
        write_coord(message.location.longitude, message.location.latitude)
        count_trash = cur.execute("""SELECT count_trash FROM Users WHERE tg_id=(?)""",
                                  (message.from_user.id,)).fetchone()
        count_trash = int(str(count_trash)[1:-2]) + 1
        cur.execute("""UPDATE Users SET count_trash=(?) WHERE tg_id=(?)""", (count_trash, message.from_user.id))
        con.commit()
        start(message)


@bot.message_handler(func=lambda m: True, content_types=["photo"])
def image(message):
    if not check_fine(message):
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = file_info.file_path
        with open("all_coordinates.txt", "a") as file:
            file.write(f"{src}")
        if path.exists(src):
            bot.send_message(message.chat.id, "+1 штраф")
            fine = cur.execute("""SELECT fine FROM Users WHERE tg_id=(?)""", (message.from_user.id,)).fetchone()
            fine = int(str(fine)[1:-2]) + 1
            cur.execute("""UPDATE Users SET fine=(?) WHERE tg_id=(?)""", (fine, message.from_user.id))
            con.commit()
            bot.send_message(message.chat.id, "Отправьте другое фото")
        else:
            with open(src, "wb") as new_file:
                new_file.write(downloaded_file)
            markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
            button_geo = types.KeyboardButton(text="Отправить местоположение🌏", request_location=True)
            back = types.KeyboardButton(text="Отмена❌")
            markup.add(button_geo, back)
            bot.send_message(message.chat.id, "Ваше фото принято, теперь отправьте свою геолокацаию",
                             reply_markup=markup)


@bot.message_handler(content_types=["text"])
def text(message):
    if message.text == "Отмена❌":
        bot.send_message(message.chat.id, "Операция отменена")
        main_menu(message)
    if message.text == "Помочь городу🌳":
        yes(message)
    if message.text == "Моя статистика📊":
        stats(message)
    if message.text == "Назад🔙":
        main_menu(message)


bot.polling(none_stop=True)
