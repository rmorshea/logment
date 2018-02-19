import os
import sys
import logging
import inspect
from importlib.abc import MetaPathFinder, Loader
from importlib.util import spec_from_file_location


LOGGERS = []
SYMBOLS = {'?': 1, ':': 2, '!': 3}


def handler(function):
    LOGGERS.append(function)
    return function


def remove(function):
    LOGGERS.remove(function)


def DEFAULT(frame, level, message):
    logger = logging.getLogger(frame.f_globals.get('__name__'))
    message = message.format(**frame.f_locals)
    logger.log(level * 10, message)


def __log__(level, message):
    frame = inspect.currentframe().f_back
    for l in LOGGERS:
        l(frame, level, message)


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

        form = "__log__({level}, '{message}')"
        augmented = ['from logment import __log__', '']

        for line in text.split('\n'):
            stripped = line.lstrip()
            if stripped.startswith('#'):
                symbol, message = stripped[1:].split(' ', 1)
                if symbol in SYMBOLS:
                    index = len(line) - len(stripped)
                    line = line[:index] + form.format(
                        level=SYMBOLS[symbol],
                        message=message)
            augmented.append(line)

        augmented = '\n'.join(augmented)
        exec(augmented, vars(module))


sys.meta_path.insert(0, _Finder())
