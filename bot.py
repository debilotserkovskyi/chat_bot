from __future__ import print_function

import datetime
import logging
import os
# import pickle
import random
import threading
import time
from re import match

import gspread
import gspread_dataframe as gdf
import pandas as pd
from opencage.geocoder import OpenCageGeocode
from telegram import *
from telegram.ext import *

# ----------------------------------------------------------------------------------------------------------------------
#                                                   VARIABLES
# ----------------------------------------------------------------------------------------------------------------------

global data, user, id_
global must_delete, pains_dict, edit

# reading google sheet json
service_account = gspread.service_account(filename='alter-data-96722a9a7e3b.json')
sh = service_account.open('alter data')  # open sheet
wk_answers = sh.worksheet('2022')  # sheet with user's answers
wk_user = sh.worksheet('users')  # sheet with usernames and id
wk_recipes = sh.worksheet('recipes')  # sheet with user's recipes

# sheet data to pandas
df_answers = pd.DataFrame(wk_answers.get_all_records())
df_users = pd.DataFrame(wk_user.get_all_records())
df_recipes = pd.DataFrame(wk_recipes.get_all_records())

# tokens tg and geo service
TELEGRAM_TOKEN, API_GEO = os.environ.get('TELEGRAM_TOKEN'), os.environ.get('geo_api')

# logs
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# new user vars
WELCOME, YES, YALLA, EMAIL, LOCATION, LOC_CHECK, LIKE, COOK, WOULD_LOVE, SHOPPING = range(10)
WHERE, TOP, FAV, BUDGET, PAIN, ANOTHER_PAIN, CHECKING, CHANGE, CHANGING_NAME = range(10, 19)

# old user vars
HI, CATEGORY, DISH = range(20, 23)

# admin vars
ADMIN, SEND_MESSAGE, SEND_MESSAGE_TXT, SENDING, DATA, PICKED, DATA_CHANGE, NEW_USER, DATA_CHANGE_2 = range(30, 39)
DATA_CHANGE_3, WHAT_CHANGE, SAVE_UPDATE, INTERFACE, NUMBER, CHANGE_USER, DEL_CHANGE, DEL_CHANGE2 = range(40, 48)
CHANGE_USERNAME, ADD_CATEGORY, ADD_INGR, ADD_RECIPY, SEND_DOCUMENT = range(50, 55)


# ----------------------------------------------------------------------------------------------------------------------
#                                                      /START
# ----------------------------------------------------------------------------------------------------------------------


def start(update: Update, context: CallbackContext):
    global data, user, id_, df_answers, df_users
    user = update.effective_message.from_user.username  # get username
    id_ = update.effective_user.id  # get user id
    context.user_data['id'] = id_
    context.user_data['username'] = user
    update_answers(update, context)
    if user == 'linayolkina' or user == 'deadpimp':
        return admin(update, context)
    elif user not in df_recipes['user'].unique().tolist() or id_ not in df_users['id'].unique().tolist():
        if id_ not in df_users['id'].unique().tolist():
            df_users.loc[len(df_users)] = [id_, user]
        
            def saving():
                threading.Timer((60.0 * 5), saving).start()
                gdf.set_with_dataframe(wk_answers, df_answers)
                gdf.set_with_dataframe(wk_user, df_users)
                print('done')
        
            saving()
    
        return wanna_buy(update, context)
    
    else:
        return wats_up(update, context)


# ----------------------------------------------------------------------------------------------------------------------
#                                                       NEW USER
# ----------------------------------------------------------------------------------------------------------------------


# >>>>>>>>>>>>>>> greetings after /start pressed <<<<<<<<<<<<<<<
def wanna_buy(update: Update, context: CallbackContext):
    reply_markup = [[InlineKeyboardButton('YES', callback_data='YES')],
                    [InlineKeyboardButton('wanna contact Lina first', callback_data='contact')],
                    [InlineKeyboardButton('want to read about the project', callback_data='read about')]]
    # df_answers.loc[len(df_answers)] = [id_, user]
    
    update.effective_message.reply_text(text='hey, foodie🧡 welcome to ALTER | NATIVE | FOOD\nwanna buy a menu?',
                                        reply_markup=InlineKeyboardMarkup(reply_markup))
    
    return WELCOME


# >>>>>>>>>>>>>>> first callback func <<<<<<<<<<<<<<<
def first_que(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    # run conv handler (questioner)
    if query.data == 'YES':
        context.bot.edit_message_text(
            text='oh yeah\\!🤘🏻\n\nso get ready for a *food questionnaire* to create your menu the most suitable to '
                 'your FOOD LIFESTYLE, your tastes and the current season\\.',
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('yalla', callback_data='yalla')]])
        )

    # send contact links
    elif query.data == 'contact':
        contact_button = [[InlineKeyboardButton('Instagram', url='https://www.instagram.com/yolkinalina/'),
                           InlineKeyboardButton('Telegram', url='https://t.me/linayolkina')]]
    
        reply_markup_start = InlineKeyboardMarkup(contact_button)
    
        context.bot.edit_message_text(text="here:", reply_markup=reply_markup_start,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)
    
        return cancel(update, context)

    # send information about the project
    elif query.data == 'read about':
        txt = '''
ALTER | NATIVE | FOOD is about your personal food education. There are 4 different levels of it - products you can buy.

LEVEL 1

ALTER | NATIVE | MENU a customized menu, based on your food preferences, place you live and its local seasonal food.
10 positions of your own menu. made exclusively by @linayolkina , designed as a culinary magazine. costs 350 shek.


LEVEL 2

ALTER | NATIVE | DELIVERY is combination of ALTER | NATIVE | MENU and delivery of all the grocery list of it to your
house. all the products hand assembled from Shuk HaCarmel (available only in Israel). costs 500 shek + price of the
products

LEVEL 3

ALTER | NATIVE | GOAL is for you if you have an appropriate pain toward to food or for couples/families. during two
weeks we are finding the best solution for you, using different tools and making your FOOD PORTRAIT best and
satisfying for you. costs 850 shek

LEVEL 4

ALTER | NATIVE | PREMIUM including ALTER | NATIVE | MENU + a FOOD DATE with @linayolkina, where you’re going to
market, learning how to pick the best stuff and cooking together. Private master-class of cooking based on the menu
you’ve got for you.'''

        context.bot.edit_message_text(text=txt,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)

        return cancel(update, context)
    
    return YES


# >>>>>>>>>>>>>>> if 'YALLA' button pressed send first question - name <<<<<<<<<<<<<<<
def yalla(update: Update, context: CallbackContext):
    update.callback_query.answer()

    if update.callback_query.data == 'yalla':
        context.user_data['in a process'] = True

        context.bot.edit_message_text(
            text='first, let me get to know you:\\) \n\n*what’s your name and surname?*\n\n\\(type everything in one '
                 'message\\)',
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
            reply_markup=None,
            parse_mode=ParseMode.MARKDOWN_V2)

    update_answers(update, context)
    return YALLA


# >>>>>>>>>>>>>>> store name and ask email <<<<<<<<<<<<<<<
def second_que(update: Update, context: CallbackContext):
    context.user_data['name'] = update.message.text

    if update.message.text:
        context.bot.send_message(text='e-mail?', chat_id=update.effective_chat.id)
        update_answers(update, context)

        return EMAIL


