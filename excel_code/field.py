#! python 3
# -*- coding: utf_8 -*-

from string import Template
from core.code import *


class SheetField(StructField):
    def __init__(self, parent, name, sign, desc, column_index, position: int, setting_str, props=None):
        if props is None:
            props = {}

        settings = process_setting(setting_str, Global.language)
        for key, val in settings.items():
            props[key] = val

        # property
        self.extend_type = None
        self.column_index = column_index

        # setting
        self.in_base = False
        self.is_key = False
        self.is_value_map = False
        self._value_map = ''
        self._value_map_names = []
        self._value_map_fields = []

        super().__init__(parent, name, desc, '', '', props, sign, position, '')

        if not self.extend_type or self.extend_type == '':
            self.extend_type = self.type.code_name

    @property
    def type_name(self):
        return self.extend_type

    @property
    def value_map_fields(self):
        return self._value_map_fields

    @property
    def value_map_names(self):
        return self._value_map_names

    def update_value_map_data(self):
        data_map = {}
        for f in self._value_map_fields:
            data_map[f.name] = f'{f.value_data}'

        data_str = Template(self._value_map).substitute(data_map)
        return self.set_data(data_str)

    def parse_maps(self):
        if self._value_map and self._value_map != '':
            names = parse_value_map(self._value_map)
            self._value_map_names.extend(names)
            for f in self._parent.fields:
                if f.name in names:
                    self._value_map_fields.append(f)
                    f.in_value_map = True

    def _process_prop(self, key, val):
        if key == 'extend_type':
            self.extend_type = val
        elif key == 'in_base':
            self.in_base = True
        elif key == 'default':
            self._default_value = val
        elif key == 'position':
            self._position = int(val)
        elif key == 'value':
            self._value_map = val
            self.is_value_map = True
        else:
            super()._process_prop(key, val)

