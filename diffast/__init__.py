import ast
import copy
import difflib

from diffast.node_enhancing import _enhance_node
from .ast2html import _diff_ast_view
from .chunk_context import _extract_chunks


def _cn(obj):
    return obj.__class__.__name__


def _node_similarity(node1, node2):
    d = difflib.SequenceMatcher(None, ast.dump(node1), ast.dump(node2))
    return d.ratio()


class _AstDiffer:

    def __init__(self):
        pass

    def _diff_node(self, a, b):

        tag = 'equal'

        if _cn(a) != _cn(b):
            if _cn(a) == 'NoneType':
                b.diff_info = 'insert'
                return True
            elif _cn(b) == 'NoneType':
                a.diff_info = 'delete'
                return True
            tag = 'modified'

        elif _cn(b) == 'NoneType':
            return False

        elif _cn(b) == 'Num':
            if a.n != b.n:
                tag = 'modified'

        elif _cn(b) == 'Str':
            if a.s != b.s:
                tag = 'modified'

        elif _cn(b) == 'List' or _cn(b) == 'Tuple':
            if self._diff_list(a.elts, b.elts):
                tag = 'update'
            if self._diff_node(a.ctx, b.ctx):
                tag = 'update'

        elif _cn(b) == 'Set':
            if self._diff_list(a.elts, b.elts):
                tag = 'update'

        elif _cn(b) == 'Dict':
            if self._diff_list(a.keys, b.keys):
                tag = 'update'
            if self._diff_list(a.values, b.values):
                tag = 'update'

        elif _cn(b) == 'Name':
            if self._diff_node(a.ctx, b.ctx):
                tag = 'update'
            if a.id != b.id:
                tag = 'modified'

        elif _cn(b) == 'Starred' or _cn(b) == 'Expr':
            if self._diff_node(a.value, b.value):
                tag = 'update'

        elif _cn(b) == 'UnaryOp':
            if self._diff_node(a.op, b.op):
                tag = 'update'
            if self._diff_node(a.operand, b.operand):
                tag = 'update'

        elif _cn(b) == 'BinOp':
            if self._diff_node(a.left, b.left):
                tag = 'update'
            if self._diff_node(a.op, b.op):
                tag = 'update'
            if self._diff_node(a.right, b.right):
                tag = 'update'

        elif _cn(b) == 'BoolOp':
            if self._diff_node(a.op, b.op):
                tag = 'update'
            if self._diff_list(a.values, b.values):
                tag = 'update'

        elif _cn(b) == 'Compare':
            if self._diff_node(a.left, b.left):
                tag = 'update'
            if self._diff_list(a.ops, b.ops):
                tag = 'update'
            if self._diff_list(a.comparators, b.comparators):
                tag = 'update'

        elif _cn(b) == 'Call':
            if self._diff_node(a.func, b.func):
                tag = 'update'
            if self._diff_list(a.args, b.args):
                tag = 'update' if tag != 'update' else 'modified'
            if self._diff_list(a.keywords, b.keywords):
                tag = 'update' if tag != 'update' else 'modified'
            if self._diff_node(a.starargs, b.starargs):
                tag = 'update' if tag != 'update' else 'modified'
            if self._diff_node(a.kwargs, b.kwargs):
                tag = 'update' if tag != 'update' else 'modified'

        elif _cn(b) == 'keyword':
            if self._diff_node(a.value, b.value):
                tag = 'update'
            if a.arg != b.arg:
                tag = 'modified'

        elif _cn(b) == 'IfExp':
            if self._diff_node(a.test, b.test):
                tag = 'update'
            if self._diff_node(a.body, b.body):
                tag = 'update'
            if self._diff_node(a.orelse, b.orelse):
                tag = 'update'

        elif _cn(b) == 'Attribute':
            if self._diff_node(a.value, b.value):
                tag = 'update'
            if self._diff_node(a.ctx, b.ctx):
                tag = 'update'
            if a.attr != b.attr:
                tag = 'modified'

        elif _cn(b) == 'Subscript':
            if self._diff_node(a.value, b.value):
                tag = 'update'
            if self._diff_node(a.slice, b.slice):
                tag = 'update'
            if self._diff_node(a.ctx, b.ctx):
                tag = 'update'

        elif _cn(b) == 'Index':
            if self._diff_node(a.value, b.value):
                tag = 'update'

        elif _cn(b) == 'Slice':
            if self._diff_node(a.lower, b.lower):
                tag = 'update'
            if self._diff_node(a.upper, b.upper):
                tag = 'update'
            if self._diff_node(a.step, b.step):
                tag = 'update'

        elif _cn(b) == 'ExtSlice':
            if self._diff_list(a.dims, b.dims):
                tag = 'update'

        elif _cn(b) == 'ListComp' or _cn(b) == 'SetComp' or _cn(b) == 'GeneratorExp':
            if self._diff_node(a.elt, b.elt):
                tag = 'update'
            if self._diff_list(a.generators, b.generators):
                tag = 'update'

        elif _cn(b) == 'DictComp':
            if self._diff_node(a.key, b.key):
                tag = 'update'
            if self._diff_node(a.value, b.value):
                tag = 'update'
            if self._diff_list(a.generators, b.generators):
                tag = 'update'

        elif _cn(b) == 'comprehension':
            if self._diff_node(a.target, b.target):
                tag = 'update'
            if self._diff_node(a.iter, b.iter):
                tag = 'update'
            if self._diff_list(a.ifs, b.ifs):
                tag = 'update'

        elif _cn(b) == 'Assign':
            if self._diff_list(a.targets, b.targets):
                tag = 'update'
            if self._diff_node(a.value, b.value):
                tag = 'update'

        elif _cn(b) == 'AugAssign':
            if self._diff_node(a.target, b.target):
                tag = 'update'
            if self._diff_node(a.op, b.op):
                tag = 'update'
            if self._diff_node(a.value, b.value):
                tag = 'update'

        elif _cn(b) == 'Print':
            if self._diff_node(a.dest, b.dest):
                tag = 'update'
            if self._diff_list(a.values, b.values):
                tag = 'update'
            if a.nl != b.nl:
                tag = 'modified'

        elif _cn(b) == 'Raise':
            if self._diff_node(a.type, b.type):
                tag = 'update'
            if self._diff_node(a.inst, b.inst):
                tag = 'update'
            if self._diff_node(a.tback, b.tback):
                tag = 'update'

        elif _cn(b) == 'Assert':
            if self._diff_node(a.test, b.test):
                tag = 'update'
            if self._diff_node(a.msg, b.msg):
                tag = 'update'

        elif _cn(b) == 'Delete':
            if self._diff_list(a.targets, b.targets):
                tag = 'update'

        elif _cn(b) == 'Import':
            if self._diff_list(a.names, b.names):
                tag = 'update'

        elif _cn(b) == 'ImportFrom':
            if self._diff_list(a.names, b.names):
                tag = 'update'
            if a.module != b.module:
                tag = 'modified'
            if a.level != b.level:
                tag = 'modified'

        elif _cn(b) == 'alias':
            if a.name != b.name:
                tag = 'modified'
            if a.asname != b.asname:
                tag = 'modified'

        elif _cn(b) == 'If':
            if self._diff_node(a.test, b.test):
                tag = 'update'
            if self._diff_list(a.body, b.body):
                tag = 'update'
            if self._diff_list(a.orelse, b.orelse):
                tag = 'update'

        elif _cn(b) == 'For':
            if self._diff_node(a.target, b.target):
                tag = 'update'
            if self._diff_node(a.iter, b.iter):
                tag = 'update'
            if self._diff_list(a.body, b.body):
                tag = 'update'
            if self._diff_list(a.orelse, b.orelse):
                tag = 'update'

        elif _cn(b) == 'While':
            if self._diff_node(a.test, b.test):
                tag = 'update'
            if self._diff_list(a.body, b.body):
                tag = 'update'
            if self._diff_list(a.orelse, b.orelse):
                tag = 'update'

        elif _cn(b) == 'Try':
            if self._diff_list(a.body, b.body):
                tag = 'update'
            if self._diff_list(a.handlers, b.handlers):
                tag = 'update'
            if self._diff_list(a.orelse, b.orelse):
                tag = 'update'
            if self._diff_list(a.finalbody, b.finalbody):
                tag = 'update'

        elif _cn(b) == 'TryFinally':
            if self._diff_list(a.body, b.body):
                tag = 'update'
            if self._diff_list(a.finalbody, b.finalbody):
                tag = 'update'

        elif _cn(b) == 'TryExcept':
            if self._diff_list(a.body, b.body):
                tag = 'update'
            if self._diff_list(a.handlers, b.handlers):
                tag = 'update'
            if self._diff_list(a.orelse, b.orelse):
                tag = 'update'

        elif _cn(b) == 'ExceptHandler':
            if self._diff_node(a.type, b.type):
                tag = 'update'
            if self._diff_list(a.body, b.body):
                tag = 'update'
            if a.name != b.name:
                tag = 'modified'

        elif _cn(b) == 'With':
            if self._diff_node(a.context_expr, b.context_expr):
                tag = 'update'
            if self._diff_node(a.optional_vars, b.optional_vars):
                tag = 'update'
            if self._diff_list(a.body, b.body):
                tag = 'update'

        elif _cn(b) == 'FunctionDef':
            if self._diff_node(a.args, b.args):
                tag = 'update'
            if self._diff_list(a.body, b.body):
                tag = 'update'
            if self._diff_list(a.decorator_list, b.decorator_list):
                tag = 'update'
            if a.name != b.name:
                tag = 'modified'

        elif _cn(b) == 'Lambda':
            if self._diff_node(a.args, b.args):
                tag = 'update'
            if self._diff_node(a.body, b.body):
                tag = 'update'

        elif _cn(b) == 'arguments':
            if self._diff_list(a.args, b.args):
                tag = 'update'
            if self._diff_list(a.defaults, b.defaults):
                tag = 'update'
            if a.vararg != b.vararg:
                tag = 'modified'
            if a.kwarg != b.kwarg:
                tag = 'modified'

        elif _cn(b) == 'Return' or _cn(b) == 'Yield':
            if self._diff_node(a.value, b.value):
                tag = 'update'

        elif _cn(b) == 'Global' or _cn(b) == 'NonLocal':
            if a.names != b.names:
                tag = 'modified'

        elif _cn(b) == 'ClassDef':
            if self._diff_list(a.bases, b.bases):
                tag = 'update'
            if self._diff_list(a.body, b.body):
                tag = 'update'
            if self._diff_list(a.decorator_list, b.decorator_list):
                tag = 'update'
            if a.name != b.name:
                tag = 'modified'

        a.diff_info = b.diff_info = tag
        if tag == 'modified':
            a.diff_info = 'delete'
            b.diff_info = 'insert'

        return tag != 'equal'  # has_difference

    def _diff_list(self, a, b):

        if _cn(a) != _cn(b) or _cn(a) != 'list':
            raise Exception("_diff_list fun accepts only lists")

        dumped_a = [ast.dump(x) for x in a]
        dumped_b = [ast.dump(x) for x in b]

        s = difflib.SequenceMatcher(None, dumped_a, dumped_b)

        has_differences = False

        for tag, i1, i2, j1, j2 in s.get_opcodes():
            #print ("%7s a[%d:%d] (%s) b[%d:%d] (%s)" % (tag, i1, i2, dumped_a[i1:i2], j1, j2, dumped_b[j1:j2]))
            if 'replace' in tag:
                has_differences = True

                if (i2 - i1) == (j2 - j1):
                    for k in range(i2 - i1):
                        self._diff_node(a[i1 + k], b[j1 + k])

                else:
                    for a_node in a[i1:i2]:
                        a_node.diff_info = 'delete'
                    for b_node in b[j1:j2]:
                        b_node.diff_info = 'insert'

                    # la massimima similarita' iniziale e' 0.5, quindi
                    # inizializziamo a 0.4 perche' si richiede di superare
                    # la similarita' di almeno 0.1
                    a_max_similarity = [0.4] * (i2 - i1)
                    b_max_similarity = [0.4] * (j2 - j1)
                    for j, b_node in enumerate(b[j1:j2]):
                        for i, a_node in enumerate(a[i1:i2]):
                            similarity = _node_similarity(a_node, b_node)
                            # print a_node, b_node, similarity
                            if similarity > a_max_similarity[i] + 0.1 and similarity > b_max_similarity[j] + 0.1:
                                a_max_similarity[i] = b_max_similarity[j] = similarity
                                self._diff_node(a_node, b_node)

            elif 'delete' in tag:
                has_differences = True
                for node in a[i1:i2]:
                    node.diff_info = tag

            elif 'insert' in tag:
                has_differences = True
                for node in b[j1:j2]:
                    node.diff_info = tag

            elif 'equal' in tag:
                for node in a[i1:i2]:
                    node.diff_info = tag
                for node in b[j1:j2]:
                    node.diff_info = tag

            else:
                raise Exception("We have an unexpected tag %s" % tag)

        return has_differences

    def diff(self, before_ast, after_ast):
        if _cn(before_ast) != _cn(after_ast) or 'Module' not in _cn(before_ast):
            raise Exception("only diff between module are admitted")

        before_ast.parent = None
        _enhance_node(before_ast)
        after_ast.parent = None
        _enhance_node(after_ast)

        before_ast.diff_info = 'update'
        after_ast.diff_info = 'update'
        self._diff_list(before_ast.body, after_ast.body)

        diff_ast = type('diff_ast', (), {})()
        diff_ast.before = before_ast
        diff_ast.after = after_ast

        return diff_ast


def diff(before_ast, after_ast):
    return _AstDiffer().diff(copy.deepcopy(before_ast), copy.deepcopy(after_ast))


def extract_chunks(diff_ast):
    if _cn(diff_ast) != 'diff_ast':
        raise Exception("extract_contexts work only with diff_ast")
    return _extract_chunks(diff_ast)


def diff2html(diff_ast, filename='diff_tree.html'):
    if _cn(diff_ast) != 'diff_ast':
        raise Exception("diff2html work only with diff_ast")

    with open(filename, "w") as f:
        f.write(_diff_ast_view(diff_ast))
