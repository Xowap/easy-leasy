from dataclasses import dataclass, fields
from datetime import datetime

from lark import Lark, Transformer, v_args

from ._base import BaseTimeSet
from ._operations import Complement, Difference, Intersection, Union
from ._scalars import (
    Always,
    Constant,
    Day,
    Hour,
    HourRange,
    Month,
    MonthName,
    Never,
    WeekDay,
    WeekDayName,
)

grammar = r"""
start: statement* return_stmt

statement: import_stmt
         | declaration

import_stmt: "from" NAME "import" NAME

return_stmt: "return" expression

declaration: "let" NAME "be" "when" expression

expression: scalar                       -> exp_scalar
          | "(" expression ")"           -> exp_paren
          | expression "|" expression    -> exp_union
          | expression "-" expression    -> exp_difference
          | expression "&" expression    -> exp_intersection
          | "~" expression               -> exp_complement

scalar: WEEKDAY           -> scalar_weekday
      | NUMBER            -> scalar_day
      | MONTH             -> scalar_month
      | hour "~" hour     -> scalar_hour_range
      | ALWAYS            -> scalar_always
      | NEVER             -> scalar_never
      | NAME              -> scalar_ref

hour: NUMBER ":" NUMBER

WEEKDAY.2: /mon|tue|wed|thu|fri|sat|sun/
MONTH.2: /jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec/
NUMBER.2: /\d+/
ALWAYS.2: "always"
NEVER.2: "never"
NAME.1: /[a-zA-Z_][a-zA-Z0-9_]*/

%import common.WS
%ignore WS
"""


@dataclass
class ReturnStatement:
    value: BaseTimeSet


@dataclass
class Declaration:
    name: str
    value: BaseTimeSet


@dataclass
class ImportStatement:
    namespace: str
    name: str


@dataclass
class Reference(BaseTimeSet):
    """
    This does not aim at being actually used, it's just a reference that is
    resolved when the program is executed.
    """

    name: str

    def _next_event(self, instant: datetime) -> datetime | None:
        raise NotImplementedError

    def value_at(self, instant: datetime) -> bool:
        raise NotImplementedError


class EasyLeasyTransformer(Transformer):
    def __init__(self, context):
        super().__init__()
        self.context = context

    NAME = str
    WEEKDAY = str
    MONTH = str
    NUMBER = int

    @v_args(inline=True)
    def exp_scalar(self, val):
        return val

    def scalar_always(self, _):
        return Always()

    def scalar_never(self, _):
        return Never()

    @v_args(inline=True)
    def scalar_weekday(self, day: WeekDayName):
        return WeekDay(day)

    @v_args(inline=True)
    def scalar_day(self, day: str):
        day = int(day)

        if not (1 <= day <= 31):
            msg = f"Day {day} is not between 1 and 31"
            raise ValueError(msg)

        return Day(day)

    @v_args(inline=True)
    def scalar_month(self, month: MonthName):
        return Month(month)

    @v_args(inline=True)
    def scalar_ref(self, name: str):
        return Reference(name)

    @v_args(inline=True)
    def hour(self, hour: str, minute: str):
        hour = int(hour)
        minute = int(minute)

        if not (0 <= hour < 24):
            msg = "Hour must be between 0 and 23"
            raise ValueError(msg)

        if not (0 <= minute < 60):
            msg = "Minute must be between 0 and 59"
            raise ValueError(msg)

        return Hour(hour, minute)

    @v_args(inline=True)
    def scalar_hour_range(self, hour_begin, hour_end):
        return HourRange(hour_begin, hour_end)

    @v_args(inline=True)
    def exp_union(self, a, b):
        return Union(a, b)

    @v_args(inline=True)
    def exp_difference(self, a, b):
        return Difference(a, b)

    @v_args(inline=True)
    def exp_intersection(self, a, b):
        return Intersection(a, b)

    @v_args(inline=True)
    def exp_complement(self, val):
        return Complement(val)

    @v_args(inline=True)
    def return_stmt(self, exp):
        return ReturnStatement(exp)

    @v_args(inline=True)
    def exp_paren(self, exp):
        return exp

    @v_args(inline=True)
    def declaration(self, name: str, exp: BaseTimeSet):
        return Declaration(name, exp)

    @v_args(inline=True)
    def import_stmt(self, ns: str, name: str):
        return ImportStatement(ns, name)

    @v_args(inline=True)
    def statement(self, val):
        return val

    def resolve_references(
        self, value: BaseTimeSet, variables: dict[str, BaseTimeSet]
    ) -> BaseTimeSet:
        def _resolve(val: BaseTimeSet, path: list[str]) -> BaseTimeSet:
            while isinstance(val, Reference):
                if val.name not in variables:
                    msg = f"Reference '{val.name}' not found in variables."
                    raise ValueError(msg)

                if val.name in path:
                    msg = f"Circular reference to {val.name!r} through {path!r}."
                    raise ValueError(msg)

                val = variables[val.name]

            for f in fields(val):
                x = getattr(val, f.name)

                if isinstance(x, BaseTimeSet):
                    x = _resolve(x, [*path, f.name])
                    setattr(val, f.name, x)

            return val

        return _resolve(value, [])

    def resolve_import(self, imp: ImportStatement):
        match imp.namespace:
            case "context":
                try:
                    val = self.context[imp.name]

                    if not isinstance(val, BaseTimeSet):
                        val = Constant(val)

                    return val
                except KeyError:
                    msg = f"Context variable {imp.name!r} not found."
                    raise ValueError(msg) from None
            case _:
                msg = f"Unknown namespace {imp.namespace!r}."
                raise ValueError(msg)

    def start(self, statements):
        variables = {}

        for stmt in statements:
            if isinstance(stmt, Declaration):
                variables[stmt.name] = stmt.value
            elif isinstance(stmt, ImportStatement):
                variables[stmt.name] = self.resolve_import(stmt)
            elif isinstance(stmt, ReturnStatement):
                return self.resolve_references(stmt.value, variables)


def parse_easy_leasy(
    expr: str, context: dict[str, bool | BaseTimeSet] | None = None
) -> BaseTimeSet:
    parser = Lark(
        grammar,
        parser="lalr",
        transformer=EasyLeasyTransformer(context or {}),
    )

    # noinspection PyTypeChecker
    return parser.parse(expr)
