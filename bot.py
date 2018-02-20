
#!/root/anaconda/bin/python
# coding: utf-8

from telegram.ext import Updater, CommandHandler
from telegram.emoji import Emoji
from telegram import ReplyKeyboardMarkup, ReplyKeyboardHide

import botan

import MySQLdb

import datetime

import logging

# Enable logging
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

logger = logging.getLogger(__name__)


# Это токен от бота vsh_emsch_bot
#TELEGRAM_TOKEN = '181895996:xxxxxxxxxx'
# Это токен от бота emsch_bot
TELEGRAM_TOKEN = "189616764:xxxxxxxxx"
# Это ботан от бота vsh_emsch_bot
#BOTAN_IO = ':Lrzuu0cC1lH-xxxxxxx'
# Это ботан от бота emsch_bot
BOTAN_IO = 'xxxxxxxxxxxx'


# HELP_MESSAGE = u'''Для управления мной вводи следующие команды:
# /schedule — узнать расписание на весь день
# /next — узнать следующий пункт расписания
# /road — узнать маршруты для доезда на автомобиле
# /travel — узнать, как добраться общественным транспортом
# /profile — получить информацию о текущем лекторе (лекторах) *если идея с профайлами людей будет воплощена в жизнь*
# /food — узнать, когда будет ближайший приём пищи
# /place *ФИО* — узнать, где проживает определённый человек *при наличии базы вида Имя — Номер*
# /orgorg — узнать контакты организаторов'''


HELP_MESSAGE = u'''Для управления мной вводи следующие команды:
/schedule — расписание на весь день
/next — следующий пункт расписания
/car — маршруты для автомобиля
/public_transport — как добраться общественным транспортом
/food — когда будет ближайший приём пищи
/org — контакты организаторов'''

YA_MAPS_URL = "https://maps.yandex.ru/-/CVHMmL-E"

HOW_TO_GET_THERE = 'http://vsh.emsch.ru/how_to_get_there.php?from=telegram'

CUSTOM_KEYBOARD = [[ '/schedule', '/next', '/food' ],
                   [ '/car', '/transport', '/org' ]
                  ]
REPLY_MARKUP = ReplyKeyboardMarkup(CUSTOM_KEYBOARD)
CUSTOM_KEYBOARD = [ ['/schedule 22'], ['/schedule 23'], ['/schedule 24'],
                     ['/schedule 25'], ['/schedule 26'] 
                  ]
REPLY_MARKUP_SUGGESTER = ReplyKeyboardMarkup(CUSTOM_KEYBOARD)

ADMIN_CHAT_ID = 116525440

def botan_track(command):
    def decorator(function):
        def wrapper(*args, **kwargs):
            function(*args, **kwargs)
            update = args[1]
            uid = update.message.from_user.id
            print uid
            message_dict = update.message.to_dict()
            #event_name = update.message.text
            botan.track(BOTAN_IO, uid, message_dict, command)

        return wrapper
    return decorator

def run_mysql(command):
    db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                         user="vsh",         # your username
                         passwd="xxxxxxxxx",  # your password
                         db="vsh",
                         charset='utf8',
                         use_unicode=True)        # name of the data base
    cur = db.cursor()
    cur.execute(command)
    res = cur.fetchall()
    db.close()
    return res

def today():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def now():
    return datetime.datetime.now().strftime("%H:%M")

def _process_lectures(fetched, bot, update):
    answer = []
    for time, title, guest1, guest2, guest3 in fetched:
        if time < "04:00":
            continue

        guests_names = []
        for guest_id in (guest1, guest2, guest3):
            if guest_id == 0:
                continue
            
            query = "SELECT first_name, last_name FROM guests WHERE id='%s'" % guest_id
            fetched = run_mysql(query)
            guests_names.append(' '.join(fetched[0]))

        answer_line = "%s: %s"%(time, title)
        if len(guests_names) > 0:
            answer_line += " | %s" % ', '.join(guests_names)
        answer.append(answer_line)
    return answer

@botan_track('start')
def start(bot, update):
   bot.sendMessage(chat_id=update.message.chat_id, text=u'''Привет! Это я, ЭМШовый бот.  
Я создан для того, чтобы упростить твоё пребывание на Выездной.\n\n''' + HELP_MESSAGE,
    reply_markup = REPLY_MARKUP)

@botan_track('help')
def help(bot, update):
    bot.sendMessage(update.message.chat_id, text=HELP_MESSAGE, reply_markup = REPLY_MARKUP)

@botan_track('schedule')
def schedule(bot, update):
    if update.message.text == '/schedule':
        date = today()
    else:
        user_date_str = update.message.text.replace('/schedule ', '')
        if user_date_str in [str(i) for i in range(19, 27)]:  # На самом деле хз когда ВШ, это проверка на идиота
            date = datetime.datetime(2017, 02, int(user_date_str)).strftime('%Y-%m-%d')
        else:
            bot.sendMessage(update.message.chat_id, 
                text="Неверный формат даты. Укажите день одним числом, например, /schedule 23")
            return

    query = "SELECT time, title, guest1, guest2, guest3 FROM events WHERE date = '%s' ORDER BY time ASC" % date
    fetched = run_mysql(query)
    answer = _process_lectures(fetched, bot, update)
    
    if len(answer) > 1:
        bot.sendMessage(update.message.chat_id, text='\n'.join(answer))
    else:
        bot.sendMessage(update.message.chat_id, 
            text="На этот день нет лекций. Кажется, ВШ ещё не началась. " 
            "Узнать расписание конкретного дня можно командой /schedule 22 (для 22 февраля)",
            reply_markup = REPLY_MARKUP_SUGGESTER)

