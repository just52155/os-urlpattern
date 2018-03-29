import re


class PatternUnit(object):
    def __init__(self, pattern_unit_string):
        self._pattern_unit_string = pattern_unit_string
        from .parse_utils import parse_pattern_unit_string
        self._rules, self._num = parse_pattern_unit_string(pattern_unit_string)
        self._fuzzy_rule = None

    @property
    def fuzzy_rule(self):
        if self._fuzzy_rule is None:
            self._fuzzy_rule = ''.join(sorted(self._rules))
        return self._fuzzy_rule

    @property
    def rules(self):
        return self._rules

    @property
    def num(self):  # return negative means wildcard '+'
        return self._num

    def __str__(self):
        return self._pattern_unit_string


class Pattern(object):
    __slots__ = ('_pattern_string', '_pattern_regex',
                 '_pattern_units', '_fuzzy_rule')

    def __init__(self, pattern_string):
        self._pattern_string = pattern_string
        self._pattern_regex = None
        self._pattern_units = None
        self._fuzzy_rule = None

    @property
    def pattern_units(self):
        from .parse_utils import parse_pattern_string
        if self._pattern_units is None:
            self._pattern_units = [PatternUnit(
                u) for u in parse_pattern_string(self._pattern_string)]
        return self._pattern_units

    def __str__(self):
        return self.pattern_string

    __repr__ = __str__

    @property
    def pattern_string(self):
        return self._pattern_string

    def __hash__(self):
        return hash(self.pattern_string)

    def __eq__(self, o):
        if not isinstance(o, Pattern):
            return False
        return self.pattern_string == o.pattern_string

    def match(self, piece):
        if not self._pattern_regex:
            self._pattern_regex = re.compile(
                ''.join(('^', self._pattern_string, '$')))
        return True if re.match(self._pattern_regex, piece) else False

    @property
    def fuzzy_rule(self):
        if self._fuzzy_rule is None:
            self._fuzzy_rule = ''.join(sorted(set.union(
                *[u.rules for u in self.pattern_units])))
        return self._fuzzy_rule
