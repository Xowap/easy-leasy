from dataclasses import dataclass
from datetime import datetime

from ._base import BaseTimeSet


@dataclass
class Union(BaseTimeSet):
    a: BaseTimeSet
    b: BaseTimeSet

    def _next_event(self, instant: datetime) -> datetime | None:
        na = self.a.next_change(instant)
        nb = self.b.next_change(instant)

        if na is None and nb is None:
            return None
        if na is None:
            return nb
        if nb is None:
            return na
        else:
            return min(na, nb)

    def value_at(self, instant: datetime) -> bool:
        return self.a.value_at(instant) or self.b.value_at(instant)


@dataclass
class Intersection(BaseTimeSet):
    a: BaseTimeSet
    b: BaseTimeSet

    def _next_event(self, instant: datetime) -> datetime | None:
        na = self.a.next_change(instant)
        nb = self.b.next_change(instant)
        va = self.a.value_at(instant)
        vb = self.b.value_at(instant)

        if na is None and nb is None:
            return None
        elif na is None:
            return nb if va else None
        elif nb is None:
            return na if vb else None
        else:
            return min(na, nb)

    def value_at(self, instant: datetime) -> bool:
        return self.b.value_at(instant) and self.a.value_at(instant)


@dataclass
class Difference(BaseTimeSet):
    a: BaseTimeSet
    b: BaseTimeSet

    def _next_event(self, instant: datetime) -> datetime | None:
        na = self.a.next_change(instant)
        nb = self.b.next_change(instant)
        va = self.a.value_at(instant)
        vb = self.b.value_at(instant)

        if na is None and nb is None:
            return None
        elif na is None:
            return nb if va and not vb else None
        elif nb is None:
            return na if va or not vb else None
        else:
            return min(na, nb)

    def value_at(self, instant: datetime) -> bool:
        return self.a.value_at(instant) and not self.b.value_at(instant)


@dataclass
class SymmetricDifference(BaseTimeSet):
    a: BaseTimeSet
    b: BaseTimeSet

    def _next_event(self, instant: datetime) -> datetime | None:
        na = self.a.next_change(instant)
        nb = self.b.next_change(instant)

        if na is None and nb is None:
            return None
        elif na is None:
            return nb
        elif nb is None:
            return na
        else:
            return min(na, nb)

    def value_at(self, instant: datetime) -> bool:
        return self.a.value_at(instant) != self.b.value_at(instant)


@dataclass
class Complement(BaseTimeSet):
    a: BaseTimeSet

    def _next_event(self, instant: datetime) -> datetime | None:
        return self.a.next_change(instant)

    def value_at(self, instant: datetime) -> bool:
        return not self.a.value_at(instant)
