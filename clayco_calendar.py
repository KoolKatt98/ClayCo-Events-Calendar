import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ics import Calendar, Event
import logging

# Configure logging
logging.basicConfig(filename="clayco_calendar.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Clayton County events page URL
url = "https://www.claytoncountyga.gov/events/"

# Add headers to the HTTP request
headers = {"User-Agent": "Mozilla/5.0"}

try:
    # Fetch the HTML content
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error if the request failed
    soup = BeautifulSoup(response.text, "html.parser")
except requests.exceptions.RequestException as e:
    logging.error(f"Error fetching the events page: {e}")
    raise SystemExit(e)

# Create a new calendar
calendar = Calendar()

# Find all event articles on the page
events = soup.find_all('article', class_='tribe-events-calendar-list__event')

for event in events:
    try:
        # Title
        title_tag = event.find("h3", class_="tribe-events-calendar-list__event-title")
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        # Link
        link_tag = title_tag.find("a") if title_tag else None
        link = link_tag["href"] if link_tag else ""

        # Date/Time
        datetime_tag = event.find("time")
        datetime_str = datetime_tag["datetime"] if datetime_tag else ""
        try:
            event_datetime = datetime.fromisoformat(datetime_str) if datetime_str else None
        except ValueError:
            logging.warning(f"Invalid date format for event: {title}")
            event_datetime = None

        # Location
        location_tag = event.find("div", class_="tribe-events-calendar-list__event-venue")
        location = location_tag.get_text(strip=True) if location_tag else "No Location"

        # Create calendar event
        e = Event()
        e.name = title
        e.begin = event_datetime
        e.location = location
        e.url = link
        calendar.events.add(e)

    except Exception as ex:
        logging.error(f"Error adding event: {ex}")

# Write to .ics file
try:
    with open("clayton_events.ics", "w") as f:
        f.write(str(calendar))
    logging.info("Calendar successfully written to clayton_events.ics")
except Exception as e:
    logging.error(f"Error writing to file: {e}")