# >>>>>>>>>>>>>>> checking email and ask about location <<<<<<<<<<<<<<<
def third_que(update: Update, context: CallbackContext):
    context.chat_data['pattern'] = \
        '^(?:(?!.*?[.]{2})[a-zA-Z0-9](?:[a-zA-Z0-9.+!%-]{1,64}|)|\"[a-zA-Z0-9.+!% -]{1,64}\")@[a-zA-Z0-9]' \
        '[a-zA-Z0-9.-]+(.[a-z]{2,}|.[0-9]{1,})$'

    if match(context.chat_data['pattern'], update.message.text):
        context.user_data['email'] = update.message.text
        loc = [[KeyboardButton('send location', request_location=True, )]]

        context.bot.send_message(
            text='ok\\!\n\n*country and city you currently reside?*\n\n\\(u may use button location\\)',
            chat_id=update.effective_chat.id,
            reply_markup=ReplyKeyboardMarkup(loc),
            parse_mode=ParseMode.MARKDOWN_V2)
        update_answers(update, context)

        return LOCATION

    else:
        context.bot.send_message(text="i can't understand this email, try again plz", chat_id=update.effective_chat.id)

        return EMAIL


# >>>>>>>>>>>>>>> checks location depend on type and ask about allergies <<<<<<<<<<<<<<<
def forth_que(update: Update, context: CallbackContext):
    if update.message.text:
        context.user_data['location'] = update.message.text

        update.message.reply_text('*do you have allergies or products you don’t like \\(and even hate\\)?*\n\n'
                                  'write it down in a single message',
                                  reply_markup=None,
                                  parse_mode=ParseMode.MARKDOWN_V2)

        return LIKE
    
    elif update.message.location:
        geo_coder = OpenCageGeocode(API_GEO)
        results = geo_coder.reverse_geocode(update.message.location.latitude, update.message.location.longitude)
        # print(results)
        
        context.bot.send_message(text=f"so, you are in {results[0]['formatted']}, *right?*",
                                 chat_id=update.effective_chat.id,
                                 parse_mode=ParseMode.MARKDOWN_V2,
                                 reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('y', callback_data='y'),
                                                                     InlineKeyboardButton('n', callback_data='n')]])
                                 )
        
        context.user_data['location'] = results[0]['formatted']
        update_answers(update, context)
        
        return LOC_CHECK


# >>>>>>>>>>>>>>> if type is .location user check it through geo api and bot ask about allergies <<<<<<<<<<<<<<<
def loc_check(update: Update, context: CallbackContext):
    update.callback_query.answer()

    if update.callback_query.data == 'y':
    
        context.bot.edit_message_text(
            '*do you have allergies or products you don’t like \\(and even hate\\)*?\n\n'
            'write it down in a single message',
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=None)
    
        return LIKE

    elif update.callback_query.data == 'n':
    
        context.bot.edit_message_text('then maybe try to write it manually?',
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=None)
    
        return LOCATION


# >>>>>>>>>>>>>>> store allergies and ask about cooking <<<<<<<<<<<<<<<
def fifth_que(update: Update, context: CallbackContext):
    context.user_data["allergies or products I don't like"] = update.message.text
    update_answers(update, context)

    if update.message.text:
        update.message.reply_text('do you love to cook?',
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('y', callback_data='y'),
                                                                      InlineKeyboardButton('n', callback_data='n')]]))
    
        return COOK


# >>>>>>>>>>>>>>> store callback and ask about shopping <<<<<<<<<<<<<<<
def eighth_que(update: Update, context: CallbackContext):
    update.callback_query.answer()
    
    if update.callback_query.data == 'y':
        context.user_data['cooking'] = 'YES'

        context.bot.edit_message_text('do you enjoy food shopping?',
                                      reply_markup=InlineKeyboardMarkup(
                                          [[InlineKeyboardButton('yep', callback_data='y'),
                                            InlineKeyboardButton('hate', callback_data='n')]]),
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)

        update_answers(update, context)
        return SHOPPING

    elif update.callback_query.data == 'n':
        context.user_data['cooking'] = 'no'

        context.bot.edit_message_text('would you like to start loving it?😉',
                                      reply_markup=InlineKeyboardMarkup(
                                          [[InlineKeyboardButton('yep', callback_data='y'),
                                            InlineKeyboardButton('nope', callback_data='n')]]),
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)

        update_answers(update, context)
        return WOULD_LOVE


# >>>>>>>>>>>>>>> if 'n' react on it and ask about shopping <<<<<<<<<<<<<<<
def would_you(update: Update, context: CallbackContext):
    update.callback_query.answer()

    if update.callback_query.data == 'y':
        context.user_data['wanna learn?'] = 'I would like'

    elif update.callback_query.data == 'n':
        context.user_data['wanna learn?'] = 'never'
        context.bot.edit_message_text('sad :(',
                                      reply_markup=None,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING,
                                     timeout=1)
        time.sleep(2)

    context.bot.edit_message_text('do you enjoy food shopping?',
                                  reply_markup=InlineKeyboardMarkup(
                                      [[InlineKeyboardButton('yep', callback_data='y'),
                                        InlineKeyboardButton('hate', callback_data='n')]]),
                                  chat_id=update.effective_chat.id,
                                  message_id=update.effective_message.message_id)

    update_answers(update, context)
    return SHOPPING


# >>>>>>>>>>>>>>> store answer and asks about top-4 <<<<<<<<<<<<<<<
def ninth_que(update: Update, context: CallbackContext):
    update.callback_query.answer()
    # print(context.user_data)
    
    if update.callback_query.data == 'y':
        context.user_data['shopping'] = 'I do'

        context.bot.edit_message_text(text='where do you usually buy stuff: markets, supermarkets etc.?',
                                      reply_markup=None,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)

        return WHERE

    elif update.callback_query.data == 'n':
        context.user_data['shopping'] = "I don't"

    context.bot.edit_message_text(text='top-4 your last or most common orders in restaurant/wolt',
                                  reply_markup=None,
                                  chat_id=update.effective_chat.id,
                                  message_id=update.effective_message.message_id)
    
    update_answers(update, context)
    return TOP


# >>>>>>>>>>>>>>> if 'y' store where and ask about top-4 <<<<<<<<<<<<<<<
def where_shop(update: Update, context: CallbackContext):
    context.user_data['where'] = update.message.text

    update.message.reply_text(text='top-4 your last or most common orders in restaurant/wolt',
                              reply_markup=None)

    update_answers(update, context)
    return TOP


# >>>>>>>>>>>>>>> stores top4 answer and ask about fav meals <<<<<<<<<<<<<<<
def tenth_que(update: Update, context: CallbackContext):
    context.user_data['top-4'] = update.message.text

    update.message.reply_text(text='*do you have your favorite/traditional meals?*'
                                   '\\(ex\\. if you’re eating same kind of breakfast everyday\\)',
                              parse_mode=ParseMode.MARKDOWN_V2)

    update_answers(update, context)
    return FAV


# >>>>>>>>>>>>>>> store answer and ask about budget <<<<<<<<<<<<<<<
def eleventh_que(update: Update, context: CallbackContext):
    context.user_data['fav'] = update.message.text
    
    update.message.reply_text(
        text="budget. how much money you spend or want to spend for food per one week?")

    update_answers(update, context)
    return BUDGET


# >>>>>>>>>>>>>>> store budget and ask pain <<<<<<<<<<<<<<<
def twelfth_que(update: Update, context: CallbackContext):
    global must_delete, pains_dict
    pains = []
    context.user_data['budget'] = update.message.text
    pains_dict = {'no_just': 'no, i just want to diversify my daily menu',
                  'changed_diet': 'i changed my diet/became vegan 🌱 and need to find a menu solution for catching '
                                  'all the nutrients',
                  'problem': 'i have a strong problem with not having a good lunch in the middle of working day',
                  'time': 'i don’t like/have time for cooking',
                  'less_money': 'i want to spent less money on my food',
                  'another': 'another pain',
                  }

    for i in pains_dict.keys():
        pains.append([InlineKeyboardButton(pains_dict[i], callback_data=i)])

    pains.append([InlineKeyboardButton("send all these pains as msg", callback_data='msg')])
    update.message.reply_text(text="if there’s any pain about food you want to solve?",
                              reply_markup=InlineKeyboardMarkup(pains))

    update_answers(update, context)
    return PAIN


