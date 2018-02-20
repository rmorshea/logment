import os
import sys
import logging
import inspect
from importlib.abc import MetaPathFinder, Loader
from importlib.util import spec_from_file_location


_loggers = []
_symbols = {
    '?': 10,
    ':': 20,
    '!': 30,
    '!!': 40,
    '!!!': 50,
}


def DEFAULT(module, level, message):
    logger = logging.getLogger(module)
    logger.log(level, message)


def register(function=DEFAULT):
    """Add a new logment handler."""
    if function not in _loggers:
        _loggers.append(function)
    return function


def remove(function):
    _loggers.remove(function)


def level(symbol, level=None, name=None):
    if name is None and level is None:
        level = _symbols[symbol]
        name = logging.getLevelName(level)
        return level, name
    else:
        if ' ' in symbol:
            raise ValueError("Level symbols cannot contain spaces.")
        _symbols[symbol] = level
        logging.addLevelName(level, name)


def __log__(module, level, message):
    for function in _loggers:
        function(module, level, message)


class _Finder(MetaPathFinder):

    def find_spec(self, fullname, path, target=None):
        if path in (None, ''):
            path = [os.getcwd()] # top level import
        if "." in fullname:
            parents, name = fullname.rsplit('.', 1)
        else:
            name = fullname
        for entry in path:
            if os.path.isdir(os.path.join(entry, name)):
                # this module has child modules
                filename = os.path.join(entry, name, '__init__.py')
                submodule_locations = [os.path.join(entry, name)]
            else:
                filename = os.path.join(entry, name + '.py')
                submodule_locations = None

            if not os.path.exists(filename):
                continue

            return spec_from_file_location(
                fullname, filename, loader=_Loader(filename),
                submodule_search_locations=submodule_locations)

        # we don't know how to import this
        return None


class _Loader(Loader):

    def __init__(self, filename):
        self.filename = filename

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        with open(self.filename) as f:
            text = f.read()

        augmented = ['from logment import __log__', '']
        form = "__log__(__name__, {level}, f{message})"

        for line in text.split('\n'):
            indent, *comment = line.split('#', 1)
            if not indent.strip() and comment:
                symbol, message = comment[0].split(' ', 1)
                if symbol in _symbols:
                    index = len(line) - len(indent)
                    line = indent + form.format(
                        level=_symbols[symbol],
                        message=repr(message))
            augmented.append(line)

        augmented = '\n'.join(augmented)
        exec(augmented, vars(module))


sys.meta_path.insert(0, _Finder())
