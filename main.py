import re
import time
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


def read_miz_schedule(cal):
    gc = gspread.service_account(filename="tmp/service_account.json")

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


def read_ee_schedule(cal):
    gc = gspread.service_account(filename="tmp/service_account.json")

    sh = gc.open_by_url(
        'https://docs.google.com/spreadsheets/d/1hJ5FJCXeaTRPb8ROR-PiEzMYKb3U7Z35ujn6mSzzHKg/edit#gid=0')

    date_regex = re.compile(r'(\w+) (\d+)\w+ \| (\w+) \| (\d+):(\d+)\w+ (\w+)')

    # Searches for all boxes with a date
    cells = sh.get_worksheet(0).findall(date_regex, in_column=4)

    for cell in cells:
        print(cell.value)
        date_string = cell.value.split("|")

        date_string = date_string[0][:-3] + date_string[2]
        print(date_string)
        format_string = "%B %d %I:%M%p %Z"

        datetime_object = parser.parse(date_string)

        title_string = sh.get_worksheet(0).cell(cell.row + 3, 4).value

        description_string = sh.get_worksheet(0).cell(cell.row + 5, 4).value

        if description_string is None:
            description_string = sh.get_worksheet(0).cell(cell.row + 6, 4).value
            collab_url = sh.get_worksheet(0).cell(cell.row + 4, 4).value

            description_string = collab_url + "\n" + description_string

        event = Event()
        event.add('summary', title_string)
        event.add('description', description_string)
        event.add('dtstart', datetime_object, parameters={'TZID': 'US/Central'})

        can_add = True

        for compontent in cal.walk("VEVENT"):
            if compontent["summary"] == event["summary"]:
                can_add = False
                # compontent['status'] = vText('CANCELLED')

        if can_add:
            cal.add_component(event)

    return cal


def read_emiru_schedule():
    calendar_path = "Emiru_calendar.ics"

    calendar = get_calendar(calendar_path)

    gc = gspread.service_account(filename="tmp/service_account.json")

    sh = gc.open_by_url(
        'https://docs.google.com/spreadsheets/d/1WFuxI2R5iLzt7x0k1LVV9Te5uQEb2X6CS5vc_VYC-AQ/edit#gid=2084945952')

    regex = re.compile(r"\d{2}/\d{2}")

    cells = sh.get_worksheet(0).findall(regex, in_column=2)

    for cell in cells:
        datetime_object = parser.parse(cell.value + " " + sh.get_worksheet(0).cell(cell.row + 1, cell.col + 3).value)

        print(datetime_object)
        title_string = sh.get_worksheet(0).cell(cell.row, cell.col + 3).value

        description_string = sh.get_worksheet(0).cell(cell.row + 2, cell.col + 3).value

        event = Event()
        event.add('summary', title_string)
        event.add('description', description_string)
        event.add('dtstart', datetime_object, parameters={'TZID': 'US/Central'})

        if "❌" in title_string:
            event['status'] = vText('CANCELLED')

        can_add = True

        # TODO turn this into a method, since ee and emiru use it
        for compontent in calendar.walk("VEVENT"):
            if compontent["summary"] == event["summary"]:
                can_add = False

        if can_add:
            calendar.add_component(event)

    save(calendar, calendar_path)


# Reads the calendar
def get_calendar(calendar_path):
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
        if start_date < datetime.today().date():
            # Print the summary of the event
            print(event.get("summary"))
            # Delete the event from the calendar
            calendar.add_component(event)

    return calendar


# Saves the calendar
def save(cal, calendar_path):
    if exists(calendar_path):
        os.remove(calendar_path)

    f = open(os.path.join(calendar_path), 'wb')
    f.write(cal.to_ical())
    f.close()


def get_miz_schedule():
    calendar_path = "calendar.ics"

    cal = get_calendar(calendar_path)

    cal = read_miz_schedule(cal)

    save(cal, calendar_path)


def get_ee_schedule():
    calendar_path = "EE_calendar.ics"

    calendar = get_calendar(calendar_path)

    calendar = read_ee_schedule(calendar)

    save(calendar, calendar_path)


if __name__ == '__main__':
    get_miz_schedule()
    time.sleep(100)

    get_ee_schedule()
    time.sleep(100)

    read_emiru_schedule()
