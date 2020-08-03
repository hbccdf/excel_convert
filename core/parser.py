#! python 3
# -*- coding: utf_8 -*-
import re
from . import code
from . type import *
from .utils import get_key_value, get_list_value


def _parse_props(props, prop_list):
    for prop in prop_list:
        strs = prop.split('=')
        key = get_list_value(strs, 0, '').strip()
        val = get_list_value(strs, 1, None)

        if key != '':
            props[key] = val


def _get_last_all_values(row, index, default_value):
    if index < len(row):
        return row[index:]

    return default_value


class EnumParser:
    _EnumNameIndex = 0
    _EnumDescIndex = 1
    _EnumDefaultValueIndex = 2
    _EnumLanguageIndex = 3
    _EnumTagIndex = 4
    _EnumPropIndex = 5

    _FieldNameIndex = 0
    _FieldDescIndex = 1
    _FieldValueIndex = 2
    _FieldLanguageIndex = 3
    _FieldTagIndex = 4
    _FieldPropIndex = 5

    @staticmethod
    def parse(rows):
        name_row = rows[0]
        field_rows = rows[1:]

        code_enum = EnumParser._parse_enum(name_row)
        if not code_enum:
            return None

        fields = EnumParser._parse_fields(code_enum, field_rows)
        if fields and len(fields) > 0:
            pass

        code_enum.add_fields(fields)
        return code_enum

    @staticmethod
    def parse_define(enums_data):
        enums = []
        if enums_data is None:
            return enums

        for enum_data in enums_data:
            code_enum = EnumParser._parse_define_enum(enum_data)
            if not code_enum:
                continue

            fields = EnumParser._parse_define_fields(code_enum, enum_data['fields'])
            if fields and len(fields) > 0:
                pass

            code_enum.add_fields(fields)
            enums.append(enum)
        return enums

    @staticmethod
    def _parse_enum(row):
        name = row[EnumParser._EnumNameIndex].strip()[len('enum '):].strip()
        desc = get_list_value(row, EnumParser._EnumDescIndex, '')
        default_value = get_list_value(row, EnumParser._EnumDefaultValueIndex, None)
        languages = get_list_value(row, EnumParser._EnumLanguageIndex, '')
        tags = get_list_value(row, EnumParser._EnumTagIndex, '')
        props_list = _get_last_all_values(row, EnumParser._EnumPropIndex, [])
        props = {}
        _parse_props(props, props_list)

        if name != '':
            is_enum_class = False
            if name.startswith('class '):
                is_enum_class = True
                name = name[len('class '):]
            return code.Enum(name, is_enum_class, desc, languages, tags, props, default_value)

        # Todo throw error
        return None

    @staticmethod
    def _parse_fields(enum, rows):
        fields = []
        for row in rows:
            name = row[EnumParser._FieldNameIndex].strip()
            desc = get_list_value(row, EnumParser._FieldDescIndex, '')
            value = get_list_value(row, EnumParser._FieldValueIndex, None)
            languages = get_list_value(row, EnumParser._FieldLanguageIndex, '')
            tags = get_list_value(row, EnumParser._FieldTagIndex, '')
            props_list = _get_last_all_values(row, EnumParser._FieldPropIndex, [])
            props = {}
            _parse_props(props, props_list)

            if name != '':
                field = code.EnumField(enum, name, desc, languages, tags, props, value)
                fields.append(field)

        return fields

    @staticmethod
    def _parse_define_enum(enum_data):
        name = enum_data['name'].strip()
        desc = get_key_value(enum_data, 'desc', '')
        default_value = get_key_value(enum_data, 'default', '')
        languages = get_key_value(enum_data, 'languages', '')
        tags = get_key_value(enum_data, 'tags', '')
        props = get_key_value(enum_data, 'props', {})

        if name != '':
            return code.Enum(name, desc, languages, tags, props, default_value)

        # Todo throw error
        return None

    @staticmethod
    def _parse_define_fields(enum, fields_data):
        fields = []
        for field_data in fields_data:
            name = get_key_value(field_data, 'name', '').strip()
            desc = get_key_value(field_data, 'desc', '')
            value = get_key_value(field_data, 'value', None)
            languages = get_key_value(field_data, 'languages', '')
            tags = get_key_value(field_data, 'tags', '')
            props = get_key_value(field_data, 'props', {})

            if name != '':
                field = code.EnumField(enum, name, desc, languages, tags, props, value)
                fields.append(field)

        return fields


