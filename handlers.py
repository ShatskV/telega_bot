from glob import glob
import ephem
import os
from random import choice
import math # для eval
from datetime import datetime




from utils import (get_smile, play_random_numbers, main_keyboard, get_city,
                    check_for_calc, is_cat)

import settings

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


def user_coordinates(update, context):
    context.user_data['emoji'] = get_smile(context.user_data)
    coords = update.message.location
    update.message.reply_text (
        f"Ваши координаты {coords} {context.user_data['emoji']}!",
        reply_markup = main_keyboard())


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
                if expression.count('|') % 2 == 0:
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
        planet_name = data[1].capitalize()
        day_now = datetime.today()
        try:
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


def check_user_photo(update, context):
    update.message.reply_text('Обрабатываем фото')
    os.makedirs("downloads", exist_ok=True)
    user_photo = context.bot.getFile(update.message.photo[-1].file_id)
    file_name = os.path.join("downloads", f"{user_photo.file_id}.jpg")
    user_photo.download(file_name)
    if is_cat(file_name):
        update.message.reply_text("Обнаружен котик, добавляю в библиотеку")
        new_filename = os.path.join("images", f"cat_{user_photo.file_id}.jpg")
        os.rename(file_name, new_filename)
    else:
        update.message.reply_text('котик на фото не обнаружен')
        os.remove(file_name)

