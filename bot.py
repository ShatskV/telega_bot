import logging
from emoji import emojize
import ephem
# import math
import warnings
from glob import glob
from random import randint, choice
from datetime import datetime
from typing import Text
import settings
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

warnings.filterwarnings("ignore", category=DeprecationWarning) 
#убрать предупреждения об устаревшем коде

logging.basicConfig(filename='bot.log', format='%(asctime)s - %(message)s', 
     datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def check_for_calc(text_to_calc): #проверка строки для вычислений
    text_to_calc = text_to_calc.lower()
    text_to_calc = text_to_calc.replace('abs', '')
    text_to_calc = text_to_calc.replace('sqrt', '')
    if text_to_calc.count('|') % 2 == 1: #проверка на модуль числа, он должен быть закрыт
        return False
    alphabet=set('12345678910/%*+-().|')
    text_to_calc = set(text_to_calc)
    return alphabet.issuperset(text_to_calc)
           
       
def get_smile(user_data):
    if 'emoji' not in user_data:
        smile = choice(settings.USER_EMOJI)
        return emojize(smile, use_aliases=True)
    return user_data['emoji']


def play_random_numbers(user_number):
    bot_number = randint(user_number-10, user_number+10)
    if user_number > bot_number:
        message = f"Ты загадал {user_number}, я загадал {bot_number}, тебе повезло в !"
    elif user_number == bot_number:
        message = f"Ты загадал {user_number}, я загадал {bot_number}, ничья!"
    else:
        message = f"Ты загадал {user_number}, я загадал {bot_number}, я выиграл!"
    return message  


def greet_user(update, context):
    print('Вызван /start')
    context.user_data['emoji'] = get_smile(context.user_data)
    update.message.reply_text(f"Привет, пользователь {context.user_data['emoji']}!\nТы вызвал команду /start\n"
                                '/planet имя_паланеты_латиницей - определение созвездия\n'
                                '/calc _выражение_ - калькулятор\n'
                                '/guess целое_число - игра с числами\n'
                                '/cat - высылаем котика Урмаса\n')


def talk_to_me(update, context):
    user_text = update.message.text 
    smile = get_smile(context.user_data)
    username = update.effective_user.first_name
    print(user_text)
    update.message.reply_text(f"Здравствуй, {username} {smile}! Ты написал: {user_text}")


def game_city(update, context):
    user_text = update.message.text
    if not context.args:
        message ="Сыграем в города?\nОтправь \"/cities название_города_на_русском\"\n"\
                    "/cities new - Сброс игры"
    else:
        if context.args[0] == "new":
            if 'list_cities' in context.user_data:
                del context.user_data['list_cities']
        else:    
            city = ' '.join(context.args)
            print(city)

    update.message.reply_text(message)
        # find_city(city, context.user_data)

         
def guess_number(update, context):
    if context.args:
        try:
            user_number = int(context.args[0])
            message = play_random_numbers(user_number)
        except (TypeError, ValueError):
            message = "Введите целое число"
    else:
        message = "Введите целое число"
    update.message.reply_text(message)


def send_cat_picture(update, context):
    cat_photos_list = glob('images/cat*.jp*g')
    cat_pic_filename = choice(cat_photos_list)
    chat_id = update.effective_chat.id
    context.bot.send_photo(chat_id=chat_id, photo=open(cat_pic_filename, 'rb'))


def calculator(update, context): 
    user_text = update.message.text
    data_to_calc = user_text.split(" ",1)
    answer = "Неверный запрос!"

    if len(data_to_calc) == 2 and data_to_calc[1]:
        expression = data_to_calc[1]
        expression = expression.replace(' ','')
        expression = expression.lower().replace(',','.')
        
        if check_for_calc(expression):
            expression = expression.replace('sqrt','math.sqrt')
            while expression.count('|') > 0: #заменим |..| на abs(..)
                if expression.count('|')%2 == 0:
                    ch = 'abs('
                else:
                    ch = ')'
                pos = expression.find('|')
                expression = expression[:pos] + ch + expression[pos+1:] 
            try:
                answer =str(eval(expression))
            except ZeroDivisionError:
                answer = "На ноль делить нельзя!"
            except SyntaxError:
                answer = "Ошибка в выражении для расчета!"
            except (ValueError, TypeError):
                answer = "Нельзя извлечь корень/возводить в степень меньше 1 если число отрицательное!"
            finally:
                print(answer)
    else:
        answer = "операторы: + , - , * , / , // , % , ** , sqrt , |..| или abs(..) "
    update.message.reply_text(answer)
    

def constellation_planet(update, context):
    user_text = update.message.text
    data = user_text.split()
    
    if len(data) == 2: # проверка на правильность запроса
        try: 
            planet_name = data[1].capitalize()
            day_now = datetime.today()
            planet = getattr(ephem, planet_name)(day_now)
            constellation = ephem.constellation(planet)
            constellation = f'{constellation[0]}, {constellation[1]}'
            
        except AttributeError: # getattr
            constellation = 'Такого объекта нет!' 
        except (ValueError, TypeError) as err: # ephem.constellation
            constellation = f'функция созвездий неисправна! Ошибка: {err}'
    else:
        constellation = 'Неверный запрос!'
    
    update.message.reply_text(constellation)

    

def main():
    mybot = Updater(settings.API_KEY, use_context=True)
    dp = mybot.dispatcher
    dp.add_handler(CommandHandler("start", greet_user))
    dp.add_handler(CommandHandler("calc", calculator))
    dp.add_handler(CommandHandler("guess", guess_number))
    dp.add_handler(CommandHandler("cities", game_city))
    dp.add_handler(CommandHandler("planet", constellation_planet))
    dp.add_handler(CommandHandler("cat", send_cat_picture))
    dp.add_handler(MessageHandler(Filters.text, talk_to_me))
    # Cities = settings.CITIES
    logging.info("Бот стартовал")
    print(settings.CITIES.keys())
    mybot.start_polling()

    mybot.idle()

if __name__ == "__main__":
    main()