import ast, astunparse


def _print_node(node):
    str_builder = [node.role, u'=', u'[', str(node.position), u'/', str(node.siblings_no), u']']
    str_builder.extend([u'(', str(node.lineno), u':', str(node.col_offset),
                        u'~', str(node.last_lineno), u':', str(node.last_col_offset), u')'])
    str_builder.extend([node.__class__.__name__])
    if hasattr(node, 'semantic_id') and node.semantic_id:
        str_builder.append(u'*')
        str_builder.append(node.semantic_id[:20])
        if len(node.semantic_id) > 10:
            str_builder.append("...")
    return u''.join(str_builder)  # .encode('utf-8').strip()


def _print_context(node):
    context = [node.parent]

    n = node.parent
    while n.parent is not None:
        context.append(n.parent)
        n = n.parent

    return u', '.join([_print_node(x) for x in reversed(context)])


class _Chunk:

    def __init__(self, node):
        self.plus_nodes = []
        self.minus_nodes = []
        self.plus_lower_lineno = None
        self.plus_upper_lineno = None
        self.minus_lower_lineno = None
        self.minus_upper_lineno = None

        self.tag = node.diff_info

        if self.tag == 'insert':
            self.plus_nodes = [node]
            self.plus_lower_lineno = node.lineno
            self.plus_upper_lineno = node.last_lineno

        elif self.tag == 'delete':
            self.minus_nodes = [node]
            self.minus_lower_lineno = node.lineno
            self.minus_upper_lineno = node.last_lineno

        self.is_semantic_change = _is_semantic_change(self)

    def same_context(self, another):

        a_node = (self.plus_nodes + self.minus_nodes)[0].parent
        the_other_node = (another.plus_nodes + another.minus_nodes)[0].parent
        while a_node is not None and the_other_node is not None:
            if not _semantically_equal_nodes(a_node,
                                             the_other_node,
                                             self.is_semantic_change or another.is_semantic_change):
                return False
            a_node = a_node.parent
            the_other_node = the_other_node.parent

        return a_node == the_other_node

    def contains(self, another):

        if self.minus_nodes and another.minus_nodes:
            for a in self.minus_nodes:
                for b in another.minus_nodes:
                    _, minus_ancestor = _find_common_ancestor(a, b)
                    if minus_ancestor == a:
                        return True

        if self.plus_nodes and another.plus_nodes:
            for a in self.plus_nodes:
                for b in another.plus_nodes:
                    _, plus_ancestor = _find_common_ancestor(a, b)
                    if plus_ancestor == a:
                        return True

        return False

    def merge(self, another):
        if self.tag != another.tag:
            self.tag = 'modified'

        self.plus_nodes.extend(another.plus_nodes)
        if another.plus_nodes:
            self.plus_lower_lineno = min(
                [x for x in [self.plus_lower_lineno, another.plus_lower_lineno] if x is not None])
            self.plus_upper_lineno = max(self.plus_upper_lineno, another.plus_upper_lineno)

        self.minus_nodes.extend(another.minus_nodes)
        if another.minus_nodes:
            self.minus_lower_lineno = min(
                x for x in [self.minus_lower_lineno, another.minus_lower_lineno] if x is not None)
            self.minus_upper_lineno = max(self.minus_upper_lineno, another.minus_upper_lineno)

    def upgrade_and_merge(self, another):

        # print "u'n'm", self, another

        minus_ancestor = minus_ancestor_bis = None
        if self.minus_nodes and another.minus_nodes:
            minus_ancestor, minus_ancestor_bis = _find_common_ancestor(self.minus_nodes[0], another.minus_nodes[0])
            if minus_ancestor == minus_ancestor_bis:
                minus_ancestor_bis = None
        elif self.minus_nodes:
            minus_ancestor = self.minus_nodes[0]
        elif another.minus_nodes:
            minus_ancestor = another.minus_nodes[0]

        plus_ancestor = plus_ancestor_bis = None
        if self.plus_nodes and another.plus_nodes:
            plus_ancestor, plus_ancestor_bis = _find_common_ancestor(self.plus_nodes[0], another.plus_nodes[0])
            if plus_ancestor == plus_ancestor_bis:
                plus_ancestor_bis = None
        elif self.plus_nodes:
            plus_ancestor = self.plus_nodes[0]
        elif another.plus_nodes:
            plus_ancestor = another.plus_nodes[0]

        if minus_ancestor and plus_ancestor:
            plus_ancestor, minus_ancestor = _find_common_ancestor(plus_ancestor, minus_ancestor)
            minus_ancestor.diff_info = 'delete'
            plus_ancestor.diff_info = 'insert'
            self.__init__(minus_ancestor)
            self.merge(_Chunk(plus_ancestor))
        elif minus_ancestor:
            minus_ancestor.diff_info = 'delete'
            self.__init__(minus_ancestor)
        elif plus_ancestor:
            plus_ancestor.diff_info = 'insert'
            self.__init__(plus_ancestor)

        if minus_ancestor_bis:
            minus_ancestor_bis.diff_info = 'delete'
            self.merge(_Chunk(minus_ancestor_bis))
        if plus_ancestor_bis:
            plus_ancestor_bis.diff_info = 'insert'
            self.merge(_Chunk(plus_ancestor_bis))

        # print "in ", self

    def __repr__(self):
        if self.minus_nodes:
            str_builder = [_print_context(self.minus_nodes[0])]
        else:
            str_builder = [_print_context(self.plus_nodes[0])]

        str_builder.extend([u'\n\t -> { ', self.tag.upper(), '\n\t\t'])

        for i, node in enumerate(self.minus_nodes):
            str_builder.append(u'- ')
            str_builder.append(str(_print_node(node)))
            str_builder.append(u'; \n\t\t')

        for i, node in enumerate(self.plus_nodes):
            str_builder.append(u'+ ')
            str_builder.append(str(_print_node(node)))
            str_builder.append(u'; \n\t\t')

        str_builder.append(u'}')

        return u''.join(str_builder)  # .encode('utf-8').strip()


