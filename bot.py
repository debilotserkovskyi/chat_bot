import logging
import os
from re import match

import telegram
from telegram import *
from telegram.ext import *

from data import data

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_GEO = os.environ.get('geo_api')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

WELCOME, YES, YALLA, EMAIL, LOCATION = range(5)

HI = range(4, 5)


def start(update: Update, context):
    user = update.effective_message.from_user.username
    if user not in data.keys():
        return wanna_buy(update, context)
    else:
        return watsup(update, context)


# --------------------------------------------------------------------
def wanna_buy(update: Update, context):
    reply_markup = [[InlineKeyboardButton('YES', callback_data='YES')],
                    [InlineKeyboardButton('contact', callback_data='contact')]]
    update.effective_message.reply_text(text='hey, foodie🧡 welcome to ALTER | NATIVE | PROJECT. wanna buy a menu?',
                                        reply_markup=InlineKeyboardMarkup(reply_markup))
    return WELCOME


def first_que(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    print(query.data)
    if query.data == 'YES':
        yalla_b = [[InlineKeyboardButton('yalla', callback_data='yalla')]]
        context.bot.edit_message_text(
            text='oh yeah! so get ready for a food questionnaire to create your menu the most '
                 'suitable to your FOOD LIFESTYLE, your tastes and the current season.',
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
            reply_markup=InlineKeyboardMarkup(yalla_b))
    
    if query.data == 'contact':
        contact_button = [[InlineKeyboardButton('Instagram', url='https://www.instagram.com/yolkinalina/')],
                          [InlineKeyboardButton('Telegram', url='https://t.me/linayolkina')]]
        reply_markup_start = InlineKeyboardMarkup(contact_button)
        context.bot.send_message(text="here:", reply_markup=reply_markup_start,
                                 chat_id=update.effective_chat.id)
        return cancel(update, context)
    
    return YES


def yalla(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == 'yalla':
        context.bot.edit_message_text(text='first, let me get to know you:) what’s your name and surname?'
                                           '\n(type everything in one message)',
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=None)
    return YALLA


def second_que(update: Update, context: CallbackContext):
    context.user_data['name'] = update.message.text
    if update.message.text:
        context.bot.send_message(text='e-mail?',
                                 chat_id=update.effective_chat.id)
        return EMAIL


def third_que(update: Update, context: CallbackContext):
    pattern = '^(?:(?!.*?[.]{2})[a-zA-Z0-9](?:[a-zA-Z0-9.+!%-]{1,64}|)|\"[a-zA-Z0-9.+!% -]{1,64}\")@[a-zA-Z0-9]' \
              '[a-zA-Z0-9.-]+(.[a-z]{2,}|.[0-9]{1,})$'
    
    if match(pattern, update.message.text):
        context.user_data['email'] = update.message.text
        loc = [[KeyboardButton('send location', request_location=True, )]]
        context.bot.send_message(text='ok!\ncountry and city you currently reside?(u may use button location)',
                                 chat_id=update.effective_chat.id,
                                 reply_markup=ReplyKeyboardMarkup(loc, one_time_keyboard=True))
        
        return LOCATION
    else:
        context.bot.send_message(text="i can't understand this email, try again plz",
                                 chat_id=update.effective_chat.id)
        return EMAIL


def forth_que(update: Update, context: CallbackContext):
    if update.message.text is not None:
        context.user_data['location'] = update.message.text
    else:
        lat = context.user_data['location_lat'] = update.message.location.latitude
        lon = context.user_data['location_long'] = update.message.location.longitude
        telegram.ReplyKeyboardRemove(True)


# --------------------------------------------------------------------
def watsup(update: Update, context):
    user = update.effective_message.from_user.username
    reply_markup = [[InlineKeyboardButton('I want to assemble my bento for tomorrow', callback_data='see_categories')],
                    [InlineKeyboardButton('see whole bento menu', callback_data='see_whole')]]
    update.effective_message.reply_text(text=f"hey,{user}, what's up?", reply_markup=InlineKeyboardMarkup(reply_markup))
    return HI


def buttons(update: Update, contex: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == 'see_categories':
        print('YOU DID IT')


# --------------------------------------------------------------------
def error(update, context):
    print("-" * 10, 'ERROR', '-' * 10)
    print(f"\nupdate {update} \ncaused error {context.error}\n")
    print("-" * 10, 'ERROR', '-' * 10)


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Name Conversation cancelled by user. Bye. Send /set_name to start again')
    return ConversationHandler.END


def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_error_handler(error)
    
    conv_handler_new_user = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            # new user:
            WELCOME: [CallbackQueryHandler(first_que)],
            YES: [CallbackQueryHandler(yalla)],
            YALLA: [MessageHandler(Filters.text, second_que)],
            EMAIL: [MessageHandler(Filters.text, third_que)],
            LOCATION: [MessageHandler(Filters.text | Filters.location, forth_que)],
            
            # existing user:
            HI: [CallbackQueryHandler(buttons)],
        },
        fallbacks=[CommandHandler('stop', cancel)]
    )
    
    dp.add_handler(conv_handler_new_user)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()