class StructParser:
    _StructNameIndex = 0
    _StructDescIndex = 1
    _StructBaseIndex = 2
    _StructLanguageIndex = 5
    _StructTagIndex = 6
    _StructPropIndex = 7

    _FieldNameIndex = 0
    _FieldDescIndex = 1
    _FieldTypeIndex = 2
    _FieldPositionIndex = 3
    _FieldValueIndex = 4
    _FieldLanguageIndex = 5
    _FieldTagIndex = 6
    _FieldPropIndex = 7

    @staticmethod
    def parse(rows):
        name_row = rows[0]
        field_rows = rows[1:]

        struct = StructParser._parse_struct(name_row)
        if not struct:
            return None

        fields = StructParser._parse_fields(struct, field_rows)
        if fields and len(fields) > 0:
            pass

        struct.add_fields(fields)
        return struct

    @staticmethod
    def parse_define(structs_data):
        structs = []
        if structs_data is None:
            return structs

        for struct_data in structs_data:
            define_struct = StructParser._parse_define_struct(struct_data)
            if not define_struct:
                continue

            fields = StructParser._parse_define_fields(define_struct, struct_data['fields'])
            if fields and len(fields) > 0:
                pass

            define_struct.add_fields(fields)
            structs.append(define_struct)

        return structs

    @staticmethod
    def _parse_struct(row):
        name = row[StructParser._StructNameIndex].strip()[len('struct '):]
        desc = get_list_value(row, StructParser._StructDescIndex, '')
        base_structs = get_list_value(row, StructParser._StructBaseIndex, '')
        languages = get_list_value(row, StructParser._StructLanguageIndex, '')
        tags = get_list_value(row, StructParser._StructTagIndex, '')
        props_list = _get_last_all_values(row, StructParser._StructPropIndex, [])
        props = {}
        _parse_props(props, props_list)

        if name != '':
            return code.Struct(name, desc, languages, tags, props, base_structs)

        # Todo throw error
        return None

    @staticmethod
    def _parse_fields(struct, rows):
        fields = []
        for row in rows:
            name = row[StructParser._FieldNameIndex].strip()
            desc = get_list_value(row, StructParser._FieldDescIndex, '')
            type = get_list_value(row, StructParser._FieldTypeIndex, None)
            default_value = get_list_value(row, StructParser._FieldValueIndex, None)
            position = get_list_value(row, StructParser._FieldPositionIndex, 0)
            languages = get_list_value(row, StructParser._FieldLanguageIndex, '')
            tags = get_list_value(row, StructParser._FieldTagIndex, '')
            props_list = get_list_value(row, StructParser._FieldPropIndex, [])
            props = {}
            _parse_props(props, props_list)

            if name != '':
                field = code.StructField(struct, name, desc, languages, tags, props, type, position, default_value)
                fields.append(field)

        return fields

    @staticmethod
    def _parse_define_struct(struct_data):
        name = struct_data['name']
        desc = get_key_value(struct_data, 'desc', '')
        base_structs = get_key_value(struct_data, 'bases', '')
        languages = get_key_value(struct_data, 'languages', '')
        tags = get_key_value(struct_data, 'tags', '')
        props = get_key_value(struct_data, 'props', {})

        if name != '':
            return code.Struct(name, desc, languages, tags, props, base_structs)

        # Todo throw error
        return None

    @staticmethod
    def _parse_define_fields(struct, fields_data):
        fields = []
        for field_data in fields_data:
            name = field_data['name'].strip()
            desc = get_key_value(field_data, 'desc', '')
            type = get_key_value(field_data, 'sign', None)
            default_value = get_key_value(field_data, 'default', '')
            position = get_key_value(field_data, 'position', 0)
            languages = get_key_value(field_data, 'languages', '')
            tags = get_key_value(field_data, 'tags', '')
            props = get_key_value(field_data, 'props', {})

            if name != '':
                field = code.StructField(struct, name, desc, languages, tags, props, type, position, default_value)
                fields.append(field)

        return fields


