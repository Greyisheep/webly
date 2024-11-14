import string
import requests
from bs4 import BeautifulSoup

# Function to get title and description
def get_page_title_and_description(url: string):
    try:
        # Send a GET request to fetch the webpage
        response = requests.get(url)
        response.raise_for_status()  # Check for errors
        
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the title
        title = soup.title.string if soup.title else "No title found"
        
        # Extract the meta description
        description = soup.find('meta', attrs={'name': 'description'})
        description_content = description['content'] if description else "No description found"
        
        # Return the title and description
        return title, description_content
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return None, None  # Return None if there was an error
