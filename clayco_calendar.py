import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ics import Calendar, Event

# URL of the Clayton County events page
url = "https://www.claytoncountyga.gov/events/"

# Fetch the HTML content
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# Create a new calendar
calendar = Calendar()

# Find all event rows (adjust this if their HTML changes)
events = soup.find_all("div", class_="tribe-events-calendar-list__event-row")

for event in events:
    try:
        # Extract title
        title_tag = event.find("h3", class_="tribe-events-calendar-list__event-title")
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        # Extract link
        link_tag = title_tag.find("a") if title_tag else None
        link = link_tag["href"] if link_tag else ""

        # Extract date/time
        datetime_tag = event.find("time")
        datetime_str = datetime_tag["datetime"] if datetime_tag else ""
        event_datetime = datetime.fromisoformat(datetime_str) if datetime_str else None

        # Extract location
        location_tag = event.find("div", class_="tribe-events-calendar-list__event-venue")
        location = location_tag.get_text(strip=True) if location_tag else "No Location"

        # Create the calendar event
        e = Event()
        e.name = title
        e.begin = event_datetime
        e.location = location
        e.url = link
        calendar.events.add(e)

    except Exception as ex:
        print(f"Error processing event: {ex}")

# Save the calendar to a file
with open("clayton_events.ics", "w") as f:
    f.writelines(calendar)
