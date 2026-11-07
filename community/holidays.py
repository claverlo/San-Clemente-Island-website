"""U.S. federal holidays, worked out from the rules in the law (5 U.S.C. 6103) so the dates are right every year.

Source: 5 U.S.C. 6103 and OPM's federal holiday schedule (opm.gov/policy-data-oversight/pay-leave/federal-holidays).
A holiday on a Saturday is observed the Friday before; on a Sunday, the Monday after.
Inauguration Day (January 20 every fourth year, for the Washington, DC area) moves to January 21 only when the 20th
is a Sunday, and is not moved when it falls on a Saturday.
"""
import calendar
from dataclasses import dataclass
from datetime import date, timedelta

MONDAY, THURSDAY = 0, 3


def nth_weekday(year, month, weekday, n):
    """The nth weekday of a month (n=1 is the first; n=-1 is the last)."""
    if n > 0:
        first = date(year, month, 1)
        return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))
    last = date(year, month, calendar.monthrange(year, month)[1])
    return last - timedelta(days=(last.weekday() - weekday) % 7)


def observed(day):
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


@dataclass(frozen=True)
class Holiday:
    slug: str
    name: str
    rule: str
    date: date
    observed: date

    @property
    def is_moved(self):
        return self.observed != self.date


# slug, official name, rule as written in the law, how to work out the date
RULES = [
    ("new-years-day", "New Year's Day", "January 1", lambda y: date(y, 1, 1)),
    ("mlk-day", "Birthday of Martin Luther King, Jr.", "Third Monday in January", lambda y: nth_weekday(y, 1, MONDAY, 3)),
    ("washingtons-birthday", "Washington's Birthday", "Third Monday in February", lambda y: nth_weekday(y, 2, MONDAY, 3)),
    ("memorial-day", "Memorial Day", "Last Monday in May", lambda y: nth_weekday(y, 5, MONDAY, -1)),
    ("juneteenth", "Juneteenth National Independence Day", "June 19", lambda y: date(y, 6, 19)),
    ("independence-day", "Independence Day", "July 4", lambda y: date(y, 7, 4)),
    ("labor-day", "Labor Day", "First Monday in September", lambda y: nth_weekday(y, 9, MONDAY, 1)),
    ("columbus-day", "Columbus Day", "Second Monday in October", lambda y: nth_weekday(y, 10, MONDAY, 2)),
    ("veterans-day", "Veterans Day", "November 11", lambda y: date(y, 11, 11)),
    ("thanksgiving-day", "Thanksgiving Day", "Fourth Thursday in November", lambda y: nth_weekday(y, 11, THURSDAY, 4)),
    ("christmas-day", "Christmas Day", "December 25", lambda y: date(y, 12, 25)),
]


def inauguration_day(year):
    """January 20 every fourth year after 1965 (2025, 2029, 2033, ...), or None in other years."""
    if year < 1965 or (year - 1965) % 4:
        return None
    day = date(year, 1, 20)
    if day.weekday() == 6:  # Sunday: moves to Monday the 21st
        day = date(year, 1, 21)
    return Holiday("inauguration-day", "Inauguration Day", "January 20, every four years", day, day)


def holidays_in_year(year):
    found = [Holiday(slug, name, rule, when(year), observed(when(year))) for slug, name, rule, when in RULES]
    inauguration = inauguration_day(year)
    if inauguration:
        found.insert(2, inauguration)
    return sorted(found, key=lambda h: h.date)


def holidays_in_month(year, month):
    """The federal holidays whose actual date falls in this month."""
    return [holiday for holiday in holidays_in_year(year) if holiday.date.month == month]


SUNDAY = 6


def easter_sunday(year):
    """Western (Gregorian) Easter, using the Meeus/Jones/Butcher method."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return date(year, month, day)


# Popular days people celebrate that are not federal holidays (shown as pictures too).
OBSERVANCES = [
    ("valentines-day", "Valentine's Day", "February 14", lambda y: date(y, 2, 14)),
    ("st-patricks-day", "St. Patrick's Day", "March 17", lambda y: date(y, 3, 17)),
    ("easter", "Easter", "Easter Sunday", easter_sunday),
    ("mothers-day", "Mother's Day", "Second Sunday in May", lambda y: nth_weekday(y, 5, SUNDAY, 2)),
    ("fathers-day", "Father's Day", "Third Sunday in June", lambda y: nth_weekday(y, 6, SUNDAY, 3)),
    ("halloween", "Halloween", "October 31", lambda y: date(y, 10, 31)),
    ("new-years-eve", "New Year's Eve", "December 31", lambda y: date(y, 12, 31)),
]


def observances_in_year(year):
    return [Holiday(slug, name, rule, when(year), when(year)) for slug, name, rule, when in OBSERVANCES]


def month_highlights(year, month):
    """Everything to picture this month: federal holidays plus popular days, in calendar order."""
    found = holidays_in_month(year, month) + [h for h in observances_in_year(year) if h.date.month == month]
    return sorted(found, key=lambda h: h.date)
