import logging
import os
import time
from re import match

import telegram
from opencage.geocoder import OpenCageGeocode
from telegram import *
from telegram.ext import *

from data import data

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_GEO = os.environ.get('geo_api')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

WELCOME, YES, YALLA, EMAIL, LOCATION, LOC_CHECK, LIKE, COOK, WOULD_LOVE, SHOPPING = range(10)
WHERE, TOP, FAV, BUDGET, PAIN, ANOTHER_PAIN, CHECKING, CHANGE, CHANGING_NAME = range(10, 19)

HI, CATEGORY, DISH = range(20, 23)


def start(update: Update, context: CallbackContext):
    print(context.user_data)
    user = update.effective_message.from_user.username
    context.user_data['username'] = "@" + user
    # delete_messages(context, id_ch=update.effective_chat.id, id_m=update.effective_message.message_id)
    # menu = [[KeyboardButton("/start")],
    #         [KeyboardButton("/stop")],
    #         [KeyboardButton("/help")], ]
    # context.bot.send_message(chat_id=update.effective_chat.id,
    #                          text='if bot stopped reply correctly press stop then start',
    #                          reply_markup=ReplyKeyboardMarkup(menu))
    print(update.effective_message.message_id, update.effective_chat.id)
    if user not in data.keys():
        return wanna_buy(update, context)
    else:
        return wats_up(update, context)


def cancel(update: Update, context: CallbackContext):
    print(update.effective_message.message_id, context.user_data)
    # update.message.reply_text(
    #     'Name Conversation cancelled by user. Bye. Send /set_name to start again')
    return ConversationHandler.END


# --------------------------------------------------------------------
def wanna_buy(update: Update, context: CallbackContext):
    reply_markup = [[InlineKeyboardButton('YES', callback_data='YES')],
                    [InlineKeyboardButton('contact', callback_data='contact')]]
    update.effective_message.reply_text(text='hey, foodie🧡 welcome to ALTER | NATIVE | PROJECT. wanna buy a menu?',
                                        reply_markup=InlineKeyboardMarkup(reply_markup))
    return WELCOME


# >>>>>>>>>>>>>>>>>>>>>>> check first question and moving to second one
def first_que(update: Update, context: CallbackContext):
    print(update.effective_message.message_id, context.user_data)
    query = update.callback_query
    query.answer()
    if query.data == 'YES':
        context.bot.edit_message_text(
            text='oh yeah! so get ready for a food questionnaire to create your menu the most '
                 'suitable to your FOOD LIFESTYLE, your tastes and the current season.',
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('yalla', callback_data='yalla')]]))
    
    if query.data == 'contact':
        contact_button = [[InlineKeyboardButton('Instagram', url='https://www.instagram.com/yolkinalina/')],
                          [InlineKeyboardButton('Telegram', url='https://t.me/linayolkina')]]
        reply_markup_start = InlineKeyboardMarkup(contact_button)
        context.bot.edit_message_text(text="here:", reply_markup=reply_markup_start,
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)
        return cancel(update, context)
    
    return YES


# >>>>>>>>>>>>>>>>>>>>>>> check if user pressed yalla button and going to third one
def yalla(update: Update, context: CallbackContext):
    print(update.effective_message.message_id, context.user_data)
    
    update.callback_query.answer()
    if update.callback_query.data == 'yalla':
        context.user_data['in a process'] = True
        context.bot.edit_message_text(
            text='first, let me get to know you:) what’s your name and surname?\n(type everything in one message)',
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
            reply_markup=None)
    
    return YALLA


# >>>>>>>>>>>>>>>>>>>>>>> getting name and ask about email
def second_que(update: Update, context: CallbackContext):
    print(update.effective_message.message_id, context.user_data)
    context.user_data['name'] = update.message.text
    if update.message.text:
        context.bot.send_message(text='e-mail?', chat_id=update.effective_chat.id)
        return EMAIL


