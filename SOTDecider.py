import requests
import os
import math
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from dotenv import load_dotenv
from typing import DefaultDict, List, Dict, Counter
from tabulate import tabulate

class SOTDecider: 

    def __init__(self, lastfm_api_key: str, 
                 range_option:str="this week"):

        """Args:   
            lastfm_api_key: 
                Lastfm API key.
            range_option: 
                The range of dates to pull listening data from; must be one of 
                ["this week", "last 7 days", "last 30 days"] where "this week" 
                is the start of the week (Monday 12AM) to now, and "last X days"
                is exactly what it sounds like.
            """

        # TODO: how to parameterize date range
            # probs make it categorical, like last week, last month
            # and I compute the range directly based on current day
        
        # grab UNIX timestamps for the range
        range_options = ["this week", "last 7 days", "last 30 days"]
        assert range_option in range_options, f"range_option MUST be one of {range_options}."
        
        today_date = datetime.now() 
        self.today = today_date.strftime("%d %b %Y")
        
        # this week: get the Monday of the current week
        if range_option == "this week": 
            monday = today_date - timedelta(days=today_date.weekday())
            monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
            
            print(f"Fetching listening history from {monday.date()}...")
            
            self.start_timestamp = int(monday.timestamp())
        
        # TODO!!!!
        elif range_option == "last 7 days":
            pass 
        else: 
            pass
        
        # needed for API calls
        self.lastfm_api_key = lastfm_api_key
        self.lastfm_username = "jasminexx18"
    
    def _get_lastfm_data(self) -> List[Dict]:

        url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=jasminexx18&api_key={self.lastfm_api_key}&from={self.start_timestamp}&format=json"
        
        # list to store all tracks across all pages
        all_tracks = []

        # helper function to fetch list of tracks from a given page
        def __fetch_tracks(page: int) -> List[Dict]:

            """Helper function to fetch the list of tracks from a given page.
            
               Args: 
                page: the page number.
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
            info = response["@attr"]
            # the response fetches one page at a time, so if there are multiple
            # we need to iterate through them to catch all tracks
            total_pages = int(info["totalPages"])
            tracks = response["track"]
            all_tracks += tracks
        
        except Exception as e: 

            print(f"Unable to fetch listening data from Last.fm: {e}")

        for i in range(1, total_pages + 1):
            all_tracks += __fetch_tracks(page=i)
        
        return all_tracks
    
    def _count_tracks(self, all_tracks: list): #-> DefaultDict[Counter]

        """Counts up the streams of each unique song for each day in the range."""

        counts = defaultdict(Counter)

        for track_dict in all_tracks: 
            # only time "date" is not a key is if I am currently playing a song
            if "date" in track_dict.keys(): 
                day_played = track_dict["date"]["#text"].split(",")[0]
                track_name = f'{track_dict["name"]} - {track_dict["artist"]["#text"]}'
                counts[day_played][track_name] += 1

        return counts

    def _get_tf(self, song, day, counts):

        """Returns the TF score for a given song in a given day. Computed as
           (# of times song s was played on day D)/(total # of songs played 
           on D)"""
        
        numerator = counts[day][song]
        denominator = sum(counts[day].values())

        return numerator/denominator

    def _get_idf(self, song, counts):
        
        """Returns the IDF score for a given song. Computed as log((# of days
           in date range)/(# of days during which song s was streamed))."""
        
        numerator = len(counts)
        denominator = sum(1 for _, day_tracks in counts.items() if song in day_tracks)

        return math.log(numerator/denominator)

    def get_scores(self): 

        all_tracks = self._get_lastfm_data()
        counts = self._count_tracks(all_tracks=all_tracks)
        
        scores = {}

        for song in counts[self.today]:

            tf = self._get_tf(song=song, day=self.today, counts=counts)
            # note that IDF will be 0 if the song is present in all days
            # not sure if I want that 
            idf = self._get_idf(song=song, counts=counts)
            scores[song] = tf * idf

        # sort songs based on their score in descending order
        scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        # table_scores = list(map(list, scores.items()))
        table_headers = ["Track", "TF-IDF Score"]

        print(tabulate(scores, headers=table_headers, tablefmt="rounded_grid"))

        return scores

    # TODO: method to format final output table


if __name__ == "__main__":

    load_dotenv()

    decider = SOTDecider(lastfm_api_key=os.environ.get("LASTFM_API_KEY"),
                         range_option="this week")
    decider.get_scores()
