# Logment

A library for Python 3 that logs augmented comments (logments).

A logment is an comment line of the form `#<symbol> <message>` where a known `symbol` corresponds to a log level.

| Symbol | Level | Name    | Example                   |
| ------ | ----- | ------- | ------------------------- |
| `?`    | 10    | DEBUG   | `#? my debug message`     |
| `:`    | 20    | INFO    | `#: my info message`      |
| `!`    | 30    | WARNING | `#! my warning message`   |
| `!!`   | 40    | ERROR   | `#!! my error message`    |
| `!!!`  | 50    | FAILURE | `#!!! my failure message` |

# The Basics

To use `logment` simply import it before the modules you'd like to augment:

```python
import logment
from test import add
logment.register()

add(1, 2) # logs a warning
```

In `test.py`:

```python
def add(x, y):
    #! adding {x} and {y}
    return x + y
```

# Register Handlers

A handler is a function with the signature `(module, level, message)`.

+ `module` : The name of the module where the message was logged.
+ `level` : A value representing the logging level (e.g. 10 is DEBUG).
+ `message` : The text content of the comment.

Handlers can be added using `logment.handler`:

```python
import logment
import logging


@logment.register
def printer(module, level, message):
  level = logging.getLevelName(level)
  print(f'{module}[{level}] {message}')
```

# Adding Symbolic Levels

Create a level with `logment.level(symbol, level, name)`.

```python
logment.level('$$$', 0, 'MONEY!')
```

Get the level and name for a symbol:

```python
level, name = logment.level('$$$')
```
