import time
from pytrends.request import TrendReq

# Connect to Google
pytrends = TrendReq(hl='en-US', tz=360, timeout=(5, 30))

def get_keyword_trend(keyword: str):
    pytrends.build_payload([keyword], cat=0, timeframe='today 5-y', geo='')
    try:
        interest_over_time_df = pytrends.interest_over_time()
        return interest_over_time_df
    except Exception as e:
        if "429" in str(e):
            print("Rate limit hit, sleeping for 30 seconds...")
            time.sleep(30)
            return get_keyword_trend(keyword)  # Retry after sleeping
        else:
            print("Error:", e)
            return None

def get_rising_queries(keyword: str):
    try:
        pytrends.build_payload([keyword])
        queries = pytrends.related_queries()
        rising_queries = queries[keyword]['rising']
        return rising_queries
    except Exception as e:
        if "429" in str(e):
            print("Rate limit hit, sleeping for 30 seconds...")
            time.sleep(30)
            return get_rising_queries(keyword)  # Retry after sleeping
        else:
            print("Error:", e)
            return None
