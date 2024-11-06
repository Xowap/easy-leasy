from datetime import datetime, timedelta

import pytest
from zoneinfo import ZoneInfo

from easy_leasy import (
    Constant,
    Day,
    DstStick,
    DstStretch,
    Hour,
    HourRange,
    Month,
    WeekDay,
)


def test_weekday():
    tz = ZoneInfo("Europe/Paris")

    wd = WeekDay("mon")
    dt = datetime(2024, 11, 4, 11, 3, 42, 231, tzinfo=tz)
    assert wd.value_at(dt) is True

    dt = wd._next_event(dt)
    assert dt == datetime(2024, 11, 5, 0, 0, 0, 0, tzinfo=tz)
    assert wd.value_at(dt) is False

    dt = wd._next_event(dt)
    assert dt == datetime(2024, 11, 11, 0, 0, 0, 0, tzinfo=tz)
    assert wd.value_at(dt) is True


def test_day():
    tz = ZoneInfo("Europe/Paris")

    d = Day(1)
    dt = datetime(2024, 11, 4, 11, 3, 42, 111, tzinfo=tz)
    assert d.value_at(dt) is False

    dt = d._next_event(dt)
    assert dt == datetime(2024, 12, 1, 0, 0, 0, 0, tzinfo=tz)
    assert d.value_at(dt) is True

    d = Day(31)
    dt = datetime(2024, 11, 4, 11, 3, 42, 111, tzinfo=tz)
    assert d.value_at(dt) is False

    dt = d._next_event(dt)
    assert dt == datetime(2024, 12, 31, 0, 0, 0, 0, tzinfo=tz)
    assert d.value_at(dt) is True

    d = Day(29)
    dt = datetime(2000, 1, 30, 11, 3, 42, 111, tzinfo=tz)
    assert d.value_at(dt) is False

    dt = d._next_event(dt)
    assert dt == datetime(2000, 2, 29, 0, 0, 0, 0, tzinfo=tz)
    assert d.value_at(dt) is True


def test_month():
    tz = ZoneInfo("Europe/Paris")

    m = Month("nov")
    dt = datetime(2024, 11, 4, 11, 3, 42, 111, tzinfo=tz)
    assert m.value_at(dt) is True

    dt = m._next_event(dt)
    assert dt == datetime(2024, 12, 1, 0, 0, 0, 0, tzinfo=tz)
    assert m.value_at(dt) is False

    dt = m._next_event(dt)
    assert dt == datetime(2025, 11, 1, 0, 0, 0, 0, tzinfo=tz)
    assert m.value_at(dt) is True