def _find_common_ancestor(a_node, another_node):
    """
    IT'S NOT A REALLY ANCESTOR! SEE THE CODE
    :param a_node:
    :param another_node:
    :return:
    """
    if a_node.level == another_node.level:
        if _semantically_equal_nodes(a_node.parent, another_node.parent) \
                and a_node.role == another_node.role:
            return a_node, another_node
        else:
            return _find_common_ancestor(a_node.parent, another_node.parent)
    elif a_node.level < another_node.level:
        return _find_common_ancestor(a_node, another_node.parent)
    elif a_node.level > another_node.level:
        return _find_common_ancestor(a_node.parent, another_node)


def _recursive_extraction(node):
    # print node.lineno, node.col_offset
    if node.diff_info in ['insert', 'delete']:
        return [_Chunk(node)]

    if node.diff_info == 'equal':
        return []

    chunks = []
    for field_name in node._fields:
        field = node.__getattribute__(field_name)

        if isinstance(field, list):
            for field_sibling in field:
                if isinstance(field_sibling, ast.AST):
                    chunks.extend(_recursive_extraction(field_sibling))

        elif isinstance(field, ast.AST):
            chunks.extend(_recursive_extraction(field))

    return chunks


def _reduce_consecutive_lines(chunks):
    chunks1 = sorted(chunks, key=lambda x: x.plus_lower_lineno)
    chunks2 = [x for x in chunks1 if x.plus_lower_lineno is None]
    considered_chunk = [x.plus_lower_lineno is None for x in chunks1]
    for i, i_chunk in enumerate(chunks1):
        if considered_chunk[i]:
            continue
        considered_chunk[i] = True
        for j, j_chunk in enumerate(chunks1[i + 1:], i + 1):
            if i_chunk.plus_upper_lineno + 1 == j_chunk.plus_lower_lineno \
                    or i_chunk.plus_upper_lineno == j_chunk.plus_lower_lineno:
                considered_chunk[j] = True
                i_chunk.upgrade_and_merge(j_chunk)
        chunks2.append(i_chunk)
    chunks2 = sorted(chunks2, key=lambda x: x.minus_lower_lineno)
    chunks3 = [x for x in chunks2 if x.minus_lower_lineno is None]
    considered_chunk = [x.minus_lower_lineno is None for x in chunks2]
    for i, i_chunk in enumerate(chunks2):
        if considered_chunk[i]:
            continue
        considered_chunk[i] = True
        for j, j_chunk in enumerate(chunks2[i + 1:], i + 1):
            if i_chunk.minus_upper_lineno + 1 == j_chunk.minus_lower_lineno \
                    or i_chunk.minus_upper_lineno == j_chunk.minus_lower_lineno:
                considered_chunk[j] = True
                i_chunk.upgrade_and_merge(j_chunk)
        chunks3.append(i_chunk)
    return chunks3


