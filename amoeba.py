from dotenv import load_dotenv
import datetime
from googleapiclient.discovery import build
import os
import sys
import re
import base64
import requests
from requests import post, get
import json
from unidecode import unidecode
from fuzzywuzzy import fuzz
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()
api_key = os.getenv("API_KEY").strip()    
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
user_id = "315pxy65te6xtrqmahwr2mhblmvu"

youtube = build('youtube', 'v3', developerKey=api_key)


def main():
    
    all_videos = []
    for playlist_id in get_all_playlists(youtube, "UC9DkCKm4_VDztRRyge4mCJQ"):
        all_videos.extend(get_videos(youtube, playlist_id))
    unique_videos = {video["snippet"]["title"]: video for video in all_videos}.values()
    while True:               
        choosen_artist = clean_text(input("Name of the artist: "))
        results = get_artists_picks(choosen_artist, unique_videos)
        if len(results[0]) == 0:
            print("There are no episodes with that artist, please write another one")
        else:
            if len(results[1]) > 1:
                print("Choose the episode for a playlist creation: ")
                for index, name in enumerate(results[1], start = 1):
                    print(f"{name} - {index}")
                try:
                    while True:
                        episode_number = int(input("Type the coresponding number: "))
                        
                        if 0 < episode_number <= (len(results[1]) + 1):
                            print("Playlist is creating...")
                            break
                        else:
                            print("Please choose one of the presented numbers")
                            continue
                                
                except ValueError:
                    sys.exit("It is not a number, try again")
            else:
                print(results[1])  
                while True:
                    decision = input('Is this the episode you are looking for? (Type "yes" or "no"): ').lower().strip()
                    
                    if decision == "yes":
                        print("Playlist is creating...")
                        break
                    elif decision == "no":
                        sys.exit("Playlist creation has been stopped")
                    else:
                        print('Type "yes" or "no"')
                        continue
                
            break
    if len(results[1]) > 1:
        episode_picks = results[0][episode_number - 1]
        playlist_name = results[1][episode_number - 1]
    else:
        print(results[0][0])
        episode_picks = results[0][0]
        playlist_name = results[1][0]
        
    
       
    print(playlist_name)
    token = get_token()
    album_results = {}
    for artist, album, _ in episode_picks:
            result = search_for_album(token, artist, album)
            album_results.update(result)

    for key, value in album_results.items():
        print(f"{key}: {value}")
        
    playlist_songs = []

    for key, value in album_results.items():
        try:
            id = most_popular_track(token, value[0])
            playlist_songs.append(id)
        except TypeError:
            continue
    print(playlist_songs)
    
    playlist_id = create_public_playlist_spotipy(user_id, playlist_name)
    print(playlist_id)
    
    added_songs = add_tracks_to_playlist(user_id, playlist_id, playlist_songs)
    print(added_songs)   
    
#Youtube part          
def get_all_playlists(youtube, channel_id):
    playlist_info = []
    next_page_token = None
    while True:
        request = youtube.playlists().list(
            channelId=channel_id,
            part="id,snippet",
            maxResults=50,
            pageToken=next_page_token
        ).execute()
            
        playlist_info.extend([
            item["id"]
            for item in request.get("items", [])
            if "What's" in item["snippet"]["title"]
        ])
            
        next_page_token = request.get("nextPageToken")
        if not next_page_token:
            break
            
    return playlist_info

def get_videos(youtube, playlist_id):  
    videos = []
    next_page_token = None
    while True:
        try:
            res = youtube.playlistItems().list(playlistId=playlist_id,
                                part="snippet",
                                maxResults=50,
                                pageToken=next_page_token).execute()
            videos += res["items"]
            next_page_token = res["nextPageToken"]
        except KeyError:
            break
            
    return videos

def clean_text(text):
    text = text.lower()
    text = text.replace("&", "and")
    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    return text

