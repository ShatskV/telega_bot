from collections import UserList
import logging
from emoji import emojize
import ephem
import math # нужно для eval
import warnings
from glob import glob
from random import randint, choice
from datetime import datetime
from typing import Text
import settings
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, KeyboardButton

warnings.filterwarnings("ignore", category=DeprecationWarning) 
#убрать предупреждения об устаревшем коде


logging.basicConfig(filename='bot.log', format='%(asctime)s - %(message)s', 
     datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


def check_for_calc(text_to_calc): #проверка строки для вычислений
    text_to_calc = text_to_calc.lower()
    text_to_calc = text_to_calc.replace('abs', '')
    text_to_calc = text_to_calc.replace('sqrt', '')
    if text_to_calc.count('|') % 2 == 1: # проверка на модуль числа, он должен быть закрыт
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
                                '/cat - высылаем котика Урмаса\n', 
                             reply_markup = main_keyboard()
                             )
    

def talk_to_me(update, context):
    user_text = update.message.text 
    smile = get_smile(context.user_data)
    username = update.effective_user.first_name
    print(user_text)
    update.message.reply_text(f"Здравствуй, {username} {smile}! Ты написал: {user_text}", reply_markup = main_keyboard())


class Citys_work():
    
    def __init__(self,city, user_list):
        self.city =  Citys_work.format_town(city)
        self.user_list = user_list
    
    @staticmethod
    def format_town(word):
        word = word.capitalize()
        word = word.replace('-',' ')
        return word

    @staticmethod
    def check_last_letter(city):
        if city[-1] in ('ьы'):
            letter = city[-2].capitalize()
        else:
            letter = city[-1].capitalize()
        return letter
    
    def check_city(self): #проверка города на язык 
        alphabet=set('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ -')
        city_set = set(self.city.upper())
        if alphabet.issuperset(city_set):
            return True
        return False

    def check_city_in_list(self): 
        letter = self.city[0]
        if 'letter' in self.user_list and self.user_list['letter'] != letter:
            let = self.user_list['letter']
            return 1 # город не с той буквы 

        if letter in self.user_list:
            for word in self.user_list[letter]: 
                word = Citys_work.format_town(word)                
                if word == self.city:
                    return 2 # город уже был

        if letter in settings.CITIES:
            print(f'Letter in CITIES = {letter}')
            for i in range(len(settings.CITIES[letter])):
                word = settings.CITIES[letter][i]
                word = Citys_work.format_town(word)   
                if word == self.city:
                    if letter not in self.user_list:
                        self.user_list[letter] = []
                    self.user_list[letter].append(settings.CITIES[letter][i])
                    return 0 # все ок
        return 3 #нет городов на эту букву! 
    
    def find_city(self):
        letter = Citys_work.check_last_letter(self.city)
        if letter in settings.CITIES:
            if letter in self.user_list:
                list_to_choose = list( set(settings.CITIES[letter])-set(self.user_list[letter]))
                if list_to_choose == []:
                    return 0 # победа пользователя
            else:
                list_to_choose = settings.CITIES[letter]   
        city_from_bot = choice(list_to_choose)
        letter_first = city_from_bot[0]
        if letter_first not in self.user_list:
                        self.user_list[letter] = []
        self.user_list[letter].append(city_from_bot)
        self.user_list['letter'] = Citys_work.check_last_letter(city_from_bot)
        return city_from_bot


def get_city(city, user_list):
    game = Citys_work(city,user_list)
    if game.check_city():
        status_check = game.check_city_in_list() 
        if not status_check:
            result = game.find_city()
            
            if not result:
                message = "Поздравляю, ты выиграл! Я не знаю больше городов"
                game.user_list = {}
            else: 
                letter = game.user_list['letter']
                message = f'{result} ! Ваш ход, вам на \"{letter}\"'
                if letter in game.user_list:
                    if len(settings.CITIES[letter]) == len(game.user_list[letter]):
                        message = f"{result} ! Вы проиграли! Больше городов на букву \"{letter}\" нет!"
                        game.user_list = {}
                        
        elif status_check == 1: 
            message = "Город не с той буквы!"
        elif status_check == 2:
            message = "Город уже был!"
        elif status_check == 3:           
            message = "Не существует такого города!"
    else: 
        message = 'Город должен быть на кирилице!'

    return message, game.user_list


def game_city(update, context):
    user_text = update.message.text
   
    if 'list_cities' not in context.user_data:
            context.user_data['list_cities']={}

    if not context.args:
        message ="Сыграем в города?\nОтправь \"/cities название_города_на_русском\"\n"\
                    "/cities new - Сброс игры"
    else:
        if settings.CITIES:
            if context.args[0] == "new":
                if 'list_cities' in context.user_data:
                    context.user_data['list_cities'] = {}
                    message = "Начата новая игра!"
            else:    
                city = ' '.join(context.args)
                message, context.user_data['list_cities'] = get_city(city, context.user_data['list_cities'])
        else: 
            message ="База городов пустая, игра невозможна!"

    update.message.reply_text(message, reply_markup = main_keyboard())

         
def guess_number(update, context):
    if context.args:
        try:
            user_number = int(context.args[0])
            message = play_random_numbers(user_number)
        except (TypeError, ValueError):
            message = "Введите целое число"
    else:
        message = "Введите целое число"
    update.message.reply_text(message, reply_markup = main_keyboard())


def send_cat_picture(update, context):
    cat_photos_list = glob('images/cat*.jp*g')
    cat_pic_filename = choice(cat_photos_list)
    chat_id = update.effective_chat.id
    context.bot.send_photo(chat_id=chat_id, photo=open(cat_pic_filename, 'rb'), reply_markup = main_keyboard())


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
            while expression.count('|') > 0: # заменим |..| на abs(..)
                if expression.count('|')%2 == 0:
                    ch = 'abs('
                else:
                    ch = ')'
                pos = expression.find('|')
                expression = expression[:pos] + ch + expression[pos+1:] 
            try:
                answer = eval(expression)
                if isinstance(answer, complex):
                    answer = f"Решения в вещественных числах нет! Комплексное: {answer}"
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
    update.message.reply_text(answer, reply_markup = main_keyboard())
    

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
    
    update.message.reply_text(constellation, reply_markup = main_keyboard())
    

def user_coordinates(update, context):
    context.user_data['emoji'] = get_smile(context.user_data)
    coords = update.message.location
    update.message.reply_text (
        f"Ваши координаты {coords} {context.user_data['emoji']}!",
        reply_markup = main_keyboard()
    )

def main_keyboard():
    return ReplyKeyboardMarkup([['Прислать котика', KeyboardButton('Мои координаты', request_location=True)]], resize_keyboard=True)


def main():
    mybot = Updater(settings.API_KEY, use_context=True)
    dp = mybot.dispatcher

    dp.add_handler(CommandHandler("start", greet_user))
    dp.add_handler(CommandHandler("calc", calculator))
    dp.add_handler(CommandHandler("guess", guess_number))
    dp.add_handler(CommandHandler("cities", game_city))
    dp.add_handler(CommandHandler("planet", constellation_planet))
    dp.add_handler(CommandHandler("cat", send_cat_picture))
    dp.add_handler(MessageHandler(Filters.regex('^(Прислать котика)$'), send_cat_picture))
    dp.add_handler(MessageHandler(Filters.location, user_coordinates))
    dp.add_handler(MessageHandler(Filters.text, talk_to_me))

    
    logging.info("Бот стартовал")
    mybot.start_polling()
    print('Bot started!')

    mybot.idle()

if __name__ == "__main__":
    main()