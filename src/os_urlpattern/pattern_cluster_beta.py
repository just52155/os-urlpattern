from collections import Counter

from .compat import iteritems, itervalues
from .definition import DIGIT_AND_ASCII_RULE_SET, BasePatternRule
from .parse_utils import URLMeta, number_rule, wildcard_rule
from .pattern import Pattern
from .piece_pattern_tree import PiecePatternTree
from .utils import Bag


class CountBag(Bag):
    def __init__(self):
        super(CountBag, self).__init__()
        self._count = 0

    @property
    def count(self):
        return self._count

    def add(self, obj):
        super(CountBag, self).add(obj)
        self._count += obj.count


class PatternCluster(object):
    def __init__(self, config, meta_info):
        self._config = config
        self._meta_info = meta_info
        self._min_cluster_num = config.getint('make', 'min_cluster_num')

    def _cluster(self):
        pass

    def _forward_clusters(self):
        yield

    def cluster(self):
        self._cluster()
        for c in self._forward_clusters():
            yield c

    def add(self, obj):
        pass


class PiecePatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(PiecePatternCluster, self).__init__(config, meta_info)
        self._piece_bags = {}
        self._forward_cluster = None

    def iter_nodes(self):
        for bag in itervalues(self._piece_bags):
            for node in bag.iter_all():
                yield node

    def add(self, piece_pattern_node):
        piece = piece_pattern_node.piece
        if piece not in self._piece_bags:
            self._piece_bags[piece] = CountBag()
        self._piece_bags[piece].add(piece_pattern_node)

    def _create_forward_cluster(self):
        cluster_cls = LengthPatternCluster
        piece_pattern_node = self._piece_bags.values()[0].pick()
        if len(piece_pattern_node.parsed_piece.pieces) > 1:
            cluster_cls = BasePatternCluster
        return cluster_cls(self._config, self._meta_info)

    def _cluster(self):
        if len(self._piece_bags) == 1:
            return

        if self._forward_cluster is None:
            self._forward_cluster = self._create_forward_cluster()

        for _, bag in iteritems(self._piece_bags):
            if not self._keep(bag):
                self._forward_cluster.add(bag)

    def _keep(self, bag):
        if bag.count < self._min_cluster_num:
            return False
        sands = set()
        for node in bag:
            parrent = node.parrent
            if parrent.children_num == 1:
                continue
            elif parrent.children_num >= self._min_cluster_num:
                return False
            else:
                for child in parrent.iter_children():
                    if child.piece != node.piece and \
                            self._piece_bags[child.piece].count < self._min_cluster_num:
                        sands.add(child.piece)
                        if len(sands) >= self._min_cluster_num - 1:
                            return False
        return True

    def _forward_clusters(self):
        yield self._forward_cluster


class LengthPatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(LengthPatternCluster, self).__init__(config, meta_info)
        self._length_bags = {}
        self._forward_cluster = FuzzyPatternCluster(config, meta_info)

    def add(self, piece_bag):
        piece_length = piece_bag.pick().parsed_piece.piece_length
        if piece_length not in self._length_bags:
            self._length_bags[piece_length] = CountBag()
        self._length_bags[piece_length].add(piece_bag)

    def _cluster(self):
        for length, bag in iteritems(self._length_bags):
            pass

    def _forward_clusters(self):
        yield self._forward_cluster


class MultiPartPatternCluster(PatternCluster):
    pass


class BasePatternCluster(MultiPartPatternCluster):
    def __init__(self, config, meta_info):
        super(BasePatternCluster, self).__init__(config, meta_info)


class FuzzyPatternCluster(PatternCluster):
    def __init__(self, config, meta_info):
        super(FuzzyPatternCluster, self).__init__(config, meta_info)


class MetaInfo(object):
    def __init__(self, url_meta, current_level):
        self._url_meta = url_meta
        self._current_level = current_level

    @property
    def current_level(self):
        return self._current_level

    @property
    def url_meta(self):
        return self._url_meta

    def is_last_level(self):
        return self.url_meta.depth == self._current_level

    def is_last_path(self):
        return self.url_meta.path_depth == self._current_level

    def next_level_meta_info(self):
        return MetaInfo(self.url_meta, self.current_level + 1)


class ClusterProcessor(object):
    def __init__(self, config, meta_info, global_processing):
        self._config = config
        self._meta_info = meta_info
        self._global_processing = global_processing
        self._entry_cluster = PiecePatternCluster(config, meta_info)

    def add_node(self, node):
        self._entry_cluster.add(node)

    def add_children(self, node):
        for child in node.iter_children():
            self.add_node(child)

    def _process(self, pattern_cluster):
        if pattern_cluster is not None:
            for c in pattern_cluster.cluster():
                self._process(c)

    def _preprocess(self):
        pass

    def process(self):
        self._process(self._entry_cluster)
        if self._meta_info.is_last_level():
            return
        next_level_processors = {}
        next_level_meta_info = self._meta_info.next_level_meta_info()
        for node in self._entry_cluster.iter_nodes():
            pattern = node.pattern
            if pattern not in next_level_processors:
                next_level_processors[pattern] = ClusterProcessor(
                    self._config, next_level_meta_info, self._global_processing)
            next_level_processor = next_level_processors[pattern]
            next_level_processor.add_children(node)
        for processor in itervalues(next_level_processors):
            processor.process()


def split(piece_pattern_tree):
    yield


def cluster(config, url_meta, piece_pattern_tree, **kwargs):
    global_processing = kwargs.get('global_processing', True)
    if global_processing and \
            piece_pattern_tree.count < config.getint('make', 'min_cluster_num'):
        return

    meta_info = MetaInfo(url_meta, 0)
    processor = ClusterProcessor(
        config, meta_info, global_processing)
    processor.add_node(piece_pattern_tree.root)
    processor.process()

    return
    if global_processing:
        for sub_piece_pattern_tree in split(piece_pattern_tree):
            cluster(config, url_meta, sub_piece_pattern_tree,
                    global_processing=False)