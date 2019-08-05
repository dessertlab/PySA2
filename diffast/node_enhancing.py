import ast
from collections import Counter

import astunparse


class CounterCounter():

    def __init__(self):
        self.d = dict()

    def update(self, __m):
        for item in __m.items():
            self.d.update({
                item[0]: self.d.get(item[0], Counter()) + item[1]
            })

    def items(self):
        return self.d.items()

    def clear(self):
        self.d.clear()


class DescriptiveCounter():

    def __init__(self):
        self.c = Counter()
        self.d = dict()

    def _update_max_or_min(self, item):
        if item[0] not in self.d:
            self.d.update({
                item[0]: item[1]
            })
        else:
            fun = max if 'max' in item[0] else min
            self.d.update({
                item[0]: fun(item[1], self.d[item[0]]),
            })

    def update(self, __m, **kwargs):
        if __m.__class__.__name__ == 'DescriptiveCounter':
            self.c.update(__m.c)
            for item in __m.d.items():
                self._update_max_or_min(item)

        else:
            for item in __m.items():
                if 'sum' in item[0]:
                    self.c.update({
                        '_'.join([item[0]]): item[1]
                    })
                elif 'max' in item[0] or 'min' in item[0]:
                    self._update_max_or_min(item)
                else:
                    self.add_statistics_and_update({item[0]: item[1]})

    def add_statistics_and_update(self, __m):
        for item in __m.items():
            self.c.update({
                '_'.join([item[0], 'sum']): item[1]
            })
            if '_'.join([item[0], 'max']) not in self.d:
                self.d.update({
                    '_'.join([item[0], 'max']): item[1],
                    '_'.join([item[0], 'min']): item[1]
                })
            else:
                self.d.update({
                    '_'.join([item[0], 'max']): max(item[1], self.d['_'.join([item[0], 'max'])]),
                    '_'.join([item[0], 'min']): min(item[1], self.d['_'.join([item[0], 'min'])])
                })

    def items(self):
        return self.c.items() + self.d.items()

    def clear(self):
        self.c.clear()
        self.d.clear()

    def __getitem__(self, key):
        if key in self.c:
            return self.c[key]
        elif key in self.d:
            return self.d[key]
        else:
            raise KeyError(key + " not present in the DescriptiveCounter")


def _get_last_lineno(node, current_lineno=0, current_col_offset=-1):
    """
    Retrieve the lower boundaries of the node in term of lineno and col_offset
    (lower boundaries mean higher lineno and col_offset)

    :param node: the node
    :param current_lineno: the current lineno (used for recursion)
    :param current_col_offset: the current col_offset (user for recursion)
    :return: the last lineno and col_offset of the node
    """
    if hasattr(node, 'lineno'):
        current_lineno = max(current_lineno, node.lineno)
        current_col_offset = max(current_col_offset, node.col_offset)
    for field_name in node._fields:
        field = node.__getattribute__(field_name)
        if isinstance(field, list) and len(field) > 0 and isinstance(field[-1], ast.AST):
            return _get_last_lineno(field[-1], current_lineno, current_col_offset)
        elif isinstance(field, ast.AST):
            return _get_last_lineno(field, current_lineno, current_col_offset)
    return current_lineno, current_col_offset