@botan_track('next')
def next_lecture(bot, update):
    date, time = today(), now()
    #DEBUG:
    #date, time = '2016-02-22', '09:55'
    query = "SELECT time, title, guest1, guest2, guest3 FROM events WHERE date = '%s' " \
            "AND type = 'lecture' AND time > '%s' ORDER BY time ASC LIMIT 1" % (date, time)
    fetched = run_mysql(query)
    answer = _process_lectures(fetched, bot, update)
    answer = [u'Следующая лекция:'] + answer
    if len(answer) > 1:
        bot.sendMessage(update.message.chat_id, text="\n".join(answer),
                        reply_markup=REPLY_MARKUP)
    else:
        bot.sendMessage(
            update.message.chat_id, text='Сегодня лекций больше нет. '
            'Расписание на завтра можно узнать командой /schedule %s' % (datetime.datetime.now().day + 1),
            reply_markup=REPLY_MARKUP_SUGGESTER
        )

@botan_track('food')
def food(bot, update):
    date, time = today(), now()
    #DEBUG:
    # date, time = '2016-02-22', '09:55'
    query = "SELECT time, title, guest1, guest2, guest3 FROM events WHERE date = '%s' " \
            "AND type = 'food' AND time > '%s' ORDER BY time ASC LIMIT 1" % (date, time)
    fetched = run_mysql(query)
    answer = _process_lectures(fetched, bot, update)
    answer = [u'Следующий приём пищи:'] + answer
    if len(answer) > 1:
        bot.sendMessage(update.message.chat_id, text="\n".join(answer),
               reply_markup = REPLY_MARKUP)
    else:
        bot.sendMessage(update.message.chat_id, text='На сегодня столовая закрыта',
               reply_markup = REPLY_MARKUP)


@botan_track('org')
def org(bot, update):
    names = ['Саша Москалева +7(915)204-26-03 @Sasha_Moskaleva',
             'Катя Лебедева +7(915)406-73-75 @katerina_lebedeva',
             'Наташа Ситникова +7(903)613-80-30',
             'Надя Николаева +7(916)342-27-64'
            ]
    prefixes = [Emoji.WHITE_MEDIUM_STAR] * len(names)
    suffixes = [''] * len(names)

    query = "SELECT num FROM options WHERE id='onduty'"
    fetched = run_mysql(query)
    onduty = int(fetched[0][0])
    print onduty

    if onduty < len(names):
        prefixes = [Emoji.SLEEPING_FACE] * len(names)
        prefixes[onduty] = Emoji.HEAVY_EXCLAMATION_MARK_SYMBOL
        suffixes[onduty] = Emoji.LEFTWARDS_BLACK_ARROW + " дежурная"

    text = 'Контакты организаторов: \n'
    text += '\n'.join((' '.join(line) for line in zip(prefixes, names, suffixes)))

    bot.sendMessage(update.message.chat_id, text=text, reply_markup = REPLY_MARKUP)

@botan_track('car')
def car(bot, update):
    short_url = botan.shorten_url(YA_MAPS_URL, BOTAN_IO, update.message.from_user.id)

    bot.sendMessage(update.message.chat_id, text=u'Маршрут построен! Выберите самый удобный ' \
        u'из трех возможных маршрутов до пансионата "Университетский": %s' % short_url,
               reply_markup = REPLY_MARKUP)

@botan_track('public_transport')
def public_transport(bot, update):
    short_url = botan.shorten_url(HOW_TO_GET_THERE, BOTAN_IO, update.message.from_user.id)

    bot.sendMessage(update.message.chat_id, text=u'Электричка отправляется с Белорусского вокзала. ' \
        u'Описание маршрутов общественного транспорта до пансионата "Университетский" ' \
        u'на сайте ВШ: %s' % short_url,
               reply_markup = REPLY_MARKUP)

def kill_keyboard(bot, update):
    reply_markup = ReplyKeyboardHide()
    bot.sendMessage(update.message.chat_id, text="Okay. \xf0\x9f\x98\xa5", reply_markup=reply_markup)

def test(bot, update):
    import time
    time.sleep(10)
    bot.sendMessage(update.message.chat_id, text="Okay. Ping. Now that?!")

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))
    # bot.sendMessage(ADMIN_CHAT_ID, text='Update "%s" caused error "%s"' % (update, error))

def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TELEGRAM_TOKEN, workers=5)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('schedule', schedule))
    dp.add_handler(CommandHandler('next', next_lecture))
    dp.add_handler(CommandHandler('org', org))
    dp.add_handler(CommandHandler('orgorg', org))
    dp.add_handler(CommandHandler('car', car))
    dp.add_handler(CommandHandler('food', food))
    dp.add_handler(CommandHandler('public_transport', public_transport))
    dp.add_handler(CommandHandler('transport', public_transport))
    dp.add_handler(CommandHandler('kill_keyboard', kill_keyboard))
    dp.add_handler(CommandHandler('hide_keyboard', kill_keyboard))
    dp.add_handler(CommandHandler('test', test))


    # log all errors
    dp.addErrorHandler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