# >>>>>>>>>>>>>>> check callback and store answer. if 'another pain' ask to write it. if 'send as message'
# send pain list as message <<<<<<<<<<<<<<<
def pain(update: Update, context: CallbackContext):
    global must_delete, pains_dict, edit
    context.user_data['changed'] = []
    txt, keyboard = '', []
    
    update.callback_query.answer()
    
    if update.callback_query.data == 'no_just':
        context.user_data['pain'] = "no, i just want to diversify my daily menu"
    
    elif update.callback_query.data == 'changed_diet':
        context.user_data[
            'pain'] = "i changed my diet/became vegan  🌱 and need to find a menu solution for catching " \
                      "all the nutrients "
    
    elif update.callback_query.data == 'problem':
        context.user_data['pain'] = "i have a strong problem with not having a good lunch in the middle of working day"
    
    elif update.callback_query.data == 'time':
        context.user_data['pain'] = "i don’t like/have time for cooking"
    
    elif update.callback_query.data == 'less_money':
        context.user_data['pain'] = "i want to spent less money on my food"
    
    elif update.callback_query.data == 'another':
        must_delete = context.bot.edit_message_text(text='write it below then',
                                                    chat_id=update.effective_chat.id,
                                                    message_id=update.effective_message.message_id,
                                                    reply_markup=None)
        
        return ANOTHER_PAIN
    
    elif update.callback_query.data == 'msg':
        
        for i, j in enumerate(pains_dict):
            txt += str(i + 1) + ': ' + pains_dict[j] + '\n\n'
            keyboard.append([InlineKeyboardButton(str(i + 1), callback_data=j)])
        
        context.bot.edit_message_text(txt, chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(keyboard), )
        
        update_answers(update, context)
        return PAIN
    
    edit = context.bot.edit_message_text(text='cool! now check your answers plz',
                                         chat_id=update.effective_chat.id,
                                         message_id=update.effective_message.message_id,
                                         reply_markup=None)
    
    update_answers(update, context)
    return checking(update, context)


# >>>>>>>>>>>>>>> stores 'another pain' and goes to checking <<<<<<<<<<<<<<<
def another_pain(update: Update, context: CallbackContext):
    global edit
    context.user_data['pain'] = update.message.text
    
    edit = context.bot.send_message(text='cool! now check your answers plz',
                                    chat_id=update.effective_chat.id,
                                    reply_markup=None)
    
    update_answers(update, context)
    return checking(update, context)


# >>>>>>>>>>>>>>> send a message w/ all answers and ask to check it  <<<<<<<<<<<<<<<
def checking(update: Update, context: CallbackContext):
    txt = ''
    # print(context.user_data)
    
    for i in context.user_data.keys():
        if i == 'in a process' or i == 'changed':
            continue
        else:
            txt += i + ": " + str(context.user_data[i]) + ';\n\n'
    
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING, timeout=1)
    time.sleep(1)
    context.bot.edit_message_text(txt,
                                  reply_markup=InlineKeyboardMarkup(
                                      [[InlineKeyboardButton('alright', callback_data='alright'),
                                        InlineKeyboardButton('wanna change', callback_data='you_better_no')]]),
                                  chat_id=edit.chat_id,
                                  message_id=edit.message_id, )
    
    return CHECKING


# >>>>>>>>>>>>>>> if 'alright' conv end if else goes to changing <<<<<<<<<<<<<<<
def last_que(update: Update, context: CallbackContext):
    update.callback_query.answer()

    if update.callback_query.data == 'alright':
        context.user_data['in a process'] = False
        contact_button = [[InlineKeyboardButton('🧡',
                                                url='https://instagram.com/alter_______native?igshid=YmMyMTA2M2Y=')]]
    
        context.bot.forward_message(message_id=update.effective_message.message_id,
                                    chat_id=632291350,
                                    from_chat_id=update.effective_chat.id)
    
        context.bot.edit_message_text('this is it for now 🧡 Lina will write you back ASAP.'
                                      'have a delicious continuation of the day\n\n'
                                      'wait. do you follow ALTER | NATIVE | FOOD on instagram?',
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(contact_button),
                                      chat_id=update.effective_chat.id)
    
        update_answers(update, context)
        return cancel(update, context)

    elif update.callback_query.data == 'you_better_no':
        change = []

        for i in context.user_data.keys():
            if i not in ['username', 'in a process', 'changed']:
                change.append([InlineKeyboardButton(i, callback_data=i)])

        context.bot.edit_message_text('pick what do you want to choose:',
                                      reply_markup=InlineKeyboardMarkup(change),
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)

        return CHANGE


# >>>>>>>>>>>>>>> ask to write new data <<<<<<<<<<<<<<<
def change_que(update: Update, context: CallbackContext):
    global edit
    update.callback_query.answer()

    for i in context.user_data.keys():
        if update.callback_query.data == i:
            context.user_data['changed'].append(i)
            edit = context.bot.edit_message_text(f'write your new {i}',
                                                 reply_markup=None,
                                                 chat_id=update.effective_chat.id,
                                                 message_id=update.effective_message.message_id)
            context.chat_data['wanna_change'] = i

    update_answers(update, context)
    return CHANGING_NAME


# >>>>>>>>>>>>>>> change old to new and goes to checking again <<<<<<<<<<<<<<<
def changing_answer(update: Update, context: CallbackContext):
    context.bot.deleteMessage(message_id=update.effective_message.message_id, chat_id=update.effective_chat.id)

    for i in context.user_data.keys():
        if i in context.chat_data['wanna_change']:
            context.user_data[i] = update.message.text

    update_answers(update, context)
    return checking(update, context)


# ----------------------------------------------------------------------------------------------------------------------
#                                               OLD USER
# ----------------------------------------------------------------------------------------------------------------------


# >>>>>>>>>>>>>>> greetings after /start pressed
# send two buttons 'see categories' and 'see whale menu' <<<<<<<<<<<<<<<
def wats_up(update: Update, context: CallbackContext):
    global user

    reply_markup = [[InlineKeyboardButton('I want to assemble my meal', callback_data='see_categories')],
                    [InlineKeyboardButton('see whole menu', callback_data='see_whole')]]

    update.effective_message.reply_text(text=f"hey, {user}, what's up?",
                                        reply_markup=InlineKeyboardMarkup(reply_markup))
    return HI


