from modules import utilities
from flask import Flask, request, redirect, render_template, jsonify
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
    """
    Trades the user code for an OAuth2 access token through the Spotify API.

    Encodes the `Authorization` header with base64.

    Returns:
    str or None: The access token, or none in the case of failure.
    """

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
    """
    Fetches user information for the current user through the Spotify API.
    
    The user information contains `display_name` and `images`.

    Returns:
    dict or None: A dictionary, or None in the case of failure.
    """
    
    response = requests.get(SPOTIFY_GET_USER_ENDPOINT, headers=authorization_header)

    if not response.ok:
        return None
    
    data = response.json()

    return {
        'display_name': data['display_name'],
        'images': data['images']
    }



def fetch_playlists_metadata(url=SPOTIFY_GET_PLAYLISTS_ENDPOINT, items=[]):
    """
    Fetches metadata for all the current user's playlists through the Spotify
    API. Subsequent pages are fetched recursively where url is the provided
    `next` url.
    
    The metadata contains `name`, `owner`, `description`, `images`, and `id`.

    Parameters:
    url (str, optional): The URL of the Spotify endpoint to fetch metadata
        for each of the current user's playlists. Defaults to the
        'SPOTIFY_GET_PLAYLISTS_ENDPOINT', intended for the initial request.
    items (list, optional): A list of accumulated playlist metadata, this
        parameter persists recursively to gather all subsequent pages of 
        metadata. Defaults to an empty list for the initial call.

    Returns:
    list: Metadata for all playlists.
    """
    
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
    """
    Fetches all the tracks for a playlist through the Spotify API. Fetches
    subsequent pages using the provided `next` url.
    
    Each track contains `name`, `album`, `artists`, `added_at`, `added_by`, 
    and `id`.

    Parameters:
    id (str, optional): The id of the playlists to fetch the tracks for.
        Defaults to None for subsequent recursive calls.
    url (str, optional): The URL of the Spotify endpoint to fetch playlist
        items from. Defaults to None for the initial call. Used by 
        subsequent recursive calls.
    items (list, optional): A list of accumulated playlist tracks, this
        parameter persists recursively to gather all subsequent pages of 
        tracks. Defaults to an empty list for the initial call.

    Returns:
    list: The playlist's tracks.
    """

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

@app.route('/', methods=['GET'])
def index():
    """
    Renders the homepage.

    If `user_code` or `access_token` is missing, redirects to the authorize
    route. Otherwise, fetches user information and each playlist's metadata, 
    and renders the home_page.html template.

    Returns:
        str or Response: Rendered HTML template of the homepage. Returns a 
        redirect response object upon bad authorization.  
    """

    if not user_code or not access_token:
        return redirect('/authorize')
    
    global fetched_user, fetched_playlists_metadata

    fetched_user = fetch_user()
    fetched_playlists_metadata = fetch_playlists_metadata()

    return render_template('home_page.html', user=fetched_user, playlists=fetched_playlists_metadata)


@app.route('/', methods=['POST'])
def backup():
    """
    Creates backups of all user playlists.

    If `user_code` or `access_token` is missing, redirects to the authorize
    route. Otherwise, fetches each playlist's items and saves them locally
    with the `save_playlist` function from the `utilities` module.

    Returns:
        Response: JSON response indicating success, or a redirect response 
        object upon bad authorization.
    """

    if not user_code or not access_token:
        return redirect('/authorize')

    global fetched_playlists_metadata

    for playlist in fetched_playlists_metadata:
        items = fetch_playlist_items(playlist['id'])
        utilities.save_playlist(playlist, items)

    return jsonify({'message': 'Playlists saved.'})


@app.route('/authorize')
def authorize_user():
    """
    Authorizes the user to access their Spotify account.

    Generates a query with credentials and desired scopes, then redirects to 
    the Spotify authorization endpoint.

    Returns:
    Response: Redirect response object to the Spotify authorization page.
    """

    global credentials

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
    """
    Callback endpoint to extract the user code from Spotify and fetch an 
    access token with it.

    If no code or state was retrieved from the response, an error page
    is rendered.

    Returns:
    Response: Redirect response object to the root route.
    """

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