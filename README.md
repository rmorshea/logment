# Logment

```bash
pip install logment
```

A library for Python 3 that logs augmented comments (logments).

A logment is a comment inside a function that takes the form `#: <message>`.

# The Basics

To use `logment` simply import it before the modules you'd like to augment:

```python
import logment
from test import add
logment.register(print)

add(1, 2)
```

Inside `test.add` we warn using a comment that starts with `:` - it can references variables via [f-string](https://www.python.org/dev/peps/pep-0498/) syntax.

```python
def add(x, y):
    #: adding {x} and {y}
    return x + y
```

Now we automagically get printed messages that look like this:

```
started test:add {'x': 1, 'y': 2}
working test:add adding 1 and 2
success test:add 3
```

# Register Handlers

A handler is a function with the signature `(state, context, message)`.

+ `state` : A string that is either `started`, `working`, `success`, `failure`
+ `context` : The name of the current module and, if present, function being called.
+ `message` : Depending on the `state` the values are:
  1. `started` : a dictionary of arguments passed to the function
  2. `working` : the formatted text of a logment.
  3. `success` : the value returned by the context function.
  4. `failure` : the error that is about to be raised by the function.

Handlers can be added using `logment.register`:

```python
import logment


@logment.register
def formater(state, context, message):
    print(f'{context}[{state.upper()}] {message}')
```
