from modules import utilities
from flask import Flask, request, redirect, render_template
import requests
import urllib.parse
import base64
from datetime import date



app = Flask(__name__)


### API
credentials = utilities.get_credentials()

user_code = None
access_token = None

SPOTIFY_AUTHORIZATION_ENDPOINT = 'https://accounts.spotify.com/authorize'
SPOTIFY_GET_PLAYLISTS_ENDPOINT = 'https://api.spotify.com/v1/me/playlists'
SPOTIFY_TOKEN_ENDPOINT = 'https://accounts.spotify.com/api/token'
REDIRECT_URI = 'http://localhost:8888/callback'

SCOPES = 'playlist-read-private'



## The data to be formatted and returned from the script
playlist_urls = []
playlist_tracks = []
formatted_playlists = []


## Get all playlists
def get_all_playlist_urls(url):
    global playlist_urls
    
    response = requests.get(
        url,
        headers = headers
    )
    json_resp = response.json()
    print(json_resp)

    # Collect href from this response
    for item in json_resp['items']:
        playlist_urls.append(item['href'])

    # Make another request if there are more playlists
    if json_resp['next'] != None:
        return get_all_playlist_urls(json_resp['next'])
    else:
        return playlist_urls


## Get a playlist
def get_playlist(url):
    response = requests.get(
        url,
        headers = headers
    )
    json_resp = response.json()
    
    tracks = get_playlist_tracks(json_resp['tracks'])

    formatted = {
        'name': json_resp['name'],
        'description': json_resp['description'],
        'owner.id': json_resp['owner']['id'],
        'owner.display_name': json_resp['owner']['display_name'],
        'href': json_resp['href'],
        'tracks.total': json_resp['tracks']['total'],
        'tracks': tracks
    }

    return formatted


## Get playlist tracks
#  Formats data and makes additional requests if necessary
def get_playlist_tracks(tracks):
    global playlist_tracks
    
    for item in tracks['items']:
        artists = list(map(get_artist_name, item['track']['artists']))

        playlist_tracks.append({
            'name': item['track']['name'],
            'album': item['track']['album']['name'],
            'artists': artists,
            'added_at': item['added_at'],
            'added_by': item['added_by']['id']
        })
    
    # If there are more tracks
    if tracks['next'] != None:
        # Make a new request
        response = requests.get(
            tracks['next'],
            headers = headers
        )
        json_resp = response.json()

        # Get the next set of tracks
        return get_playlist_tracks(json_resp)

    else:
        tracks = playlist_tracks.copy()
        playlist_tracks = []
        return tracks
    

## Gather only name of the artist
def get_artist_name(artist):
    return {
        'name': artist['name']
    }



## Main
def main():
    global playlist_urls, formatted_playlists

    playlist_urls = get_all_playlist_urls(SPOTIFY_GET_PLAYLISTS_ENDPOINT)

    for playlist_url in playlist_urls:
        playlist = get_playlist(playlist_url)
        formatted_playlists.append(playlist)

    for playlist in formatted_playlists:
        f = open('output/{0}_{1}.json'.format(
                playlist['name'].replace('/', ' and ').replace('\"', '_'),
                date.today().strftime('%Y-%m-%d')
            ), 'w')
        f.write(json.dumps(playlist))
        f.close()






### Requests

def fetch_and_save_access_token():
    global credentials

    print(credentials)

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
        access_token = response.json()['access_token']
        utilities.save_token()
    except:
        access_token = None



### Routes

@app.route('/')
def index():
    if not user_code:
        return redirect('/authorize')
    
    return render_template('home_page.html')


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
    return(redirect(auth_url))


@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')

    if not code or not state:
        return render_template('error_page.html')
    else:
        global user_code
        user_code = code
        
    fetch_and_save_access_token()

    return redirect('/')



### Entry point
if __name__ == '__main__':
    app.run(port=8888, debug=True)