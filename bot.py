import datetime
import logging
import os
import random
import time

import requests
from telegram import *
from telegram.ext import *

from data import data

TOKEN = os.environ['TELEGRAM_TOKEN']
ADMIN = os.environ['USER_ID']
resend = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={ADMIN}&text='

BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
allowed_usernames = list(data.keys())
admins = []

logged = 0


def start_command(update, context):
    update.message.reply_text("it's me, your pocket lina!\nfollow the bot i hope you'll like it")
    update.message.reply_text("or press /help to get info about this bot")
    return user_check(update, context)


def menu(update, context):
    buttons = [[KeyboardButton("/repeat")],
               [KeyboardButton("/contact")],
               [KeyboardButton("/help")],
               ]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='when you will be ready we can tap any button',
                             reply_markup=ReplyKeyboardMarkup(buttons))


def help_command(update, context):
    buttons = [[KeyboardButton("/start")],
               [KeyboardButton("/contact")]]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='if you need help write me in inst or wherever\n'
                                  'also you can start over or get my contacts',
                             reply_markup=ReplyKeyboardMarkup(buttons))


def contact(update, context):
    contact_button = [[InlineKeyboardButton('Instagram', url='https://www.instagram.com/yolkinalina/')],
                      [InlineKeyboardButton('Telegram', url='https://t.me/linayolkina')]]
    reply_markup_start = InlineKeyboardMarkup(contact_button)
    update.message.reply_text("here:", reply_markup=reply_markup_start)


def user_check(update, context):
    text = str(update.message.text).lower()
    username = update.message.from_user.username
    print(username)
    
    if text in ['putin', 'путін', "путин"]:
        if text == 'putin':
            update.message.reply_text('p*tin – huilo')
            time.sleep(1)
            return menu(update, context)
        elif text == 'путін' or 'путин':
            update.message.reply_text('п*тін - хуйло')
            time.sleep(1)
            return menu(update, context)
    
    if text:
        if username == os.environ['boss']:
            context.bot.send_message(text="hehe",
                                     reply_markup=InlineKeyboardMarkup(
                                         [[InlineKeyboardButton('start admin', callback_data='start')]]),
                                     chat_id=update.message.chat.id)
            return generate_buttons(update, context)
        else:
            requests.get(f"{resend}\n"
                         f"messege send: {datetime.datetime.now()}\n"
                         f"from User: @{update.message.from_user.username}\n"
                         f"Message: {text}\n"
                         f"Message id: {update.message.message_id}")
            update.message.reply_text("I'm not actually a real person I'm a bot, so I can't understand what you sent")
            
            # check username and continue
            if username not in allowed_usernames:
                update.message.reply_text(f"Sorry, we don't met yet :( \nPress /contact to make it real")
            else:
                update.message.reply_text(f"hi, {update.message.chat.first_name}")
                return first_buttons(update, context)


def first_buttons(update, context):
    keyboard_start = [[
        InlineKeyboardButton("I want to assemble my bento for tomorrow", callback_data='01'),
    ], [InlineKeyboardButton("I want to see my whole bento menu 🍱 ", callback_data='whole_menu')]
    ]
    reply_markup_start = InlineKeyboardMarkup(keyboard_start)
    update.message.reply_text("what's up? 🧡", reply_markup=reply_markup_start)