def test_hour_range():
    tz = ZoneInfo("Europe/Paris")

    hr = HourRange(Hour(11, 0), Hour(12, 0))
    dt = datetime(2024, 11, 4, 11, 3, 42, 111, tzinfo=tz)
    assert hr.value_at(dt) is True

    dt = hr._next_event(dt)
    assert dt == datetime(2024, 11, 4, 12, 0, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is False

    dt = hr._next_event(dt)
    assert dt == datetime(2024, 11, 5, 11, 0, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is True

    dt = datetime(2024, 11, 4, 9, 4, 53, 195, tzinfo=tz)
    assert hr.value_at(dt) is False

    dt = hr._next_event(dt)
    assert dt == datetime(2024, 11, 4, 11, 0, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is True


@pytest.fixture(params=list(DstStick))
def stick(request):
    return request.param


@pytest.fixture(params=list(DstStretch))
def stretch(request):
    return request.param


def test_dst_jump_case_1(stick: DstStick, stretch: DstStretch):
    tz = ZoneInfo("Europe/Paris")
    # March 31, 2024 - DST starts, clock jumps from 2:00 to 3:00

    # Case 1: Starts before, ends after jump
    hr = HourRange(Hour(1, 30), Hour(3, 30), dst_stick=stick, dst_stretch=stretch)
    dt = datetime(2024, 3, 31, 0, 0, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is False

    dt = hr._next_event(dt)

    match (stick, stretch):
        case (DstStick.STICK_TO_END, DstStretch.KEEP_DURATION):
            assert dt == datetime(2024, 3, 31, 0, 30, 0, 0, tzinfo=tz)
        case _:
            assert dt == datetime(2024, 3, 31, 1, 30, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is True

    dt = hr._next_event(dt)
    match (stick, stretch):
        case (DstStick.STICK_TO_BEGIN, DstStretch.KEEP_DURATION):
            assert dt == datetime(2024, 3, 31, 4, 30, 0, 0, tzinfo=tz)
        case _:
            assert dt == datetime(2024, 3, 31, 3, 30, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is False


def test_dst_jump_case_2(stick: DstStick, stretch: DstStretch):
    tz = ZoneInfo("Europe/Paris")
    # March 31, 2024 - DST starts, clock jumps from 2:00 to 3:00

    # Case 2: Starts before, ends during jump
    hr = HourRange(Hour(1, 30), Hour(2, 30), dst_stick=stick, dst_stretch=stretch)
    dt = datetime(2024, 3, 31, 1, 0, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is False

    dt = hr._next_event(dt)
    assert dt == datetime(2024, 3, 31, 1, 30, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is True

    dt = hr._next_event(dt)
    assert dt == datetime(2024, 3, 31, 3, 30, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is False


def test_dst_jump_case_3(stick: DstStick, stretch: DstStretch):
    tz = ZoneInfo("Europe/Paris")
    # March 31, 2024 - DST starts, clock jumps from 2:00 to 3:00

    # Case 3: Starts during, ends after jump
    hr = HourRange(Hour(2, 30), Hour(4, 30), dst_stick=stick, dst_stretch=stretch)
    dt = datetime(2024, 3, 31, 2, 0, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is False
    dt = hr._next_event(dt)
    assert dt == datetime(2024, 3, 31, 3, 30, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is True
    dt = hr._next_event(dt)
    if stretch == DstStretch.KEEP_WALL_CLOCK:
        assert dt == datetime(2024, 3, 31, 4, 30, 0, 0, tzinfo=tz)
    else:  # KEEP_DURATION
        assert dt == datetime(2024, 3, 31, 5, 30, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is False


def test_dst_jump_case_4(stick: DstStick, stretch: DstStretch):
    tz = ZoneInfo("Europe/Paris")
    # March 31, 2024 - DST starts, clock jumps from 2:00 to 3:00

    # Case 4: Entirely within jump (should be skipped)
    hr = HourRange(Hour(2, 15), Hour(2, 45), dst_stick=stick, dst_stretch=stretch)
    dt = datetime(2024, 3, 31, 0, 0, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is False

    dt = hr._next_event(dt)
    assert dt == datetime(2024, 3, 31, 3, 15, tzinfo=tz)
    assert hr.value_at(dt) is True

    dt = hr._next_event(dt)
    assert dt == datetime(2024, 3, 31, 3, 45, tzinfo=tz)
    assert hr.value_at(dt) is False


def test_dst_repeat_case_1(stick: DstStick, stretch: DstStretch):
    tz = ZoneInfo("Europe/Paris")
    # October 27, 2024 - DST ends, clock goes from 3:00 back to 2:00

    # Case 1: Starts before, ends after repeat
    hr = HourRange(Hour(1, 30), Hour(3, 30), dst_stick=stick, dst_stretch=stretch)
    dt = datetime(2024, 10, 27, 1, 0, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is False
    dt = hr._next_event(dt)

    match (stick, stretch):
        case (DstStick.STICK_TO_END, DstStretch.KEEP_DURATION):
            assert dt == datetime(2024, 10, 27, 2, 30, 0, 0, fold=0, tzinfo=tz)
        case _:
            assert dt == datetime(2024, 10, 27, 1, 30, 0, 0, fold=0, tzinfo=tz)

    assert hr.value_at(dt) is True
    dt = hr._next_event(dt)

    match (stick, stretch):
        case (DstStick.STICK_TO_BEGIN, DstStretch.KEEP_DURATION):
            assert dt == datetime(2024, 10, 27, 2, 30, 0, 0, fold=1, tzinfo=tz)
        case _:
            assert dt == datetime(2024, 10, 27, 3, 30, 0, 0, fold=0, tzinfo=tz)

    assert hr.value_at(dt) is False

    # Additional check to ensure no flapping
    next_start = hr._next_event(dt)
    assert next_start.date() != datetime(2024, 10, 27, tzinfo=tz).date()


def test_dst_repeat_case_2(stick: DstStick, stretch: DstStretch):
    tz = ZoneInfo("Europe/Paris")
    # October 27, 2024 - DST ends, clock goes from 3:00 back to 2:00

    # Case 2: Starts before, ends during repeat
    hr = HourRange(Hour(1, 30), Hour(2, 30), dst_stick=stick, dst_stretch=stretch)
    dt = datetime(2024, 10, 27, 1, 0, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is False
    dt = hr._next_event(dt)

    match (stick, stretch):
        case (DstStick.STICK_TO_END, DstStretch.KEEP_DURATION):
            assert dt == datetime(2024, 10, 27, 2, 30, 0, 0, fold=0, tzinfo=tz)
        case _:
            assert dt == datetime(2024, 10, 27, 1, 30, 0, 0, tzinfo=tz)

    assert hr.value_at(dt) is True
    dt = hr._next_event(dt)

    match (stick, stretch):
        case (DstStick.STICK_TO_BEGIN, DstStretch.KEEP_DURATION):
            assert dt == datetime(2024, 10, 27, 2, 30, 0, 0, fold=0, tzinfo=tz)
        case _:
            assert dt == datetime(2024, 10, 27, 2, 30, 0, 0, fold=1, tzinfo=tz)

    assert hr.value_at(dt) is False

    # Additional check to ensure no flapping
    next_start = hr._next_event(dt)
    assert next_start.date() != datetime(2024, 10, 27, tzinfo=tz).date()


def test_dst_repeat_case_3(stick: DstStick, stretch: DstStretch):
    tz = ZoneInfo("Europe/Paris")
    # October 27, 2024 - DST ends, clock goes from 3:00 back to 2:00

    # Case 3: Starts during, ends after repeat
    hr = HourRange(Hour(2, 30), Hour(3, 30), dst_stick=stick, dst_stretch=stretch)
    dt = datetime(2024, 10, 27, 2, 0, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is False

    dt = hr._next_event(dt)

    match (stick, stretch):
        case (DstStick.STICK_TO_END, DstStretch.KEEP_DURATION):
            assert dt == datetime(2024, 10, 27, 2, 30, 0, 0, fold=1, tzinfo=tz)
        case _:
            assert dt == datetime(2024, 10, 27, 2, 30, 0, 0, fold=0, tzinfo=tz)

    assert hr.value_at(dt) is True

    dt = hr._next_event(dt)

    match (stick, stretch):
        case (DstStick.STICK_TO_BEGIN, DstStretch.KEEP_DURATION):
            assert dt == datetime(2024, 10, 27, 2, 30, 0, 0, fold=1, tzinfo=tz)
        case _:
            assert dt == datetime(2024, 10, 27, 3, 30, 0, 0, fold=0, tzinfo=tz)

    assert hr.value_at(dt) is False

    # Additional check to ensure no flapping
    next_start = hr._next_event(dt)
    assert next_start.date() != datetime(2024, 10, 27, tzinfo=tz).date()


def test_dst_repeat_case_4(stick: DstStick, stretch: DstStretch):
    tz = ZoneInfo("Europe/Paris")
    # October 27, 2024 - DST ends, clock goes from 3:00 back to 2:00

    # Case 4: Entirely within repeat hour
    hr = HourRange(Hour(2, 15), Hour(2, 45), dst_stick=stick, dst_stretch=stretch)
    dt = datetime(2024, 10, 27, 2, 0, 0, 0, tzinfo=tz)
    assert hr.value_at(dt) is False

    # The start time is ambiguous, so we need to consider both possibilities
    start_times = [
        datetime(2024, 10, 27, 2, 15, 0, 0, tzinfo=tz),
        datetime(2024, 10, 27, 2, 15, 0, 0, tzinfo=tz).replace(fold=1),
    ]

    if stick == DstStick.STICK_TO_BEGIN:
        expected_start = start_times[0]
    else:  # STICK_TO_END
        expected_start = start_times[1]

    dt = hr._next_event(dt)
    assert dt == expected_start
    assert hr.value_at(dt) is True

    dt = hr._next_event(dt)

    if stretch == DstStretch.KEEP_DURATION:
        # When keeping duration, it should always end after 30 minutes
        expected_end = expected_start + timedelta(minutes=30)
    else:  # KEEP_WALL_CLOCK
        # The end time is also ambiguous
        end_times = [
            datetime(2024, 10, 27, 2, 45, 0, 0, tzinfo=tz),
            datetime(2024, 10, 27, 2, 45, 0, 0, tzinfo=tz).replace(fold=1),
        ]
        if stick == DstStick.STICK_TO_BEGIN:
            expected_end = end_times[0]
        else:  # STICK_TO_END
            expected_end = end_times[1]

    assert dt == expected_end
    assert hr.value_at(dt) is False

    # Ensure no flapping
    next_start = hr._next_event(dt)
    assert next_start.date() != datetime(2024, 10, 27, tzinfo=tz).date()


def test_constant():
    c = Constant(True)
    tz = ZoneInfo("Europe/Paris")
    assert c.value_at(datetime.now(tz=tz)) is True
    assert c.next_change(datetime.now(tz=tz)) is None
