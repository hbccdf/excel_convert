#! python 3
# -*- coding: utf_8 -*-

from enum import Enum as CreateEnum
from . import type
from .check import *
from . utils import *


class CodeTypeMap:
    def __init__(self):
        self._type_map = {}
        self._enums = {}
        self._structs = {}

    def __getitem__(self, item):
        if item in self._type_map:
            return self._type_map[item]

        return None

    def register(self, code_type, is_enum):
        if code_type in self._type_map:
            return

        self._type_map[code_type.name] = code_type

        if is_enum:
            self._enums[code_type.name] = code_type
        else:
            self._structs[code_type.name] = code_type

    @property
    def enums(self):
        return self._enums

    @property
    def structs(self):
        return self._structs


GCodeTypeMap = CodeTypeMap()


class BaseField:
    def __init__(self, parent, name, desc, languages, tags, props):
        self._parent = parent
        self._name = name
        self._desc = desc.strip().replace('\n', ' ')
        self._languages = languages
        self._tags = tags
        self._props = props

        self._code_name = self._name
        self._type = None

    @property
    def name(self):
        return self._name

    @property
    def code_name(self):
        return self._code_name

    @property
    def info(self):
        return f'{self._parent.info}.{self.name}'

    @property
    def type(self):
        return self._type

    @property
    def desc(self):
        return self._desc


class EnumField(BaseField):
    def __init__(self, parent, name, desc, languages, tags, props, value):
        super().__init__(parent, name, desc, languages, tags, props)
        self._value = int(value)

    @property
    def value(self):
        return self._value


class FieldDataType:
    def __init__(self, field, sign, only_define=False):
        self._field = field
        self._sign = sign
        self._type, self._reader, self._handle = Global.SignMap.get_sign_info(self._field, self._sign)
        if not self._handle and not only_define:
            raise Exception(f'invalid sign {sign}, no handle')

        # read from type
        if not self._type:
            self._type = self._handle.code_name if self._handle else sign

    @property
    def name(self):
        return self._sign

    @property
    def code_name(self):
        return self._type

    @property
    def reader(self):
        return self._reader

    def convert(self, data):
        return self._handle.convert(data)

    def check(self, data, check_setting):
        return self._handle.check(data, check_setting)

    def pack(self, data):
        if not type.PackTType:
            return self._handle.pack(data)

        data_bytes = [type.Int8.pack_value(self._handle.ttype.value),
                      type.Int16.pack_value(self._field.position),
                      self._handle.pack(data)]
        return bytes.join(b'', data_bytes)

    def __repr__(self):
        return self._sign


class StructField(BaseField):
    def __init__(self, parent, name, desc, languages, tags, props, type_name, position, default_value):
        super().__init__(parent, name, desc, languages, tags, props)
        self._position = int(position)
        self._require = 'require' in props
        self._only_define = 'only_define' in props
        self._default_value = ''
        self._type = FieldDataType(self, type_name, self._only_define)
        self.in_value_map = False

        if default_value is not None:
            if default_value == 0:
                self._default_value = '0'
            else:
                self._default_value = str(default_value)

        # setting
        self._ignore = 'ignore' in props or not is_valid_language(languages)
        self._check_setting = CheckSetting()

        # data
        self._target = None

        # 二次处理
        for key, val in self._props.items():
            self._process_prop(key, val)

    @property
    def type_name(self):
        return self._type.code_name

    @property
    def position(self):
        return self._position

    @property
    def is_require(self):
        return self._require

    @property
    def is_optional(self):
        return not self.is_require

    @property
    def is_required_str(self):
        return 'true' if self.is_require else 'false'

    @property
    def default_value(self):
        return self._default_value

    @property
    def has_default_value(self):
        return self._default_value and self.default_value != ''

    @property
    def ignore(self):
        return self._ignore

    @property
    def only_define(self):
        return self._only_define

    @property
    def value_data(self):
        return self._target

    def _process_prop(self, key, val):
        if key == 'range':
            self._check_setting.set_range(val)
        elif key == 'len_range':
            self._check_setting.set_len_range(val)
        elif key == 'language':
            if not self._ignore:
                self._ignore = not is_valid_language(val)
        elif key != '' and key not in ['require', 'ignore', 'only_define']:
            print(f'--- warning invalid prop {key}, field {self.info}')

    def _convert(self, dat):
        return self.type.convert(dat)

    def _check(self, dat):
        return self.type.check(dat, self._check_setting)

    def _pack(self, dat):
        return self.type.pack(dat)

    def set_data(self, data):
        try:
            ok, self._target = self._convert(data)

            if not ok:
                return False, f'{self.info} convert to {self.type} failed, data {data}'
        except Exception as e:
            return False, f'{self.info} convert to {self.type} failed, data {data}, {e}'

        ok, info = self._check(self._target)
        if not ok:
            return False, f'{self.info} check failed, {info}, data {data}, target {self._target}'

        return True, ''

    def pack_data(self, stream):
        bin_bytes = self._pack(self._target)
        stream.write(bin_bytes)


class BaseType:
    def __init__(self, name, desc, languages, tags, props):
        self._name = name
        self._desc = desc
        self._languages = languages
        self._tags = tags
        self._props = props

        self._code_name = self._name

        self._type = None
        self._value = None

    @property
    def name(self):
        return self._name

    @property
    def code_name(self):
        return self._code_name

    @property
    def type(self):
        return self._type

    @property
    def info(self):
        return self._name


class Enum(BaseType):
    def __init__(self, name, is_enum_class, desc, languages, tags, props, default_value):
        super().__init__(name, desc, languages, tags, props)
        self._is_enum_class = is_enum_class
        self._default_value = default_value
        self._fields = []
        self._fields_map = {}

        GCodeTypeMap.register(self, True)

    def add_fields(self, fields):
        if self._type:
            return

        self._fields.extend(fields)
        for f in fields:
            self._fields_map[f.name] = f

        # create type
        enum_type = type.GTypeMap[self.name]
        if not enum_type:
            enum_fields = [(f.name, f.value) for f in fields]
            enum_class_type = CreateEnum(self.name, enum_fields)
            enum_type = type.Enum(self.name, enum_class_type, self._default_value)

        self._type = enum_type

    @property
    def is_enum_class(self):
        return self._is_enum_class

    @property
    def fields(self):
        return self._fields

    @property
    def fields_name_str(self):
        return ','.join([field.code_name for field in self.fields])


class Struct(BaseType):
    def __init__(self, name, desc, languages, tags, props, base_structs):
        super().__init__(name, desc, languages, tags, props)
        self._base_structs = parse_value_list(base_structs)
        self._fields_map = {}
        self._fields = []
        self._all_fields = []  # include all base struct fields

        self._process_bases()

        GCodeTypeMap.register(self, False)

    @property
    def fields(self):
        return self._fields

    @property
    def all_fields(self):
        return self._all_fields

    @property
    def bases(self):
        return self._base_structs

    def add_fields(self, fields):
        if self._type:
            return

        self._fields.extend(fields)
        for f in fields:
            self._fields_map[f.name] = f

        self._all_fields.extend(self._fields)

        struct_type = type.GTypeMap[self.name]
        if not struct_type:
            fields_info = []
            for f in self._all_fields:
                fields_info.append((f.name, f.type.name, f.position))
            struct_type = type.Struct(self.name, fields_info)

        self._type = struct_type

    def _process_bases(self):
        for base_name in self._base_structs:
            base = GCodeTypeMap[base_name]
            if not base:
                # error
                continue

            self._all_fields.extend(base.fields)

