#! python 3
# -*- coding: utf_8 -*-
from .sheet import DataStream
import core.type as tp


class BaseDataWriter:
    def __init__(self, file_name):
        self._file_name = file_name

    def write_file(self):
        pass

    def write_begin(self):
        pass

    def write_end(self):
        pass

    def write_version(self, version):
        pass

    def write_sheet_begin(self, sheet, row_len):
        pass

    def write_sheet_end(self, sheet):
        pass

    def write_row_begin(self, sheet, row_index, row_count):
        pass

    def write_row_end(self, sheet, row_index, row_count):
        pass

    def write_field_begin(self, field):
        pass

    def write_field_end(self, field):
        pass


class SimpleBinDataWriter(BaseDataWriter):
    def __init__(self, file_name):
        super().__init__(file_name)
        self._stream = DataStream()

    def _write(self, bin_bytes):
        self._stream.write(bin_bytes)

    def write_file(self):
        with open(self._file_name, 'wb') as fp:
            fp.write(self._stream.data_bytes)

    def write_begin(self):
        tp.PackTType = False

    def write_version(self, version):
        self._write(tp.String.pack_value(version))

    def write_sheet_begin(self, sheet, row_len):
        self._write(tp.Int.pack_value(row_len))

    def write_field_begin(self, field):
        field.pack_data(self._stream)


class ThriftBinDataWriter(SimpleBinDataWriter):
    def __init__(self, file_name):
        super().__init__(file_name)
        self._full_stream = DataStream()

    def write_file(self):
        with open(self._file_name, 'wb') as fp:
            fp.write(self._full_stream.data_bytes)

    def write_begin(self):
        tp.PackTType = True

    def write_version(self, version):
        self._full_stream.write(tp.String.pack_value(version))

    def write_sheet_begin(self, sheet, row_len):
        self._full_stream.write(tp.String.pack_value(sheet.name))
        self._full_stream.write(tp.Int.pack_value(row_len))

    def write_sheet_end(self, sheet):
        data_bytes = self._stream.data_bytes
        self._full_stream.write(tp.Int.pack_value(len(data_bytes)))
        self._full_stream.write(data_bytes)

        self._stream = DataStream()

    def write_row_end(self, sheet, row_index, row_count):
        self._write(tp.Int8.pack_value(tp.TType.STOP.value))


class BaseXmlDataWriter(BaseDataWriter):
    def __init__(self, file_name):
        super().__init__(file_name)
        self._lines = []

    @staticmethod
    def _get_indent_content(indent):
        current_line = ''
        i = 0
        while i < indent:
            current_line += '    '
            i = i + 1
        return current_line

    def _write(self, line, indent=0):
        current_line = self._get_indent_content(indent)
        self._lines.append(f'{current_line}{line}')

    def write_file(self):
        content = '\n'.join(self._lines)
        with open(self._file_name, 'w') as fp:
            fp.write(content)

    def write_begin(self):
        self._write('<root>')

    def write_end(self):
        self._write('</root>')

    def write_version(self, version):
        self._write(f'<version>{version}</version>', 1)


class XmlDataWriter(BaseXmlDataWriter):
    def __init__(self, file_name):
        super().__init__(file_name)

    def write_sheet_begin(self, sheet, row_len):
        self._write('')
        self._write(f'<{sheet.member_name}>', 1)

    def write_sheet_end(self, sheet):
        self._write(f'</{sheet.member_name}>', 1)

    def write_row_begin(self, sheet, row_index, row_count):
        self._write(f'<{sheet.name}>', 2)

    def write_row_end(self, sheet, row_index, row_count):
        self._write(f'</{sheet.name}>', 2)

    def write_field_begin(self, field):
        self._write(f'<{field.name}>{field.value_data}</{field.name}>', 3)


class MetaDataWriter(BaseXmlDataWriter):
    def __init__(self, file_name):
        super().__init__(file_name)
        self._ids = []

    def write_sheet_begin(self, sheet, row_len):
        self._write('')
        self._write(f'<{sheet.name}>', 1)

        self._write(f'<fields>', 2)
        for field in sheet.fields:
            self._write(f'<{field.name}>{field.desc}</{field.name}>', 3)

        self._write(f'</fields>', 2)

    def write_sheet_end(self, sheet):
        ids_str = ''
        if len(self._ids) > 0:
            ids_str = ','.join(self._ids)

        self._write(f'<ids>{ids_str}</ids>', 2)

        self._ids.clear()

        self._write(f'</{sheet.name}>', 1)

    def write_row_end(self, sheet, row_index, row_count):
        if not sheet.single:
            row_id = sheet.key_field.value_data
            self._ids.append(str(row_id))


class MetaWithDescDataWriter(MetaDataWriter):
    def __init__(self, file_name):
        super().__init__(file_name)
        self._current_desc = ''

    def write_sheet_end(self, sheet):
        self._write('<ids>', 2)
        for row_id, desc in self._ids:
            self._write(f'<{row_id}>{desc}</{row_id}>', 3)
        self._write('</ids>', 2)

        self._write(f'</{sheet.name}>', 1)

        self._ids.clear()
        self._current_desc = ''

    def write_row_end(self, sheet, row_index, row_count):
        if not sheet.single:
            row_id = sheet.key_field.value_data
            id_data = (row_id, self._current_desc)
            self._ids.append(id_data)

            self._current_desc = ''

    def write_field_begin(self, field):
        if field.name in ['desc', 'name', 'Desc', 'Name', 'Player_Name']:
            self._current_desc = field.value_data


class IDsDataWriter(MetaWithDescDataWriter):
    def __init__(self, file_name):
        super().__init__(file_name)

    def write_sheet_begin(self, sheet, row_len):
        self._write('')
        self._write(f'<{sheet.name}>', 1)
