#! python 3
# -*- coding: utf_8 -*-

import struct
import enum
from .utils import parse_value_list, expend_array


class TType(enum.IntEnum):
    BEGIN = -1,
    STOP = 0,
    VOID = 1,
    BOOL = 2,
    BYTE = 3,
    I08 = 3,
    I16 = 6,
    I32 = 8,
    U64 = 9,
    I64 = 10,
    FLOAT = 4,
    DOUBLE = 5,
    STRING = 11,
    UTF7 = 11,
    STRUCT = 12,
    MAP = 13,
    SET = 14,
    LIST = 15,
    ARRAY = 16,
    UTF8 = 17,
    UTF16 = 18,
    END = 19,


StringEncodingOfPack = 'utf-8'
PackTType = False


def _pack_str(val):
    val_bytes = val.encode(encoding=StringEncodingOfPack)
    length = len(val_bytes)
    if length == 0:
        return struct.pack('<i', 0)
    return struct.pack(f'<i{length}s', length, val_bytes)


class TypeMap:
    def __init__(self):
        self._type_map = {
            'B': Bool(),
            'I': Int(),
            'F': Float(),
            'S': String()
        }

    def __getitem__(self, item):
        value = item.replace(' ', '')
        if value in self._type_map:
            return self._type_map[value]

        return None

    def register(self, type):
        if type in self._type_map:
            return

        self._type_map[type.name] = type


class Handler:
    @property
    def name(self):
        return ''

    @property
    def code_name(self):
        return ''

    def convert(self, val):
        pass

    def check(self, val, setting):
        return True, ''

    def pack(self, val):
        return self.pack_value(val)

    @staticmethod
    def check_range(val, setting):
        if not setting.check_range(val):
            return False, f'check range failed, val {val}, range {setting.range_str()}'

        return True, ''

    @staticmethod
    def check_len_range(val, setting):
        if not setting.check_len_range(val):
            return False, f'check len range failed, val {val}, range {setting.len_range_str()}'

        return True, ''

    @staticmethod
    def check_list(val, setting):
        if not isinstance(val, list) and not isinstance(val, set):
            return False, f'val {val}, is not list and not set'

        ok, info = Handler.check_len_range(len(val), setting)
        if not ok:
            return ok, info

        for v in val:
            if isinstance(v, int) or isinstance(v, float):
                if v > 2147483647 or v < -2147483648:
                    return False, f'invalid int data {v}, too big or too small'
            ok, info = Handler.check_range(v, setting)
            if not ok:
                return ok, info

        return True, ''

    @staticmethod
    def pack_value(val):
        return ''

    def _parse_value_list(self, value_data):
        val_list = value_data

        assert isinstance(value_data, list) or isinstance(value_data, str)

        if isinstance(value_data, str):
            split_char = self._split_char_of_value_list()
            val_list = parse_value_list(value_data, split_char)
        return val_list

    def _split_char_of_value_list(self):
        return ','

    @staticmethod
    def _expend_array(value_list, value_type_name):
        if value_type_name not in ['I', 'I8', 'I16', 'I32', 'I64']:
            return value_list

        return expend_array(value_list, 200)


class Bool(Handler):
    ttype = TType.BOOL

    @property
    def name(self):
        return 'B'

    @property
    def code_name(self):
        return 'bool'

    def convert(self, val, default=False):
        if val is None:
            return True, default
        try:
            if isinstance(val, str):
                return True, val.strip() not in ['0', 'false', 'False', 'FALSE', 'off', 'Off', 'OFF']
            else:
                return True, bool(val)
        except ValueError as e:
            return False, default

    def pack(self, val):
        return self.pack_value(val)

    @staticmethod
    def pack_value(val):
        return struct.pack('?', val)


