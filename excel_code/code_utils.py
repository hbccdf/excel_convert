#! python 3
# -*- coding: utf_8 -*-
from .field import SheetField
from core.utils import Global, get_key_value


def load_define_data(sheet, define_data):
    fields = []

    if 'sheets' not in define_data or sheet.name not in define_data['sheets']:
        return fields

    sheet_define = define_data['sheets'][sheet.name]
    if 'fields' not in sheet_define:
        return fields

    for field_dict in sheet_define['fields']:
        language = get_key_value(field_dict, 'language', None)
        if language and Global.language not in language:
            continue

        field_name = field_dict['name']
        field_sign = field_dict['sign']
        field_desc = get_key_value(field_dict, 'desc', '')
        new_dict = {}
        for key, val in field_dict.items():
            if key not in ['name', 'sign', 'desc', 'language']:
                new_dict[key] = val

        props = get_key_value(field_dict, 'props', {})
        for key, val in props.items():
            new_dict[key] = val

        f = SheetField(sheet, field_name, field_sign, field_desc, -1, 0, '', new_dict)
        fields.append(f)

    return fields


def load_maps(sheet, define_data):
    fields = []
    if 'maps' not in define_data or sheet.name not in define_data['maps']:
        return fields

    sheet_maps = define_data['maps'][sheet.name]
    if 'fields' not in sheet_maps:
        return fields

    for field_dict in sheet_maps['fields']:
        language = get_key_value(field_dict, 'language', None)
        if language and Global.language not in language:
            continue

        field_name = field_dict['name']
        field_sign = field_dict['sign']
        field_desc = get_key_value(field_dict, 'desc', '')
        new_dict = {}
        for key, val in field_dict.items():
            if key not in ['name', 'sign', 'desc', 'language']:
                new_dict[key] = val

        props = get_key_value(field_dict, 'props', {})
        for key, val in props.items():
            new_dict[key] = val

        f = SheetField(sheet, field_name, field_sign, field_desc, -1, 0, '', new_dict)
        fields.append(f)

    return fields