import os
import imp
import sys
import marshal
import logging
import inspect
from uuid import uuid1
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


def log(module, level, message):
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

        code = compile(self._augmented(text), self.filename, 'exec')

        with open(self._cache(module), 'wb+') as f:
            f.write(imp.get_magic())
            marshal.dump(code, f)

        exec(code, vars(module))

    def _augmented(self, text):
        unique = int(uuid1()) # prevent namespace clash
        form = "__log%s(__name__, {level}, f{message})" % unique
        rewrite = 'from logment import log as __log%s\n\n' % unique

        for line in text.split('\n'):
            indent, *comment = line.split('#', 1)
            if not indent.strip() and comment:
                symbol, message = comment[0].split(' ', 1)
                if symbol in _symbols:
                    index = len(line) - len(indent)
                    line = indent + form.format(
                        level=_symbols[symbol],
                        message=repr(message))
            rewrite += line + '\n'

        return rewrite

    def _cache(self, module):
        if hasattr(imp, "get_tag"):
            tag = imp.get_tag() + "-logment"
        else:
            if hasattr(sys, "pypy_version_info"):
                impl = "pypy"
            elif sys.platform == "java":
                impl = "jython"
            else:
                impl = "cpython"
            ver = sys.version_info
            tag = "%s-%s%s-logment" % (impl, ver[0], ver[1])
        ext = ".py" + (__debug__ and "c" or "o")
        tail = "." + tag + ext
        return os.path.join(
            os.path.dirname(self.filename),
            '__pycache__', module.__name__ + tail)


sys.meta_path.insert(0, _Finder())
