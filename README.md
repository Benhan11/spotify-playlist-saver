# Spotify Playlist Saver

## Description
This personal web application fetches and saves the user's Spotify playlists for backup purposes.
The server runs on [Flask](https://flask.palletsprojects.com/en), processing and serving responses.
[Jinja](https://jinja.palletsprojects.com/en) enables dynamic web pages. An authorized session is 
established with an OAuth2 handshake according to the Spotify API, resulting in an access token 
being granted. Backups are saved as JSON files, fit for further development.


## Installation instructions
***NOTE*** As this project was intended only for personal use, anyone seeking to try this out for themselves
will need to create their own Spotify Developer project.

1. **Clone the repository**
```
git clone https://github.com/Benhan11/spotify-playlist-saver
```

2. **Create `token.json` and `credentials.json` files**

`credentials.json` should look like this:

```json
{
    "client_id": "your_client_id",
    "client_secret": "your_client_secret"
}
```

3. **(Docker) Build Docker image**
```
docker build -t spotify-playlist-saver .
```

3. **(Without Docker) Install dependencies**
```
pip install -r requirements.txt
```

## Usage
**(Docker) Run Docker container**
```
docker run --name spotify-playlist-saver -p 8888:8888 spotify-playlist-saver
```

**(Without Docker) Run Flask**
```
py .\main.py
```

The application can now be access at `http://localhost:8888`

*Docker Note* Generated backups can be found at `/app/output/` within the container.


## Dependencies
- Flask (v3.0.3)
- requests (v2.28.2)
