from datetime import datetime

from zoneinfo import ZoneInfo

from easy_leasy import (
    Always,
    Complement,
    Day,
    Difference,
    Hour,
    HourRange,
    Intersection,
    Month,
    Never,
    Union,
    WeekDay,
    parse_easy_leasy,
)


def test_parser_always():
    p = parse_easy_leasy("return always")
    assert isinstance(p, Always)


def test_parser_never():
    p = parse_easy_leasy("return never")
    assert isinstance(p, Never)


def test_parser_weekday():
    p = parse_easy_leasy("return mon")
    assert isinstance(p, WeekDay)
    assert p.day == "mon"


def test_parser_day():
    p = parse_easy_leasy("return 11")
    assert isinstance(p, Day)
    assert p.day == 11


def test_parser_month():
    p = parse_easy_leasy("return may")
    assert isinstance(p, Month)
    assert p.month == "may"


def test_parse_hour_range():
    p = parse_easy_leasy("return 1:00~2:00")
    assert isinstance(p, HourRange)
    assert p.hour_begin == Hour(1, 0)
    assert p.hour_end == Hour(2, 0)


def test_parse_exp_union():
    p = parse_easy_leasy("return mon | tue")
    assert isinstance(p, Union)
    assert p.a == WeekDay("mon")
    assert p.b == WeekDay("tue")


def test_parse_exp_diff():
    p = parse_easy_leasy("return always - sun")
    assert isinstance(p, Difference)
    assert isinstance(p.a, Always)
    assert isinstance(p.b, WeekDay)
    assert p.b.day == "sun"


def test_parse_exp_intersection():
    p = parse_easy_leasy("return 1:00~2:00 & 1:30~3:00")
    assert isinstance(p, Intersection)
    assert isinstance(p.a, HourRange)
    assert isinstance(p.b, HourRange)
    assert p.a.hour_begin == Hour(1, 0)
    assert p.a.hour_end == Hour(2, 0)
    assert p.b.hour_begin == Hour(1, 30)
    assert p.b.hour_end == Hour(3, 0)


def test_parse_exp_complement():
    p = parse_easy_leasy("return ~1:00~2:00")
    assert isinstance(p, Complement)
    assert isinstance(p.a, HourRange)
    assert p.a.hour_begin == Hour(1, 0)
    assert p.a.hour_end == Hour(2, 0)


def test_parse_exp_paren():
    p = parse_easy_leasy("return (always | never) & mon")
    assert isinstance(p, Intersection)
    assert isinstance(p.a, Union)

    p = parse_easy_leasy("return always | (never & mon)")
    assert isinstance(p, Union)
    assert isinstance(p.b, Intersection)


def test_parse_declaration():
    p = parse_easy_leasy("let foo be when always return foo")
    assert isinstance(p, Always)


def test_parser_case_1():
    expr = """
    from context import has_pr

    let work_hour be when 9:30~13:30 | 14:30~18:30
    let work_day be when mon | tue | wed | thu | fri
    let business_hour be when work_hour & work_day

    let xmas be when 25 & dec
    let ny be when 1 & jan
    let work be when 1 & may
    let holiday be when xmas | ny | work

    return business_hour - holiday
    """

    tz = ZoneInfo("Europe/Paris")
    p = parse_easy_leasy(expr, {"has_pr": True})

    dt = datetime(2024, 11, 4, 11, 3, 42, tzinfo=tz)
    assert p.value_at(dt) is True
    assert p.next_change(dt) == datetime(2024, 11, 4, 13, 30, tzinfo=tz)

    dt = datetime(2024, 12, 25, 11, 45, tzinfo=tz)
    assert p.value_at(dt) is False
    assert p.next_change(dt) == datetime(2024, 12, 26, 9, 30, tzinfo=tz)
