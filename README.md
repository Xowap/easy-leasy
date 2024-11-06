# Easy Leasy

Easy Leasy is a Python library for defining time-based rules and manipulating
time sets.

The idea is to express easily things like "open from 9am to 5pm from Monday to
Friday" as a single expression, and then use it both to know if a given time
is in the time set, and to compute the next time change.

## Usage

You can use the `parse_easy_leasy` function to parse an expression into a
`BaseTimeSet` object, which will allow you query that time set.

```python
from easy_leasy import parse_easy_leasy
from datetime import datetime
from zoneinfo import ZoneInfo

p = parse_easy_leasy(
    """
    from context import has_pr

    let work_hour be when 9:30~13:30 | 14:30~18:30
    let work_day be when mon | tue | wed | thu | fri
    let business_hour be when work_hour & work_day

    let xmas be when 25 & dec
    let ny be when 1 & jan
    let work be when 1 & may
    let holiday be when xmas | ny | work

    return business_hour - holiday
    """,
    dict(has_pr=True),
)

now = datetime.now(tz=ZoneInfo("Europe/Paris"))
print(p.value_at(now))
print(p.next_change(now))
```

The `parse_easy_leasy` function takes two arguments: the expression to parse,
and a dictionary of context variables which can either be a boolean or a
`BaseTimeSet` object.

## Language reference

The language is simple and has 3 different statements:

- `from <namespace> import <name>`: import a variable from the context.
- `let <name> be when <expression>`: declare a new variable `<name>` with the 
  value of `<expression>`.
- `return <expression>`: return the value of `<expression>`.

The only statement that is mandatory is `return`, which is the expression that
will be evaluated to determine the value of the time set.

Expressions are composed of the different types:

- **Hour ranges**: `hour:minute~hour:minute`
- **Days of the week**: `mon | tue | wed | thu | fri | sat | sun`
- **Days of the month**: `1 | 2 | ... | 31`
- **Months**: `jan | feb | ... | dec`
- **Absolutes**: `always | never`

These expressions can be combined using the same operators as the Python sets:

- `|`: union
- `&`: intersection
- `-`: difference
- `~`: complement

## API reference

Everything is based on the `BaseTimeSet` class, which can also be used directly
from Python.

It has different implementations, which are:

- `Always`: always true
- `Never`: always false
- `HourRange`: a range of hours
- `Day`: a single day of the week
- `WeekDay`: a single day of the month
- `Month`: a single month
- `Constant`: a constant value

As they are subclasses of `BaseTimeSet`, they can be used with the standard
Python set operators, for example:

```python
from easy_leasy import Always, Month

p = Always() & Month('jan')
```

Once you have a `BaseTimeSet` object, you can use the `value_at` and
`next_change` methods to query the time set.

```python
from easy_leasy import Always
from datetime import datetime
from zoneinfo import ZoneInfo

p = Always()

# Check if the time set is true at a given instant
p.value_at(datetime.now(tz=ZoneInfo("Europe/Paris")))

# Get the next time change
p.next_change(datetime.now(tz=ZoneInfo("Europe/Paris")))
```
