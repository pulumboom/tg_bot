# Imports packages
import os
import time
from os.path import join, dirname

import telebot
from dotenv import load_dotenv

# Getting TOKEN from .env
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TOKEN = os.environ.get("TOKEN")

# Bot instance initialization
state_storage = telebot.storage.StateMemoryStorage()

bot = telebot.TeleBot(TOKEN, state_storage=state_storage)

chat_users_with_id = dict()
chat_users_money = dict()


# Handlers
@bot.message_handler(content_types=["new_chat_members"])
def new_user(event):
    chat_users_with_id[event.chat.id] = dict()
    chat_users_with_id[event.chat.id]['@' + event.json['new_chat_member']['username']] = event.json['new_chat_member'][
        'id']
    bot.reply_to(event, f'Welcome, {event.json["new_chat_member"]["first_name"]}! havau?')


@bot.message_handler(commands=['promote'])
def promote_user(message):
    user_info = bot.get_chat_member(message.chat.id, message.from_user.id)
    if user_info.status != 'creator' and not user_info.can_promote_members:
        bot.send_message(message.chat.id, "Only admins can promote users! Check your rights...")
        return

    if len(message.text.split()) != 2 or message.text.split()[1][0] != '@':
        bot.send_message(message.chat.id, 'Incorrect using of command. Try following: /promote @<user>')
        return

    try:
        new_admin = bot.get_chat_member(message.chat.id, chat_users_with_id[message.chat.id][message.text.split()[1]])
    except:
        bot.send_message(message.chat.id, 'Bot enable get users\'s id')
        return

    try:
        info = bot.promote_chat_member(message.chat.id, chat_users_with_id[message.chat.id][message.text.split()[1]],
                                       True, True, True)
        if info:
            bot.send_message(message.chat.id, 'User has been successfully promoted')

    except:
        bot.send_message(message.chat.id, "Something went wrong!")


@bot.message_handler(commands=['ban'])
def ban(message):
    if len(message.text.split()) != 2 or message.text.split()[1][0] != '@':
        bot.send_message(message.chat.id, 'Incorrect using of command. Try following: /ban @<user>')
        return

    try:
        bot.ban_chat_member(message.chat.id, chat_users_with_id[message.chat.id][message.text.split()[1]])
        bot.send_message(message.chat.id, 'Banned successfully!')
    except:
        bot.send_message(message.chat.id, "Something went wrong!")


@bot.message_handler(commands=['unban'])
def unban(message):
    if len(message.text.split()) != 2 or message.text.split()[1][0] != '@':
        bot.send_message(message.chat.id, 'Incorrect using of command. Try following: /unban @<user>')
        return

    try:
        bot.unban_chat_member(message.chat.id, chat_users_with_id[message.chat.id][message.text.split()[1]])
        bot.send_message(message.chat.id, 'Unbanned successfully!')
    except:
        bot.send_message(message.chat.id, "Something went wrong!")


@bot.message_handler(commands=['members'])
def get_members_number(message):
    members_number = bot.get_chat_members_count(message.chat.id)
    bot.send_message(message.chat.id, f'There are {members_number} memberes in the chat')


@bot.message_handler(commands=['admins'])
def get_admins_number(message):
    admins_number = bot.get_chat_administrators(message.chat.id)
    bot.send_message(message.chat.id, f'There are {len(admins_number)} admins in the chat')


@bot.message_handler(commands=['leave'])
def leave(message):
    bot.send_message(message.chat.id, "Goodbye.")
    try:
        bot.leave_chat(message.chat.id)
    except:
        bot.send_message(message.chat.id, 'Something went wrong')


