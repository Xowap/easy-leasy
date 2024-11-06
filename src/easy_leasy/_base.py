from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

# Maximum number of iterations to perform when computing the next change
NEXT_CHANGE_SAFEGUARD = 1_000


def safeguard(n: int):
    def _safeguard(val):
        nonlocal n
        n -= 1

        if n < 0:
            return None

        return val

    return _safeguard


@dataclass
class BaseTimeSet(ABC):
    @abstractmethod
    def _next_event(self, instant: datetime) -> datetime | None:
        raise NotImplementedError

    @abstractmethod
    def value_at(self, instant: datetime) -> bool:
        raise NotImplementedError

    def next_change(self, instant: datetime) -> datetime | None:
        start_value = self.value_at(instant)
        s = safeguard(NEXT_CHANGE_SAFEGUARD)
        new_instant = instant

        while s(new_instant := self._next_event(new_instant)):
            if start_value != self.value_at(new_instant):
                return new_instant

    def __or__(self, other) -> "BaseTimeSet":
        from ._operations import Union

        assert isinstance(  # noqa: S101
            other, BaseTimeSet
        ), f"Cannot union {self.__class__} with {other.__class__}"

        return Union(self, other)

    def __and__(self, other) -> "BaseTimeSet":
        from ._operations import Intersection

        assert isinstance(  # noqa: S101
            other, BaseTimeSet
        ), f"Cannot intersect {self.__class__} with {other.__class__}"

        return Intersection(self, other)

    def __sub__(self, other) -> "BaseTimeSet":
        from ._operations import Difference

        assert isinstance(  # noqa: S101
            other, BaseTimeSet
        ), f"Cannot subtract {self.__class__} with {other.__class__}"

        return Difference(self, other)

    def __xor__(self, other) -> "BaseTimeSet":
        from ._operations import SymmetricDifference

        assert isinstance(  # noqa: S101
            other, BaseTimeSet
        ), f"Cannot symmetric difference {self.__class__} with {other.__class__}"

        return SymmetricDifference(self, other)

    def __invert__(self) -> "BaseTimeSet":
        from ._operations import Complement

        return Complement(self)
