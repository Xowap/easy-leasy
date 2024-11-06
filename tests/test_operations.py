from datetime import datetime

from zoneinfo import ZoneInfo

from easy_leasy import (
    Always,
    Difference,
    Hour,
    HourRange,
    Intersection,
    Never,
    SymmetricDifference,
    Union,
    WeekDay,
)


def test_union():
    tz = ZoneInfo("Europe/Paris")
    u = WeekDay("mon") | WeekDay("wed")
    assert isinstance(u, Union)

    dt = datetime(2024, 11, 6, 1, 42, 29, tzinfo=tz)
    assert u.value_at(dt) is True
    assert u.next_change(dt) == datetime(2024, 11, 7, 0, 0, 0, tzinfo=tz)

    dt = datetime(2024, 11, 7, 1, 42, 29, tzinfo=tz)
    assert u.value_at(dt) is False
    assert u.next_change(dt) == datetime(2024, 11, 11, 0, 0, 0, tzinfo=tz)


def test_workday():
    tz = ZoneInfo("Europe/Paris")
    u = WeekDay("mon") & WeekDay("wed")

    dt = datetime(2024, 11, 6, 1, 42, 29, tzinfo=tz)
    assert u.value_at(dt) is False
    assert u.next_change(dt) is None

    u = WeekDay("mon") & (
        HourRange(Hour(9, 30), Hour(13, 30)) | HourRange(Hour(14, 30), Hour(18, 30))
    )

    dt = datetime(2024, 11, 4, 11, 3, 42, tzinfo=tz)
    assert u.value_at(dt) is True
    assert u.next_change(dt) == datetime(2024, 11, 4, 13, 30, tzinfo=tz)

    dt = datetime(2024, 11, 4, 13, 30, tzinfo=tz)
    assert u.value_at(dt) is False
    assert u.next_change(dt) == datetime(2024, 11, 4, 14, 30, tzinfo=tz)

    dt = datetime(2024, 11, 4, 15, 28, tzinfo=tz)
    assert u.value_at(dt) is True
    assert u.next_change(dt) == datetime(2024, 11, 4, 18, 30, tzinfo=tz)

    dt = datetime(2024, 11, 4, 18, 42, tzinfo=tz)
    assert u.value_at(dt) is False
    assert u.next_change(dt) == datetime(2024, 11, 11, 9, 30, tzinfo=tz)


def test_intersection():
    tz = ZoneInfo("Europe/Paris")

    u = Always() & Never()
    dt = datetime(2024, 11, 4, 11, 3, 42, tzinfo=tz)
    assert isinstance(u, Intersection)
    assert u.value_at(dt) is False
    assert u.next_change(dt) is None

    u = Always() & WeekDay("mon")
    dt = datetime(2024, 11, 4, 11, 3, 42, tzinfo=tz)
    assert isinstance(u, Intersection)
    assert u.value_at(dt) is True
    assert u.next_change(dt) == datetime(2024, 11, 5, 0, 0, tzinfo=tz)

    u = WeekDay("mon") & Always()
    dt = datetime(2024, 11, 4, 11, 3, 42, tzinfo=tz)
    assert isinstance(u, Intersection)
    assert u.value_at(dt) is True
    assert u.next_change(dt) == datetime(2024, 11, 5, 0, 0, tzinfo=tz)

    u = Never() & WeekDay("mon")
    dt = datetime(2024, 11, 4, 11, 3, 42, tzinfo=tz)
    assert isinstance(u, Intersection)
    assert u.value_at(dt) is False
    assert u.next_change(dt) is None

    u = HourRange(Hour(10, 0), Hour(12, 0)) & HourRange(Hour(11, 0), Hour(13, 0))
    dt = datetime(2024, 11, 4, 11, 3, 42, tzinfo=tz)
    assert isinstance(u, Intersection)
    assert u.value_at(dt) is True
    assert u.next_change(dt) == datetime(2024, 11, 4, 12, 0, tzinfo=tz)
    dt = datetime(2024, 11, 4, 12, 42, tzinfo=tz)
    assert u.value_at(dt) is False
    assert u.next_change(dt) == datetime(2024, 11, 5, 11, 0, tzinfo=tz)


def test_difference():
    tz = ZoneInfo("Europe/Paris")

    r1 = HourRange(Hour(10, 0), Hour(12, 0))
    r2 = HourRange(Hour(10, 0), Hour(11, 0))
    d = r1 - r2
    assert isinstance(d, Difference)

    dt = datetime(2024, 11, 4, 10, 3, 42, tzinfo=tz)
    assert d.value_at(dt) is False
    assert d.next_change(dt) == datetime(2024, 11, 4, 11, 0, tzinfo=tz)

    dt = datetime(2024, 11, 4, 11, 3, 42, tzinfo=tz)
    assert d.value_at(dt) is True
    assert d.next_change(dt) == datetime(2024, 11, 4, 12, 0, tzinfo=tz)

    dt = datetime(2024, 11, 4, 12, 3, 42, tzinfo=tz)
    assert d.value_at(dt) is False
    assert d.next_change(dt) == datetime(2024, 11, 5, 11, 0, tzinfo=tz)


def test_complement():
    c = ~Always()
    tz = ZoneInfo("Europe/Paris")
    assert c.value_at(datetime.now(tz=tz)) is False
    assert c.next_change(datetime.now(tz=tz)) is None


def test_symmetric_difference():
    tz = ZoneInfo("Europe/Paris")

    d = Always() ^ WeekDay("mon")
    assert isinstance(d, SymmetricDifference)

    dt = datetime(2024, 11, 4, 11, 3, 42, tzinfo=tz)
    assert d.value_at(dt) is False
    assert d.next_change(dt) == datetime(2024, 11, 5, 0, 0, tzinfo=tz)

    dt = datetime(2024, 11, 5, 11, 4, tzinfo=tz)
    assert d.value_at(dt) is True
    assert d.next_change(dt) == datetime(2024, 11, 11, 0, 0, tzinfo=tz)
