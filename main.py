from modules import utilities
from flask import Flask, request, redirect, render_template
import requests
import urllib.parse
import base64



app = Flask(__name__)


### API
credentials = utilities.get_credentials()

user_code = None
access_token = None
authorization_header = None

SPOTIFY_AUTHORIZATION_ENDPOINT = 'https://accounts.spotify.com/authorize'
SPOTIFY_GET_USER_ENDPOINT = 'https://api.spotify.com/v1/me'
SPOTIFY_GET_PLAYLISTS_ENDPOINT = 'https://api.spotify.com/v1/me/playlists'
SPOTIFY_GET_PLAYLIST_ITEMS_ENDPOINT = lambda id: f'https://api.spotify.com/v1/playlists/{id}/tracks'
SPOTIFY_TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token'
REDIRECT_URI = 'http://localhost:8888/callback'

SCOPES = 'user-read-private user-read-email playlist-read-private'


### Instance variables
fetched_user = None
fetched_playlists_metadata = None



### Requests

def fetch_access_token():
    global credentials

    headers = {
        'Authorization': 'Basic ' + base64.b64encode(f'{credentials["client_id"]}:{credentials["client_secret"]}'.encode()).decode(),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'code': user_code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    
    response = requests.post(SPOTIFY_TOKEN_ENDPOINT, headers=headers, data=data, json=True)

    global access_token

    try:
        return response.json()['access_token']
    except:
        return None


def fetch_user():
    response = requests.get(SPOTIFY_GET_USER_ENDPOINT, headers=authorization_header)

    if not response.ok:
        return None
    
    data = response.json()

    return {
        'display_name': data['display_name'],
        'images': data['images']
    }



def fetch_playlists_metadata(url=SPOTIFY_GET_PLAYLISTS_ENDPOINT, items=[]):
    # Ensure items gets reset each time this function is called anew
    if url == SPOTIFY_GET_PLAYLISTS_ENDPOINT:
        items = []
    
    response = requests.get(url, headers=authorization_header)

    if not response.ok:
        return []
    
    data = response.json()

    for item in data['items']:
        items.append({
            'name': item['name'],
            'owner': item['owner']['display_name'],
            'description': item['description'],
            'images': item['images'],
            'id': item['id']
        })

    if data['next']:
        return fetch_playlists_metadata(url=data['next'], items=items)
    
    return items


def fetch_playlist_items(id=None, url=None, items=[]):
    if id:
        url = SPOTIFY_GET_PLAYLIST_ITEMS_ENDPOINT(id)
        items = []

    response = requests.get(url, headers=authorization_header)

    if not response.ok:
        return []
    
    data = response.json()

    for item in data['items']:
        items.append({
            'name': item['track']['name'],
            'album': item['track']['album']['name'],
            'artists': list(map(lambda artist: artist['name'], item['track']['artists'])),
            'added_at': item['added_at'],
            'added_by': item['added_by']['id'],
            'id': item['track']['id']
        })

    if data['next']:
        return fetch_playlist_items(url=data['next'], items=items)

    return items



### Routes

@app.route('/')
def index():
    if not user_code or not access_token:
        return redirect('/authorize')
    
    global fetched_user, fetched_playlists_metadata

    fetched_user = fetch_user()
    fetched_playlists_metadata = fetch_playlists_metadata()

    return render_template('home_page.html', user=fetched_user, playlists=fetched_playlists_metadata)


@app.route('/backup')
def backup():
    if not user_code or not access_token:
        return redirect('/authorize')

    global fetched_playlists_metadata

    for playlist in fetched_playlists_metadata:
        items = fetch_playlist_items(playlist['id'])
        utilities.save_playlist(playlist, items)

    return render_template('success_page.html')


@app.route('/authorize')
def authorize_user():
    global credentials

    ### TODO Check token validity
    # if token is valid, redirect to homepage

    state = utilities.generate_random_string(16)

    query_params = {
        'client_id': credentials['client_id'],
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'state': state
    }

    auth_url = f'{SPOTIFY_AUTHORIZATION_ENDPOINT}?{urllib.parse.urlencode(query_params)}'
    return redirect(auth_url)


@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')

    if not code or not state:
        return render_template('error_page.html')
    else:
        global user_code
        user_code = code
        
    global access_token
    access_token = fetch_access_token()

    if access_token != None:
        global authorization_header
        
        authorization_header = { 'Authorization': f'Bearer {access_token}' }
        utilities.save_token(access_token)
    else:
        return render_template('error_page.html')

    return redirect('/')



### Entry point
if __name__ == '__main__':
    app.run(port=8888, debug=True)