# python 3
# -*- coding: utf_8 -*-

import fnmatch
from mako.template import Template
from .type import *
from .parser import TypeParser
from .utils import cache_attr, Global, load_yaml_data


def get_type(sign, allow_none=False):
    if sign is None:
        raise Exception(f'No Type Handler of {sign}')

    val_type = TypeParser.parse_str(sign)
    if not val_type:
        if not allow_none:
            raise Exception(f'No Type Handler of {sign}, or invalid sign')
        else:
            return None

    return GTypeMap[sign]


class SignMap:
    def __init__(self, sign_data):
        self._language = 'cpp'
        self._normal_map = {}
        self._glob_map = []
        self._class_map = {}

        self.load_sign_data(sign_data)

    @property
    def language(self):
        return self._language

    def load_sign_data(self, sign_data):
        if sign_data:
            self._language = sign_data['language']
            self._load_normal_map(sign_data)
            self._load_glob_map(sign_data)
            self._load_class_map(sign_data)

    def get_sign_info(self, field, sign):
        if sign in self._normal_map:
            sign_type, sign_reader, sign_handler, sign_raw_type = self._normal_map[sign]
            if not sign_handler:
                sign_handler = get_type(sign_raw_type)
                self._normal_map[sign] = (sign_type, sign_reader, sign_handler, sign_raw_type)

            if sign_reader and '$' in sign_reader:
                sign_reader = Template(text=sign_reader).render(field=field, Type=sign_handler)

            return sign_type, sign_reader, sign_handler

        # find in glob map
        for glob_info in self._glob_map:
            glob_sign, glob_raw, glob_type, glob_reader = glob_info
            if not fnmatch.fnmatch(sign, glob_sign):
                continue

            sign_handler = self._get_sign_handler(get_type(sign), glob_raw)
            sign_type = Template(text=glob_type).render(Type=sign_handler)
            sign_reader = None
            if glob_reader:
                sign_reader = Template(text=glob_reader).render(field=field, Type=sign_handler)
            return sign_type, sign_reader, sign_handler

        # find in class map
        sign_real_handler = get_type(sign, True)
        if not sign_real_handler:
            return None, None, None

        if isinstance(sign_real_handler, Enum):
            raw_str, type_str, reader_str = self._class_map['enum']
        elif isinstance(sign_real_handler, Struct):
            raw_str, type_str, reader_str = self._class_map['struct']
        else:
            return None, None, None

        sign_handler = self._get_sign_handler(sign_real_handler, raw_str)
        sign_type = Template(text=type_str).render(Type=sign_handler)
        sign_reader = None
        if reader_str:
            sign_reader = Template(text=reader_str).render(field=field, Type=sign_handler)
        return sign_type, sign_reader, sign_handler

    @staticmethod
    def _get_sign_handler(handler, raw):
        if '$' in raw:
            handler_str = Template(text=raw).render(Type=handler)
            sign_handler = get_type(handler_str)
        else:
            sign_handler = get_type(raw)
        return sign_handler

    def _load_normal_map(self, sign_data):
        if 'normal' not in sign_data or sign_data['normal'] is None:
            return

        for sign_info in sign_data['normal']:
            sign = sign_info['sign']
            raw = sign_info['raw']
            sign_type = sign_info['type']
            reader = sign_info['reader']
            self._normal_map[sign] = (sign_type, reader, get_type(raw, True), raw)

    def _load_glob_map(self, sign_data):
        if 'glob' not in sign_data or sign_data['glob'] is None:
            return

        for sign_info in sign_data['glob']:
            sign = sign_info['sign']
            raw = sign_info['raw']
            sign_type = sign_info['type']
            reader = sign_info['reader']
            self._glob_map.append((sign, raw, sign_type, reader))

    def _load_class_map(self, sign_data):
        if 'class' not in sign_data or sign_data['class'] is None:
            return

        for sign_info in sign_data['class']:
            class_type = sign_info['class_type']
            raw = sign_info['raw']
            sign_type = sign_info['type']
            reader = sign_info['reader']
            self._class_map[class_type] = (raw, sign_type, reader)


def load_sign_map(filepath):
    data = load_yaml_data(filepath)
    if data:
        sign_map = SignMap(data)
        cache_attr(Global, 'language', sign_map.language)
        return cache_attr(Global, 'SignMap', sign_map)
    return None

