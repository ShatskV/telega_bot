import logging
import ephem
import warnings
from datetime import datetime
from typing import Text
import settings
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

warnings.filterwarnings("ignore", category=DeprecationWarning) 
#убрать предупреждения об устаревшем коде


logging.basicConfig(filename='bot.log', format='%(asctime)s - %(message)s', 
     datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def greet_user(update, context):
    print('Вызван /start')
    update.message.reply_text('Привет, пользователь! Ты вызвал команду /start')

def talk_to_me(update, context):
    user_text = update.message.text 
    print(user_text)
    update.message.reply_text(user_text)

def constellation_planet(update, context):
    user_text = update.message.text
    data = user_text.split()
    
    if len(data) == 2: # проверка на правильность запроса
        try: 
            planet = getattr(ephem, data[1].capitalize())(datetime.today())
            constellation = ephem.constellation(planet)
            constellation = f'{constellation[0]}, {constellation[1]}'
        except AttributeError: 
            constellation = 'Такого объекта нет!'
    else:
        constellation = 'Неверный запрос!'
    
    update.message.reply_text(constellation)

    

def main():
    mybot = Updater(settings.API_KEY, use_context=True)

    dp = mybot.dispatcher
    dp.add_handler(CommandHandler("start", greet_user))
    dp.add_handler(CommandHandler("planet", constellation_planet))
    dp.add_handler(MessageHandler(Filters.text, talk_to_me))

    logging.info("Бот стартовал")

    mybot.start_polling()

    mybot.idle()

if __name__ == "__main__":
    main()