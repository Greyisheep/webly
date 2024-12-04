# tracker.py

from pytrends.request import TrendReq
import json

# Initialize pytrends
pytrends = TrendReq(hl="en-US", tz=360)


# Function to fetch trend data for given keywords
def fetch_trend_data(keywords: str):
    try:
        # Build payload for keywords
        pytrends.build_payload(keywords, timeframe="today 12-m")

        # Get interest over time
        data = pytrends.interest_over_time()

        if not data.empty:
            # Drop the 'isPartial' column
            data = data.drop(columns=["isPartial"], errors="ignore")

            # Convert the DataFrame to JSON
            trend_data_json = data.to_json(orient="index", date_format="iso")
            return trend_data_json
        else:
            return {"error": "No data available for the selected keywords."}
    except Exception as e:
        return {"error": str(e)}


# Main execution
if __name__ == "__main__":

    # Get user input
    user_input = input("Enter keywords: ")
    keywords = [keyword.strip() for keyword in user_input.split(",") if keyword.strip()]

    if keywords:
        print(f"Fetching trends for: {', '.join(keywords)}...")
    else:
        print("No keywords entered. Exiting program.")

    # Fetch trend data
    trend_data = fetch_trend_data(keywords)

    # Save to JSON file
    with open("trend_data.json", "w") as file:
        json.dump(trend_data, file, indent=4)

    print("Trend data has been saved to 'trend_data.json'.")
