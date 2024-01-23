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
        self.dataItem = []

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


    def Scrape(self, slug):
        try:
            # Making a GET request
            r = requests.get(f'https://www.sarkariresult.com/{slug}/')

            # Parsing the HTML
            soup = BeautifulSoup(r.content, 'html.parser')

            # Define a regular expression pattern for date extraction
            date_pattern = re.compile(r'(\d{1,2}/\d{1,2}/\d{4})')

            post_div = soup.find('div', id='post')

            if post_div:
                for ul in post_div.find_all('ul'):
                    item = ul.find('a')
                    
                    if item:
                        href = item['href']
                        # text without date
                        text = item.get_text(strip=True)

                        # text with date 
                        date_match = date_pattern.search(ul.get_text(strip=True))
                        self.dataItem.append({'href': href, 'text': text, 'last_date': date_match.group(1)} if date_match else {'href': href, 'text': text})
            return self
        except Exception as e:
            print(e)
        

    def filterDate(self, date_from = None):
        self.dataItem = [
            item for item in self.dataItem 
            if 'last_date' not in item or (item.get('last_date') and self.compare_dates(item.get('last_date'), date_from))
        ]

        return self


# Define a GET route
@app.get("/")
def read_hello():
    return {'message': 'Sarkari Result Scraper API', 'version': '1.4'}


@app.get("/scrape/{slug}")
def scrape_endpoint(slug:str, date: Optional[str] = Query(None, description="Date in format DD/MM/YYYY")):
    
    if slug not in {"latestjob", "admission", "admitcard","syllabus","answerkey","result"}:
        return {'error': "Invalid Endpoint"}
    
    try: 
        # if date is None:
        #     date = datetime.now().strftime("%d/%m/%Y")

        redis_key = f"{slug}:{date}" if date else slug
        cached_data = redis_client.get(redis_key)

        if cached_data:
            print("Cache Get ", redis_key)
            response_data = json.loads(cached_data.decode('utf-8'))
        else:
            sarkari_instance = SarkariResult()
            sarkari_instance = sarkari_instance.Scrape(slug)

            if date:
                sarkari_instance = sarkari_instance.filterDate(date)

            response_data = sarkari_instance.dataItem

            redis_client.setex(redis_key, 300, json.dumps(response_data))

        return {'totalcount': len(response_data), 'date': date, 'result': response_data}
    except Exception as e:
        return {'error': str(e)}

