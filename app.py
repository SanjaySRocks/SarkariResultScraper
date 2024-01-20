import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime


from fastapi import FastAPI, Query
from typing import Optional

# Create an instance of the FastAPI class
app = FastAPI()

# Define a GET route
@app.get("/")
def read_hello():
    return {'message': 'Sarkari Result Scraper API', 'version': '1.0'}


@app.get("/scrape/admission")
def read_admission(date: Optional[str] = Query(None, description="Date in format DD/MM/YYYY")):
    try: 

        if date is None:
            date = datetime.now().strftime("%d/%m/%Y")

        response_data = checkSiteFor("admission", date)

        return {'totalcount': len(response_data), 'date': date, 'result': response_data}
    except Exception as e:
        return {'error': str(e)}


@app.get("/scrape/latestjob")
def read_latestjob(date: Optional[str] = Query(None, description="Date in format DD/MM/YYYY")):
    try: 

        if date is None:
            date = datetime.now().strftime("%d/%m/%Y")

        response_data = checkSiteFor("latestjob", date)

        return {'totalcount': len(response_data), 'date': date, 'result': response_data}
    except Exception as e:
        return {'error': str(e)}
    

def compare_dates(date1_str, date2_str):
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

def checkSiteFor(slug, date_from = None):

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

                        if compare_dates(last_date_str, date_from):
                            # print(f"Link: {href}\nText: {text}\nLast Date: {last_date_str}\n")
                            dataItem.append({'href': href, 'text': text, 'last_date': last_date_str})
                    else:
                        # print(f"Link: {href}\nText: {text}\nLast Date: No Date Found\n")
                        dataItem.append({'href': href, 'text': text, 'last_date': None})
            return dataItem
        else:
            print("No 'post' div found.")

    except Exception as e:
         print(e)

