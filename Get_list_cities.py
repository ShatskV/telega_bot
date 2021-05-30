import json
def get_cities(path_cities):
    cities = {}
    try: 
        with open(path_cities, 'r') as file:
            raw_data = file.read()
            if raw_data:
                cities = json.loads(raw_data)
    except FileNotFoundError as err:
        print("файл не найден!")
    finally:
        return cities