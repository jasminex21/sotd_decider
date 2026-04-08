import spotipy
import os
import pytz
from datetime import datetime
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

class AlignmentScorer: 

    """Class definition to compute the alignment score between the mental
       model playlist and the algorithmically-derived playlist. Will produce
       a measure of the overlap between the two playlists (order-dependent)
       to determine how well my self-determined "most salient" STODs align
       with the objective SOTDs."""

    def __init__(self, 
                 client_id, 
                 client_secret,
                 mental_id,
                 algo_id):
        
        self.mental_id = mental_id
        self.algo_id = algo_id
        
        # API authorization
        auth_manager = SpotifyClientCredentials(client_id=client_id,
                                                client_secret=client_secret)
        self.SPOTIFY = spotipy.Spotify(auth_manager=auth_manager)

    def _fetch_playlist_tracks(self, playlist_id):

        """Helper function to fetch tracks and artists from a playlist, 
           given the playlist ID. Returns a list containing the song 
           titles and artist names."""
        
        # list to store all tracks iteratively
        all_tracks = []

        try:
            # returns a dictionary with metadata 
            results = self.SPOTIFY.playlist_tracks(playlist_id=playlist_id)
            # list of dicts of tracks and associated metadata
            tracks = results["items"]

            # each page is limited to 100 tracks, so need pagination
            while results["next"]: 
                results = self.SPOTIFY.next(results)
                tracks.extend(results["items"])
            
            for track_dict in tracks: 
                track = track_dict["track"]
                # just append the track name and main artist to the list
                all_tracks.append(f"{track['name']} - {track['artists'][0]['name']}")
            
        except Exception as e: 
            print(f"Error fetching tracks from playlist {playlist_id}: {e}")

        return all_tracks

    def fetch_tracks(self): 

        """Fetch and store the tracks from both playlists."""

        self.mental_tracks = self._fetch_playlist_tracks(playlist_id=self.mental_id)
        # need to remove 4 songs from the mental playlist bc they
        # do not have corresponding algorithmic songs (was on cruise)
        # removing songs at (1-indexed) positions 110-113 inclusive
        del self.mental_tracks[109:113]
        self.algo_tracks = self._fetch_playlist_tracks(playlist_id=self.algo_id)

    def compute_alignment(self):

        """Returns the alignment score between the two playlists.
           Computed as (shared_songs) / (total_songs)."""

        min_length = min(len(self.mental_tracks), 
                         # this will be shorter
                         len(self.algo_tracks))
        
        # keep the last min_length tracks in each playlist (this
        # is bc I started tracking mental SOTDs before I had the algo)
        self.mental_tracks = self.mental_tracks[-min_length:]
        self.algo_tracks = self.algo_tracks[-min_length:]

        # for this we cannot compute a pure intersection with sets bc
        # the order must be preserved
        def _get_sorted_intersection():

            """Helper function to get the ordered intersection count
               btwn the two track lists. As in, only tracks that are
               in both lists at the same position contribute to the 
               intersection count. O(n)."""
            
            i = 0
            # counter for shared songs
            shared = 0

            while i < min_length:

                # print(f"{i+1}: {self.mental_tracks[i]} | {self.algo_tracks[i]}")
                if self.mental_tracks[i] == self.algo_tracks[i]:
                    shared += 1
                # increment index
                i += 1
            
            return shared
    
        shared_count = _get_sorted_intersection()
        alignment_score = shared_count / min_length

        return f"{shared_count}/{min_length} = {round(alignment_score, 3)}"
    
    def get_all(self):

        """Pipeline."""

        # get and format current datetime
        cst_timezone = pytz.timezone("America/Chicago")
        today_date = datetime.now().astimezone(cst_timezone).strftime('%Y-%m-%d %H:%M:%S')

        self.fetch_tracks()
        alignment_str = self.compute_alignment()
        print(f"Alignment score for {today_date}\n\t" + alignment_str)

if __name__ == "__main__": 

    load_dotenv()

    CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

    scorer = AlignmentScorer(client_id=CLIENT_ID,
                             client_secret=CLIENT_SECRET,
                             mental_id="1TsgqA7bkOcBKJOhfiJm7U",
                             algo_id="17eqTWTtmI2pm5cHuT4psH")
    
    scorer.get_all()

"""Small note on a data inconsistency. I somehow missed a mental SOTD for 11/13/2025; the
   algorithmic SOTD for that day was I'll Always Be Around - Waterparks. Tripped me up for 
   genuinely SO long bc I was trying to figure out why my two playlists were misaligned ffs.
   I ended up removing I'll Always Be Around - Waterparks from the algorithmic playlist."""