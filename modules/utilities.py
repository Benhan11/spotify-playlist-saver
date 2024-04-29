import random
import string
import json



### File management

def get_credentials():
    cred_f = open('credentials.json')
    cred_data = json.load(cred_f)

    return {
        'client_id': cred_data['client_id'],
        'client_secret': cred_data['client_secret']
    }


def get_stored_token():
    token_f = open('token.json')
    token_data = json.load(token_f)

    return token_data['access_token']


def save_token(access_token):
    with open('token.json', 'w', encoding='utf-8') as f:
        json.dump({'access_token': access_token}, f, ensure_ascii=False, indent=4)



### Helper functions

def generate_random_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