# >>>>>>>>>>>>>>> if 'categories' chosen send a buttons with categories names
# if 'whole menu' chosen send whole menu buttons <<<<<<<<<<<<<<<
def buttons(update: Update, context: CallbackContext):
    global must_delete, user
    query = update.callback_query
    username = user
    query.answer()
    keyboard, cat_list, used = [], [], set()
    context.chat_data['category'], context.chat_data['callback'] = [], []
    short = df_recipes[df_recipes['user'] == user]

    if query.data == 'see_categories':
        cat_list = short['category'].unique().tolist()
        for category in cat_list:
            keyboard.append([InlineKeyboardButton(str(category),
                                                  callback_data=category)])
            context.chat_data['category'].append(category)
            context.chat_data['callback'].append(category)
    
        keyboard.append([InlineKeyboardButton('back', callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                      text="chose a category")
        context.bot.edit_message_reply_markup(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                              reply_markup=reply_markup)
    
        return CATEGORY

    elif query.data == 'see_whole':
        for j, i in enumerate(short['name']):
            context.chat_data['callback'].append('dish_' + str(j))
            keyboard.append([InlineKeyboardButton(i, callback_data='dish_' + str(j))])
    
        keyboard.append([InlineKeyboardButton('see whole menu as message', callback_data='txt')])
        keyboard.append([InlineKeyboardButton('random', callback_data='random')])
        keyboard.append([InlineKeyboardButton('back', callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        must_delete = context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                                    text="here is your whole menu", reply_markup=reply_markup)
    
        return DISH


# >>>>>>>>>>>>>>> activates when user in 'categories' and depending on category show dishes <<<<<<<<<<<<<<<
def categories(update: Update, context: CallbackContext):
    global must_delete, user
    query = update.callback_query
    query.answer()
    choice = query.data
    keyboard = []
    short = df_recipes[df_recipes['user'] == user]
    context.chat_data['category_dishes'], context.chat_data['category_callback'] = [], []
    s = 0
    username = user

    if choice == 'back':
        reply_markup = [
            [InlineKeyboardButton('I want to assemble my meal', callback_data='see_categories')],
            [InlineKeyboardButton('see whole menu', callback_data='see_whole')]]
        context.bot.edit_message_text(text=f"so, what's up?", chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(reply_markup))

        return HI

    for i in data[username]:
        if choice in i['category']:
            s += 1
            keyboard.append([InlineKeyboardButton(i['name'], callback_data=i['callback'])])
            context.chat_data['category_dishes'].append(i['name'])
            context.chat_data['category_callback'].append(i['callback'])

    if len(keyboard) == s:
        keyboard.append([InlineKeyboardButton('see these dishes in message', callback_data='txt_cat')])
        keyboard.append([InlineKeyboardButton('back', callback_data='back_to_categories')])
    
    must_delete = context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                message_id=query.message.message_id,
                                                reply_markup=InlineKeyboardMarkup(keyboard),
                                                text=f'here is recipes w/ {choice}')

    return DISH


# >>>>>>>>>>>>>>> send recipy <<<<<<<<<<<<<<<
def send_dish(update: Update, context: CallbackContext):
    global user
    username = user
    update.callback_query.answer()
    query = update.callback_query
    choice = update.callback_query.data
    txt = ''  # when user want to see whole list of dishes
    buttons_, keyboard = [[]], []
    short = df_recipes[df_recipes['user'] == user]
    k, s = 0, 0  # indicators for buttons
    
    if choice == 'back_to_categories':
        for i, j in enumerate(context.chat_data['category']):
            keyboard.append([InlineKeyboardButton(j, callback_data=context.chat_data['callback'][i])])

        keyboard.append([InlineKeyboardButton('back', callback_data='back')])
        context.bot.edit_message_text(
            text='all categories is below:',
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return CATEGORY

    elif choice == 'back':
        reply_markup = [
            [InlineKeyboardButton('I want to assemble my meal', callback_data='see_categories')],
            [InlineKeyboardButton('see whole menu', callback_data='see_whole')]]
    
        context.bot.edit_message_text(text=f"so, what's up?", chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(reply_markup))
    
        return HI

    for j, i in enumerate(context.chat_data['callback']):
        if choice == i:
            context.bot.deleteMessage(message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id)
            context.bot.send_message(text=f'this is *{short["name"].iloc[j]}* recipy',
                                     chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN)
            context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING,
                                         timeout=1)
            time.sleep(2)
            context.bot.send_message(text=short['ingr'].iloc[j], chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN)
            context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING,
                                         timeout=1)
            time.sleep(2)
            context.bot.send_message(text=short['recipy'].iloc[j], chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN, )
            cancel(update, context)

        elif choice == 'random':
            rand = random.randint(0, len(data[username]))
            context.bot.deleteMessage(message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id)
            # context.chat_data['picked dish'][username][data[username][rand]["name"]] += 1
            context.bot.send_message(text=f'hey, maybe {data[username][rand]["name"]} will be nice?',
                                     chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN)
            context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING, timeout=1)
            time.sleep(2)
            context.bot.send_message(text=data[username][rand]['ingredients'], chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN)
            context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING, timeout=1)
            time.sleep(2)
            context.bot.send_message(text=data[username][rand]['recipy'], chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN, )
            # with open('users_data_picked.pkl', 'wb') as ud:
            #     pickle.dump(context.chat_data, ud)

            return cancel(update, context)

    if choice == 'txt':
        for i, j in enumerate(data[username]):
            s += 1
            if s % 7 == 0:
                buttons_.append([])
                k += 1

            txt += str(i + 1) + ': ' + j['name'] + '\n\n'
            buttons_[k].append(InlineKeyboardButton(str(i + 1), callback_data=j['callback']))

        buttons_.append([InlineKeyboardButton('back', callback_data='back')])
        context.bot.edit_message_text(txt, chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(buttons_))

        return DISH

    elif choice == 'txt_cat':
        for i, j in enumerate(context.chat_data['category_dishes']):
            txt += str(i + 1) + ': ' + j + '\n\n'
            buttons_[k].append(InlineKeyboardButton(str(i + 1),
                                                    callback_data=context.chat_data['category_callback'][i]))
        context.bot.edit_message_text(txt, chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(buttons_))

        return DISH

    return cancel(update, context)


# ----------------------------------------------------------------------------------------------------------------------
#                                               ADMIN PANEL
# ----------------------------------------------------------------------------------------------------------------------


# >>>>>>>>>>>>>>> starts when /start is pressed by admin user <<<<<<<<<<<<<<<
# noinspection SpellCheckingInspection
def admin(update: Update, context: CallbackContext):
    context.bot_data['pages'] = 0  # counting pages if there are more than 80 users
    admins_button = []
    context.bot_data['admin_phrases'] = ["donat' na ZSU :)", "sheeeesh", 'tak sho', 'sho tam', 'yak spravu?',
                                         "skrt skrt", 'Poroshenko Petro Oleksiyovuch = PPO', 'YU-SHE-NKO!',
                                         'rukola- girka ta ne smachna', 'red bull nadaye krula', 'hto ya?',
                                         'a y pravda, krylatym gruntu ne treba. \nZemli nemaye, to bude nebo.',
                                         'Nemaye polya, to bude volya.\nNemaye pary, to budutʹ khmary.',
                                         'vichnyy revolyutsioner – dukh, shcho tilo rve do boyu, '
                                         'rve za postup, shchastya y volyu,- vin zhyve, vin shche ne vmer. '
                                         'ni popivsʹkiyi tortury, ni tyuremni tsarsʹki mury, '
                                         'ani viysʹka mushtrovani, ni harmaty lashtovani, ni shpionsʹke remeslo '
                                         'v hrib yoho shche ne zvelo.', 'a negroni...sbagliato...with prosecco init',
                                         '15 zhovtnya 64700 mertvoi rusni', 'omae wa mou shindeiru', 'nani????????', ]
    context.bot_data['admin_buttons'] = {'send message': 'send message to a user/to all users',
                                         'answers': 'see users answers for query',
                                         'data': 'change or add recipy data or delete user data',
                                         'start_pressed': 'see who pressed /start',
                                         # 'picked': 'see which dishes are picked',
                                         'interface': 'see how interface looks for a user'}

    for i in context.bot_data['admin_buttons'].keys():
        admins_button.append([InlineKeyboardButton(context.bot_data['admin_buttons'][i], callback_data=i)])
    
    update.message.reply_text(f"hey, bossss, let's go!", reply_markup=InlineKeyboardMarkup(admins_button))

    return ADMIN


