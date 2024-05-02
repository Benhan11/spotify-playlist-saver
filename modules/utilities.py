import random
import string
import json
import os
import re
from datetime import date


output_path = 'output'


### File management

def get_credentials():
    """
    Reads `client_id` and `client_secret` credentials from the 
    `credentials.json` file and returns them.

    Returns:
    dict: Dictionary containing the credentials.
    """

    cred_f = open('credentials.json')
    cred_data = json.load(cred_f)

    return cred_data


def get_stored_token():
    """
    Reads `access_token` from the `token.json` file and returns it.

    Returns:
    dict: Dictionary containing the access token.
    """

    token_f = open('token.json')
    token_data = json.load(token_f)

    return token_data


def save_token(access_token):
    """
    Saves the access token to the `token.json` file.

    Parameters:
    access_token (str): The access token to be saved.
    """

    with open('token.json', 'w', encoding='utf-8') as f:
        json.dump({'access_token': access_token}, f, ensure_ascii=False, indent=4)


def save_playlist(playlist, items):
    """
    Saves a playlist and it's items to a JSON file.

    The file will contain `name`, `owner`, `description`, and the `tracks` of 
    the playlist. Additionally, a directory named after the current date will
    be created to store this file if it doesn't already exist. The filename
    will be the playlist name with unallowed file characters replaced with
    whitespace.

    Parameters:
    playlist (dict): The playlist metadata.
    items (list): List of playlist tracks.
    """

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
    """
    Generates a random string of the requested length, consisting letters
    and digits.

    Parameters:
    length (int): The length of the string.
    """

    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))