# >>>>>>>>>>>>>>>>>>>>>>> checking email and goes to location
def third_que(update: Update, context: CallbackContext):
    print(update.effective_message.message_id, context.user_data)

    context.chat_data['pattern'] = \
        '^(?:(?!.*?[.]{2})[a-zA-Z0-9](?:[a-zA-Z0-9.+!%-]{1,64}|)|\"[a-zA-Z0-9.+!% -]{1,64}\")@[a-zA-Z0-9]' \
        '[a-zA-Z0-9.-]+(.[a-z]{2,}|.[0-9]{1,})$'

    if match(context.chat_data['pattern'], update.message.text):
        context.user_data['email'] = update.message.text
        loc = [[KeyboardButton('send location', request_location=True, )]]
    
        context.bot.send_message(
            text='ok!\ncountry and city you currently reside?(u may use button location)',
            chat_id=update.effective_chat.id,
            reply_markup=ReplyKeyboardMarkup(loc))
        return LOCATION
    else:
        context.bot.send_message(text="i can't understand this email, try again plz", chat_id=update.effective_chat.id)
        return EMAIL


# >>>>>>>>>>>>>>>>>>>>>>> checks location and moving forward
def forth_que(update: Update, context: CallbackContext):
    print(update.effective_message.message_id, context.user_data)
    if update.message.text:
        context.user_data['location'] = update.message.text

        update.message.reply_text('do you have allergies or products you don’t like (and even hate)?\n'
                                  'write it down in a single message',
                                  reply_markup=None)
        return LIKE
    elif update.message.location:
        geo_coder = OpenCageGeocode(API_GEO)
        results = geo_coder.reverse_geocode(update.message.location.latitude, update.message.location.longitude)

        print(results)
        context.bot.send_message(text=f"so, you are in {results[0]['formatted']}, "
                                      f"right?",
                                 chat_id=update.effective_chat.id,
                                 reply_markup=InlineKeyboardMarkup(
                                     [[InlineKeyboardButton('y', callback_data='y')],
                                      [InlineKeyboardButton('n', callback_data='n')]]))
        context.user_data['location'] = results[0]['formatted']
        return LOC_CHECK


# >>>>>>>>>>>>>>>>>>>>>>> if user sent loc we're checking if it's right and asks about hates
def loc_check(update: Update, context: CallbackContext):
    print(update.effective_message.message_id, context.user_data)
    update.callback_query.answer()

    if update.callback_query.data == 'y':
        context.bot.edit_message_text(
            'do you have allergies or products you don’t like (and even hate)?\n'
            'write it down in a single message',
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
            reply_markup=None)
        return LIKE
    elif update.callback_query.data == 'n':
        context.bot.edit_message_text('then maybe try to write it manually?',
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=None)
        return LOCATION


# >>>>>>>>>>>>>>>>>>>>>>> stores allergies and asks about cooking
def fifth_que(update: Update, context: CallbackContext):
    print(update.effective_message.message_id, context.user_data)
    
    context.user_data["allergies or products I don't like"] = update.message.text

    if update.message.text:
        context.chat_data['cooking'] = update.message.reply_text(
            'do you love to cook?',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('y', callback_data='y'),
                                                InlineKeyboardButton('n', callback_data='n')]]))
        return COOK


# >>>>>>>>>>>>>>>>>>>>>>> stores answer and asks about shopping
def eighth_que(update: Update, context: CallbackContext):
    update.callback_query.answer()
    print(context.user_data)
    print()
    print(context.chat_data['cooking'])
    
    if update.callback_query.data == 'y':
        context.user_data['cooking'] = 'YES'
        context.bot.edit_message_text('do you enjoy food shopping?',
                                      reply_markup=InlineKeyboardMarkup(
                                          [[InlineKeyboardButton('yep', callback_data='y'),
                                            InlineKeyboardButton('hate', callback_data='n')]]
                                      ),
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)
        return SHOPPING
    elif update.callback_query.data == 'n':
        context.user_data['cooking'] = 'nope'
        context.bot.edit_message_text('would you like to start loving it?😉',
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('yep',
                                                                                               callback_data='y'),
                                                                          InlineKeyboardButton('nope',
                                                                                               callback_data='n')]]
                                                                        ),
                                      chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id)
        return WOULD_LOVE


