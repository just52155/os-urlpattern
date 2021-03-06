import json

from .compat import StringIO
from .definition import BasePatternRule, Symbols
from .parse_utils import pack
from .utils import dump_tree


class Formatter(object):

    def format(self, url_meta, tree, **kwargs):
        pass


class PatternFormatter(Formatter):
    def format(self, url_meta, root, **kwargs):
        for nodes in dump_tree(root):
            yield pack(url_meta, [p.pattern for p in nodes[1:]])
            break


class ClusterFormatter(PatternFormatter):
    def format(self, url_meta, root, **kwargs):
        for r in super(ClusterFormatter, self).format(url_meta, root, **kwargs):
            yield r

        for nodes in dump_tree(root):
            for url in nodes[-1].meta:
                yield u'\t'.join((u'', url))


class JsonFormatter(Formatter):
    def format(self, url_meta, root, **kwargs):
        for nodes in dump_tree(root):
            p = pack(url_meta, [p.pattern for p in nodes[1:]])
            yield json.dumps({u'ptn': p, u'cnt': root.count})
            break


class ETEFormatter(Formatter):
    def format(self, url_meta, root, **kwargs):

        def f(pattern_node):
            sep = Symbols.EMPTY
            query_key = Symbols.EMPTY
            path_depth = url_meta.path_depth
            query_depth = url_meta.query_depth
            current_level = pattern_node.level
            if path_depth < current_level \
                    and current_level <= (path_depth + query_depth):
                sep = Symbols.AMPERSAND
                if current_level == path_depth + 1:
                    sep = BasePatternRule.SINGLE_QUESTION
                query_key = url_meta.query_keys[current_level - path_depth - 1]
            elif current_level == path_depth + query_depth + 1:
                sep = Symbols.NUMBER
            return u' {sep}{query_key}{pattern_string}({count}) '.format(
                count=pattern_node.count,
                pattern_string=pattern_node.value,
                query_key=query_key,
                sep=sep)

        if root.count <= 0:
            return

        ete_tree = get_ete_tree(root, format=f)
        yield ete_tree.get_ascii(show_internal=True)


def get_ete_tree(root_node, format=str):
    from ete3 import Tree

    def add_children(node, ete_node):
        for child in node.children:
            ete_child = ete_node.add_child(name=format(child))
            add_children(child, ete_child)

    ete_root_node = Tree(name=format(root_node))
    add_children(root_node, ete_root_node)
    return ete_root_node


FORMATTERS = {
    'PATTERN': PatternFormatter,
    'CLUSTER': ClusterFormatter,
    'JSON': JsonFormatter,
}
try:
    import ete3
    FORMATTERS['ETE'] = ETEFormatter
except:
    pass