class IntBase(Handler):
    @staticmethod
    def convert_value(val, default=0):
        if val is None or (isinstance(val, str) and val == ''):
            return True, default
        try:
            return True, int(float(val))
        except ValueError as e:
            return False, None

    def convert(self, val, default=0):
        return IntBase.convert_value(val, default)

    def check(self, val, setting):
        if val > 2147483647 or val < -2147483648:
            return False, f'invalid int data {val}, too big or too small'

        return self.check_range(val, setting)

    def pack(self, val):
        return self.pack_value(val)


class Int8(IntBase):
    ttype = TType.I08

    @property
    def name(self):
        return 'I8'

    @property
    def code_name(self):
        return 'int8_t'

    @staticmethod
    def pack_value(val):
        return struct.pack('<b', val)


class Int16(IntBase):
    ttype = TType.I16

    @property
    def name(self):
        return 'I16'

    @property
    def code_name(self):
        return 'int16_t'

    @staticmethod
    def pack_value(val):
        return struct.pack('<h', val)


class Int(IntBase):
    ttype = TType.I32

    @property
    def name(self):
        return 'I'

    @property
    def code_name(self):
        return 'int'

    @staticmethod
    def pack_value(val):
        return struct.pack('<i', val)


class Float(Handler):
    ttype = TType.FLOAT

    @property
    def name(self):
        return 'F'

    @property
    def code_name(self):
        return 'float'

    def convert(self, val, default=0.0):
        if val is None:
            return True, default
        try:
            return True, float(val)
        except ValueError as e:
            return False, default

    def check(self, val, setting):
        return self.check_range(val, setting)

    def pack(self, val):
        return self.pack_value(val)

    @staticmethod
    def pack_value(val):
        return struct.pack('<f', val)


class String(Handler):
    ttype = TType.STRING

    def __init__(self, type_name='S'):
        self._type_name = type_name

    def _to_str(self, val):
        if not isinstance(val, str):
            return str(val)

        if self._type_name != 'LEffect' and self._type_name != 'Effect':
            return val

        return val.strip('[').strip(']')

    @property
    def name(self):
        return self._type_name

    @property
    def code_name(self):
        return 'string'

    def convert(self, val, default=''):
        if val is None:
            return True, default
        try:
            return True, self._to_str(val)
        except ValueError as e:
            return False, default

    def check(self, val, setting):
        return self.check_range(len(val), setting)

    def pack(self, val):
        return self.pack_value(val)

    @staticmethod
    def pack_value(val):
        return _pack_str(val)


GTypeMap = TypeMap()


class Enum(Handler):
    ttype = TType.I32

    def __init__(self, enum_name, enum_class, default_value):
        self._name = enum_name
        self._enum = enum_class
        self._default = default_value

        GTypeMap.register(self)

    @property
    def name(self):
        return self._name

    @property
    def code_name(self):
        return self.name

    def convert(self, val):
        result, int_val = IntBase.convert_value(val)

        for name, member in self._enum.__members__.items():
            if result and member.value == int_val:
                return True, int_val
            elif isinstance(val, str) and name == val:
                return True, member.value

        raise Exception(f"invalid value {val}, in enum {self.name}")

    def check(self, val, setting):
        return self.check_range(int(val), setting)

    def pack(self, val):
        return self.pack_value(val)

    @staticmethod
    def pack_value(val):
        return struct.pack('<i', val)


class Array(Handler):
    ttype = TType.ARRAY

    def __init__(self, val_type, val_len):
        self._val_type = val_type
        self._val_len = val_len
        self._val_handler = GTypeMap[self._val_type]

        GTypeMap.register(self)

    @property
    def name(self):
        return f'array<{self._val_handler.name}, {self._val_len}>'

    @property
    def code_name(self):
        return f'array<{self._val_handler.code_name}, {self._val_len}>'

    def convert(self, val):
        if val is None:
            return True, []

        result_list = []
        val_list = val
        if isinstance(val, str):
            val_list = self._parse_value_list(val)
        elif not isinstance(val, list):
            val_list = [val]

        val_list = self._expend_array(val_list, self._val_handler.name)

        for i, v in enumerate(val_list):
            ok, target = self._val_handler.convert(v)
            if not ok:
                raise Exception(f"invalid value {v}, in val_list {val_list}, index {i}, val {val}")
            result_list.append(target)
        return True, result_list

    def check(self, val, setting):
        return self.check_list(val, setting)

    def pack(self, val_data):
        val_bytes = []
        val_list = self._parse_value_list(val_data)

        if PackTType:
            val_bytes.append(Int8.pack_value(self._val_handler.ttype.value))

        val_bytes.append(Int.pack_value(len(val_list)))

        for val in val_list:
            val_bytes.append(self._val_handler.pack(val))
        
        return bytes.join(b'', val_bytes)