def get_artists_picks(choosen_artist, unique_videos):
    artists = filter(lambda s: choosen_artist in clean_text(s["snippet"]["title"]), unique_videos)
    final_list = []
    title_list = []
    title = None
    for artist in sorted(artists, key=lambda s: (s["snippet"]["title"], s["snippet"]["description"])):
        title = artist["snippet"]["title"]
        description = artist["snippet"]["description"]
        lines = description.split("\n")
        episode_content = []
        for line in lines:
            if match := re.search(r'(.+?)(?: - | – )(.+?) (\(LP\)|\(CD\)|\[LP\]|\[CD\]|\(CASSETTE\)|\(\d+"\))', line.strip(), re.IGNORECASE):
                name, album, album_format = match.groups()                 
                episode_content.append((name, album, album_format))
        title_list.append(title)        
        final_list.append(episode_content)
    return (final_list, title_list)

#Spotify part

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_headers(token):
    return {"Authorization": "Bearer " + token}

def clean_album_name(name):
    # Replace specific characters first
    name = name.replace('&', 'and')
    name = name.replace('/', ' ')
    name = name.replace('-', ' ')
    
    # List of words/phrases that might be non-essential
    filters = [
        "Remastered", "Anniversary", "Remaster", "Re-master", "Edition", "Deluxe", "Reissue",            
        "Bonus Track Version", "Expanded", "Explicit", "Clean", "Special", 
        "Limited", "Unlimited", "Expended", "Version", "Extended", 
        "Director's Cut", "Anniversary Edition", "Original Motion Picture Soundtrack", 
        "OST", "Unplugged", "Volume", "Redux", "Collector's", "Import", "Acoustic", 
        "Instrumental", "Single", "EP", "180 Gram Vinyl"
    ]
    current_year = datetime.datetime.now().year
    years = list(map(str, range(1900, current_year + 1)))
    filters.extend(years)
    
    for word in filters:
        # Using regex replacement to manage additional spaces
        name = re.sub(r'\b{}\b'.format(word), '', name, flags=re.IGNORECASE)
    
    # Now, remove unwanted characters
    name = re.sub(r'[^a-zA-Z0-9 ]', '', name)
    
    return name.strip()