# >>>>>>>>>>>>>>> callback <<<<<<<<<<<<<<<
def admin_2(update: Update, context: CallbackContext):
    update.callback_query.answer()
    keyboard, buttons_, txt = [], [[]], ''
    k, s, text = 0, 0, ''
    global df_answers, df_users

    if update.callback_query.data == 'back' or update.callback_query.data == 'back_m':
        return back_to_admin(update, context)

    # >>>>>>>>>>>>>>> send message <<<<<<<<<<<<<<<
    for j, i in enumerate(df_users['username']):
    
        if update.callback_query.data == i or update.callback_query.data == 'send to all' and \
                context.bot_data['is message']:
        
            if update.callback_query.data == i and len(i) > 1:
                context.bot_data['admin send message: users_id'].append(str(df_users['id'][j]))
                context.bot_data['admin send message: user_name'].append(i)
        
                text = f'ok, what message do you want to send to @{i}? \n\nIf it is file than it must be .pdf ' \
                       f'and you need to send it separately from text message'
        
            elif update.callback_query.data == 'send to all':
                context.bot_data['admin send message: users_id'].append(str(df_users['id'][j]))
                context.bot_data['admin send message: user_name'].append(i)
                text = f'ok, what message do you want to send to all users?'
        
            context.bot.edit_message_text(text=text,
                                          message_id=update.effective_message.message_id,
                                          chat_id=update.effective_chat.id,
                                          reply_markup=None)
        
            return SEND_MESSAGE_TXT
    
        elif update.callback_query.data == 'send message' or update.callback_query.data == 'next_m':
            if update.callback_query.data == 'next_m' or update.callback_query.data == 'send message':
                for m, n in enumerate(df_users['username']):
        
                    if m < context.bot_data['pages'] and context.bot_data['pages'] > 80:
                        continue
        
                    elif m < context.bot_data['pages'] + 80:
                        k += 1
                        if k <= 4 and len(n) != 0:
                            buttons_[s].append(InlineKeyboardButton(n, callback_data=n))
                        if k == 4:
                            buttons_.append([])
                            s += 1
                            k = 0
        
                    if m == context.bot_data['pages'] + 80:
                        buttons_.append([InlineKeyboardButton('>>', callback_data='next')])
                        break
            
                buttons_.append([InlineKeyboardButton('send to all', callback_data='send to all')])
                buttons_.append([InlineKeyboardButton('back', callback_data='back_m')])
                text = 'choose user who u want to send message:\n' \
                       '!note that u can send message only to user who pressed start'
                context.bot.edit_message_text(text,
                                              chat_id=update.effective_chat.id,
                                              message_id=update.effective_message.message_id,
                                              reply_markup=InlineKeyboardMarkup(buttons_))
                context.bot_data['pages'] += 80
            
                return SEND_MESSAGE

    # >>>>>>>>>>>>>>> see answers <<<<<<<<<<<<<<<
    for k, j in enumerate(df_answers['username']):

        if update.callback_query.data == j and context.bot_data['is answers']:
            for s, m in enumerate(df_answers[df_answers['username'] == update.callback_query.data].values[0]):
                txt += str(df_answers.columns.values[s]) + ':' + '*' + str(m) + '*' + '\n\n'

            context.bot.edit_message_text(txt,
                                          message_id=update.effective_message.message_id,
                                          chat_id=update.effective_chat.id,
                                          parse_mode=ParseMode.MARKDOWN,
                                          reply_markup=None)

            return cancel(update, context)

        elif update.callback_query.data == 'answers' or update.callback_query.data == 'next' or \
                update.callback_query.data == 'back':
            txt = "pick who's data u wanna see:\nor just click here:\n\n" \
                  "https://docs.google.com/spreadsheets/d/1e8Z1k3DPzTfipcNsKzxXNt" \
                  "-ON1T2ZR_O3sosfyzzlbI/edit#gid=0\n\n"

            if update.callback_query.data == 'answers' or update.callback_query.data == 'next':
                for y, i in enumerate(df_answers['username']):
                    if y < context.bot_data['pages'] and context.bot_data['pages'] > 80:
                        continue
                    elif y < context.bot_data['pages'] + 80:
                        k += 1
                        if i and k <= 4:
                            buttons_[s].append(InlineKeyboardButton(str(i), callback_data=str(i)))
                        if k == 4:
                            s += 1
                            k = 0
                            buttons_.append([])
                    if y == context.bot_data['pages'] + 80:
                        buttons_.append([InlineKeyboardButton('>>', callback_data='next')])
                        break

                buttons_.append([InlineKeyboardButton('back', callback_data='back')])
                context.bot.edit_message_text(txt,
                                              chat_id=update.effective_chat.id,
                                              message_id=update.effective_message.message_id,
                                              reply_markup=InlineKeyboardMarkup(buttons_))
                context.bot_data['pages'] += 80

                return DATA

    # >>>>>>>>>>>>>>> see who pressed start <<<<<<<<<<<<<<<

    if update.callback_query.data == 'start_pressed':
        text = f'here is {len(df_users)} users: \n\n'

        for i in df_users['username']:
            text += '@' + i + ' '

        context.bot.edit_message_text(text=text,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=None)

        return cancel(update, context)

    # >>>>>>>>>>>>>>> add or change data for user <<<<<<<<<<<<<<<

    elif update.callback_query.data == 'data':
    
        keyboard.append([InlineKeyboardButton('change existing', callback_data='change')])
        keyboard.append([InlineKeyboardButton('del or change username', callback_data='del')])
        keyboard.append([InlineKeyboardButton('add new user', callback_data='new user')])
        keyboard.append([InlineKeyboardButton('back', callback_data='back')])
        text = "ok it's simpler here link: " \
               "https://docs.google.com/spreadsheets/d/1e8Z1k3DPzTfipcNsKzxXNt-ON1T2ZR_O3sosfyzzlbI/edit#gid=19480151" \
               ""
        context.bot.edit_message_text(text, chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(keyboard))
    
        return DATA_CHANGE

    # >>>>>>>>>>>>>>> see how interface look for a user <<<<<<<<<<<<<<<

    elif update.callback_query.data == 'interface':
        for i in df_recipes['user'].unique().tolist():
            keyboard.append([InlineKeyboardButton(i, callback_data=i)])

        keyboard.append([InlineKeyboardButton('new user', callback_data='new user')])
        keyboard.append([InlineKeyboardButton('back', callback_data='back')])
        text = 'pick a user to to see how they see interface'
        context.bot.edit_message_text(text, chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(keyboard))

        return INTERFACE


# >>>>>>>>>>>>>>> send message <<<<<<<<<<<<<<<
def send_message(update: Update, context: CallbackContext):
    global df_users
    context.bot_data['is message'] = True
    update.callback_query.answer()
    context.bot_data['admin send message: users_id'], context.bot_data['admin send message: user_name'] = [], []
    text, buttons_, s, k = '', [[]], 0, 0

    if update.callback_query.data == 'back_m':
        return back_to_admin(update, context)
    
    elif update.callback_query.data == 'next':
        for j, i in enumerate(df_users['username']):
            if j < context.bot_data['pages']:
                continue
            elif j < context.bot_data['pages'] + 80:
                k += 1
                if k <= 4:
                    buttons_[s].append(InlineKeyboardButton(i, callback_data=i))
                if k == 4:
                    buttons_.append([])
                    s += 1
                    k = 0
            if j == context.bot_data['pages'] + 80:
                buttons_.append([InlineKeyboardButton('>>', callback_data='next_m')])
                break

        buttons_.append([InlineKeyboardButton('send to all', callback_data='send to all')])
        buttons_.append([InlineKeyboardButton('back', callback_data='back_m')])
        text = 'choose user who u want to send message:\n!note that u can send message only to user who pressed start'
        context.bot.edit_message_text(text,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(buttons_))
        context.bot_data['pages'] += 80

        return ADMIN

    else:
        for j, i in enumerate(df_users['username']):
            if update.callback_query.data == i:
                context.bot_data['admin send message: users_id'].append(str(df_users['id'][j]))
                context.bot_data['admin send message: user_name'].append(i)
                text = f'ok, what message do you want to send to @{i}? \n\nIf it is file than it must be .pdf ' \
                       f'and you need to send it separately from text message'
            
            elif update.callback_query.data == 'send to all':
                context.bot_data['admin send message: users_id'].append(str(df_users['id'][j]))
                context.bot_data['admin send message: user_name'].append(i)
                text = f'ok, what message do you want to send to all users?'
        
        context.bot.edit_message_text(text=text,
                                      message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id,
                                      reply_markup=None)

        return SEND_MESSAGE_TXT


