import requests
import json
import base64
from datetime import date


## Credentials
cred_f = open('credentials.json')
cred_data = json.load(cred_f)

client_id = cred_data['client_id']
client_secret = cred_data['client_secret']


## Generate a token
token_f = open('token.json')
token_data = json.load(token_f)
ACCESS_TOKEN = token_data['access_token']

# Headers for all requests
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}


## API request URLs
SPOTIFY_GET_PLAYLISTS_ENDPOINT = 'https://api.spotify.com/v1/me/playlists'


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
        f = open("output/{0}_{1}.json".format(
                playlist['name'].replace('/', ' and ').replace('\"', '_'),
                date.today().strftime('%Y-%m-%d')
            ), "w")
        f.write(json.dumps(playlist))
        f.close()

## Entry point
if __name__ == '__main__':
    main()
