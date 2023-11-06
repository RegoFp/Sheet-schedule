# Sheet-schedule

Reads the sheet schedule of the streamers: Mizkif, Emiru and ExtraEmily and turns them into a icalendar file you can add to your calendar.

![Sin título-2](https://github.com/RegoFp/Sheet-schedule/assets/92778484/becade0a-f9b6-4d87-a1bf-a97341e9f374)

The calendar are automatically updated everyday at 6 am US CT

To add to your calendar simply add the url of the .ics files from the repo to your calendar app.

- Mizkif: https://raw.githubusercontent.com/RegoFp/Sheet-schedule/main/main.py
- Emiru: https://raw.githubusercontent.com/RegoFp/Sheet-schedule/main/Emiru_calendar.ics
- ExtraEmily: https://raw.githubusercontent.com/RegoFp/Sheet-schedule/main/EE_calendar.ics

## Libraries used:
- [gspread](https://github.com/burnash/gspread)
- [icalendar](https://github.com/collective/icalendar)

## Installation:
To have a local installation of this app you need to create a google service account, download a JSON key and place it a folder named tmp with the name service_account.json on the root of the project.
