import random
import string
import json
import os
import re
from datetime import date


output_path = 'output'


### File management

def get_credentials():
    cred_f = open('credentials.json')
    cred_data = json.load(cred_f)

    return cred_data


def get_stored_token():
    token_f = open('token.json')
    token_data = json.load(token_f)

    return token_data


def save_token(access_token):
    with open('token.json', 'w', encoding='utf-8') as f:
        json.dump({'access_token': access_token}, f, ensure_ascii=False, indent=4)


def save_playlist(playlist, items):
    folder_path = f'./{output_path}/{date.today().strftime("%Y-%m-%d")}'

    # Create folder for the current date if it does not exist already
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Replace unallowed file name characters with whitespaces
    safe_filename = re.sub(r'[^\w\s\-_.,~+]', ' ', playlist['name'])
    file_path = f'{folder_path}/{safe_filename}.json'

    data = {
        'name': playlist['name'],
        'owner': playlist['owner'],
        'description': playlist['description'],
        'tracks': items
    }

    f = open(file_path, 'w')
    f.write(json.dumps(data, indent=4))
    f.close()



### Helper functions

def generate_random_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))
