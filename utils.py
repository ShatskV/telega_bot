from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc, service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2
from pprint import PrettyPrinter
from emoji import emojize
from random import choice, randint
from telegram import ReplyKeyboardMarkup, KeyboardButton

import settings


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


def main_keyboard():
    return ReplyKeyboardMarkup(
        [['Прислать котика', 
        KeyboardButton('Мои координаты', request_location=True), 
         'Заполнить анкету']], resize_keyboard=True)


def check_for_calc(text_to_calc): # проверка строки для вычислений
    text_to_calc = text_to_calc.lower()
    text_to_calc = text_to_calc.replace('abs', '')
    text_to_calc = text_to_calc.replace('sqrt', '')
    if text_to_calc.count('|') % 2 == 1: # проверка на модуль числа, он должен быть закрыт
        return False
    alphabet=set('12345678910/%*+-().|')
    text_to_calc = set(text_to_calc)
    return alphabet.issuperset(text_to_calc)
       

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

def is_cat(file_name):
    channel = ClarifaiChannel.get_grpc_channel()
    app = service_pb2_grpc.V2Stub(channel)
    metadata = (('authorization', f'Key {settings.CLARIFAI_API_KEY}'),)
    with open(file_name, 'rb') as f:
        file_data = f.read()
        image = resources_pb2.Image(base64=file_data)
    
    request = service_pb2.PostModelOutputsRequest(
        model_id='aaa03c23b3724a16a56b629203edc62c',
        inputs=[
            resources_pb2.Input(data=resources_pb2.Data(image=image))
        ])

    response = app.PostModelOutputs(request, metadata=metadata)

    return check_responce_for_cat(response)


def check_responce_for_cat(response):
    if response.status.code == status_code_pb2.SUCCESS:
        for concept in response.outputs[0].data.concepts:
            if concept.name == 'cat' and concept.value >= 0.85:
                return True
    else:
        print(f"Ошибка распознавания: {response.outputs[0].status.details}")

    return False


if __name__ == "__main__":
    pp = PrettyPrinter(indent=2)
    pp.pprint(is_cat("images/cat_band.JPEG"))    