#! python 3
# -*- coding: utf_8 -*-
import os
import yaml


def process_setting(setting_str, language):
    dict = {}

    if not setting_str or setting_str == '':
        return dict

    setting = setting_str.replace('\n', '|')
    settings = setting.split('|')
    if len(settings) == 0:
        return dict

    for s in settings:
        s = s.strip()

        # 判断是否是针对当前language的设置
        language_setting = s.split(':')
        if len(language_setting) > 1:
            setting_language = language_setting[0].strip()
            if setting_language != language:
                continue
            s = language_setting[1].strip()

        vals = s.split('=')
        key = vals[0].strip()
        if key == '':
            continue

        val = None
        if len(vals) > 1:
            val = vals[1].strip()

        dict[key] = val

    return dict


def xml2py(node):
    """
    convert xml to python object
    node: xml.etree.ElementTree object
    import xml.etree.ElementTree as ET
    menza_xml_tree = ET.fromstring(xml_str)
    """

    name = node.tag

    py_type = type(name, (object,), {})
    py_obj = py_type()

    for attr in node.attrib.keys():
        setattr(py_obj, attr, node.get(attr))

    if node.text and node.text != '' and node.text != ' ' and node.text != '\n':
        setattr(py_obj, 'text', node.text)

    for cn in node:
        if not hasattr(py_obj, cn.tag):
            setattr(py_obj, cn.tag, [])
        getattr(py_obj, cn.tag).append(xml2py(cn))

    return py_obj


def cache_attr(obj, name, val):
    if not hasattr(obj, name):
        setattr(obj, name, val)
    return val


def cache_attr_function(obj, name, function):
    """add and cache an object member which is the result of a given function.
    This is for implementing lazy getters when the function call is expensive."""
    if hasattr(obj, name):
        val = getattr(obj, name)
    else:
        val = function()
        setattr(obj, name, val)
    return val


class _GlobalInfo:
    pass


Global = _GlobalInfo()


def get_key_value(data_dict, key, default):
    if key not in data_dict or data_dict[key] is None:
        return default

    return data_dict[key]


def get_list_value(value_list, index, default):
    if index >= len(value_list) or value_list[index] is None:
        return default

    return value_list[index]


def is_valid_language(languages):
    if languages and languages != '' and Global.language not in languages:
        return False

    return True


