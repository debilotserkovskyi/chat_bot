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

WELCOME, YES, YALLA, EMAIL, LOCATION, LOC_CHECK, LIKE, COOK, WOULD_LOVE, SHOPPING = range(10)
WHERE, TOP, FAV, BUDGET, PAIN = range(10, 15)

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


# >>>>>>>>>>>>>>>>>>>>>>> stores allergies and asks about cooking
def fifth_que(update: Update, context: CallbackContext):
    context.user_data['allegies'] = update.message.text
    if update.message.text:
        update.message.reply_text('do you love to cook?',
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('y', callback_data='y')],
                                                                     [InlineKeyboardButton('n', callback_data='n')]]))
        return COOK


# >>>>>>>>>>>>>>>>>>>>>>> stores answer and asks about shopping
def eighth_que(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == 'y':
        context.user_data['cook'] = 'YES'
        context.bot.edit_message_text('do you enjoy food shopping?',
                                      reply_markup=InlineKeyboardMarkup(
                                          [[InlineKeyboardButton('yep', callback_data='y')],
                                           [InlineKeyboardButton('hate', callback_data='n')]]
                                      ),
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)
        return SHOPPING
    elif query.data == 'n':
        context.user_data['cook'] = 'nope'
        context.bot.edit_message_text('would you like to start loving it?😉',
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('y', callback_data='y')],
                                                                         [InlineKeyboardButton('n', callback_data='n')]]
                                                                        ),
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)
        return WOULD_LOVE


# >>>>>>>>>>>>>>>>>>>>>>> if user dont like to cook and asks about shoping
def would_you(update: Update, context: CallbackContext):
    update.callback_query.answer()
    if update.callback_query.data == 'y':
        context.user_data['cook_study'] = 'I would like'
    elif update.callback_query.data == 'n':
        context.user_data['cook_study'] = 'never'
        context.bot.edit_message_text('sad :(',
                                      reply_markup=None,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)
    
    context.bot.edit_message_text('do you enjoy food shopping?',
                                  reply_markup=InlineKeyboardMarkup(
                                      [[InlineKeyboardButton('yep', callback_data='y')],
                                       [InlineKeyboardButton('hate', callback_data='n')]]
                                  ),
                                  chat_id=update.effective_chat.id,
                                  message_id=update.effective_message.message_id)
    return SHOPPING


# >>>>>>>>>>>>>>>>>>>>>>> stores answer and asks goes to top-4
def nineth_que(update: Update, context: CallbackContext):
    update.callback_query.answer()
    
    if update.callback_query.data == 'y':
        context.user_data['shoping'] = 'I do'
        context.bot.edit_message_text(text='where do you usually buy stuff: markets, supermarkets etc.?',
                                      reply_markup=None,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)
        return WHERE
    elif update.callback_query.data == 'n':
        context.user_data['shoping'] = "I don't"
    
    context.bot.edit_message_text(text='top-4 your last or most common orders in restaurant/wolt',
                                  reply_markup=None,
                                  chat_id=update.effective_chat.id,
                                  message_id=update.effective_message.message_id)
    return TOP


# >>>>>>>>>>>>>>>>>>>>>>> if he likes asks where user buys and goes to top-4
def where_shop(update: Update, context: CallbackContext):
    context.user_data['where'] = update.message.text
    update.message.reply_text(text='top-4 your last or most common orders in restaurant/wolt',
                              reply_markup=None)
    return TOP


# >>>>>>>>>>>>>>>>>>>>>>> stores answer about top4 and goes to fav
def tenth_que(update: Update, context: CallbackContext):
    context.user_data['top-4'] = update.message.text
    update.message.reply_text(text='do you have your favorite/traditional meals? '
                                   '(ex. if you’re eating same kind of breakfast everyday)')
    return FAV


# >>>>>>>>>>>>>>>>>>>>>>> stores answer about fav and goes to budget
def eleventh_que(update: Update, context: CallbackContext):
    context.user_data['fav'] = update.message.text
    print(context.user_data)
    update.message.reply_text(text="budget. how much money you spend or want to spend for food per one week?")
    return BUDGET


# >>>>>>>>>>>>>>>>>>>>>>> stores answer about budget and goes to budget
def twelfth_que(update: Update, context: CallbackContext):
    context.user_data['budget'] = update.message.text
    solve = [[InlineKeyboardButton('no, i just want to diversify my daily menu', callback_data='no_just')],
             [InlineKeyboardButton('i changed my diet/became vegan  🌱 and need to find a menu '
                                   'solution for catching all the nutrients', callback_data='changed_diet')],
             [InlineKeyboardButton("i have a strong problem with not having a good lunch in"
                                   "the middle of working day", callback_data='problem')],
             [InlineKeyboardButton("i don’t like/have time for cooking", callback_data='time')],
             [InlineKeyboardButton("i want to spent less money on my food", callback_data="less_money")],
             [InlineKeyboardButton("another pain", callback_data='another')]
             ]
    update.message.reply_text(text="if there’s any pain about food you want to solve?",
                              reply_markup=InlineKeyboardMarkup(solve))
    return PAIN


# >>>>>>>>>>>>>>>>>>>>>>> stores answer about budget and goes to budget
def pain(update: Update, context: CallbackContext):
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
            WOULD_LOVE: [CallbackQueryHandler(would_you)],
            SHOPPING: [CallbackQueryHandler(nineth_que)],
            WHERE: [MessageHandler(Filters.text, where_shop)],
            TOP: [MessageHandler(Filters.text, tenth_que)],
            FAV: [MessageHandler(Filters.text, eleventh_que)],
            BUDGET: [MessageHandler(Filters.text, twelfth_que)],
            PAIN: [CallbackQueryHandler(pain)],
    
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
