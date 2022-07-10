import logging
import os
from re import match

from opencage.geocoder import OpenCageGeocode
from telegram import *
from telegram.ext import *

from data import data

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_GEO = os.environ.get('geo_api')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

WELCOME, YES, YALLA, EMAIL, LOCATION, LOC_CHECK, LIKE = range(7)
COOK, SHOPPING = range(8, 10)

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


# >>>>>>>>>>>>>>>>>>>>>>> check first question and moving to second one
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


# >>>>>>>>>>>>>>>>>>>>>>> check if user pressed yalla button and going to third one
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


# >>>>>>>>>>>>>>>>>>>>>>> getting name and ask about email
def second_que(update: Update, context: CallbackContext):
    context.user_data['name'] = update.message.text
    if update.message.text:
        context.bot.send_message(text='e-mail?',
                                 chat_id=update.effective_chat.id)
        return EMAIL


# >>>>>>>>>>>>>>>>>>>>>>> checking email and goes to location
def third_que(update: Update, context: CallbackContext):
    pattern = '^(?:(?!.*?[.]{2})[a-zA-Z0-9](?:[a-zA-Z0-9.+!%-]{1,64}|)|\"[a-zA-Z0-9.+!% -]{1,64}\")@[a-zA-Z0-9]' \
              '[a-zA-Z0-9.-]+(.[a-z]{2,}|.[0-9]{1,})$'
    
    if match(pattern, update.message.text):
        context.user_data['email'] = update.message.text
        loc = [[KeyboardButton('send location', request_location=True, )]]
        context.bot.send_message(text='ok!\ncountry and city you currently reside?(u may use button location)',
                                 chat_id=update.effective_chat.id,
                                 reply_markup=ReplyKeyboardMarkup(loc))
        
        return LOCATION
    else:
        context.bot.send_message(text="i can't understand this email, try again plz",
                                 chat_id=update.effective_chat.id)
        return EMAIL


# >>>>>>>>>>>>>>>>>>>>>>> checks location and moving forward
def forth_que(update: Update, context: CallbackContext):
    if update.message.text:
        print(1)
        context.user_data['location'] = update.message.text
        update.message.reply_text('do you have allergies or products you don’t like (and even hate)?\n'
                                  'write it down in a single message',
                                  reply_markup=None)
        return LIKE
    elif update.message.location:
        print(2)
        lat = context.user_data['location_lat'] = update.message.location.latitude
        lon = context.user_data['location_long'] = update.message.location.longitude
        geo_coder = OpenCageGeocode(API_GEO)
        results = geo_coder.reverse_geocode(lat, lon)
        
        context.bot.send_message(text=f"so, you are in {results[0]['components']['country']}, "
                                      f"{results[0]['components']['state']}, {results[0]['components']['town']}, "
                                      f"right?",
                                 chat_id=update.effective_chat.id,
                                 reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('y', callback_data='y')],
                                                                    [InlineKeyboardButton('n', callback_data='n')]]))
        context.user_data['country'] = results[0]['components']['country']
        context.user_data['state'] = results[0]['components']['state']
        context.user_data['town'] = results[0]['components']['town']
        return LOC_CHECK


# >>>>>>>>>>>>>>>>>>>>>>> if user sent loc we're checking if it's right and asks about hates
def loc_check(update: Update, context: CallbackContext):
    print(3)
    query = update.callback_query
    query.answer()
    if query.data == 'y':
        context.bot.edit_message_text('do you have allergies or products you don’t like (and even hate)?\n'
                                      'write it down in a single message',
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=None)
        return LIKE
    elif query.data == 'n':
        context.bot.edit_message_text('then maybe try to write it manually?',
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=None)
        return LOCATION


# >>>>>>>>>>>>>>>>>>>>>>> check if user pressed yalla button and going to third one
def fifth_que(update: Update, context: CallbackContext):
    print(4)
    print(context.user_data)
    print(update.effective_chat.id)
    context.user_data['allegies'] = update.message.text
    if update.message.text:
        update.message.reply_text('do you love to cook?',
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('y', callback_data='y')],
                                                                     [InlineKeyboardButton('n', callback_data='n')]]))
        return COOK


def eighth_que(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == 'y':
        return SHOPPING
    elif query.data == 'n':
        context.bot.edit_message_text('would you like to start loving it?😉',
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('y', callback_data='y')],
                                                                         [InlineKeyboardButton('n', callback_data='n')]]
                                                                        ),
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)


def nineth_que(update: Update, context: CallbackContext):
    pass


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
            LOC_CHECK: [CallbackQueryHandler(loc_check)],
            LIKE: [MessageHandler(Filters.text, fifth_que)],
            COOK: [CallbackQueryHandler(eighth_que)],
            SHOPPING: [CallbackQueryHandler(nineth_que)],
    
            # existing user:
            HI: [CallbackQueryHandler(buttons)],
        },
        fallbacks=[CommandHandler('stop', cancel)],
    )
    
    dp.add_handler(conv_handler_new_user)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
