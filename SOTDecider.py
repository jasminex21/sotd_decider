import requests
import os
import pytz
import math
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from dotenv import load_dotenv
from typing import DefaultDict, List, Dict, Counter
from tabulate import tabulate

class SOTDecider: 

    def __init__(self, lastfm_api_key: str, 
                 range_option:str="this week"):

        """
        Constructor. The key task done here is translating the start date to a
        UNIX timestamp.

        Args:   
            lastfm_api_key: 
                Lastfm API key.
            range_option: 
                The range of dates to pull listening data from; must be one of 
                ["this week", "last 7 days", "last 30 days"] where "this week" 
                is the start of the week (Monday 12AM) to now, and "last X days"
                is (today - X) 12AM. 
        """
        
        # grab UNIX timestamps for the range
        range_options = ["this week", "last 7 days", "last 30 days"]
        assert range_option in range_options, f"range_option MUST be one of {range_options}."
        
        # I want all times to be in CST bc I do listen to a lot of music 
        # close to midnight and tz being UTC would mess scores up
        cst_timezone = pytz.timezone("America/Chicago")
        today_date = datetime.now().astimezone(cst_timezone) # -timedelta(days=1)
        self.today = today_date.strftime("%d %b %Y")
        
        # this week: get the Monday of the current week
        if range_option == "this week": 
            monday = today_date - timedelta(days=today_date.weekday())
            monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
            
            print(f"Fetching listening history from {monday.date()} on...")
            
            self.start_timestamp = int(monday.timestamp())
        
        # last 7 days (midnight)
        elif range_option == "last 7 days":
            seven_ago = today_date - timedelta(days=7)
            seven_ago = seven_ago.replace(hour=0, minute=0, second=0, microsecond=0)
            
            print(f"Fetching listening history from {seven_ago.date()} on...")

            self.start_timestamp = int(seven_ago.timestamp())
        
        # last 30 days (midnight)
        else: 
            thirty_ago = today_date - timedelta(days=30)
            thirty_ago = thirty_ago.replace(hour=0, minute=0, second=0, microsecond=0)

            print(f"Fetching listening history from {thirty_ago.date()} on...")

            self.start_timestamp = int(thirty_ago.timestamp())
        
        self.lastfm_api_key = lastfm_api_key
        self.lastfm_username = "jasminexx18"
    
    def _get_lastfm_data(self) -> List[Dict]:

        """Fetches listening history from Last.fm from the selected time range."""

        url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=jasminexx18&api_key={self.lastfm_api_key}&from={self.start_timestamp}&format=json"
        
        # list to store all tracks across all pages
        all_tracks = []

        def __fetch_tracks(page: int) -> List[Dict]:

            """Helper function to fetch the list of tracks from a given page.
            
               Args: 
                page: 
                    The page number.
            """
            
            url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=jasminexx18&page={page}&api_key={self.lastfm_api_key}&from={self.start_timestamp}&format=json"
            tracks = []

            try: 
                response = requests.get(url).json().get("recenttracks", {})
                tracks = response["track"]

            except Exception as e: 
                print(f"Unable to fetch listening data from Last.fm: {e}")
            
            return tracks

        try: 

            response = requests.get(url).json().get("recenttracks", {})
            info = response.get("@attr", {})
            # the response fetches one page at a time, so if there are multiple
            # pages we need to iterate through them to catch all tracks
            total_pages = int(info.get("totalPages", -1))
            tracks = response.get("track", [])
            all_tracks += tracks
        
        except Exception as e: 

            print(f"Unable to fetch listening data from Last.fm: {e}")

        for i in range(1, total_pages + 1):
            all_tracks += __fetch_tracks(page=i)
        
        return all_tracks
    
    def _count_tracks(self, all_tracks: list) -> DefaultDict[str, Counter]:

        """Counts up the streams of each unique song for each day in the range.
        
           Args:
            all_tracks: The list of all tracks obtained from self._get_lastfm_data().
        """

        counts = defaultdict(Counter)

        for track_dict in all_tracks: 
            # only time "date" is not a key is if I am currently playing a song
            if "date" in track_dict.keys(): 
                # need to convert the date from the timestamp bc the text date
                # is in UTC
                timestamp_played = int(track_dict["date"]["uts"])
                day_played = datetime.fromtimestamp(timestamp_played).strftime("%d %b %Y")
                track_name = f'{track_dict["name"]} - {track_dict["artist"]["#text"]}'
                counts[day_played][track_name] += 1

        return counts

    def _get_tf(self, song: str, day: str, counts: DefaultDict[str, Counter]) -> int:

        """Returns the TF score for a given song in a given day. Computed as
           (# of times song s was played on day D)/(total # of songs played 
           on D).

           Args: 
            song: The name of the song.
            day: The text string of the current date.
            counts: The day-by-day stream counts, obtained via self._count_tracks().   
        """
        
        numerator = counts[day][song]
        denominator = sum(counts[day].values())

        return numerator/denominator

    def _get_idf(self, song: str, counts: DefaultDict[str, Counter]):
        
        """Returns the IDF score for a given song. Computed as log((# of days
           in date range)/(# of days during which song s was streamed)).
           
           Args: 
            song: The name of the song.
            counts: The day-by-day stream counts, obtained via self._count_tracks().
           """
        
        numerator = len(counts)
        denominator = sum(1 for _, day_tracks in counts.items() if song in day_tracks)

        return math.log(numerator/denominator)

    def get_scores(self) -> None: 

        """Pipeline to compute scores for all songs on the current day relative
           to all days in the time frame. Calls all utility functions and prints
           a table of the scores."""

        all_tracks = self._get_lastfm_data()
        counts = self._count_tracks(all_tracks=all_tracks)
        day_counts = counts[self.today]

        print(f"{len(all_tracks)} total tracks fetched; {len(day_counts)} from {self.today}.")
        
        scores = {}

        for song in day_counts:

            tf = self._get_tf(song=song, day=self.today, counts=counts)
            idf = self._get_idf(song=song, counts=counts)
            # adding a multiple of TF to prevent the score being 0 if IDF = 0;
            # essentially emphasising repetition  
            scores[song] = ((tf * idf) + (tf * 0.3), tf, idf)

        # sort songs based on their score in descending order
        scores = sorted([(song, score, tf, idf) for song, (score, tf, idf) 
                         in scores.items()],
                         key=lambda item: item[1], reverse=True)
        table_headers = ["Track", "TF-IDF", "TF", "IDF"]

        print(tabulate(scores, headers=table_headers, 
                       tablefmt="rounded_grid", showindex="always"))

if __name__ == "__main__":

    load_dotenv()

    decider = SOTDecider(lastfm_api_key=os.environ.get("LASTFM_API_KEY"),
                         range_option="this week")
    decider.get_scores()
