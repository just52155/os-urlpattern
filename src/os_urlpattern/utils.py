import logging
import os
import time

from .compat import itervalues


def pretty_counter(counter):
    return ", ".join(['{0}:{1}'.format(k, v) for k, v in counter.items()])


class Bag(object):
    def __init__(self):
        self._objs = set()

    def add(self, obj):
        self._objs.add(obj)

    def __len__(self):
        return len(self._objs)

    def pick(self):
        obj = self._pick()
        while isinstance(obj, Bag):
            obj = obj._pick()
        return obj

    def _pick(self):
        for obj in self._objs:
            return obj

    def __iter__(self):
        return iter(self._objs)

    def iter_all(self):
        for obj in self:
            if isinstance(obj, Bag):
                for o in obj.iter_all():
                    yield o
            else:
                yield obj


class Stack(object):
    def __init__(self):
        self._objs = []

    def push(self, obj):
        self._objs.append(obj)

    def pop(self):
        return self._objs.pop()

    def top(self):
        return self._objs[-1]

    def __len__(self):
        return len(self._objs)


class TreeNode(object):
    def __init__(self, value):
        self._parrent = None
        self._children = None
        self._count = 0
        self._value = value
        self._meta = None

    def leaf(self):
        return not self._children

    def level(self):
        l = 0
        n = self.parrent
        while n is not None:
            l += 1
            n = n.parrent

        return l

    @property
    def value(self):
        return self._value

    @property
    def meta(self):
        return self._meta

    @meta.setter
    def meta(self, meta):
        self._meta = meta

    @property
    def parrent(self):
        return self._parrent

    @parrent.setter
    def parrent(self, parrent):
        self._parrent = parrent

    @property
    def children(self):
        return itervalues(self._children if self._children is not None else {})

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, count):
        self._count = count

    def add_child(self, kv):
        if self._children is None:
            self._children = {}
        k, v = kv
        is_new = False
        if k not in self._children:
            self._children[k] = self.__class__(v)
            self._children[k].parrent = self
            is_new = True
        child = self._children[k]
        return child, is_new


def build_tree(root, kv_list, count=1, meta=None):
    node = root
    node.count += count
    for kv in kv_list:
        node, is_new = node.add_child(kv)
        node.count += count
    if meta is not None:
        node.meta = meta

    return node, is_new


def dump_tree(root):
    olist = []

    def _dump(node, _nodes):
        _nodes.append(node)
        if node.leaf():
            yield _nodes
            return
        for child in node.children:
            for nodes in _dump(child, _nodes):
                yield nodes
            _nodes.pop(-1)

    for nodes in _dump(root, olist):
        yield nodes


class LogSpeedAdapter(logging.LoggerAdapter):
    def __init__(self, logger, interval):
        super(LogSpeedAdapter, self).__init__(logger, {})
        self._count = 0
        self._interval = interval
        self._start_time = time.time()

    def process(self, msg, kwargs):
        self._count += 1

        if self._count % self._interval == 0:
            speed = self._speed()
            mem = used_memory()
            extra_msg = '[{mem}] {count} {speed:.1f}/s'.format(
                count=self._count, speed=speed, mem=mem)
            msg = ' '.join((msg, extra_msg))
            return msg, kwargs

    def debug(self, msg, *args, **kwargs):
        returnd = self.process(msg, kwargs)
        if not returnd:
            return
        msg, kwargs = returnd
        self.logger.debug(msg, *args, **kwargs)

    def _speed(self):
        now = time.time()
        return self._count / (now - self._start_time)


def used_memory():
    try:
        import psutil
    except:
        return '-'
    p = psutil.Process(os.getpid())
    memory = p.memory_info().rss / 1024.0
    for i in ['K', 'M', 'G']:
        if memory < 1024.0:
            return '%.1f%s' % (memory, i)
        memory = memory / 1024.0
    return '%.1fG' % memory