# >>>>>>>>>>>>>>> confirmation about message <<<<<<<<<<<<<<<
def second_que_txt(update: Update, context: CallbackContext):
    if update.message.text:
        message = context.bot_data['admin send message: message'] = update.message.text
        update.message.reply_text(
            text=f"so, message:\n\n{message}\n\nto user(s): @{context.bot_data['admin send message: user_name']}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('send', callback_data='send'),
                                                InlineKeyboardButton('change', callback_data='change')]]))

        return SENDING

    elif update.message.document:
        context.bot.get_file(update.message.document).download()
        context.bot_data['file'] = update.message.document['file_name']

        with open(f"pdf/{context.bot_data['file']}.pdf", 'wb') as f:
            context.bot.get_file(update.message.document).download(out=f)
            update.message.reply_text(
                text=f"I kept it. wanna send?",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('send', callback_data='send'),
                                                    InlineKeyboardButton('cancel', callback_data='cancel')]]))

        return SEND_DOCUMENT

    else:
        update.message.reply_text("i dont know this file type..... I BROKE PRES /start again")

        return cancel(update, context)


# >>>>>>>>>>>>>>> if we send a document <<<<<<<<<<<<<<<
def sending_document(update: Update, context: CallbackContext):
    update.callback_query.answer()

    if update.callback_query.data == 'send':
        document = open(f"pdf/{context.bot_data['file']}.pdf", 'rb')
    
        for i in context.bot_data['admin send message: users_id']:
            context.bot.send_document(document=document, chat_id=i)
    
        context.bot.edit_message_text('done!',
                                      reply_markup=None,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)

    elif update.callback_query.data == 'cancel':
        context.bot.edit_message_text('canceled, press /start again', chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=None)

    return cancel(update, context)


# >>>>>>>>>>>>>>> sending message via bot <<<<<<<<<<<<<<<
def sending(update: Update, context: CallbackContext):
    update.callback_query.answer()

    if update.callback_query.data == 'send':
        for i in context.bot_data['admin send message: users_id']:
            context.bot.send_message(text=context.bot_data['admin send message: message'], chat_id=i)
    
        context.bot.edit_message_text('done!',
                                      reply_markup=None,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)
    
        return cancel(update, context)

    elif update.callback_query.data == 'change':
        context.bot.edit_message_text('type a new one:',
                                      reply_markup=None,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)

        return SEND_MESSAGE_TXT


# >>>>>>>>>>>>>>> if 'show data' chosen show usernames <<<<<<<<<<<<<<<
def user_data(update: Update, context: CallbackContext):
    global df_answers
    context.bot_data['is answers'] = True
    update.callback_query.answer()
    buttons_, k, s = [[]], 0, 0
    txt = "pick who's data u wanna see:\nor just click here:\n\n" \
          "https://docs.google.com/spreadsheets/d/1e8Z1k3DPzTfipcNsKzxXNt" \
          "-ON1T2ZR_O3sosfyzzlbI/edit#gid=0\n\n"
    
    if update.callback_query.data == 'back':
        return back_to_admin(update, context)
    
    if update.callback_query.data == 'next':
        for j, i in enumerate(df_answers['username']):
            if j < context.bot_data['pages']:
                continue

            elif j < context.bot_data['pages'] + 80:
                k += 1
                if i and k <= 4:
                    buttons_[s].append(InlineKeyboardButton(str(i), callback_data=str(i)))
                if k == 4:
                    s += 1
                    k = 0
                    buttons_.append([])

            else:
                buttons_.append([InlineKeyboardButton('>>', callback_data='next')])
                break

        buttons_.append([InlineKeyboardButton('back', callback_data='back')])
        context.bot.edit_message_text(txt,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(buttons_))
        context.bot_data['pages'] += 80

        return ADMIN

    else:
        txt = ''
        for k, j in enumerate(df_answers[df_answers['username'] == update.callback_query.data].values[0]):
            txt += str(df_answers.columns.values[k]) + ': ' + str(j) + '\n\n'

        context.bot.edit_message_text(txt,
                                      message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id,
                                      reply_markup=None)

        return cancel(update, context)