def _enhance_node(node, role=u'ROOT', level=0, position=0, siblings_no=1, p_lineno=0, p_col_offset=0):
    # type: (ast.AST, str, int, int, int, int, int) -> None
    """
    Enhance an ast node (_ast.AST) and its descendants with other useful information

    :param node: the ast node to enhance
    :param role: the role of the node i.e., the field in the node's parent where the node is
    :param level:
    :param position:
    :param siblings_no: the number of siblings nodes (including the node itself)
    :param p_lineno: the lineno of the parent
    :param p_col_offset: the col_offset of the parent
    """
    node.role = role
    node.level = level
    node.position = position
    node.siblings_no = siblings_no

    # if the node has no lineno and col_offset,
    # it is in the same lineno and col_offset of the parent
    if not hasattr(node, 'lineno'):
        node.lineno = p_lineno
    if not hasattr(node, 'col_offset'):
        node.col_offset = p_col_offset

    node.last_lineno, node.last_col_offset = _get_last_lineno(node)
    node.semantic_id = _extract_semantic_id(node)

    _init_counters(node)

    for node_field_name in node._fields:
        field = node.__getattribute__(node_field_name)

        if isinstance(field, list):
            # _add_size_to_node_counter(node, node_field_name, len(field))
            i = 0
            for child in field:
                if isinstance(child, ast.AST):
                    child.parent = node
                    _enhance_node(child,
                                  role=node_field_name,
                                  level=level + 1,
                                  position=i,
                                  siblings_no=len(field),
                                  p_lineno=node.lineno,
                                  p_col_offset=node.col_offset)
                    _update_node_counters(child, node, node_field_name)
                i += 1

        elif isinstance(field, ast.AST):
            # _add_size_to_node_counter(node, node_field_name, 1)
            field.parent = node
            _enhance_node(field, role=node_field_name, level=level + 1, p_lineno=node.lineno,
                          p_col_offset=node.col_offset)
            _update_node_counters(field, node, node_field_name)


def _init_counters(node):
    # type: (ast.AST) -> None
    """
    Initialize all the counters used to describe the node (its features)
    :param node: the node
    """

    # node contents (fields) counter
    node.content_counter = Counter()

    # how many variable names in this node and its descendants?
    node.tokens = Counter()

    if isinstance(node, ast.Name):
        node.tokens.update([node.id])
    elif isinstance(node, ast.Attribute):
        node.tokens.update([node.attr])
    elif isinstance(node, ast.Str):
        node.tokens.update([node.s])
    elif isinstance(node, ast.Num):
        node.tokens.update([node.n])



# def _add_size_to_node_counter(node, node_field_name, size):
#     # type: (ast.AST, str, int) -> None
#     """
#     Add the size of a specific filed of a node
#     (invoked when enhancing the node and we started exploring a new field)
#
#     :param node: the node
#     :param node_field_name: the field of the name that has been considered
#     :param size: the size of the field (=1 if a single node, >= 1 if a list)
#     """
#
#     # it counts the size of the field of the node type
#     # e.g., for_body_size: 10
#     #       if_orelse_size: 0
#     node.content_counter.update({
#         '_'.join([node.__class__.__name__, node_field_name, 'size']): size
#     })


def _update_node_counters(child, node, node_field_name):
    """
    Update the counters of the node
    :param child: the child of the node
    :param node: the node
    :param node_field_name: the field of the node where the child is
    """

    # it counts the types of nodes in specific fields of the node
    # e.g., for_body_if: 1
    #       if_orelse_if: 1
    node.content_counter.update({
        '_'.join([node.__class__.__name__, node_field_name, child.__class__.__name__]): 1
    })

    node.tokens.update(child.tokens)

def _extract_semantic_id(node):
    """
    Extract the string that represent the semantic of the node (e.g., Str string,
    Name ids, FunctionDef names etc.)
    :param node: the node
    :return: the string
    """
    node_name = node.__class__.__name__

    if node_name in ['Str']:
        return node.s
    elif node_name in ['Name']:
        return node.id
    elif node_name in ['Call']:
        return astunparse.unparse(node.func).strip()
    elif node_name in ['keyword']:
        return node.arg
    elif node_name in ['Attribute']:
        return node.attr
    elif node_name in ['Assign']:
        return '_'.join([astunparse.unparse(x).strip() for x in node.targets])
    elif node_name in ['AugAssign']:
        return astunparse.unparse(node.target).strip()
    elif node_name in ['ImportFrom']:
        return node.module
    elif node_name in ['alias']:
        return node.name
    elif node_name in ['ClassDef', 'FunctionDef']:
        return node.name
    elif node_name in ['arguments']:
        r = []
        if node.vararg:
            r.append(node.vararg)
        if node.kwarg:
            r.append(node.kwarg)
        return '_'.join(r)
    elif node_name in ['Global', 'Nonlocal']:
        return '_'.join(node.names)

    return ''
