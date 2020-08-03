#! python 3
# -*- coding: utf_8 -*-

import re


class CheckBase:
    def check(self, val):
        pass


class _RangePair:
    def __init__(self, min: int, max: int, contain_min: bool, contain_max: bool):
        self.min = min
        self.max = max
        self.contain_min = contain_min
        self.contain_max = contain_max

    def check(self, val: int):
        if self.contain_min:
            if val < self.min:
                return False
        else:
            if val <= self.min:
                return False

        if self.contain_max:
            if val > self.max:
                return False
        else:
            if val >= self.max:
                return False

        return True


class Range(CheckBase):
    _range_re = re.compile(r'\s*([\[\(])(\d+)\s*,\s*(\d+)([\]\)])', re.S)

    def __init__(self, range_str):
        self._list = []
        self._range_str = ''
        self._parse_range_str(range_str)

    def _parse_range_str(self, range_str):
        matched = False
        search_pos = 0
        while True:
            m = Range._range_re.match(range_str, search_pos)
            if not m:
                if not matched:
                    raise Exception(f'invalid range str {range_str}')
                else:
                    break

            matched = True
            search_pos += len(m[0])
            range_pair = _RangePair(int(m[2]), int(m[3]), m[1] == '[', m[4] == ']')
            self._range_str += m[0]
            self._list.append(range_pair)

    @staticmethod
    def _is_whitespace(self, c):
        return c in ' \t\r\n'

    def check(self, val: int):
        # 在任意一个range范围内
        for range_pair in self._list:
            if range_pair.check(val):
                return True

        return False

    def __str__(self):
        return self._range_str


class Index(CheckBase):
    def __init__(self, index_str):
        pass

    def check(self, val):
        pass


class Eval(CheckBase):
    def __init__(self, eval_str):
        pass

    def check(self, val):
        pass


class CheckSetting:
    def __init__(self):
        self._val_range = None
        self._len_range = None

    def set_range(self, range_str):
        self._val_range = Range(range_str)

    def set_len_range(self, range_str):
        self._len_range = Range(range_str)

    def check_range(self, val):
        if self._val_range:
            return self._val_range.check(val)

        return True

    def check_len_range(self, val):
        if self._len_range:
            return self._len_range.check(val)

        return True

    def range_str(self):
        return str(self._val_range)

    def len_range_str(self):
        return str(self._len_range)