# >>>>>>>>>>>>>>> show interface for either new or existent user <<<<<<<<<<<<<<<
def interface(update: Update, context: CallbackContext):
    global user
    update.callback_query.answer()

    if update.callback_query.data == 'back':
        return back_to_admin(update, context)

    for i in df_recipes['user'].unique().tolist():
        if update.callback_query.data == i:
            user = i
            reply_markup = [
                [InlineKeyboardButton('I want to assemble my meal', callback_data='see_categories')],
                [InlineKeyboardButton('see whole menu', callback_data='see_whole')]]
            update.effective_message.reply_text(text=f"hey, {i}, what's up?",
                                                reply_markup=InlineKeyboardMarkup(reply_markup))
        
            return HI

    if update.callback_query.data == 'new user':
        reply_markup = [[InlineKeyboardButton('YES', callback_data='YES')],
                        [InlineKeyboardButton('wanna contact Lina first', callback_data='contact')],
                        [InlineKeyboardButton('want to read about the project', callback_data='read about')]]
        update.effective_message.reply_text(text='hey, foodie🧡 welcome to ALTER | NATIVE | FOOD\nwanna buy a menu?',
                                            reply_markup=InlineKeyboardMarkup(reply_markup))

        return WELCOME


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def data_change(update: Update, context: CallbackContext):
    update.callback_query.answer()
    context.bot_data['recipy data'] = ['number', 'name', 'category', 'ingredients', 'recipy', 'change', 'delete']
    keyboard, text = [[]], ''

    if update.callback_query.data == 'new user':
        text = "type his/her/their username carefully!\n" \
               "*Note, that u need to type it without @ symbol otherwise it won't work*"
        context.bot.edit_message_text(text, chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id, reply_markup=None,
                                      parse_mode=ParseMode.MARKDOWN)

        return NEW_USER

    if update.callback_query.data == 'del':
        text += 'pick who you want to delete or change username. once you do it you cannot restore the data'

        for i in data:
            keyboard.append([InlineKeyboardButton(i, callback_data=i)])

        keyboard.append([InlineKeyboardButton('back', callback_data='back')])
        context.bot.edit_message_text(text, chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(keyboard))

        return DEL_CHANGE

    elif update.callback_query.data == 'change':
        for i in data:
            keyboard.append([InlineKeyboardButton(i, callback_data=i)])

        keyboard.append([InlineKeyboardButton('back', callback_data='back')])
        text += 'pick who you wanna change'
        context.bot.edit_message_text(text, chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(keyboard))

        return CHANGE_USER

    elif update.callback_query.data == 'back':
    
        return back_to_admin(update, context)


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def back_to_changing(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton('change existing', callback_data='change')],
                [InlineKeyboardButton('del or change username', callback_data='del')],
                [InlineKeyboardButton('add new user', callback_data='new user')],
                [InlineKeyboardButton('back', callback_data='back')]]
    text = 'pick a user to change or add a new one or delete or change his/her/their name'
    context.bot.edit_message_text(text, chat_id=update.effective_chat.id,
                                  message_id=update.effective_message.message_id,
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    
    return DATA_CHANGE


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def change_user(update: Update, context: CallbackContext):
    update.callback_query.answer()
    text, keyboard = f'here is his/her/their menu:\n\n', [[]]

    if update.callback_query.data == 'back':
        return back_to_changing(update, context)
    
    for i in data:
        if update.callback_query.data == i:
            s, k = 0, 0
            context.bot_data['picked user'] = i
            for n, j in enumerate(data[i]):
                text += str(n + 1) + ': ' + str(j['name']) + '\n'
                s += 1
                if s % 7 == 0:
                    keyboard.append([])
                    k += 1
                keyboard[k].append(InlineKeyboardButton(str(n + 1), callback_data=j['number']))

            keyboard.append([InlineKeyboardButton('add new dish', callback_data='add dish'),
                             InlineKeyboardButton('back', callback_data='back')])
            text += '\npick what do u want to change here'
            context.bot.edit_message_text(text, chat_id=update.effective_chat.id,
                                          message_id=update.effective_message.message_id,
                                          reply_markup=InlineKeyboardMarkup(keyboard))

            return WHAT_CHANGE


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def del_change(update: Update, context: CallbackContext):
    update.callback_query.answer()
    context.bot_data['del or change'] = update.callback_query.data

    if update.callback_query.data == 'back':
        return back_to_changing(update, context)
    
    keyboard = [[InlineKeyboardButton('del', callback_data='delete'),
                 InlineKeyboardButton('change', callback_data='change')],
                [InlineKeyboardButton('back', callback_data='back')]]
    context.bot.edit_message_text(f'change username or delete? {context.bot_data["del or change"]}',
                                  chat_id=update.effective_chat.id,
                                  message_id=update.effective_message.message_id,
                                  reply_markup=InlineKeyboardMarkup(keyboard))

    return DEL_CHANGE2


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def del_change2(update: Update, context: CallbackContext):
    update.callback_query.answer()
    keyboard = [[InlineKeyboardButton('save', callback_data='save'),
                 InlineKeyboardButton('cancel', callback_data='cancel')]]
    
    if update.callback_query.data == 'back':
        return back_to_changing(update, context)

    elif update.callback_query.data == 'delete':
        for i in data:
            if context.bot_data['del or change'] == i:
                del data[i]
                context.bot.edit_message_text('done', chat_id=update.effective_chat.id,
                                              message_id=update.effective_message.message_id,
                                              reply_markup=InlineKeyboardMarkup(keyboard))

                return SAVE_UPDATE

    elif update.callback_query.data == 'change':
        context.bot.edit_message_text("type new username\n*Note, that u need to type it without @ "
                                      "symbol otherwise it won't work*", chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id, parse_mode=ParseMode.MARKDOWN,
                                      reply_markup=None)

        return CHANGE_USERNAME


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def change_username(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton('save', callback_data='save'),
                 InlineKeyboardButton('cancel', callback_data='cancel')]]

    for i in data:
        if context.bot_data['del or change'] == i:
            data[update.message.text] = data[i]
            del data[i]
            update.message.reply_text('done', reply_markup=InlineKeyboardMarkup(keyboard))

            return SAVE_UPDATE


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def add_new_user(update: Update, context: CallbackContext):
    data[update.message.text] = []
    context.bot_data['new user'] = update.message.text
    update.message.reply_text(f'ok{"." * 333} u need to save to continue or cancel',
                              reply_markup=InlineKeyboardMarkup(
                                  [[InlineKeyboardButton('save', callback_data='save'),
                                    InlineKeyboardButton('cancel', callback_data='cancel')]])
                              )
    
    return SAVE_UPDATE


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def what_do_we_change(update: Update, context: CallbackContext):
    # print('What we change')
    update.callback_query.answer()
    text, keyboard = '', []
    context.bot_data['changing'] = {}

    if update.callback_query.data == 'back':
        return back_to_changing(update, context)

    elif update.callback_query.data == 'add dish':
        text = f"ok, now write a dish name"
        context.bot.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id, reply_markup=None)

        return NUMBER

    for i, j in enumerate(data[context.bot_data['picked user']]):
        if update.callback_query.data == str(i + 1):
            context.bot_data['changing']['what_number'] = i
            text += str(j['number']) + ': ' + str(j['name']) + '\n\n' + 'CATEGORY: ' + str(j['category']) + '\n\n'
            # str(j['ingredients'][:150]) + '...\n\n' + '*RECIPY*: '+str(j['recipy'][:150]) + '...'

    for k in context.bot_data['recipy data']:
        if k in ['number', 'add dish', 'delete', 'change']:
            continue
        else:
            keyboard.append([InlineKeyboardButton(k, callback_data=k)])

    context.bot.edit_message_text(text, chat_id=update.effective_chat.id,
                                  message_id=update.effective_message.message_id,
                                  reply_markup=InlineKeyboardMarkup(keyboard), )

    return DATA_CHANGE_2


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def new_number(update: Update, context: CallbackContext):
    basic_dict = {
        "number": int,
        "callback": f"dish_{int}",
        
        "name": '',
        "category": '',
        "difficulty": '',
        "ingredients": '',
        "recipy": ''}
    i_ = len(data[context.bot_data['picked user']])
    data[context.bot_data['picked user']].append(basic_dict)
    data[context.bot_data['picked user']][i_]['number'] = len(data[context.bot_data['picked user']])
    data[context.bot_data['picked user']][i_]['callback'] = f"dish_{len(data[context.bot_data['picked user']])}"
    data[context.bot_data['picked user']][i_]['name'] = update.message.text
    # print(data[context.bot_data['picked user']])
    text = f"now add category.\n\n*all dishes are grouped by categories, for example all dishes with category RICE " \
           f"will be grouped and user can pick one of them, so type category which better describes this dish\nalso " \
           f"these categories for different dishes must be the same to group them, so if u have category <rice> it " \
           f"should be <rice> again. I also guess that u can use emoji for categories, but this is another lvl of " \
           f"managing user's menu* "
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    return ADD_CATEGORY


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def add_category(update: Update, context: CallbackContext):
    # print(data[context.bot_data['picked user']])
    data[context.bot_data['picked user']][len(data[context.bot_data['picked user']]) - 1][
        'category'] = update.message.text
    text = f"got you. \n\n*now you need to add ingredients to the data. \ntype everything in one msg*"
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    return ADD_INGR


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def add_ing(update: Update, context: CallbackContext):
    # print(data[context.bot_data['picked user']])
    data[context.bot_data['picked user']][len(data[context.bot_data['picked user']]) - 1][
        'ingredients'] = update.message.text
    text = f"cool. last step is add recipy. \n\n*once again type everything in a single msg*"
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    return ADD_RECIPY


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def add_rec(update: Update, context: CallbackContext):
    # print(data[context.bot_data['picked user']])
    data[context.bot_data['picked user']][len(data[context.bot_data['picked user']]) - 1][
        'recipy'] = update.message.text
    text = f"ok, now check everything:\n" \
           f"\n{data[context.bot_data['picked user']]}\n\nsave?"
    update.message.reply_text(text,
                              reply_markup=InlineKeyboardMarkup([
                                  [InlineKeyboardButton('save', callback_data='save'),
                                   InlineKeyboardButton('cancel', callback_data='cancel'),
                                   ]]))

    return SAVE_UPDATE


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def data_change_2(update: Update, context: CallbackContext):
    update.callback_query.answer()
    text = ''
    
    for i in context.bot_data['recipy data']:
        context.bot_data['changing'][i] = False
        if update.callback_query.data == i:
            context.bot_data['changing'][i] = True
            text = 'it was: \n\n' + \
                   data[context.bot_data['picked user']][context.bot_data['changing']['what_number']][i] + \
                   '\n\nTYPE A NEW ONE BELOW'
    
    context.bot.edit_message_text(text, chat_id=update.effective_chat.id,
                                  message_id=update.effective_message.message_id,
                                  reply_markup=None)

    return DATA_CHANGE_3