def _reduce_same_context_single(chunks):
    same_context_chunk = []
    considered_chunk = [False] * len(chunks)
    for i, i_chunk in enumerate(chunks):
        if considered_chunk[i]:
            continue
        considered_chunk[i] = True
        for j, j_chunk in enumerate(chunks[i + 1:], i + 1):
            if i_chunk.same_context(j_chunk):
                considered_chunk[j] = True
                i_chunk.merge(j_chunk)
        same_context_chunk.append(i_chunk)

    return same_context_chunk


def _reduce_included(chunks):
    whole_chunks = chunks
    considered_chunk = [False] * len(chunks)
    for i, i_chunk in enumerate(chunks):
        if considered_chunk[i]:
            continue
        considered_chunk[i] = True
        for j, j_chunk in enumerate(chunks[i + 1:], i + 1):
            if i_chunk.contains(j_chunk):
                considered_chunk[j] = True
                whole_chunks.remove(j_chunk)
    return whole_chunks


def _reduce_same_context_and_node(chunks):
    same_context_chunk = [x for x in chunks if x.tag == 'modified']
    considered_chunk = [x.tag == 'modified' for x in chunks]
    for i, i_chunk in enumerate(chunks):
        if considered_chunk[i]:
            continue
        considered_chunk[i] = True
        # if i_chunk.tag == 'modified':
        #     continue
        for j, j_chunk in enumerate(chunks[i + 1:], i + 1):
            if ((i_chunk.tag == 'insert' and j_chunk.tag == 'delete')
                    or (i_chunk.tag == 'delete' and j_chunk.tag == 'insert')) \
                and len(i_chunk.plus_nodes) == 1 \
                and len(j_chunk.minus_nodes) == 1 \
                and _semantically_equal_nodes(i_chunk.plus_nodes[0], j_chunk.minus_nodes[0],
                                              i_chunk.is_semantic_change or j_chunk.is_semantic_change):
                considered_chunk[j] = True
                i_chunk.merge(j_chunk)
                break
        same_context_chunk.append(i_chunk)
    return same_context_chunk


def _semantically_equal_nodes(node, another, is_semantic_change=False):
    return node.__class__.__name__ == another.__class__.__name__ \
           and node.role == another.role \
           and node.level == another.level \
           and (is_semantic_change or node.semantic_id == another.semantic_id)

def _is_semantic_change(chunk):
    """
    Return true if the chunk contains a change of the semantic of the context.
    (check node_enhancing._extract_semantic_id)

    :param node:
    :return:
    """
    roles = [x.role for x in (chunk.plus_nodes + chunk.minus_nodes)]
    for role in roles:
        if role in ['func', 'arg', 'attr', 'targets', 'target', 'name', 'vararg', 'kwarg']:
            return True
    return False

def _extract_chunks(diff_ast):
    # every chunk is a insert|delete node
    chunks = []
    chunks.extend(_recursive_extraction(diff_ast.before))
    chunks.extend(_recursive_extraction(diff_ast.after))

    len_chunk = len(chunks)
    while True:
        chunks = _reduce_same_context_single(chunks)
        chunks = _reduce_consecutive_lines(chunks)
        if len(chunks) == len_chunk:
            break
        len_chunk = len(chunks)

    chunks = _reduce_same_context_and_node(chunks)

    chunks = _reduce_included(chunks)

    return chunks
