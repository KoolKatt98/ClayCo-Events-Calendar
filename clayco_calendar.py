import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ics import Calendar, Event

# Target URL
url = "https://www.claytoncountyga.gov/events/"
headers = {"User-Agent": "Mozilla/5.0"}

# Try fetching the page content
try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
except requests.RequestException as e:
    print(f"Failed to fetch events page: {e}")
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")
calendar = Calendar()

# Find all event articles
events = soup.find_all('article', class_='tribe-events-calendar-list__event')

if not events:
    print("No events found. Check HTML structure.")
else:
    for event in events:
        try:
            # Title
            title_tag = event.find("h3", class_="tribe-events-calendar-list__event-title")
            title = title_tag.get_text(strip=True) if title_tag else "Untitled Event"

            # Link
            link_tag = title_tag.find("a") if title_tag else None
            link = link_tag["href"] if link_tag and "href" in link_tag.attrs else ""

            # Date/time
            datetime_tag = event.find("time")
            datetime_str = datetime_tag["datetime"] if datetime_tag and "datetime" in datetime_tag.attrs else ""
            try:
                event_datetime = datetime.fromisoformat(datetime_str)
            except ValueError:
                print(f"Invalid date format: {datetime_str}")
                continue

            # Location
            location_tag = event.find("div", class_="tribe-events-calendar-list__event-venue")
            location = location_tag.get_text(strip=True) if location_tag else "Location TBD"

            # Create calendar event
            e = Event()
            e.name = title
            e.begin = event_datetime
            e.url = link
            e.location = location
            calendar.events.add(e)

        except Exception as ex:
            print(f"Error parsing event: {ex}")

# Write to .ics file
try:
    with open("clayton_events.ics", "w", encoding="utf-8") as f:
        f.write(str(calendar))
    print("clayton_events.ics successfully created.")
except Exception as e:
    print(f"Failed to write .ics file: {e}")