def search_for_album(token, artist_name, album_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_headers(token)
    #Get rid of transliteration
    artist_name_uni = unidecode(artist_name)
    album_name_uni = unidecode(album_name)
    #Checking if there is an artist with that name
    
    #Checking if there an album with that name
    query = f"artist:{artist_name_uni} album:{album_name_uni}"
    params = {
        "q": query,
        "type": "album",
        "limit": 50
        }
    response = requests.get(url, headers=headers, params=params)
    results = response.json()
    found_albums = results.get("albums", {}).get("items", [])
    
    album_names = [(album["name"], album["id"], [artist["name"] for artist in album["artists"]]) for album in found_albums]
    result_dict = {}
   
    if album_names:
        
        album_found = False
        for album in album_names:
            
            if len(album[-1]) > 1:
                result_dict[f"{artist_name} - {album_name}"] = [album[1], album[2], album[0]]
                album_found = True
                break
            else:
     
                if artist_name_uni.lower() == unidecode(album[-1][0].lower()):
          
                    result_dict[f"{artist_name} - {album_name}"] = [album[1], album[2], album[0]]
                    album_found = True
                    break
                else:

                    result_dict[f"{artist_name} - {album_name}"] = None
                    album_found = True
                    break   
                 
                           
    else:
  
        artists = re.split(r' & | and |, | with ', artist_name_uni.lower())
        artist_ids = []
        for artist in artists:
            
            query = f"artist:{artist.strip()}"
            params = {
                "q": query,
                "type": "artist",
                "limit": 50
            }
            response = requests.get(url, headers=headers, params=params)
            results = response.json()
            found_artists = results.get("artists", {}).get("items", [])
            if found_artists:
                exact_match_found = False
                for a in found_artists:
                    if a["name"].lower() == artist.strip():
                        artist_ids.append(a["id"])
                        exact_match_found = True
                        break

                if not exact_match_found:
                    artist_ids.append(found_artists[0]["id"])
        album_found = False
    
        all_found_albums = []
        
        for artist_id in artist_ids:
            
        # Fetch albums for the artist
            albums_url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
            
            while albums_url:
                response = requests.get(albums_url, headers=headers)
                results = response.json()
                found_albums = results.get("items", [])
                all_found_albums.extend(found_albums)
                albums_url = results.get('next')

            
            album_names = [(album["name"], album["id"], [artist["name"] for artist in album["artists"]]) for album in all_found_albums]
            max_score = -1
            best_match = None
            threshold = 55

            for album in album_names:

                current_score = 0
                current_condition = None

                if len(clean_album_name(album_name_uni).lower()) == len(clean_album_name(album[0]).lower()):
                    current_score = fuzz.ratio(unidecode(clean_album_name(album[0]).lower()), clean_album_name(album_name_uni).lower())
                    if current_score > 86:
                        current_condition = "3"
                elif len(clean_album_name(album_name_uni)) > len(clean_album_name(album[0])):
                    current_score = fuzz.ratio(unidecode(clean_album_name(album[0]).lower()), clean_album_name(album_name_uni).lower())
                    current_condition = "4"
                elif len(clean_album_name(album_name_uni)) < len(clean_album_name(album[0])):
                    current_score = fuzz.ratio(unidecode(clean_album_name(album[0]).lower()), clean_album_name(album_name_uni).lower())
                    current_condition = "5"

                if current_score > max_score:
                    max_score = current_score
                    best_match = album

            if best_match and max_score > threshold:
                result_dict[f"{artist_name} - {album_name}"] = [best_match[1], best_match[2], best_match[0]]
                album_found = True
                    
        if not album_found:

            album_checked = False
            for album in album_names:
          
                if clean_album_name(album_name_uni).lower() == clean_album_name(album[0]).lower():
                    
                    result_dict[f"{artist_name} - {album_name}"] = [album[1], album[2], album[0]]
                    album_checked = True
                    break   

                elif len(clean_album_name(album_name_uni)) > len(clean_album_name(album[0])): 

                    if unidecode(clean_album_name(album[0]).lower()) in clean_album_name(album_name_uni).lower():
                        result_dict[f"{artist_name} - {album_name}"] = [album[1], album[2], album[0]]
                        album_checked = True
                        break
                elif len(clean_album_name(album_name_uni)) < len(clean_album_name(album[0])):
       
                    if clean_album_name(album_name_uni).lower() in unidecode(clean_album_name(album[0]).lower()):
                        result_dict[f"{artist_name} - {album_name}"] = [album[1], album[2], album[0]] 
                        album_checked = True
                        break
                    
            if not album_checked:    
                result_dict[f"{artist_name} - {album_name}"] = None
                
                    
                
        if not album_names:
            result_dict[f"{artist_name} - {album_name}"] = None 
     
    return result_dict

def most_popular_track(token, album_id):
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
    track_ids = []
    while url:
        headers = get_auth_headers(token)
        response = requests.get(url, headers=headers)
        results = response.json()
        for item in results.get("items", []):              
            track_ids.append(item["id"])
        url = results.get('next')
        
    max_popularity = 0
    best_song_id = None
    
    for track_id in track_ids:
        url = f"https://api.spotify.com/v1/tracks/{track_id}"
        headers = get_auth_headers(token)
        response = requests.get(url, headers=headers)
        track_data = response.json()
        current_popularity = track_data.get("popularity")
        if current_popularity >= max_popularity:
            max_popularity = current_popularity
            best_song_id = track_id
            
    return best_song_id


#Creating playlist

def connect():
    
    connect = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.getenv("CLIENT_ID"),
                                                client_secret=os.getenv("CLIENT_SECRET"),
                                                redirect_uri="http://localhost:8888/callback",
                                                scope="playlist-modify-public"))
    return connect

def create_public_playlist_spotipy(user_id, playlist_name, description="Inspired by the 'What's In My Bag?' series from Amoeba's YouTube channel, this playlist captures the top tracks from every artist featured in each episode. Dive into a curated collection that brings together the favorites of your favorite artists. From hidden gems to chart-toppers, experience music through the ears of the artists you admire. #WhatsInMyPlaylist"):
    
    ct = connect()
    playlist = ct.user_playlist_create(user_id, playlist_name, description=description, public=True)
    playlist_id = playlist['id']
    
    return playlist_id

def add_tracks_to_playlist(user_id, playlist_id, tracks):
    ct = connect()
    ct.user_playlist_add_tracks(user_id, playlist_id, tracks)
    return f"Successfully added {len(tracks)} tracks to playlist with ID {playlist_id}"

        
        
if __name__ == "__main__":
    main()