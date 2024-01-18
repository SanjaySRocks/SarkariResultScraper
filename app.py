import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime


def checkSiteFor(slug):
    # Making a GET request
    r = requests.get(f'https://www.sarkariresult.com/{slug}/')

    # Parsing the HTML
    soup = BeautifulSoup(r.content, 'html.parser')

    # Take Input
    user_input_date = "19/01/2024"
    current_date = datetime.strptime(user_input_date, "%d/%m/%Y").date()

    # Define a regular expression pattern for date extraction
    date_pattern = re.compile(r'(\d{1,2}/\d{1,2}/\d{4})')

    # Extract data from the HTML
    i = 0
    post_div = soup.find('div', id='post')

    if post_div:
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

                    #  Convert lastdate string to date object
                    last_date_obj = datetime.strptime(last_date_str, "%d/%m/%Y").date()

                    if last_date_obj >= current_date:
                        print(f"Link: {href}\nText: {text}\nLast Date: {last_date_str}\n")
                    else:
                        print(f"Link: {href}\nText: {text}\nLast Date: No Date Found\n")

            i = i + 1
            if i == 11:
                exit(0)
    else:
        print("No 'post' div found.")


checkSiteFor("latestjob")
