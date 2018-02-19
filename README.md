# Logment

A logging library for Python 3 that uses augmented comments (logments). Simply import `logment`, and if the first character of your comment is a
`?`, `:`, or `!` it will be converted to a corresponding debug, info, or warning log
statement.

# Basic Usage

In `test.py`:

```python
def add(x, y):
    #! adding {x} and {y}
    return x + y
```

In `run.py`

```python
import logment
from test import add
logment.handler(logment.DEFAULT)

add(1, 2) # will warning about adding.
```

# Handler

A handler is a function with the signature `(frame, level, message)`.

+ `frame` : The current [stack frame](https://docs.python.org/3/library/inspect.html#inspect.currentframe).
+ `level` : A value representing the log level (either 1, 2, or 3 by default).
+ `message` : The text content of the comment.

Handlers can be added using `logment.handler`:

```python
@logment.handler
def printer(frame, level, message):
  name = frame.f_globals['__name__']
  level = ['DEBUG', 'INFO', 'WARNING'][level - 1]
  message = message.format(**frame.f_locals)
  print(f'{name}[{level}] {message}')
```

# Symbolic Levels

A mapping of symbols to levels can be found in `logment.SYMBOLS`.

```python
SYMBOLS = {'?': 1, ':': 2, '!': 3}
```

For now, directly add them (symbols containing spaces will never match).
