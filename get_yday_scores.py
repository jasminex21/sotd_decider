import SOTDecider
from SOTDecider import SOTDecider

import os
import pytz
from dotenv import load_dotenv
from datetime import datetime, timedelta

if __name__ == "__main__":

    load_dotenv()

    # get yesterday's date midnight timestamp
    cst_timezone = pytz.timezone("America/Chicago")
    yday_date = datetime.now().astimezone(cst_timezone) - timedelta(days=1)
    yday_date = yday_date.replace(hour=23, minute=59, second=59, microsecond=59)

    decider = SOTDecider(lastfm_api_key=os.environ.get("LASTFM_API_KEY"),
                         range_option="last 5 days",
                         end_time=yday_date)
    decider.get_scores()