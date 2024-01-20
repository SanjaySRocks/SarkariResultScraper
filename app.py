from datetime import datetime
from os import getenv
import requests
from bs4 import BeautifulSoup
import re
import redis
import json

from fastapi import FastAPI, Query
from typing import Optional
from dotenv import load_dotenv, find_dotenv

# find the .env file and load it 
load_dotenv(find_dotenv())
redis_url = getenv("REDIS_URL")

# Create an instance of the FastAPI class
app = FastAPI()

redis_client = redis.StrictRedis.from_url(redis_url)

class SarkariResult:

    def __init__(self):
        pass

    def compare_dates(self, date1_str, date2_str):
        """
        Compare two date strings.

        Args:
        - date1_str (str): The first date string in the format '%d/%m/%Y'.
        - date2_str (str): The second date string in the format '%d/%m/%Y'.

        Returns:
        - bool: True if date1 is later than date2, False otherwise.
        """

        # Parse date strings into datetime objects
        date1 = datetime.strptime(date1_str, "%d/%m/%Y")
        date2 = datetime.strptime(date2_str, "%d/%m/%Y")

        # Compare dates
        return date1 >= date2


    def Scrape(self, slug, date_from = None):
        try:
            # Making a GET request
            r = requests.get(f'https://www.sarkariresult.com/{slug}/')

            # Parsing the HTML
            soup = BeautifulSoup(r.content, 'html.parser')

            # Define a regular expression pattern for date extraction
            date_pattern = re.compile(r'(\d{1,2}/\d{1,2}/\d{4})')

            post_div = soup.find('div', id='post')

            if post_div:
                dataItem = []
                for ul in post_div.find_all('ul'):
                    item = ul.find('a')
                    
                    if item:
                        href = item['href']
                        text = item.get_text(strip=True)

                        # Search for the date pattern in the list item text
                        date_match = date_pattern.search(ul.get_text(strip=True))

                        # Check if date exists
                        if date_match:
                            last_date_str = date_match.group(1)

                            if self.compare_dates(last_date_str, date_from):
                                # print(f"Link: {href}\nText: {text}\nLast Date: {last_date_str}\n")
                                dataItem.append({'href': href, 'text': text, 'last_date': last_date_str})
                        else:
                            # print(f"Link: {href}\nText: {text}\nLast Date: No Date Found\n")
                            dataItem.append({'href': href, 'text': text, 'last_date': None})
                return dataItem
            else:
                return []

        except Exception as e:
            print(e)


        


# Define a GET route
@app.get("/")
def read_hello():
    return {'message': 'Sarkari Result Scraper API', 'version': '1.3'}


@app.get("/scrape/{slug}")
def read_admission(slug:str, date: Optional[str] = Query(None, description="Date in format DD/MM/YYYY")):
    
    if slug not in {"latestjob", "admission"}:
        return {'error': "Invalid Endpoint"}
    
    try: 
        if date is None:
            date = datetime.now().strftime("%d/%m/%Y")

        redis_key = f"{slug}:{date}"
        cached_data = redis_client.get(redis_key)

        if cached_data:
            print("Cache Result Sent for ", redis_key)
            response_data = json.loads(cached_data.decode('utf-8'))
        else:

            response_data = SarkariResult().Scrape(slug, date)
            redis_client.setex(redis_key, 300, json.dumps(response_data))

        return {'totalcount': len(response_data), 'date': date, 'result': response_data}
    except Exception as e:
        return {'error': str(e)}