# >>>>>>>>>>>>>>> changing data for a user <<<<<<<<<<<<<<<
def data_change_3(update: Update, context: CallbackContext):
    for i in context.bot_data['recipy data']:
        if context.bot_data['changing'][i]:
            context.bot_data['changing'][i] = False
            data[context.bot_data['picked user']][context.bot_data['changing']['what_number']][i] = update.message.text

    update.message.reply_text(f'ok{"." * 100}\nwanna save or continue?',
                              reply_markup=InlineKeyboardMarkup([
                                  [InlineKeyboardButton('save', callback_data='save'),
                                   InlineKeyboardButton('continue', callback_data='continue')
                                   ]]))

    return SAVE_UPDATE


# >>>>>>>>>>>>>>> saving data for a user <<<<<<<<<<<<<<<
def save_update(update: Update, context: CallbackContext):
    update.callback_query.answer()
    text, keyboard = '', [[]]

    if update.callback_query.data == 'save':
        # with open('data.pkl', 'wb') as save_:
        #     pickle.dump(data, save_)
        context.bot.edit_message_text('done, press /start', chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)
    
        return cancel(update, context)

    elif update.callback_query.data == 'continue':
        for i in data:
            if i == context.bot_data['picked user']:
                s, k = 0, 0
                for n, j in enumerate(data[i]):
                    text += str(n + 1) + ': ' + str(j['name']) + '\n'
                    s += 1
                    if s % 7 == 0:
                        keyboard.append([])
                        k += 1
                    keyboard[k].append(InlineKeyboardButton(str(n + 1), callback_data=j['number']))
                text += '\npick what do u want to change here'

        context.bot.edit_message_text(text, chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(keyboard))

        return WHAT_CHANGE

    elif update.callback_query.data == 'cancel':
        context.bot.edit_message_text('canceled, pres /start', chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=None)

        return cancel(update, context)


# >>>>>>>>>>>>>>> back func that return interface to main admin stage <<<<<<<<<<<<<<<
def back_to_admin(update: Update, context: CallbackContext):
    update.callback_query.answer()
    context.bot_data['pages'] = 0

    if update.callback_query.data == 'back' or update.callback_query.data == 'back_m':
        admins_button = []
        for i in context.bot_data['admin_buttons'].keys():
            admins_button.append([InlineKeyboardButton(context.bot_data['admin_buttons'][i], callback_data=i)])
    
        context.bot.edit_message_text(text=random.choice(context.bot_data['admin_phrases']),
                                      reply_markup=InlineKeyboardMarkup(admins_button),
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)
    
        return ADMIN


# ----------------------------------------------------------------------------------------------------------------------
#                                               COMMANDS
# ----------------------------------------------------------------------------------------------------------------------


def error(update: Update, context: CallbackContext):
    print("-" * 10, 'ERROR', '-' * 10)
    print(update.effective_chat.username, datetime.datetime.now())
    print(f"\nupdate {update} \ncaused error {context.error}\n")
    print("-" * 10, 'ERROR', '-' * 10)


def contacts(update: Update, context: CallbackContext):
    contact_button = [[InlineKeyboardButton('Instagram', url='https://www.instagram.com/yolkinalina/')],
                      [InlineKeyboardButton('Telegram', url='https://t.me/linayolkina')]]
    reply_markup_start = InlineKeyboardMarkup(contact_button)
    update.message.reply_text(text="here are Lina's contacts:", reply_markup=reply_markup_start)


def help_command(update: Update, context: CallbackContext):
    text = f"so, this is a bot that should help you to answer the question 'WHAT TO EAT?'\nonce you don't have your " \
           f"own menu, you need to pass the query, which starts when you press /start command - then ASAP you will " \
           f"get your personal menu. And when it will be ready -- after you press /start command, you'll have access " \
           f"to the menu\n\nenjoy this bot! If you have any problem using this bot, just send a message directly " \
           f"to LINA. It's easy to find her contacts by pressing /contact button"
    update.message.reply_text(text=text)


# def about_command(up)


def update_answers(update: Update, context: CallbackContext):
    """saving users data to gs"""
    global df_answers
    # print(context.user_data)
    print(datetime.datetime.now())
    
    df_answers = df_answers.set_index('id')
    
    if context.user_data['id'] not in df_answers.index.to_list():
        print('first if')
        df_answers = pd.concat([df_answers.reset_index(),
                                pd.DataFrame({'id': context.user_data['id'], 'username': context.user_data['username']},
                                             index=[len(df_answers)])], ignore_index=True)
    else:
        for i in context.user_data:
            df_answers.loc[context.user_data['id']][i] = context.user_data[i]
    
    if df_answers.index.name == 'id':
        df_answers = df_answers.reset_index()
    
    print(datetime.datetime.now())
    

def cancel(update: Update, context: CallbackContext):
    # update.message.reply_text(
    #     'Name Conversation cancelled by user. Bye. Send /set_name to start again')
    return ConversationHandler.END


def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_error_handler(error)
    dp.add_handler(CommandHandler('contacts', contacts))
    dp.add_handler(CommandHandler('help', help_command))
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
            SHOPPING: [CallbackQueryHandler(ninth_que)],
            WHERE: [MessageHandler(Filters.text, where_shop)],
            TOP: [MessageHandler(Filters.text, tenth_que)],
            FAV: [MessageHandler(Filters.text, eleventh_que)],
            BUDGET: [MessageHandler(Filters.text, twelfth_que)],
            PAIN: [CallbackQueryHandler(pain)],
            ANOTHER_PAIN: [MessageHandler(Filters.text, another_pain)],
            CHECKING: [CallbackQueryHandler(last_que)],
            CHANGE: [CallbackQueryHandler(change_que)],
            CHANGING_NAME: [MessageHandler(Filters.text, changing_answer)],
    
            # existing user:
            HI: [CallbackQueryHandler(buttons)],
            CATEGORY: [CallbackQueryHandler(categories)],
            DISH: [CallbackQueryHandler(send_dish)],
    
            # admin panel:
            ADMIN: [CallbackQueryHandler(admin_2)],
            SEND_MESSAGE: [CallbackQueryHandler(send_message)],
            SEND_MESSAGE_TXT: [MessageHandler(Filters.text | Filters.document, second_que_txt)],
            SEND_DOCUMENT: [CallbackQueryHandler(sending_document)],
            SENDING: [CallbackQueryHandler(sending)],
            DATA: [CallbackQueryHandler(user_data)],
            # PICKED: [CallbackQueryHandler(picked_dishes)],
            DATA_CHANGE: [CallbackQueryHandler(data_change)],
            WHAT_CHANGE: [CallbackQueryHandler(what_do_we_change)],
            DATA_CHANGE_2: [CallbackQueryHandler(data_change_2)],
            DATA_CHANGE_3: [MessageHandler(Filters.text, data_change_3)],
            SAVE_UPDATE: [CallbackQueryHandler(save_update)],
            INTERFACE: [CallbackQueryHandler(interface)],
            NEW_USER: [MessageHandler(Filters.text, add_new_user)],
            NUMBER: [MessageHandler(Filters.text, new_number)],
            CHANGE_USER: [CallbackQueryHandler(change_user)],
            DEL_CHANGE: [CallbackQueryHandler(del_change)],
            DEL_CHANGE2: [CallbackQueryHandler(del_change2)],
            CHANGE_USERNAME: [MessageHandler(Filters.text, change_username)],
            ADD_CATEGORY: [MessageHandler(Filters.text, add_category)],
            ADD_INGR: [MessageHandler(Filters.text, add_ing)],
            ADD_RECIPY: [MessageHandler(Filters.text, add_rec)]
        },
        fallbacks=[MessageHandler(Filters.command, start)],
        # run_async=True,
        # per_user=True,
        allow_reentry=True
    )
    
    dp.add_handler(conv_handler_new_user)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
