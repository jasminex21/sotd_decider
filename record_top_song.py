"""Script that adds the top song computed in SCORES.txt to a Spotify playlist.
   Intended to run at the end of every day. (Or rather, it will run at the start
   of the next day such that all songs from the previous day have been recorded
   in the Last.fm history.)"""

# TODO: there's something wrong w the song extraction from last.fm - it works
# just fine when run manually but somehow it cuts off the last few songs. So
# maybe the time conversion in SOTDecider is in UTC. Also the date range is 
# off again

import subprocess
import os
import pickle
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

def run_makefile():

    """Function that runs the makefile."""
    
    command = ["make"]
    txt_path = "SCORES.txt"

    # run make -f yday_makefile.mk (NOT make SCORES.txt)
    command.extend(["-f", "wf_yday_makefile.mk"]) 
    
    try:
        if os.path.exists(txt_path):
            os.remove(txt_path)
            print(f"File {txt_path} successfully removed.")

        result = subprocess.run(command, check=True, 
                                         text=True, 
                                         capture_output=True)
        
        print("Makefile Output:\n", result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"Makefile failed with exit code {e.returncode}")
        print("Error Output:\n", e.stderr)

def add_song(spotify_client_id, 
             spotify_client_secret,
             song_name,
             artist_name,
             playlist_id="https://open.spotify.com/playlist/5z0jE44oDlGiqckBhZOvVS?si=d3e662b23a92476f"):
    
    try:

        SPOTIFY = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=spotify_client_id,
                                                            client_secret=spotify_client_secret,
                                                            redirect_uri="http://127.0.0.1:8080/callback",
                                                            scope="playlist-modify-public",
                                                            cache_path=".cache",  
                                                            open_browser=True))
        # query Spotify using track and artist names
        query = f"track:{song_name} artist:{artist_name}"
        results = SPOTIFY.search(q=query, type='track', limit=1)

        tracks = results.get('tracks', {}).get('items', [])
        if not tracks:
            print("No song found with that criteria.")
            return
            
        track = tracks[0]
        track_id = track["id"]

        SPOTIFY.playlist_add_items(playlist_id=playlist_id, items=[track_id])
        print(f"Successfully added top song ({track['name']} - {track['artists'][0]['name']}) to your Spotify playlist!")
    
    except Exception as e:
        print(f"Error adding track to playlist: {e}")


if __name__ == "__main__":

    load_dotenv()

    run_makefile() 

    # get top song via pickle file
    with open("SCORES.pickle", "rb") as file:
        scores = pickle.load(file)

    top_song = scores[0][0].split("-")
    song_name = top_song[0].strip()
    artist_name = top_song[-1].strip()

    add_song(spotify_client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
             spotify_client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"), 
             song_name=song_name,
             artist_name=artist_name)