class List(Handler):
    ttype = TType.LIST

    def __init__(self, val_type, type_name=None):
        self._val_type = val_type
        self._val_handler = GTypeMap[self._val_type]
        self._type_name = type_name
        if not self._type_name:
            self._type_name = f'list<{self._val_handler.name}>'

        GTypeMap.register(self)

    @property
    def name(self):
        return self._type_name

    @property
    def code_name(self):
        return f'vector<{self._val_handler.code_name}>'

    def _split_char_of_value_list(self):
        if self._val_handler.name == 'SSNextSkillEffectCfg':
            return ';'

        return super()._split_char_of_value_list()

    def convert(self, val, default=None):
        if default is None:
            default = []

        if val is None:
            return True, default

        result_list = []
        val_list = val
        if isinstance(val, str):
            val_list = self._parse_value_list(val)
        elif not isinstance(val, list):
            val_list = [val]

        val_list = self._expend_array(val_list, self._val_handler.name)

        for i, v in enumerate(val_list):
            ok, target = self._val_handler.convert(v)
            if not ok:
                raise Exception(f"invalid value {v}, in val_list {val_list}, index {i}, val {val}")
            result_list.append(target)
        return True, result_list

    def check(self, val, setting):
        return self.check_list(val, setting)

    def pack(self, val_data):
        val_bytes = []
        val_list = self._parse_value_list(val_data)

        if PackTType:
            val_bytes.append(Int8.pack_value(self._val_handler.ttype.value))

        val_bytes.append(Int.pack_value(len(val_list)))
        for val in val_list:
            val_bytes.append(self._val_handler.pack(val))

        return bytes.join(b'', val_bytes)


GTypeMap.register(List('B', 'LB'))
GTypeMap.register(List('I', 'LI'))
GTypeMap.register(List('F', 'LF'))
GTypeMap.register(List('S', 'LS'))
GTypeMap.register(String('LEffect'))
GTypeMap.register(String('Effect'))


class Set(Handler):
    ttype = TType.SET

    def __init__(self, val_type):
        self._val_type = val_type
        self._val_handler = GTypeMap[self._val_type]

        GTypeMap.register(self)

    @property
    def name(self):
        return f'set<{self._val_handler.name}>'

    @property
    def code_name(self):
        return f'set<{self._val_handler.code_name}>'

    def convert(self, val, default=None):
        if default is None:
            default = set()

        if val is None:
            return True, default

        result_list = []
        val_list = val
        if isinstance(val, str):
            val_list = self._parse_value_list(val)
        elif not isinstance(val, list):
            val_list = [val]

        val_list = self._expend_array(val_list, self._val_handler.name)

        for i, v in enumerate(val_list):
            ok, target = self._val_handler.convert(v)
            if not ok:
                raise Exception(f"invalid value {v}, in val_list {val_list}, index {i}, val {val}")
            result_list.append(target)
        return True, set(result_list)

    def check(self, val, setting):
        return self.check_list(val, setting)

    def pack(self, val_data):
        val_bytes = []
        val_list = self._parse_value_list(val_data)

        if PackTType:
            val_bytes.append(Int8.pack_value(self._val_handler.ttype.value))

        val_bytes.append(Int.pack_value(len(val_list)))
        for val in val_list:
            val_bytes.append(self._val_handler.pack(val))

        return bytes.join(b'', val_bytes)


