"""A PyCascades Portland 2020 Countdown timer for the PyPortal

Author: Nina Zakharenko
"""

import time

import board
from adafruit_pyportal import PyPortal

import events
from themes import themes


pyportal = PyPortal(status_neopixel=board.NEOPIXEL, default_bg="/bgs/loading.bmp")

event_time = time.struct_time((2020, 2, 8, 0, 0, 0, None, None, None))
themes.initialize(pyportal)

theme_switch_mins = 5
time_last_refreshed = None

while True:
    # Decide if we should refresh the PyPortal's local time from the internet
    if events.should_refresh_time(event_time, time_last_refreshed):
        time_last_refreshed = events.update_local_time_from_internet(pyportal)

    # Get the time remaining until the event
    days_remaining, hours_remaining, mins_remaining = events.days_hours_mins_to_event(event_time)

    # Update the display with the time remaining
    themes.current_theme.update_time(days_remaining, hours_remaining, mins_remaining)

    # Switch themes occasionally, for the mins defined in theme_switch_mins
    if mins_remaining % theme_switch_mins == 0:
        themes.next_theme(pyportal)
        time.sleep(60)  # Sleep for one minute in seconds

    # If the event has passed, clear the screen and show the event started background
    if events.event_passed(event_time):
        print("Event passed! Setting event background, stopping countdown.")

        pyportal.splash.pop()
        pyportal.set_background("/bgs/party.bmp")

        while True:
            pass