def load_yaml_data(data_file):
    if not os.path.exists(data_file):
        return None

    with open(data_file, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(e)
    return None


def parse_value_map(value_map_str):
    assert isinstance(value_map_str, str)
    map_start = -1
    names = []
    if '$' not in value_map_str:
        return names

    for i in range(len(value_map_str)):
        c = value_map_str[i]
        if i + 1 < len(value_map_str):
            if c == '$' and value_map_str[i + 1] == '{':
                assert map_start == -1
                map_start = i
                continue
        if c == '}' and map_start != -1:
            # find
            name = value_map_str[map_start + 2:i]
            names.append(name)
            map_start = -1

    return names


def remove_quoted(string, escape_char='\\', quote_chars='\'"'):
    out = []
    i = 0
    l = len(string)
    while i < l:
        is_escaped = (i + 1 < l and string[i] == escape_char and string[i + 1] in escape_char)
        c = string[i]
        if is_escaped:
            out.append(string[i + 1])
            i += 2
        else:
            if c not in quote_chars:
                out.append(c)
            i += 1

    return ''.join(out)


def is_split_char(c, split_char):
    if split_char == ',':
        return c == split_char or c == '，'
    else:
        return c == split_char


def parse_value_list(value_str, split_char=','):
    assert isinstance(value_str, str)

    value_str = value_str.strip()
    value_list = []
    start = 0
    end = -1
    if value_str == '':
        return value_list

    if value_str[start] == '(' and value_str[end] == ')':
        start = 1
        value = value_str[start:end]
        value_list.append(value.strip())
        return value_list

    if value_str[start] == '{' and value_str[end] == '}':
        start = 1
    elif value_str[start] == '[' and value_str[end] == ']':
        start = 1

    if start > 0:
        value_str = value_str[start:end]
    i = 0
    l = len(value_str)
    prev = 0
    escape_map = {'{': '}', '[': ']', '(': ')', '\'': '\'', '"': '"'}
    escape_chars = []
    cur_escape_char = None
    while i < l:
        is_escaped = (i < l and value_str[i - 1] == '\\')
        if is_escaped:
            i += 1
            continue

        c = value_str[i]
        if c in '{[("\'':
            if cur_escape_char:
                escape_chars.append(cur_escape_char)
            cur_escape_char = c
            i += 1
            continue

        if cur_escape_char and c == escape_map[cur_escape_char]:
            if len(escape_chars) == 0:
                cur_escape_char = None
            else:
                cur_escape_char = escape_chars.pop()
            i += 1
            if i == l:
                value = value_str[prev:]
                value_list.append(value.strip())
            continue

        if not cur_escape_char and (is_split_char(c, split_char) or i + 1 == l):
            if i + 1 == l:
                value = value_str[prev:]
            else:
                value = value_str[prev:i]
            value_list.append(value.strip())
            prev = i + 1

        i += 1

    return value_list


def find_any_char_in_string(str_value, chars):
    for c in chars:
        if c in str_value:
            return True

    return False


def find_all_char_in_string(str_value, chars):
    for c in chars:
        if c not in str_value:
            return False

    return True


def expand_array_value(val, max_length=0):
    value_list = []
    if not isinstance(val, str):
        value_list.append(val)
        return value_list, False

    value = val.strip()
    if find_any_char_in_string(value, '{[("\'') or not find_all_char_in_string(value, '<->'):
        value_list.append(value)
        return value_list, False

    node_list = []

    is_need_expand = False
    begin_value = ''
    end_value = ''
    prev = 0
    l = len(value)
    for i in range(l):
        c = value[i]
        if not is_need_expand:
            if c == '<':
                is_need_expand = True
                node = value[prev:i]
                node_list.append(node)
                prev = i + 1
            elif i + 1 == l:
                node = value[prev:]
                node_list.append(node)

        else:
            if c == '-':
                begin_value = value[prev:i]
                prev = i + 1
            elif c == '>':
                end_value = value[prev:i]
                is_need_expand = False
                prev = i + 1
                node = (begin_value, end_value)
                node_list.append(node)

    tuple_count = 0
    begin = 0
    end = 0
    for node in node_list:
        if isinstance(node, tuple):
            tuple_count += 1
            if tuple_count > 1:
                raise Exception(f'not support more expand node in expend_array {value}')

            begin_value, end_value = node
            begin_value = begin_value.strip()
            end_value = end_value.strip()
            if begin_value == '' or end_value == '':
                raise Exception(f'invalid expend node ({begin_value} - {end_value}) in expand_array {value}')

            begin = int(begin_value)
            end = int(end_value)

    # head_list = []
    # tail_list = []
    # for node in node_list:
    #     if isinstance(node, tuple):
    #         head_list.append(node[0].strip())
    #         tail_list.append(node[1].strip())
    #     else:
    #         head_list.append(node)
    #         tail_list.append(node)
    #
    # head_value = int(''.join(head_list))
    # tail_value = int(''.join(tail_list))

    head_value = begin
    tail_value = end
    step = 1
    if head_value > tail_value:
        step = -1
        tail_value = tail_value - 1
    else:
        step = 1
        tail_value = tail_value + 1

    step_length = abs(head_value - tail_value)
    if 0 < max_length < step_length:
        raise Exception(
            f'the length {step_length} is more than {max_length}, expend node ({head_value} - {tail_value}) in expand_array {value}')

    for i in range(head_value, tail_value, step):
        result_list = []
        for node in node_list:
            if isinstance(node, tuple):
                result_list.append(f'{i}')
            else:
                result_list.append(node)

        result = int(''.join(result_list))
        value_list.append(result)

    return value_list, True


def expend_array(value_list, max_expend_length=0):
    result = []
    is_result_expend = False
    for value in value_list:
        expend_list, is_expend = expand_array_value(value, max_expend_length)
        result.extend(expend_list)
        if is_expend:
            is_result_expend = True

    # if is_result_expend:
    #     print(f'val {value_list}, expend to {result}')
    return result


class obj(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [obj(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, obj(b) if isinstance(b, dict) else b)


if __name__ == '__main__':
    test_value = '11<45000-44450>33'
    value_list_result = expand_array_value(test_value)
    print(value_list_result)