def generate_buttons(update: Update, context: CallbackContext):
    keyboard = []
    query = update.callback_query
    username = query.from_user.username
    query.answer()
    choice = query.data
    cat_list = []
    dishes_to_dict = {}
    used = set()
    
    # admin section
    if username == os.environ['boss']:
        return admin_panel(update=update, context=context, choice=choice, keyboard=keyboard, query=query)
    
    # generate whole menu in MENU button + add random button and back button:
    if choice == 'whole_menu':
        for i in data[username]:
            keyboard.append([InlineKeyboardButton(i['name'], callback_data=i['callback'])])
        keyboard.append([InlineKeyboardButton('random', callback_data='random')])
        keyboard.append([InlineKeyboardButton('back', callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                      text="here is your whole menu")
        context.bot.edit_message_reply_markup(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                              reply_markup=reply_markup)
    
    # generate base bento (rice, etc):
    if choice == '01':
        for i in range(len(data[username])):
            cat_list.append(data[username][i]['category'])
            unique_categories = [x for x in cat_list if x not in used and (used.add(x) or True)]
            for category in unique_categories:
                keyboard.append([InlineKeyboardButton(str(category),
                                                      callback_data=data[username][i]['category'])])
        keyboard.append([InlineKeyboardButton('back', callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                      text="chose the bento base")
        context.bot.edit_message_reply_markup(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                              reply_markup=reply_markup)

    for i in data[username]:
        dishes_to_dict[i['category']] = []
    for i in data[username]:
        dishes_to_dict[i['category']].append(i['name'])

    # send ingredients and recipy to the client depends on recipy was chosen
    for i in data[username]:
        if choice in i['callback']:
            context.bot.send_message(text=f'this is a recipy for *{i["name"]}* ',
                                     chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN)
            context.bot.send_message(text=i['ingredients'], chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN)
            time.sleep(2)
            context.bot.send_message(text=i['recipy'], chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN, )
        
        # generate 2 dish names depends on category is
        if choice in i['category']:
            keyboard_new = i['name']
            keyboard.append([InlineKeyboardButton(keyboard_new, callback_data=i['callback'])])
            context.bot.edit_message_reply_markup(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                                  reply_markup=InlineKeyboardMarkup(keyboard))
            if len(keyboard) == len(dishes_to_dict[choice]):
                keyboard.append([InlineKeyboardButton('back', callback_data='01')])
                context.bot.edit_message_reply_markup(chat_id=query.message.chat_id,
                                                      message_id=query.message.message_id,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))
    
    # send a random ingredient and recipy to the client
    if choice == 'random':
        rand = random.randint(0, len(data[username]))
        context.bot.send_message(text=f'hey, maybe {data[username][rand]["name"]} will be nice?',
                                 chat_id=query.message.chat_id,
                                 parse_mode=ParseMode.MARKDOWN)
        context.bot.send_message(text=data[username][rand]['ingredients'], chat_id=query.message.chat_id,
                                 parse_mode=ParseMode.MARKDOWN)
        time.sleep(2)
        context.bot.send_message(text=data[username][rand]['recipy'], chat_id=query.message.chat_id,
                                 parse_mode=ParseMode.MARKDOWN, )
    
    # return to the main menu (dunno and whole menu)
    if choice == 'back':
        keyboard_start = [[
            InlineKeyboardButton("base bento", callback_data='01'),
        ], [InlineKeyboardButton("my WHOLE bento menu", callback_data='whole_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard_start)
        context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                      text="what's up?")
        context.bot.edit_message_reply_markup(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                              reply_markup=reply_markup)


def admin_panel(update: Update, context: CallbackContext, choice, keyboard, query):
    if choice == 'start':
        keyboard.append([InlineKeyboardButton('send message to a user', callback_data='send_message')])
        keyboard.append([InlineKeyboardButton('something else', callback_data='something')])
        context.bot.edit_message_reply_markup(chat_id=query.message.chat_id,
                                              message_id=query.message.message_id,
                                              reply_markup=InlineKeyboardMarkup(keyboard))
    
    if choice == 'send_message':
        keyboard.append([InlineKeyboardButton('see all users', callback_data='all_users')])
        context.bot.edit_message_reply_markup(chat_id=query.message.chat_id,
                                              message_id=query.message.message_id,
                                              reply_markup=InlineKeyboardMarkup(keyboard))
    if choice == 'all_users':
        for i in data.keys():
            keyboard.append([InlineKeyboardButton(i, callback_data=i)])
        keyboard.append([InlineKeyboardButton('back', callback_data='send_message')])
        context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                      text="choose a user")
        context.bot.edit_message_reply_markup(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                              reply_markup=InlineKeyboardMarkup(keyboard))
    for i in data.keys():
        if choice == i:
            context.bot.send_message(text=f'@{i}', chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN)


def error(update, context):
    print(f"\nupdate {update} \ncaused error {context.error}\n")


def questionnaire():
    pass


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start_command))
    dp.add_handler(CommandHandler('help', help_command))
    dp.add_handler(CommandHandler('contact', contact))
    dp.add_handler(CommandHandler('repeat', first_buttons))

    dp.add_handler(CommandHandler('admin', admin_panel))
    
    dp.add_handler(MessageHandler(Filters.text, user_check))
    dp.add_handler(CallbackQueryHandler(generate_buttons))
    
    dp.add_error_handler(error)
    
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