# >>>>>>>>>>>>>>>>>>>>>>> if user dont like to cook and asks about shopping
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
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING,
                                     timeout=1)
        time.sleep(2)
    
    context.bot.edit_message_text('do you enjoy food shopping?',
                                  reply_markup=InlineKeyboardMarkup(
                                      [[InlineKeyboardButton('yep', callback_data='y'),
                                        InlineKeyboardButton('hate', callback_data='n')]]
                                  ),
                                  chat_id=update.effective_chat.id,
                                  message_id=update.effective_message.message_id)
    return SHOPPING


# >>>>>>>>>>>>>>>>>>>>>>> stores answer and asks goes to top-4
def ninth_que(update: Update, context: CallbackContext):
    print(context.user_data)
    
    update.callback_query.answer()

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
    return TOP


# >>>>>>>>>>>>>>>>>>>>>>> if he likes asks where user buys and goes to top-4
def where_shop(update: Update, context: CallbackContext):
    print(context.user_data)
    
    context.user_data['where'] = update.message.text
    
    update.message.reply_text(text='top-4 your last or most common orders in restaurant/wolt',
                              reply_markup=None)
    return TOP


# >>>>>>>>>>>>>>>>>>>>>>> stores answer about top4 and goes to fav
def tenth_que(update: Update, context: CallbackContext):
    print(context.user_data)
    
    context.user_data['top-4'] = update.message.text
    update.message.reply_text(text='do you have your favorite/traditional meals? '
                                   '(ex. if you’re eating same kind of breakfast everyday)')
    return FAV


# >>>>>>>>>>>>>>>>>>>>>>> stores answer about fav and goes to budget
def eleventh_que(update: Update, context: CallbackContext):
    print(context.user_data)
    
    context.user_data['fav'] = update.message.text
    
    update.message.reply_text(
        text="budget. how much money you spend or want to spend for food per one week?")
    return BUDGET


# >>>>>>>>>>>>>>>>>>>>>>> stores answer about budget and goes to budget
def twelfth_que(update: Update, context: CallbackContext):
    global must_delete, pains_dict
    print(context.user_data)
    
    context.user_data['budget'] = update.message.text
    
    pains_dict = {'no_just': 'no, i just want to diversify my daily menu',
                  'changed_diet': 'i changed my diet/became vegan 🌱 and need to find a menu solution for catching '
                                  'all the nutrients',
                  'problem': 'i have a strong problem with not having a good lunch in the middle of working day',
                  'time': 'i don’t like/have time for cooking',
                  'less_money': 'i want to spent less money on my food',
                  'another': 'another pain',
                  }
    pains = []
    for i in pains_dict.keys():
        pains.append([InlineKeyboardButton(pains_dict[i], callback_data=i)])
    pains.append([InlineKeyboardButton("send all these pains as msg", callback_data='msg')])
    
    update.message.reply_text(text="if there’s any pain about food you want to solve?",
                              reply_markup=InlineKeyboardMarkup(pains))
    return PAIN


