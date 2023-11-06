import re
import time
from datetime import datetime

import dateutil.parser
import gspread
from icalendar import Calendar, Event, vText
from os.path import exists
import os

from dateutil import parser, tz

us_tzinfos = {
    "CT": tz.gettz("US/Central"),
    "PT": tz.gettz("US/Pacific")
}


def read_day(box, sh):
    # Get time
    time_str = sh.sheet1.cell(box + 1, 5).value

    time_object = parser.parse(time_str, tzinfos=us_tzinfos)

    # Get date
    date_str = sh.sheet1.cell(box, 2).value  # month/day
    # Combine date and time
    date_object = parser.parse(date_str, tzinfos=us_tzinfos)

    date_object = datetime.combine(date_object, time_object.time(), tzinfo=time_object.tzinfo)

    # Create event object
    event = Event()
    event.add('summary', sh.sheet1.cell(box + 2, 5).value)
    event.add('description', "https://www.twitch.tv/mizkif")
    event.add('dtstart', date_object)

    print("    " + event["summary"])

    return event


def read_miz_schedule():
    # Get calendar
    calendar_path = "calendar.ics"
    cal = load_calendar(calendar_path)

    # Load service account
    gc = gspread.service_account(filename="tmp/service_account.json")

    # Load spreadsheet
    sh = gc.open_by_url(
        'https://docs.google.com/spreadsheets/d/1cJyQsoi07DV7NIaWi9ywLEMLa6wWVzWgus0fQX8dcnc/edit#gid=902918299')

    # regex for a date in the format mm/dd
    date_regex = re.compile(r"^(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])$")

    counter = 0

    # find the 1st 10 dates
    cells = sh.get_worksheet(0).findall(date_regex, in_column=2)

    print("  new events:")
    for day in cells:

        # repeat until the API doesn't return an error
        while True:
            try:
                event = read_day(day.row, sh)

                can_add = True

                for compontent in cal.walk("VEVENT"):
                    if compontent["summary"] == event["summary"]:
                        can_add = False

                if can_add:
                    cal.add_component(event)

            except gspread.exceptions.APIError:
                print("API limit reached, waiting 70 seconds")
                time.sleep(70)
            break

        counter = counter + 1
        if counter == 11:
            break

    save_calendar(cal, calendar_path)


def read_ee_schedule():
    calendar_path = "EE_calendar.ics"

    cal = load_calendar(calendar_path)

    gc = gspread.service_account(filename="tmp/service_account.json")

    sh = gc.open_by_url(
        'https://docs.google.com/spreadsheets/d/1hJ5FJCXeaTRPb8ROR-PiEzMYKb3U7Z35ujn6mSzzHKg/edit#gid=0')

    date_regex = re.compile(r'(\w+) (\d+)\w+ \| (\w+) \| (\d+):(\d+)\w+ (\w+)')

    while True:
        # Searches for all boxes with a date
        try:
            cells = sh.get_worksheet(0).findall(date_regex, in_column=4)
            break
        except gspread.exceptions.APIError:
            print("API limit reached, waiting 70 seconds")
            time.sleep(70)

    print("  new events:")
    for cell in cells:
        while True:
            try:
                date_string = cell.value.split("|")

                date_string = date_string[0][:-3] + date_string[2]

                datetime_object = parser.parse(date_string, tzinfos=us_tzinfos)

                title_string = sh.get_worksheet(0).cell(cell.row + 3, 4).value

                description_string = sh.get_worksheet(0).cell(cell.row + 5, 4).value

                if description_string is None:
                    description_string = sh.get_worksheet(0).cell(cell.row + 6, 4).value
                    collab_url = sh.get_worksheet(0).cell(cell.row + 4, 4).value

                    description_string = collab_url + "\n" + description_string

                break

            except gspread.exceptions.APIError:
                print("API limit reached, waiting 70 seconds")
                time.sleep(70)

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
            print("    " + event["summary"])
            cal.add_component(event)

    save_calendar(cal, calendar_path)


def read_emiru_schedule():
    calendar_path = "Emiru_calendar.ics"

    calendar = load_calendar(calendar_path)

    gc = gspread.service_account(filename="tmp/service_account.json")

    sh = gc.open_by_url(
        'https://docs.google.com/spreadsheets/d/1WFuxI2R5iLzt7x0k1LVV9Te5uQEb2X6CS5vc_VYC-AQ/edit#gid=2084945952')

    regex = re.compile(r"\d{2}/\d{2}")

    while True:
        try:
            cells = sh.get_worksheet(0).findall(regex, in_column=2)
            break
        except gspread.exceptions.APIError:
            print("API limit reached, waiting 70 seconds")
            time.sleep(70)

    print("  new events:")
    for cell in cells:
        while True:
            try:
                date_string = sh.get_worksheet(0).cell(cell.row + 1, cell.col + 3).value

                try:
                    datetime_object = parser.parse(cell.value + " " + date_string, tzinfos=us_tzinfos)
                except dateutil.parser.ParserError:
                    print("     No time, defaulted to 4 pm:")
                    datetime_object = parser.parse("4:00 PM CT", tzinfos=us_tzinfos)

                title_string = sh.get_worksheet(0).cell(cell.row, cell.col + 3).value

                description_string = sh.get_worksheet(0).cell(cell.row + 2, cell.col + 3).value

                break

            except gspread.exceptions.APIError:
                print("API limit reached, waiting 70 seconds")
                time.sleep(70)

        event = Event()
        event.add('summary', title_string)
        event.add('description', description_string)
        event.add('dtstart', datetime_object, parameters={'TZID': 'US/Central'})

        if "❌" in title_string:
            event['status'] = vText('CANCELLED')

        can_add = True

        for compontent in calendar.walk("VEVENT"):
            if compontent.get("dtstart").dt == event["dtstart"].dt:
                can_add = False

        if can_add:
            print("    " + event["summary"])
            calendar.add_component(event)

    save_calendar(calendar, calendar_path)


# Reads the calendar
def load_calendar(calendar_path):
    calendar = Calendar()

    if not exists(calendar_path):
        calendar.add('prodid', 'dregoc')
        calendar.add('version', '2.0')
        calendar.add('TZID', 'UTC-5')

        f = open(os.path.join(calendar_path), 'wb')
        f.write(calendar.to_ical())
        f.close()

    with open(calendar_path, "rb") as f:
        old_calendar = Calendar.from_ical(f.read())

    print("  old events:")
    for event in old_calendar.walk('VEVENT'):
        start_date = event.get("dtstart").dt.date()
        # Check if it matches the target date

        if start_date < datetime.today().date():
            # Print the summary of the event

            print("    " + event.get("summary"))
            # Delete the event from the calendar
            calendar.add_component(event)

    return calendar


# Saves the calendar
def save_calendar(cal, calendar_path):
    # If the calendar already exists deletes it
    if exists(calendar_path):
        os.remove(calendar_path)

    f = open(os.path.join(calendar_path), 'wb')
    f.write(cal.to_ical())
    f.close()


if __name__ == '__main__':
    print("Miz")
    read_miz_schedule()

    # print("ExtraEmily")
    # read_ee_schedule()
    #
    # print("Emiru")
    # read_emiru_schedule()
