import random
import time
import datetime

from telegram import *
from telegram.ext import *
import bot_token as keys
import logging

# dictionary with data
from data import data


allowed_usernames = list(data.keys())

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def start_command(update, context):
    update.message.reply_text("hi! it's me, your pocket lina!\nfollow the bot i hope you'll like it")
    update.message.reply_text("or press /help to get info about this bot")
    return user_check(update, context)


def menu(update, context):
    buttons = [[KeyboardButton("/repeat")],
               [KeyboardButton("/contact")],
               [KeyboardButton("/help")],
               ]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='When you will be ready we can tap any button',
                             reply_markup=ReplyKeyboardMarkup(buttons))


def help_command(update, context):
    buttons = [[KeyboardButton("/start")],
               [KeyboardButton("/contact")]]
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='if you need help write me in inst or wherever\n'
                                  'also you can startover or get my contacts',
                             reply_markup=ReplyKeyboardMarkup(buttons))


def contact(update, context):
    contact_button = [[InlineKeyboardButton('Instagram', url='https://www.instagram.com/yolkinalina/')],
                      [InlineKeyboardButton('Telegramm', url='https://t.me/linayolkina')]]
    reply_markup_start = InlineKeyboardMarkup(contact_button)
    update.message.reply_text("here:", reply_markup=reply_markup_start)


def user_check(update, context):
    text = str(update.message.text).lower()
    username = update.message.from_user.username
    print(username)
    
    with open('loggins.txt', 'a') as f:
        f.write(f'\n {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}: {username}\n')
    
    if text in ['putin', 'путін', "путин"]:
        update.message.reply_text('p*tin – huilo')
    
    if username not in allowed_usernames:
        update.message.reply_text(f"Sorry, we don't met yet :( \nPress /contact to make it real")
    else:
        update.message.reply_text(f"hi, {update.message.chat.first_name}")
        return first_buttons(update, context)


def first_buttons(update, context):
    keyboard_start = [[
        InlineKeyboardButton("i dunno what to eat", callback_data='01'),
    ], [InlineKeyboardButton("MENU", callback_data='whole_menu')]
    ]
    reply_markup_start = InlineKeyboardMarkup(keyboard_start)
    update.message.reply_text("what's up?", reply_markup=reply_markup_start)


def generate_buttons(update: Update, context: CallbackContext):
    keyboard = []
    query = update.callback_query
    username = query.from_user.username
    query.answer()
    choice = query.data
    
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
    
    # generate how hungry you are range buttons (1-2, 2-3 etc):
    if choice == '01':
        for i in range(len(data[username])):
            if (i + 1) % 2 == 0:
                keyboard.append([InlineKeyboardButton(data[username][i]['category'],
                                                      callback_data=data[username][i - 1]['category'])])
        keyboard.append([InlineKeyboardButton('back', callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                      text="how hungry u are?")
        context.bot.edit_message_reply_markup(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                              reply_markup=reply_markup)
    
    for i in data[username]:
        # send ingredients and recipy to the client depends on recipy was chosen
        if choice in i['callback']:
            context.bot.send_message(text=f'this is a recipy for *{i["name"]}* ',
                                     chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN)
            context.bot.send_message(text=i['ingredients'], chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN)
            time.sleep(2)
            context.bot.send_message(text=i['recipy'], chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN, )
        
        # generate 2 dish names depends on how hungry he is
        if choice in i['category']:
            keyboard_new = i['name']
            keyboard.append([InlineKeyboardButton(keyboard_new, callback_data=i['callback'])])
            context.bot.edit_message_reply_markup(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                                  reply_markup=InlineKeyboardMarkup(keyboard))
            if len(InlineKeyboardMarkup(keyboard)['inline_keyboard']) == 2:
                keyboard.append([InlineKeyboardButton('back', callback_data='01')])
                context.bot.edit_message_reply_markup(chat_id=query.message.chat_id,
                                                      message_id=query.message.message_id,
                                                      reply_markup=InlineKeyboardMarkup(keyboard))
    
    # send a random ingr and recipy to the client
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
            InlineKeyboardButton("i dunno what to eat", callback_data='01'),
        ], [InlineKeyboardButton("MENU", callback_data='whole_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard_start)
        context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                      text="what's up?")
        context.bot.edit_message_reply_markup(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                              reply_markup=reply_markup)


def error(update, context):
    print(f"update {update} \ncaused error {context.error}")


def repeat(update, context):
    time.sleep(1)
    menu(update, context)


def main():
    updater = Updater(keys.API_KEY, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(MessageHandler(Filters.text, user_check))
    
    dp.add_handler(CommandHandler('start', start_command))
    dp.add_handler(CommandHandler('repeat', first_buttons))
    dp.add_handler(CommandHandler('dish1', start_command))
    dp.add_handler(CallbackQueryHandler(generate_buttons))
    dp.add_handler(CommandHandler('help', help_command))
    dp.add_handler(CommandHandler('contact', contact))
    
    dp.add_error_handler(error)
    
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
