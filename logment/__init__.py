import os
import ast
import imp
import sys
import marshal
import inspect
from uuid import uuid1
from functools import wraps
from importlib.abc import MetaPathFinder, Loader
from importlib.util import spec_from_file_location
from contextlib import contextmanager


_loggers = []


def register(function):
    """Add a new logment handler."""
    if function not in _loggers:
        _loggers.append(function)
    return function


def remove(function):
    _loggers.remove(function)


def _log(state, context, message):
    for l in _loggers:
        l(state, context, message)


def _logged(function):
    sig = inspect.signature(function)
    context = function.__module__ + ':' + function.__name__
    if inspect.iscoroutinefunction(function):
        async def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            _log('started', context, dict(bound.arguments))
            try:
                result = await function(*args, **kwargs)
            except Exception as e:
                _log('failure', context, e)
                raise
            else:
                _log('success', context, result)
            return result
    elif inspect.isgeneratorfunction(function):
        def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            _log('started', context, dict(bound.arguments))
            try:
                yield from function(*args, **kwargs)
            except Exception as e:
                _log('failure', context, e)
                raise
            else:
                _log('success', context, result)
    else:
        def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            _log('started', context, dict(bound.arguments))
            try:
                result = function(*args, **kwargs)
            except Exception as e:
                _log('failure', context, e)
                raise
            else:
                _log('success', context, result)
            return result
    return wraps(function)(wrapper)


class _Finder(MetaPathFinder):

    def find_spec(self, fullname, path, target=None):
        if path in (None, ''):
            path = [os.getcwd()] # top level import
        if '.' in fullname:
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
        code = self._compile(module)
        with open(self._cache(module), 'wb+') as f:
            f.write(imp.get_magic())
            marshal.dump(code, f)
        exec(code, vars(module))

    def _compile(self, module):
        with open(self.filename) as f:
            aug = _Augmenter().parse(module, f.read())
            return compile(aug, self.filename, 'exec')

    def _cache(self, module):
        if hasattr(imp, 'get_tag'):
            tag = imp.get_tag() + '-logment'
        else:
            if hasattr(sys, 'pypy_version_info'):
                impl = 'pypy'
            elif sys.platform == 'java':
                impl = 'jython'
            else:
                impl = 'cpython'
            ver = sys.version_info
            tag = '%s-%s%s-logment' % (impl, ver[0], ver[1])
        ext = '.py' + (__debug__ and 'c' or 'o')
        tail = '.' + tag + ext
        return os.path.join(
            os.path.dirname(self.filename),
            '__pycache__', module.__name__ + tail)


class _Augmenter(ast.NodeTransformer):

    def __init__(self):
        self._contextualized = set()
        self._stack = []

    @contextmanager
    def stack(self, node):
        is_context = type(node) in (ast.FunctionDef, ast.ClassDef)
        if is_context:
            self._stack.append(node)
        yield
        if is_context:
            self._stack.pop()

    def parse(self, module, text):
        self._messages = []
        self._context = module.__name__
        self._marker = '_' + str(int(uuid1()))
        self._logment = '_logment_' + str(int(uuid1()))
        rewrite = 'import logment as ' + self._logment + '\n\n'
        for line in text.split('\n'):
            indent, *comment = line.split('#', 1)
            if not indent.strip() and comment:
                symbol, msg = comment[0].split(' ', 1)
                if symbol == ':':
                    self._messages.insert(0, msg)
                    line = indent + self._marker
            rewrite += line + '\n'
        tree = self.visit(ast.parse(rewrite))
        return ast.fix_missing_locations(tree)

    def visit(self, node):
        with self.stack(node):
            return super().visit(node)

    def visit_Expr(self, node):
        if node.value.id == self._marker:
            if self._stack:
                node.value = self._make_log_statement()
            else:
                return
        return node

    def _make_log_statement(self):
        if type(self._stack[-1]) is ast.FunctionDef:
            if self._stack[-1] not in self._contextualized:
                self._stack[-1].decorator_list.append(ast.Attribute(
                    ast.Name(self._logment, ast.Load()), '_logged', ast.Load()))
                self._contextualized.add(self._stack[-1])
        context = self._context
        if self._stack:
            context += ':' + '.'.join(n.name for n in self._stack)
        message = self._messages.pop()
        cmd = f'{self._logment}._log("working", "{context}", f"{message}")'
        return ast.parse(cmd, mode='eval').body


sys.meta_path.insert(0, _Finder())