class Map(Handler):
    ttype = TType.MAP

    def __init__(self, key_type, val_type):
        self._key_type = key_type
        self._val_type = val_type

        self._key_handler = GTypeMap[self._key_type]
        self._val_handler = GTypeMap[self._val_type]

        GTypeMap.register(self)

    @property
    def name(self):
        return f'map<{self._key_handler.name},{self._val_handler.name}>'

    @property
    def code_name(self):
        return f'map<{self._key_handler.code_name},{self._val_handler.code_name}>'

    def convert(self, val, default=None):
        if default is None:
            default = {}

        if val is None:
            return True, default

        result_map = {}
        val_list = val
        if isinstance(val, str):
            val_list = self._parse_value_list(val)
        elif not isinstance(val, list):
            val_list = [val]

        for i, v in enumerate(val_list):
            key_value = parse_value_list(v, ':')
            ok = True
            key = None
            value = None
            if len(key_value) == 2:
                ok, key = self._key_handler.convert(key_value[0])
                if ok:
                    ok, value = self._val_handler.convert(key_value[1])
            if not ok or len(key_value) != 2:
                raise Exception(f"invalid value {v}, in val_list {val_list}, index {i}, val {val}")

            result_map[key] = value
        return True, result_map

    def pack(self, val_map):
        val_bytes = []

        if PackTType:
            val_bytes.append(Int8.pack_value(self._key_handler.ttype.value))
            val_bytes.append(Int8.pack_value(self._val_handler.ttype.value))

        val_bytes.append(Int.pack_value(len(val_map)))

        for key, val in val_map.items():
            val_bytes.append(self._key_handler.pack(key))
            val_bytes.append(self._val_handler.pack(val))

        return bytes.join(b'', val_bytes)


class _StructField:
    def __init__(self, name, val_type, position):
        self._name = name
        self._val_type = val_type
        self._val_handler = GTypeMap[self._val_type]
        self._position = position

    @property
    def name(self):
        return self._name

    @property
    def position(self):
        return self._position

    def convert(self, val):
        return self._val_handler.convert(val)

    def pack(self, val):
        val_bytes = []
        if PackTType:
            val_bytes.append(Int8.pack_value(self._val_handler.ttype.value))
            val_bytes.append(Int16.pack_value(self._position))
        val_bytes.append(self._val_handler.pack(val))
        return bytes.join(b'', val_bytes)


class Struct(Handler):
    ttype = TType.STRUCT

    def __init__(self, name, fields_info):
        self._name = name
        self._fields_info = fields_info
        self._field_names = []
        self._fields = []
        self._fields_map = {}

        for f in fields_info:
            name, val_type, position = f
            field = _StructField(name, val_type, position)
            self._field_names.append(name)
            self._fields_map[name] = field
            self._fields.append(field)

        # sort fields by position
        self._fields.sort(key=lambda elem: elem.position)
        GTypeMap.register(self)

    @property
    def name(self):
        return self._name

    @property
    def code_name(self):
        return self.name

    def _split_char_of_value_list(self):
        if self.name == 'SSNextSkillEffectCfg':
            return ':'

        return super()._split_char_of_value_list()

    def convert(self, val):
        result_list = []
        val_list = val
        if isinstance(val, str):
            val_list = self._parse_value_list(val)
        elif not isinstance(val, list):
            val_list = [val]

        for i, v in enumerate(val_list):
            field = self._fields[i]
            ok, target = field.convert(v)
            if not ok:
                raise Exception(f"field {self._name}.{field.name}, invalid value {v}, in val_list {val_list}, index {i}, val {val}")
            result_list.append(target)
        return True, result_list

    def pack(self, val_data):
        val_bytes = []
        val_list = self._parse_value_list(val_data)
        for i in range(len(val_list)):
            val = val_list[i]
            field = self._fields[i]
            val_bytes.append(field.pack(val))

        if PackTType:
            val_bytes.append(Int8.pack_value(TType.STOP))

        return bytes.join(b'', val_bytes)

