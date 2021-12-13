import logging
import ephem
import math # нужно для eval
import warnings
from random import choice
import settings
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, commandhandler

from anketa import anketa_start, anketa_name, anketa_rating, anketa_skip, anketa_comment, anketa_dontknow
from handlers import  (greet_user, guess_number, send_cat_picture, user_coordinates,
                        talk_to_me, calculator, game_city, constellation_planet,
                        check_user_photo)

warnings.filterwarnings("ignore", category=DeprecationWarning) 
# убрать предупреждения об устаревшем коде

logging.basicConfig(filename='bot.log', format='%(asctime)s - %(message)s', 
     datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


def main():
    mybot = Updater(settings.API_KEY, use_context=True)
    dp = mybot.dispatcher
    anketa = ConversationHandler(
                entry_points=[
                    MessageHandler(Filters.regex('^(Заполнить анкету)$'), anketa_start)
                ],
                states={
                    "name":[MessageHandler(Filters.text, anketa_name)],
                    "rating": [MessageHandler(Filters.regex('^(1|2|3|4|5)$'), anketa_rating)],
                    "comment": [CommandHandler("skip", anketa_skip),
                                MessageHandler(Filters.text, anketa_comment)                    
                    ]
                },
                fallbacks=[
                    MessageHandler(Filters.text | Filters.photo | Filters.video | Filters.document | Filters.location, anketa_dontknow)
                ]
                        )
    dp.add_handler(anketa)
    dp.add_handler(CommandHandler("start", greet_user))
    dp.add_handler(CommandHandler("calc", calculator))
    dp.add_handler(CommandHandler("guess", guess_number))
    dp.add_handler(CommandHandler("cities", game_city))
    dp.add_handler(CommandHandler("planet", constellation_planet))
    dp.add_handler(CommandHandler("cat", send_cat_picture))
    dp.add_handler(MessageHandler(Filters.regex('^(Прислать котика)$'), send_cat_picture))
    dp.add_handler(MessageHandler(Filters.photo, check_user_photo))
    dp.add_handler(MessageHandler(Filters.location, user_coordinates))
    dp.add_handler(MessageHandler(Filters.text, talk_to_me))

    
    logging.info("Бот стартовал")
    mybot.start_polling()
    print('Bot started!')

    mybot.idle()

if __name__ == "__main__":
    main()