@bot.message_handler(commands=['play'])
def choose_number(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 3

    buttons = []
    for i in range(1, 7):
        buttons.append(telebot.types.InlineKeyboardButton(str(i), callback_data=f"chosen_{i}"))
    markup.add(*buttons)
    markup.add(telebot.types.InlineKeyboardButton('cancel', callback_data="chosen_cancel"))

    msg = bot.send_message(message.chat.id, "Choose a digit from 1-6.", reply_markup=markup)
    global wtf
    wtf = msg.message_id


@bot.callback_query_handler(func=lambda call: len(call.data) > 7 and call.data[:7] == 'chosen_')
def callback_handler(call):
    chat_id = call.message.chat.id
    print(call.message.message_id)

    if call.data[7:] == 'cancel':
        print(123)
        bot.answer_callback_query(call.id, 'Приходи еще')
        bot.delete_message(chat_id, call.message.message_id)
        return

    dice = bot.send_dice(chat_id, emoji="🎲")
    time.sleep(6)
    if dice.dice.value != int(call.data[7:]):
        bot.answer_callback_query(call.id, 'Есть пробитие!')
        try:
            bot.ban_chat_member(chat_id, call.from_user.id)
        except:
            bot.answer_callback_query(call.id, 'Играешь нечестно!')
    else:
        bot.answer_callback_query(call.id, 'Не пробил! Попробуй еще')
    bot.delete_message(chat_id, dice.message_id, 3)
    bot.delete_message(chat_id, call.message.message_id)


@bot.message_handler(commands=['balance'])
def balance(message):
    if message.chat.id not in chat_users_money or message.from_user.id not in chat_users_money[message.chat.id]:
        bot.reply_to(message,
                     "У тебя нет баланса. Ты можешь получить свои 35 coin'ов: /roll")
        return

    bot.reply_to(message,
                 f"У тебя на счету: {chat_users_money[message.chat.id][message.from_user.id][0]}, твоя ставка: {chat_users_money[message.chat.id][message.from_user.id][1]}")


@bot.message_handler(commands=['stake'])
def change_stake(message):
    if message.chat.id not in chat_users_money or message.from_user.id not in chat_users_money[message.chat.id]:
        bot.reply_to(message, "Введи: /roll, чтобы активировать баланс")
        return

    if len(message.text.split()) != 2 or not message.text.split()[1].isdigit():
        bot.reply_to(message, "Неправильный ввод. Нужно: /stake *int (> 0)*")
        return

    if int(message.text.split()[1]) <= 0:
        bot.reply_to(message, "Учёл)")
        return

    if int(message.text.split()[1]) > chat_users_money[message.chat.id][message.from_user.id][0]:
        bot.reply_to(message, "Ты балик чекал?")
        return

    chat_users_money[message.chat.id][message.from_user.id][1] = int(message.text.split()[1])
    bot.reply_to(message, f"Твоя ставка: {int(message.text.split()[1])}")


@bot.message_handler(commands=['roll'])
def casino(message):
    if message.chat.id not in chat_users_money:
        chat_users_money[message.chat.id] = dict()
    if message.from_user.id not in chat_users_money[message.chat.id]:
        chat_users_money[message.chat.id][message.from_user.id] = [35, 5]
        if message.chat.id not in chat_users_with_id:
            chat_users_with_id[message.chat.id] = dict()
        if '@' + message.from_user.username not in chat_users_with_id[message.chat.id]:
            chat_users_with_id[message.chat.id]['@' + message.from_user.username] = message.from_user.id

    if chat_users_money[message.chat.id][message.from_user.id][0] < \
            chat_users_money[message.chat.id][message.from_user.id][1]:
        bot.reply_to(message, 'Чекал балик?')
        return

    chat_users_money[message.chat.id][message.from_user.id][0] -= \
        chat_users_money[message.chat.id][message.from_user.id][1]
    roll = bot.send_dice(message.chat.id, emoji="🎰")
    time.sleep(3)
    if roll.dice.value in [1, 22, 43]:
        chat_users_money[message.chat.id][message.from_user.id][0] += 5 * chat_users_money[message.chat.id][
            message.from_user.id][1]
        msg = bot.reply_to(message,
                           f'Выигрыш: {5 * chat_users_money[message.chat.id][message.from_user.id][1]}. Твой баланс: {chat_users_money[message.chat.id][message.from_user.id][0]}')
    elif roll.dice.value == 64:
        chat_users_money[message.chat.id][message.from_user.id][0] += 10 * chat_users_money[message.chat.id][
            message.from_user.id][1]
        msg = bot.reply_to(message,
                           f'Выигрыш: {10 * chat_users_money[message.chat.id][message.from_user.id][1]}. Твой баланс: {chat_users_money[message.chat.id][message.from_user.id][0]}')
    else:
        msg = bot.reply_to(message,
                           f"Ты проиграл {chat_users_money[message.chat.id][message.from_user.id][1]}. Твой баланс: {chat_users_money[message.chat.id][message.from_user.id][0]}")

    time.sleep(2)
    bot.delete_message(message.chat.id, message.message_id, timeout=3)
    bot.delete_message(message.chat.id, roll.message_id, timeout=3)
    bot.delete_message(message.chat.id, msg.message_id, timeout=3)


@bot.message_handler(commands=['give'])
def give(message):
    if len(message.text.split()) != 3 or not message.text.split()[2].isdigit():
        bot.reply_to(message, f'Неправильная комманда. Нужно: /give <all/@<username>> <int>')
        return

    try:
        if bot.get_chat_member(message.chat.id, message.from_user.id).status == 'member':
            bot.reply_to(message, f'Только одмины могут пополнять балик')
            return

        add = int(message.text.split()[2])
        if message.text.split()[1] == 'all':
            if message.chat.id not in chat_users_money:
                chat_users_money[message.chat.id] = dict()
                return
            for user in chat_users_money[message.chat.id]:
                chat_users_money[message.chat.id][user][0] += add
        elif message.text.split()[1] not in chat_users_with_id[message.chat.id]:
            bot.reply_to(message, "Нет такого пользователя")
            return
        else:
            chat_users_money[message.chat.id][chat_users_with_id[message.chat.id][message.text.split()[1]]][0] += add
        bot.reply_to(message, 'Successful give away!')
    except:
        bot.reply_to(message, "Something went wrong")


# Start polling
while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except:
        continue