class TypeParser:
    _ArrayRe = re.compile(r'^array<(\w+)\s*,\s*(\d+)>$', re.S)
    _ListRe = re.compile(r'list<(\w+)>$', re.S)
    _SetRe = re.compile(r'^set<(\w+)>$', re.S)
    _MapRe = re.compile(r'^map<(\w+.*?)\s*,\s*(\w+.*?)>$', re.S)

    @staticmethod
    def parse_str(type_str):
        if GTypeMap[type_str]:
            return GTypeMap[type_str]

        if '<' not in type_str or '>' not in type_str:
            return None

        if type_str.startswith('array'):
            return TypeParser._parse_array_type(type_str)
        elif type_str.startswith('list'):
            return TypeParser._parse_list_type(type_str)
        elif type_str.startswith('set'):
            return TypeParser._parse_set_type(type_str)
        elif type_str.startswith('map'):
            return TypeParser._parse_map_type(type_str)

        return None

    @staticmethod
    def parse(rows):
        type_rows = []
        enums = []
        structs = []
        for row in rows:
            if len(row) == 0 or row[0].strip() == '':
                # 空行结束定义
                if len(type_rows) > 0:
                    TypeParser._parse_rows(type_rows, enums, structs)
                    type_rows.clear()

                continue
            elif len(row) > 0:
                if len(type_rows) > 0:
                    # 已经找到定义
                    type_rows.append(row)
                elif row[0].strip().startswith('enum ') or row[0].strip().startswith('struct '):
                    # 定义开始
                    type_rows.append(row)

        if len(type_rows) > 0:
            TypeParser._parse_rows(type_rows, enums, structs)
            type_rows.clear()

        return enums, structs

    @staticmethod
    def parse_define_data(define_data):
        enums_data = define_data['enums']
        EnumParser.parse_define(enums_data)

        structs_data = define_data['structs']
        StructParser.parse_define(structs_data)

    @staticmethod
    def _parse_rows(rows, enums, structs):
        if 'enum' in rows[0][0]:
            enums.append(EnumParser.parse(rows))
        elif 'struct' in rows[0][0]:
            structs.append(StructParser.parse(rows))

    @staticmethod
    def _parse_array_type(type_str):
        m = TypeParser._ArrayRe.match(type_str)
        if not m:
            return None

        val_type_str = m[1]
        val_len_str = m[2]

        val_type = TypeParser.parse_str(val_type_str)
        if not val_type:
            return None

        return Array(val_type_str, val_len_str)

    @staticmethod
    def _parse_list_type(type_str):
        m = TypeParser._ListRe.match(type_str)
        if not m:
            return None

        val_type_str = m[1]
        val_type = TypeParser.parse_str(val_type_str)
        if not val_type:
            return None

        return List(val_type_str)

    @staticmethod
    def _parse_set_type(type_str):
        m = TypeParser._SetRe.match(type_str)
        if not m:
            return None

        val_type_str = m[1]
        val_type = TypeParser.parse_str(val_type_str)
        if not val_type:
            return None

        return Set(val_type_str)

    @staticmethod
    def _parse_map_type(type_str):
        m = TypeParser._MapRe.match(type_str)
        if not m:
            return None

        key_type_str = m[1]
        val_type_str = m[2]

        key_type = TypeParser.parse_str(key_type_str)
        val_type = TypeParser.parse_str(val_type_str)
        if not key_type or not val_type:
            return None

        return Map(key_type_str, val_type_str)
