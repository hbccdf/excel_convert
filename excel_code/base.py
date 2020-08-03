#! python 3
# -*- coding: utf_8 -*-
from .code_utils import load_define_data


class BaseCode:
    def __init__(self, name):
        self.name = name
        self.fields_map = {}
        self.fields = []

    def add_fields(self, name, fields):
        self.fields_map[name] = fields

    def process(self, define_data):
        self.fields = []
        fields_count_map = {}
        # 统计每个field出现的次数
        for _, fields in self.fields_map.items():
            for field in fields:
                name = field.name
                if name not in fields_count_map:
                    fields_count_map[name] = (1, field)
                    continue

                field_info = fields_count_map[name]
                (count, f) = field_info
                count += 1
                fields_count_map[name] = (count, f)

        # 找到出现多次的field
        for _, field_info in fields_count_map.items():
            (count, f) = field_info
            if count > 1:
                self.fields.append(f)
            elif f.in_base:
                self.fields.append(f)

        self._load_define_data(define_data)

    def __contains__(self, field):
        for f in self.fields:
            if f.name == field.name:
                return True

        return False

    def _load_define_data(self, define_data):
        fields = load_define_data(self, define_data)
        self.fields.extend(fields)