# >>>>>>>>>>>>>>>>>>>>>>> stores answer about pain and asks if there is another pain
def pain(update: Update, context: CallbackContext):
    global must_delete, pains_dict, edit
    print(context.user_data)
    context.user_data['changed'] = []
    
    update.callback_query.answer()
    if update.callback_query.data == 'no_just':
        context.user_data['pain'] = "no, i just want to diversify my daily menu"
    elif update.callback_query.data == 'changed_diet':
        context.user_data['pain'] = "i changed my diet/became vegan  🌱 and need to find a menu solution \n" \
                                    "for catching all the nutrients"
    elif update.callback_query.data == 'problem':
        context.user_data['pain'] = "i have a strong problem with not having a good lunch\nin the middle of working day"
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
        txt = ''
        keyboard = []
        for i, j in enumerate(pains_dict):
            txt += str(i + 1) + ': ' + pains_dict[j] + '\n\n'
            keyboard.append([InlineKeyboardButton(str(i + 1), callback_data=j)])

        context.bot.edit_message_text(txt, chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(keyboard),
                                      )
        return PAIN
    
    edit = context.bot.edit_message_text(text='cool! now check your answers plz',
                                         chat_id=update.effective_chat.id,
                                         message_id=update.effective_message.message_id,
                                         reply_markup=None)
    
    return checking(update, context, edit)


# >>>>>>>>>>>>>>>>>>>>>>> stores answer about pain and asks if there is another pain and goes to next step
def another_pain(update: Update, context: CallbackContext):
    print(context.user_data)
    
    context.user_data['pain'] = update.message.text
    
    edit = context.bot.send_message(text='cool! now check your answers plz',
                                    chat_id=update.effective_chat.id,
                                    reply_markup=None)
    
    return checking(update, context, edit)


# >>>>>>>>>>>>>>>>>>>>>>> stores answer about pain and asks if there is another pain
def checking(update: Update, context: CallbackContext, edit):
    txt = ''
    for i in context.user_data.keys():
        if i == 'in a process':
            continue
        else:
            txt += "*" + i + "*" + ": " + str(context.user_data[i]) + ';\n\n'
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=telegram.ChatAction.TYPING,
                                 timeout=1)
    time.sleep(1)
    context.bot.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton('alright', callback_data='alright'),
         InlineKeyboardButton('wanna change', callback_data='you_better_no')], ]),
                                  chat_id=edit.chat_id,
                                  message_id=edit.message_id, )

    return CHECKING


# >>>>>>>>>>>>>>>>>>>>>>> IS EVERYTHING FINE????
def last_que(update: Update, context: CallbackContext):
    print(context.user_data)
    update.callback_query.answer()
    if update.callback_query.data == 'alright':
        context.user_data['in a process'] = False
        context.bot.forward_message(message_id=update.effective_message.message_id,
                                    chat_id=133495703,
                                    from_chat_id=update.effective_chat.id)
        context.bot.edit_message_text('this is it for now 🧡 Lina will write you back ASAP.\n'
                                      'have a delicious continuation of the day',
                                      message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id)
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


# >>>>>>>>>>>>>>>>>>>>>>> sends user to whatever he wants to change
def change_que(update: Update, context: CallbackContext):
    global edit
    print(context.user_data)
    
    update.callback_query.answer()
    for i in context.user_data.keys():
        if update.callback_query.data == i:
            context.user_data['changed'].append(i)
            edit = context.bot.edit_message_text(f'write your new {i}',
                                                 reply_markup=None,
                                                 chat_id=update.effective_chat.id,
                                                 message_id=update.effective_message.message_id)
            context.chat_data['wanna_change'] = i
    return CHANGING_NAME


def changing_answer(update: Update, context: CallbackContext):
    context.bot.deleteMessage(message_id=update.effective_message.message_id, chat_id=update.effective_chat.id)
    for i in context.user_data.keys():
        if i in context.chat_data['wanna_change']:
            context.user_data[i] = update.message.text
    
    return checking(update, context, edit)


# --------------------------------------------------------------------
def wats_up(update: Update, context: CallbackContext):
    user = update.message.from_user.username

    reply_markup = [[InlineKeyboardButton('I want to assemble my bento for tomorrow', callback_data='see_categories')],
                    [InlineKeyboardButton('see whole bento menu', callback_data='see_whole')]]
    update.effective_message.reply_text(text=f"hey, {user}, what's up?",
                                        reply_markup=InlineKeyboardMarkup(reply_markup))
    return HI


