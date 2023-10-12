from dataclasses import dataclass
from datetime import datetime

import gspread
import pytz
import x_wr_timezone
from icalendar import Calendar, Event, vCalAddress, vText
from os.path import exists
from pathlib import Path
import os
from icalevents.icalevents import events

from dateutil import parser

calendar_path = "calendar.ics"


@dataclass
class Stream:
    title: str
    start: datetime


def read_day(box, sh):
    time_str = sh.sheet1.cell(box + 1, 5).value
    date_object = parser.parse(time_str)


    date_str = sh.sheet1.cell(box, 2).value  # month/day
    month = int(date_str.split("/")[0])
    day = int(date_str.split("/")[1])

    date_object = date_object.replace(month=month)
    date_object = date_object.replace(day=day)
    date_object = date_object.replace(datetime.today().year)
    date_object = date_object.replace(tzinfo=pytz.timezone('US/Central'))

    stream = Stream(
        title=sh.sheet1.cell(box + 2, 5).value,
        start=date_object
    )

    print(stream)
    # Add stream

    return stream


def read_schedule(cal):
    gc = gspread.service_account(filename="service_account.json")

    sh = gc.open_by_url(
        'https://docs.google.com/spreadsheets/d/1cJyQsoi07DV7NIaWi9ywLEMLa6wWVzWgus0fQX8dcnc/edit#gid=902918299')

    events = [read_day(12, sh), read_day(20, sh), read_day(28, sh), read_day(36, sh), read_day(44, sh),
              read_day(52, sh), read_day(60, sh), read_day(68, sh), read_day(76, sh)]

    for stream in events:
        event = Event()
        event.add('summary', stream.title)
        event.add('description', "https://www.twitch.tv/mizkif")
        event.add('dtstart', stream.start, parameters={'TZID': 'US/Central'})

        cal.add_component(event)

    return cal


# Reads the calendar
def get_calendar():
    calendar = Calendar()

    if not exists(calendar_path):
        calendar.add('prodid', 'dregoc')
        calendar.add('version', '2.0')
        calendar.add('TZID', 'US/Central')

        f = open(os.path.join(calendar_path), 'wb')
        f.write(calendar.to_ical())
        f.close()

    with open(calendar_path, "rb") as f:
        old_calendar = Calendar.from_ical(f.read())

    for event in old_calendar.walk('VEVENT'):
        start_date = event.get("dtstart").dt.date()
        # Check if it matches the target date
        if start_date <= datetime.today().date():
            # Print the summary of the event
            print(event.get("summary"))
            # Delete the event from the calendar
            calendar.add_component(event)

    return calendar


# Saves the calendar
def save(cal):
    if exists(calendar_path):
        os.remove(calendar_path)

    f = open(os.path.join(calendar_path), 'wb')
    f.write(cal.to_ical())
    f.close()


if __name__ == '__main__':

    cal = get_calendar()

    for component in cal.walk():
        print(component.name)

    cal = read_schedule(cal)

    save(cal)
