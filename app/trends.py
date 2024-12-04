import time
from pytrends.request import TrendReq

# Connect to Google
pytrends = TrendReq(hl='en-US', tz=360, timeout=(5, 30))

def get_keyword_trend(keyword: str, timeframe='today 5-y'):
    """
    Get interest over time for a keyword
    Returns:
        pandas.DataFrame or None: DataFrame containing trend data if successful, None if failed
    """
    try:
        pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo='')
        interest_over_time_df = pytrends.interest_over_time()
        
        if interest_over_time_df.empty:
            return None
            
        return interest_over_time_df.drop('isPartial', axis=1, errors='ignore')
        
    except Exception as e:
        if "429" in str(e):
            time.sleep(30)
            return get_keyword_trend(keyword, timeframe)
        return None

def get_rising_queries(keyword: str):
    """
    Get rising related queries for a keyword
    Returns:
        pandas.DataFrame or None: DataFrame containing rising queries if successful, None if failed
    """
    try:
        pytrends.build_payload([keyword], timeframe='today 5-y')
        queries = pytrends.related_queries()
        rising_queries = queries[keyword]['rising']
        
        if rising_queries is None or rising_queries.empty:
            return None
            
        return rising_queries
        
    except Exception as e:
        if "429" in str(e):
            time.sleep(30)
            return get_rising_queries(keyword)
        return None

def analyze_keyword(keyword: str):
    """
    Analyze a keyword and return both trend data and rising queries
    Args:
        keyword (str): The keyword to analyze
    Returns:
        tuple: (trend_data, rising_queries) where each element is either a pandas DataFrame or None
    """
    trend_data = get_keyword_trend(keyword)
    rising_data = get_rising_queries(keyword)
    
    return trend_data, rising_data