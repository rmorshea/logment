import os
import sys
import logging
import inspect
from importlib.abc import MetaPathFinder, Loader
from importlib.util import spec_from_file_location

LOGGERS = []


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

        augmented = ['from logment import __log__', '']
        for line in text.split('\n'):
            indent_strip = line.lstrip()
            if indent_strip.startswith('#'):
                comment_strip = indent_strip.lstrip('#')
                if comment_strip.startswith(":"):
                    level = len(indent_strip.split(':', 1)[0])
                    all_stripped = comment_strip[1:].lstrip()
                    index = len(line) - len(indent_strip)
                    message = '__log__(%s, %r)' % (level, all_stripped)
                    line = line[:index] + message
            augmented.append(line)

        augmented = '\n'.join(augmented)
        exec(augmented, vars(module))


sys.meta_path.insert(0, _Finder())
