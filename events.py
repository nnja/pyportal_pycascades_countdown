"""Calculate time periods, handle PyPortal time refresh from the internet.

Some methods based on code from this guide by John Park:
learn.adafruit.com/pyportal-event-countdown-clock

Author: Nina Zakharenko
"""
import time

import rtc


def _time_periods_in_epoch(epoch):
    """
    Args:
        epoch (int): the Unix-time epoch to extract time periods from.

    Returns:
        tuple: A tuple of ints (days, hours, mins) in the epoch.
    """
    epoch = epoch // 60
    mins = epoch % 60
    epoch = epoch // 60
    hours = epoch % 24
    epoch = epoch // 24
    days = epoch

    return days, hours, mins


def should_refresh_time(event_time, last_refresh_time, refresh_after_mins=60):
    """
    The clock on the PyPortal drifts, and should be refreshed
    from the internet periodically for accuracy.

    We want to refresh the local time when:
    - The local time isn't set
    - After refresh_after_mins have passed
    - If the event time hasn't passed

    Args:
        event_time (time.struct_time): Time of the event.
        last_refresh_time (time.monotonic): Time local time
            was last refreshed from the internet.
        refresh_after_mins (int, optional): How many minutes to wait
            between refreshing from the internet. Defaults to 60.

    Returns:
        bool: If the local device time should be refreshed from
            the internet.
    """
    just_turned_on = not last_refresh_time
    if just_turned_on:
        print("Refreshing time: PyPortal just turned on.")
        return True

    time_since_refresh = time.monotonic() - last_refresh_time
    refresh_time_period_expired = time_since_refresh > refresh_after_mins * 60
    if refresh_time_period_expired:
        print(
            "Refreshing time: last refreshed over {} mins ago.".format(
                refresh_after_mins
            )
        )
        return True

    if event_passed(event_time):
        print("Won't refresh time: event over.")
        return False


def event_passed(event_time):
    """Calculate if the event time has passed or not.

    Arguments:
        event_time (time.struct_time): Time of the event.

    Returns:
        bool: True if the event has passed, False otherwise.
    """
    remaining_time = time.mktime(event_time) - time.mktime(time.localtime())
    return remaining_time and remaining_time < 0


def update_local_time_from_internet(pyportal, timezone="Etc/UTC", debug=False):
    """
    Fetches the local time from the internet, and sets it on the PyPortal.

    Make sure you get the local time at the timezone you want, since
    the location set in your secrets file can override this value.

    Set debug to skip fetching time from the internet. Useful for
    faster startup time while reloading code.

    TODO NZ: Figure out why timezone doesn't match https://pythonclock.org/
    TODO NZ: The pyportal library clobbers all exceptions, and sleeps.
        Rewrite for better error handling.

    Args:
        pyportal (adafruit_pyportal.PyPortal): PyPortal instance.
        timezone (str, optional): Timezone to fetch time from.
            Overwritten by value in secrets.py. Defaults to "Etc/UTC".
        debug (bool, optional): Use the rtc clock time if set.
            Defaults to False.

    Returns:
        float: Monotonic timestamp of the current time.
    """
    is_rtc_clock_set = rtc.RTC().datetime.tm_year != 2000
    if debug and is_rtc_clock_set:
        print("Debug mode. Using cached localtime.")
    else:
        print("Trying to update local time from internet.")
        pyportal.get_local_time()

    time_now = time.monotonic()
    print("Time last refreshed at", time_now)
    return time_now


def days_hours_mins_to_event(event_time):
    """
    Args:
        event_time (time.struct_time): Time of the event.

    Returns:
        tuple: A tuple of ints (days, hours, mins) remaining until
                the event time.
    """
    now = time.localtime()
    time_remaining = time.mktime(event_time) - time.mktime(now)

    days_remaining, hours_remaining, mins_remaining = _time_periods_in_epoch(time_remaining)
    return days_remaining, hours_remaining, mins_remaining
