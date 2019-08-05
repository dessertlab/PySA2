"""
Modified from the work of Eduardo Naufel Schettino: pyRegurgitator
https://github.com/schettino72/pyRegurgitator/
"""

import platform
import os
import ast
import json

from pkg_resources import resource_filename
import jinja2


class _AstField(object):
    """There are 3 basic kinds of AST fields
     * TypeField - contains a basic type (not an AST node/element)
     * NodeField - contains a single AST element
     * ListField - contains a list of AST elements
    """


class _TypeField(_AstField):
    def __init__(self, value, path, lines):
        self.value = value
        self.path = path

    def to_text(self):
        return repr(self.value)

    def to_map(self):
        return ["%s => %s" % (self.path, repr(self.value))]

    def to_html(self):
        if isinstance(self.value, str):
            #TODO escape HTML from docstrings
            str_value = repr(self.value.replace('\n', '\n<br/>'))
        else:
            str_value = repr(self.value)
        return '<span class="final">%s</span>' % str_value


class _NodeField(_AstField):
    def __init__(self, value, path, lines, parent):
        self.value = parent.__class__(value, path, lines, parent)
        self.path = path

    def to_text(self):
        return self.value.to_text()

    def to_map(self):
        ll = ["%s (%s)" % (self.path, self.value.node.__class__.__name__)]
        ll.extend(self.value.to_map())
        return ll

    def to_html(self):
        return self.value.to_html()


class _ListField(_AstField):
    def __init__(self, value, path, lines, parent):
        self.value = []
        for i,n in enumerate(value):
            path = "%s[%d]" % (path,i)
            if isinstance(n , ast.AST):
                node = parent.__class__(n, path, lines, parent)
                self.value.append(node)
            else:
                self.value.append(_TypeField(n, path, lines))
        self.path = path

    def to_text(self):
        return "[%s]" % ", ".join((n.to_text() for n in self.value))

    def to_map(self):
        ll = ["%s []" % self.path]
        for n in self.value:
            ll.append("%s (%s)" % (n.path, n.node.__class__.__name__))
            ll.extend(n.to_map())
        return ll

    def to_html(self):
        t_head = '<table class="field_list">'
        row = "<tr><td>%s</td></tr>"
        t_body = "".join(row % n.to_html() for n in self.value)
        t_foot = '</table>'
        return t_head + t_body + t_foot


class _AstNode(object):
    """friendly AST class

    @ivar node: stdlib AST node
    @ivar path: python variable's "path" to this node
    @ivar lines: node location on file
    @ivar class_: AST type
    @ivar attrs: list of tuple (name, value) of all attributes
    @ivar fields: dict of AstField
    """

    # this values are injected by ast2html
    node_template = None
    MAP = None

    @classmethod
    def tree(cls, tree):
        cls.line_list = []
        return cls(tree, '', [], None)

    @classmethod
    def load_map(cls):
        """load type map/info from json file"""
        # load ASDL based on python version
        py_version = platform.python_version_tuple()
        json_name = 'python{}{}.asdl.json'.format(*py_version[:2])
        asdl_json_file = resource_filename('diffast',
                                           os.path.join('asdl', json_name))
        with open(asdl_json_file) as fp:
            cls.MAP = json.load(fp)


    def __init__(self, node, path, lines, parent):
        self.node = node
        self.path = path
        self.lines = lines
        self.parent = parent
        self.class_ = node.__class__.__name__
        self.line_nums = set()
        self.diff_info = node.diff_info if hasattr(node, 'diff_info') else ''
        self.diff_info_class = node.diff_info + "_css_class" if hasattr(node, 'diff_info') else ''

        # normalize values when using python2.5
        # on python2.5 node might not have _attributes, ...
        if not hasattr(node, '_attributes'):
            node._attributes = []
        # ... _fields is None instead of []
        if node._fields is None:
            node._fields = []
        # end - python2.5

        # set fields / create sub-nodes
        self.attrs = [(name, getattr(node, name)) for name in node._attributes]
        if self.attrs:
            self.line = self.attrs[0][1]
            self.column = self.attrs[1][1]
        self.fields = {}
        for name in node._fields: # _fields is a tuple of str
            value = getattr(node, name)
            f_path = "%s.%s" % (self.path, name)
            if isinstance(value, ast.AST):
                self.fields[name] = _NodeField(value, f_path, lines, self)
            elif isinstance(value, list):
                self.fields[name] = _ListField(value, f_path, lines, self)
            else:
                self.fields[name] = _TypeField(value, f_path, lines)

    def __repr__(self):
        return '{}(path={}, node={}, attrs={})'.format(
            self.__class__.__name__, self.path, self.node.__class__, self.attrs)

    def to_html(self):
        """return HTML string for node
          - set line_nums of node
        """
        class_info = self.MAP[self.class_]
        category = class_info['category']

        # add line number of this node to the contatining statement
        if self.attrs:
            curent = self
            while True:
                if self.MAP[curent.class_]['category'] != "stmt":
                    if curent.parent:
                        curent = curent.parent
                        continue
                    else:
                        break
                else:
                    curent.line_nums.add(self.attrs[0][1])
                    break

        attrs = [v for k,v in self.attrs]
        return self.node_template.module.node(self, class_info, category, attrs)


    def to_text(self):
        """dumps node info in plain text
        @returns string
        """
        attrs = ["%s=%s" % (k, v) for k,v in self.attrs]
        fields = ["%s=%s" % (k, v.to_text()) for k,v in
                  sorted(self.fields.items())]
        return "%s(%s)" % (self.class_, ", ".join(attrs + fields))

    def to_map(self):
        items = []
        for name, value in sorted(self.fields.items()):
            items.extend(value.to_map())
        return items


def _astdiff2html(before_tree, after_tree):
    """pretty print ast in HTML"""
    jinja_env = jinja2.Environment(
        loader=jinja2.PackageLoader('diffast', 'templates'),
        undefined=jinja2.StrictUndefined,
        trim_blocks=True)
    template = jinja_env.get_template("ast.html")

    # inject some global variables into AstNode class
    _AstNode.node_template = jinja_env.get_template("ast_node.html")
    _AstNode.load_map()

    # ready to generate the HTML
    return template.render(before_tree=before_tree, after_tree=after_tree)


def _diff_ast_view(ast_diff, format='html'):

    before_tree = _AstNode.tree(ast_diff.before)
    after_tree = _AstNode.tree(ast_diff.after)

    if format == 'html':
        html = _astdiff2html(before_tree, after_tree)
        return html
    elif format == 'map':
        return before_tree.to_map(), after_tree.to_map()
    elif format == 'txt':
        return before_tree.to_text(), after_tree.to_text()