def buttons(update: Update, context: CallbackContext):
    global must_delete
    query = update.callback_query
    query.answer()
    username = update.effective_user.username
    keyboard = []
    cat_list = []
    used = set()
    
    if query.data == 'see_categories':
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
        return CATEGORY
    elif query.data == 'see_whole':
        for i in data[username]:
            keyboard.append([InlineKeyboardButton(i['name'], callback_data=i['callback'])])
        keyboard.append([InlineKeyboardButton('see whole menu ass message', callback_data='txt')])
        keyboard.append([InlineKeyboardButton('random', callback_data='random')])
        keyboard.append([InlineKeyboardButton('back', callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        must_delete = context.bot.edit_message_text(chat_id=query.message.chat_id, message_id=query.message.message_id,
                                                    text="here is your whole menu", reply_markup=reply_markup)

        return DISH


def categories(update: Update, context: CallbackContext):
    global must_delete
    query = update.callback_query
    query.answer()
    choice = query.data
    keyboard = []
    s = 0
    username = update.effective_user.username
    for i in data[username]:
        if choice in i['category']:
            s += 1
            keyboard.append([InlineKeyboardButton(i['name'], callback_data=i['callback'])])
    if len(keyboard) == s:
        keyboard.append([InlineKeyboardButton('back', callback_data='back_to_categories')])

    must_delete = context.bot.edit_message_text(chat_id=query.message.chat_id,
                                                message_id=query.message.message_id,
                                                reply_markup=InlineKeyboardMarkup(keyboard),
                                                text=f'here is recipes w/ {choice}')
    return DISH


def send_dish(update: Update, context: CallbackContext):
    username = update.effective_user.username
    update.callback_query.answer()
    query = update.callback_query
    choice = update.callback_query.data
    # context.bot.deleteMessage(message_id=must_delete.message_id, chat_id=must_delete.chat_id)
    if choice == 'back_to_categories':
        return
    elif choice == 'back':
        reply_markup = [
            [InlineKeyboardButton('I want to assemble my bento for tomorrow', callback_data='see_categories')],
            [InlineKeyboardButton('see whole bento menu', callback_data='see_whole')]]
        context.bot.edit_message_text(text=f"so, what's up?", chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(reply_markup))
        return HI
    for i in data[username]:
        if choice in i['callback']:
            context.bot.send_message(text=f'this is a recipy for *{i["name"]}* ',
                                     chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN)
            context.bot.send_chat_action(chat_id=query.message.chat_id, action=telegram.ChatAction.TYPING,
                                         timeout=1)
            time.sleep(2)
            context.bot.send_message(text=i['ingredients'], chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN)
            context.bot.send_chat_action(chat_id=query.message.chat_id, action=telegram.ChatAction.TYPING,
                                         timeout=1)
            time.sleep(2)
            context.bot.send_message(text=i['recipy'], chat_id=query.message.chat_id,
                                     parse_mode=ParseMode.MARKDOWN, )

    if choice == 'txt':
        txt = ''
        buttons_ = [[]]
        k, s = 0, 0
        for i, j in enumerate(data[username]):
            s += 1
            if s % 7 == 0:
                buttons_.append([])
                k += 1
            txt += str(i + 1) + ': ' + j['name'] + '\n\n'
            buttons_[k].append(InlineKeyboardButton(str(i + 1), callback_data=j['callback']))
    
        context.bot.edit_message_text(txt, chat_id=update.effective_chat.id,
                                      message_id=update.effective_message.message_id,
                                      reply_markup=InlineKeyboardMarkup(buttons_))
        return DISH
    return cancel(update, context)


# --------------------------------------------------------------------
def error(update, context):
    print("-" * 10, 'ERROR', '-' * 10)
    print(f"\nupdate {update} \ncaused error {context.error}\n")
    print("-" * 10, 'ERROR', '-' * 10)


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
        },
        fallbacks=[CommandHandler('stop', cancel)],
        run_async=True,
        per_user=True
    )
    
    dp.add_handler(conv_handler_new_user)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
