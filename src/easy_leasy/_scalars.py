import calendar
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Literal

from dateutil import tz as du_tz
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo

from ._base import BaseTimeSet

WeekDayName = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
MonthName = Literal[
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"
]


def _to_weekday(name: WeekDayName) -> int:
    try:
        return {
            "mon": 0,
            "tue": 1,
            "wed": 2,
            "thu": 3,
            "fri": 4,
            "sat": 5,
            "sun": 6,
        }[name]
    except KeyError:
        msg = f"Unknown weekday: {name}"
        raise ValueError(msg) from None


def _to_month(name: MonthName) -> int:
    try:
        return {
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }[name]
    except KeyError:
        msg = f"Unknown weekday: {name}"
        raise ValueError(msg) from None


def _ensure_aware(dt: datetime) -> datetime:
    """If dt is not aware, fucking die"""

    assert dt.tzinfo  # noqa: S101
    return dt


@dataclass
class WeekDay(BaseTimeSet):
    day: WeekDayName

    def _next_event(self, instant: datetime) -> datetime | None:
        target = _to_weekday(self.day)
        day = instant.weekday()

        if target == day:
            return instant + relativedelta(
                days=1, hour=0, minute=0, second=0, microsecond=0
            )
        else:
            days_until_target = (target - day) % 7
            return instant + relativedelta(
                days=days_until_target, hour=0, minute=0, second=0, microsecond=0
            )

    def value_at(self, instant: datetime) -> bool:
        return instant.weekday() == _to_weekday(self.day)


@dataclass
class Day(BaseTimeSet):
    day: int

    def __post_init__(self):
        if self.day < 1 or self.day > 31:
            msg = "Day must be between 1 and 31"
            raise ValueError(msg)

    def _next_event(self, instant: datetime) -> datetime | None:
        current_month = instant.month
        current_year = instant.year

        # Check if the day exists in the current month
        _, last_day = calendar.monthrange(current_year, current_month)

        if self.day > last_day:
            # Move to the next month that has this day
            while True:
                instant += relativedelta(months=1, day=1)
                _, last_day = calendar.monthrange(instant.year, instant.month)
                if self.day <= last_day:
                    break

        target = instant.replace(
            day=self.day, hour=0, minute=0, second=0, microsecond=0
        )

        if target <= instant:
            # If the target is in the past or present, move to the next month
            target += relativedelta(months=1)
            # Adjust for months that don't have this day
            while target.day != self.day:
                target += relativedelta(months=1)
                target = target.replace(
                    day=min(self.day, calendar.monthrange(target.year, target.month)[1])
                )

        return target

    def value_at(self, instant: datetime) -> bool:
        return instant.day == self.day


@dataclass
class Month(BaseTimeSet):
    month: MonthName

    def _next_event(self, instant: datetime) -> datetime | None:
        target = _to_month(self.month)
        month = instant.month

        if target == month:
            return instant + relativedelta(
                months=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        else:
            months_until_target = (target - month) % 12
            return instant + relativedelta(
                months=months_until_target,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

    def value_at(self, instant: datetime) -> bool:
        return instant.month == _to_month(self.month)


@dataclass(frozen=True, eq=True, order=True)
class Hour:
    hour: int
    minute: int

    def __post_init__(self):
        assert 0 <= self.hour < 24  # noqa: S101
        assert 0 <= self.minute < 60  # noqa: S101

    @classmethod
    def from_datetime(cls, dt: datetime) -> "Hour":
        return cls(dt.hour, dt.minute)

    def seconds(self) -> int:
        return self.hour * 3600 + self.minute * 60


class DstStretch(Enum):
    KEEP_WALL_CLOCK = auto()
    KEEP_DURATION = auto()


class DstStick(Enum):
    STICK_TO_BEGIN = auto()
    STICK_TO_END = auto()


@dataclass
class HourRange(BaseTimeSet):
    hour_begin: Hour
    hour_end: Hour
    dst_stretch: DstStretch = DstStretch.KEEP_DURATION
    dst_stick: DstStick = DstStick.STICK_TO_BEGIN

    @property
    def duration(self) -> relativedelta:
        return relativedelta(
            seconds=(self.hour_end.seconds() - self.hour_begin.seconds())
        )

    def __post_init__(self):
        if not self.hour_end > self.hour_begin:
            msg = "hour_end must be greater than hour_begin"
            raise ValueError(msg)

    def _adjust_datetime_range(self, instant: datetime) -> tuple[datetime, datetime]:
        dt_begin = instant + relativedelta(
            hour=self.hour_begin.hour,
            minute=self.hour_begin.minute,
            second=0,
            microsecond=0,
        )
        dt_end = instant + relativedelta(
            hour=self.hour_end.hour,
            minute=self.hour_end.minute,
            second=0,
            microsecond=0,
        )

        if not du_tz.datetime_exists(dt_begin):
            dt_begin = du_tz.resolve_imaginary(dt_begin)
            if self.dst_stretch == DstStretch.KEEP_DURATION:
                dt_end = dt_begin + self.duration
        elif du_tz.datetime_ambiguous(dt_begin):
            dt_begin = du_tz.enfold(dt_begin, fold=0)

        if not du_tz.datetime_exists(dt_end):
            dt_end = du_tz.resolve_imaginary(dt_end)
        elif du_tz.datetime_ambiguous(dt_end):
            dt_end = du_tz.enfold(dt_end, fold=1)

        utc_end = dt_end.astimezone(ZoneInfo("UTC"))
        utc_begin = dt_begin.astimezone(ZoneInfo("UTC"))

        dt_duration = (utc_end - utc_begin).total_seconds()
        normal_duration = self.hour_end.seconds() - self.hour_begin.seconds()

        if (
            dt_duration != normal_duration
            and self.dst_stretch == DstStretch.KEEP_DURATION
        ):
            if self.dst_stick == DstStick.STICK_TO_BEGIN:
                utc_end = utc_begin + self.duration
            else:
                utc_begin = utc_end - self.duration

            dt_begin = utc_begin.astimezone(dt_begin.tzinfo)
            dt_end = utc_end.astimezone(dt_begin.tzinfo)

        return dt_begin, dt_end

    def _next_event(self, instant: datetime) -> datetime:
        dt_begin, dt_end = self._adjust_datetime_range(instant)
        utc = ZoneInfo("UTC")

        if dt_begin.astimezone(utc) <= instant.astimezone(utc) < dt_end.astimezone(utc):
            return dt_end
        elif instant.astimezone(utc) < dt_begin.astimezone(utc):
            return dt_begin
        else:
            return instant + relativedelta(
                days=1,
                hour=self.hour_begin.hour,
                minute=self.hour_begin.minute,
                second=0,
                microsecond=0,
            )

    def value_at(self, instant: datetime) -> bool:
        dt_begin, dt_end = self._adjust_datetime_range(instant)
        utc = ZoneInfo("UTC")

        return (
            dt_begin.astimezone(utc) <= instant.astimezone(utc) < dt_end.astimezone(utc)
        )


@dataclass()
class Always(BaseTimeSet):
    def value_at(self, instant: datetime) -> bool:
        return True

    def _next_event(self, instant: datetime) -> datetime | None:
        return None


@dataclass()
class Never(BaseTimeSet):
    def value_at(self, instant: datetime) -> bool:
        return False

    def _next_event(self, instant: datetime) -> datetime | None:
        return None


@dataclass()
class Constant(BaseTimeSet):
    value: bool

    def value_at(self, instant: datetime) -> bool:
        return self.value

    def _next_event(self, instant: datetime) -> datetime | None:
        return None
