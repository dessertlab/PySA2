import ast

from tokens_extraction import extract_tokens
from collections import Counter

NODE_TYPE_VALUE = 1000
NODE_CONTENT_RATIO = 0.1
CONTENT_TYPE_VALUE = NODE_TYPE_VALUE * NODE_CONTENT_RATIO

NODE_CHILD_RATIO = 0.1


def _extract_from_context(chunk):
    d = dict()
    strings = []

    if chunk.minus_nodes:
        n = chunk.minus_nodes[0].parent
    else:
        n = chunk.plus_nodes[0].parent

    level = 0

    closest_found=False
    closest_potential_nodes = ['Assign', 'Return', 'Call', 'If', 'While', 'For', 'TryExcept', 'TryFinally', 'FunctionDef', 'ClassDef', 'Module']

    while n is not None:
        alpha = NODE_CONTENT_RATIO**level

        if not strings and n.__class__.__name__ in ['FunctionDef', 'ClassDef', 'Module']:
            d.update(Counter(
                extract_tokens(
                    [str(x) for item in n.tokens.items() for x in [item[0]] * item[1]]
                )
            ))

        d.update({
            '_'.join(['ctx', n.__class__.__name__]): NODE_TYPE_VALUE * alpha
        })

        for item in n.content_counter.items():
            role = item[0].rsplit('_', 1)[0]
            value = (item[1] * alpha * CONTENT_TYPE_VALUE) + d.get(role, 0)
            d.update({
                '_'.join(['ctx', role]): value
            })

        # check for the closest node
        if not closest_found:
            if not strings and n.__class__.__name__ in closest_potential_nodes:

                closest_size = 0
                closest_ops_size = dict()
                ops = ["BinOp", "BoolOp", "Attribute", "Subscript"]
                for node_field_name in n._fields:
                    field = n.__getattribute__(node_field_name)
                    if isinstance(field, list):
                        closest_size = closest_size + len(field)
                    elif isinstance(field, ast.AST):
                        closest_size = closest_size + 1
                        if field.__class__.__name__ in ops:
                            closest_ops_size[field.__class__.__name__] = closest_ops_size.get(field.__class__.__name__, 0) +1

                d.update({
                    '_'.join(['new_ctx', 'closest', n.__class__.__name__]): 1 ,
                    '_'.join(['new_ctx', 'closest', 'size']) : closest_size
                })
                for k,v in closest_ops_size.items():
                    d.update({
                        '_'.join(['new_ctx', 'closest', k, 'count']): v
                    })

                if n.__class__.__name__ == 'Call':
                    d.update({
                        '_'.join(['new_ctx_closest_Call', 'args_count']): len(n.args),
                        '_'.join(['new_ctx_closest_Call', 'keywords_count']): len(n.keywords)
                    })

                closest_found = True

        #check function def for internal use only
        if not strings and n.__class__.__name__ in ['FunctionDef']:
            if n.name.startswith('_'):
                d.update({
                    'new_ctx_FunctionDef_internal' : 1
                })

        #count function def into the context class and module
        if not strings and n.__class__.__name__ in ['ClassDef', 'Module']:
            function_def_children = 0
            for child in n.body:
                if isinstance(child, ast.FunctionDef):
                    function_def_children = function_def_children + 1
            d.update({
                '_'.join(['new_ctx', n.__class__.__name__ ,'body_size_only_fun']) : function_def_children
            })

        # go to the parent node
        n = n.parent
        level = level+1

    return d


def _extract_from_node(node, prefix, alpha=1):
    # type: (ast.AST, str, float) -> object
    """
    Extract the counter from the node with the features
    :param node: the node
    :param prefix: 'add' or 'rem'
    :param alpha: the weight of the features
    :return: the feature counter
    """
    c = Counter()

    # the ast type of the node e.g., add_if : 1000
    c.update({
        '_'.join([prefix, node.__class__.__name__]): NODE_TYPE_VALUE * alpha
    })

    # for counting the globals and expressions
    if node.__class__.__name__ in ["Global", "Expr", "BinOp", "BoolOp", "Attribute", "Subscript"]:
        c.update({
            '_'.join(["aggr", prefix, node.__class__.__name__, "count"]): 1
        })

    if node.__class__.__name__ in ["Expr", "Assign", "AnnAssign", "AugAssign", "Print", "Raise", "Assert", "Delete", "Delete", "Pass"]:
        c.update({
            '_'.join(["aggr", prefix, "expressions_count"]): 1
        })


    # the contents of the node e.g., add_if_body_assign : 100
    for item in node.content_counter.items():
        c.update({
            '_'.join([prefix, item[0]]): item[1] * alpha * CONTENT_TYPE_VALUE
        })
        role = item[0].rsplit('_', 1)[0]
        c.update({
            '_'.join(["aggr", prefix, role, "count"]): 1
        })


    # the children of the node
    for node_field_name in node._fields:
        field = node.__getattribute__(node_field_name)
        if isinstance(field, list):
            for child in field:
                if isinstance(child, ast.AST):
                    c.update(_extract_from_node(child, prefix, alpha * NODE_CONTENT_RATIO))

        elif isinstance(field, ast.AST):
            c.update(_extract_from_node(field, prefix, alpha * NODE_CONTENT_RATIO))

    return c


def extract_features(chunk):
    d = dict()

    #######
    # context
    #######
    d.update(_extract_from_context(chunk))

    #######
    # nodes
    #######
    tmp_c = Counter()

    if chunk.minus_nodes:
        for node in chunk.minus_nodes:
            tmp_c.update(_extract_from_node(node, 'rem'))
        tmp_c.update({"aggr_rem_node_count":len(chunk.minus_nodes)})
    if chunk.plus_nodes:
        for node in chunk.plus_nodes:
            tmp_c.update(_extract_from_node(node, 'add'))
        tmp_c.update({"aggr_add_node_count":len(chunk.plus_nodes)})


    d.update(tmp_c.items())

    # syntetic features
    if 'ctx_FunctionDef_body' in d:
        d.update({
            'new_ctx_FunctionDef_body_size' : (d['ctx_FunctionDef_body'] / d['ctx_FunctionDef']) / NODE_CONTENT_RATIO
        })
    if 'ctx_FunctionDef_args' in d:
        d.update({
            'new_ctx_FunctionDef_args_size' : (d['ctx_FunctionDef_args'] / d['ctx_FunctionDef']) / NODE_CONTENT_RATIO
        })
    if 'ctx_ClassDef_body' in d:
        d.update({
            'new_ctx_ClassDef_body_size' : (d['ctx_ClassDef_body'] / d['ctx_ClassDef']) / NODE_CONTENT_RATIO
        })
    if 'ctx_Module_body' in d:
        d.update({
            'new_ctx_Module_body_size' : (d['ctx_Module_body'] / d['ctx_Module']) / NODE_CONTENT_RATIO
        })



    return d
