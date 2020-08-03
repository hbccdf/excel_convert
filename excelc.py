# python 3
# -*- coding: utf_8 -*-

import os
import sys
import argparse
import glob
import xlrd
from mako.template import Template

import core.type as tp
from core.git_version import GitVersion
from core.sign_map import load_sign_map
from excel_code.sheet import SheetRef, AllCode
from excel_code.data_writer import SimpleBinDataWriter, ThriftBinDataWriter, XmlDataWriter
from excel_code.data_writer import MetaDataWriter, MetaWithDescDataWriter, IDsDataWriter

_languages = ['cpp', 'csharp']

if getattr(sys, 'frozen', False):
    cwd = os.path.dirname(sys.executable)
else:
    cwd = os.path.dirname(__file__)

_writer_type = {
    'bin': lambda f: SimpleBinDataWriter(f),
    'thrift': lambda f: ThriftBinDataWriter(f),
    'xml': lambda f: XmlDataWriter(f),
    'meta': lambda f: MetaDataWriter(f),
    'meta_with_desc': lambda f: MetaWithDescDataWriter(f),
    'ids': lambda f: IDsDataWriter(f)
}

_writer_file_name = {
    'bin': 'tables.bytes',
    'thrift': 'tables.bytes',
    'xml': 'tables.xml',
    'meta': 'meta.xml',
    'meta_with_desc': 'meta_with_desc.xml',
    'ids': 'ids.xml'
}


def load_sheet_refs(folder, subdir):
    wildcard = os.path.join(folder, '*.xls*')
    sheet_refs = []

    subdir_path = None
    if subdir is not None and subdir != '':
        subdir_path = os.path.join(folder, subdir)

    files = []
    sub_files = []
    for file in glob.glob(wildcard):
        _, filename = os.path.split(file)
        if filename.startswith('~$'):
            continue

        if subdir_path and os.path.exists(subdir_path):
            subdir_file = os.path.join(subdir_path, filename)
            if os.path.exists(subdir_file):
                print(f'subdir {subdir} file: {subdir_file}')
                file = subdir_file
                sub_files.append(subdir_file)

        files.append(file)

    if subdir_path and os.path.exists(subdir_path):
        wildcard = os.path.join(subdir_path, '*.xls*')

        for file in glob.glob(wildcard):
            _, filename = os.path.split(file)
            if filename.startswith('~$'):
                continue

            if file in sub_files:
                continue

            files.append(file)

    for file in files:
        _, filename = os.path.split(file)
        with xlrd.open_workbook(file, ragged_rows=True) as book:
            sheets = []
            for sheet in book.sheets():
                if sheet.name.startswith('Sheet') or sheet.name.startswith('$'):
                    continue

                sheets.append(sheet)

            if len(sheets) > 0:
                sheet_refs.append(SheetRef(file, filename, sheets))

    return sheet_refs


def load_excel_files(excel_dir, subdir):
    print('/> load excels ...')
    sheet_refs = load_sheet_refs(excel_dir, subdir)
    if len(sheet_refs) <= 0:
        raise Exception(f'can not find excels in dir : {excel_dir}')

    for sh in sheet_refs:
        print(f'find sheet : {sh.book_name} >> {sh.name}')

    return sheet_refs


def load_sheets(sheet_refs, define_file, test_data, namespace):
    define_path = os.path.join(cwd, define_file)
    all_code = AllCode(sheet_refs, define_path, test_data, namespace)
    return all_code


def write_data(all_code, filepath, git_version, writer_name, show_test_data):
    version = git_version.Version
    if show_test_data:
        print(f'data version is: {version}')

    if writer_name not in _writer_type:
        raise Exception(f'invalid writer_type {writer_name}, support {_writer_type.keys()}')

    writer = _writer_type[writer_name](filepath)

    writer.write_begin()
    writer.write_version(version)

    for sh in all_code.sheets:
        sh.write_data(writer, show_test_data)

    writer.write_end()
    writer.write_file()


def write_code(all_code, code_fold, language):
    print('/> load templates ...')
    wildcard = os.path.join(cwd, f'templates\\{language}\\*.*')
    templates = glob.glob(wildcard)
    if len(templates) <= 0:
        raise Exception(f'load templates error : no file by {wildcard}')

    for t in templates:
        print(t)

    for template in templates:
        basename = os.path.basename(template)
        if basename == "CSCfgVersion.h":
            continue

        engine = Template(filename=template)
        content = engine.render(all=all_code)
        filepath = os.path.join(code_fold, basename)
        with open(filepath, 'wb') as ofp:
            ofp.write(content.encode('gbk'))


def write_code_version(code_fold, git_version, language):
    version_file = os.path.join(cwd, f'templates\\{language}\\CSCfgVersion.h')
    if not os.path.exists(version_file):
        return

    filepath = os.path.join(code_fold, 'CSCfgVersion.h')
    engine = Template(filename=version_file)
    with open(filepath, 'wb') as ofp:
        content = engine.render(git=git_version)
        ofp.write(content.encode())


def load_data(language, excel_dir, subdir, define_file, test_data, namespace):
    print('/> load language config ...')
    filepath = os.path.join(cwd, 'templates', f'{language}.yml')
    sign_map = load_sign_map(filepath)
    if not sign_map:
        raise Exception(f'load language config error : {filepath}')

    print(filepath)

    sheet_refs = load_excel_files(excel_dir, subdir)

    print('/> start loading..')
    all_code = load_sheets(sheet_refs, define_file, test_data, namespace)

    return all_code


def mk_dirs(opts):
    if not os.path.exists(opts.code):
        os.makedirs(opts.code)

    bin_dir = os.path.dirname(opts.bin)
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)


def update_excel(all_code, configs):
    print('> update excel')
    for sh in all_code.sheets:
        if configs and sh.name not in configs:
            continue

        sh.update_data()


def execute(opts):
    mk_dirs(opts)
    git_dir = opts.git_dir
    git_version = None

    if git_dir and opts.generate_version:
        if os.path.exists(git_dir):
            print(git_dir)
            git_version = GitVersion(git_dir, 0)
        else:
            print(f'git path not exist: {git_dir}')

    if git_version is None:
        git_version = GitVersion(None, 0)

    if opts.encoding:
        tp.StringEncodingOfPack = opts.encoding

    all_code = load_data(opts.language, opts.exceldir, opts.subdir, opts.define, opts.test_data, opts.namespace)

    if opts.update_excel:
        update_excel(all_code, opts.configs)
        return

    print('/> writing code ...')
    write_code(all_code, opts.code, opts.language)
    write_code_version(opts.code, git_version, opts.language)

    print('/> writing binary ...')
    for i, writer_name in enumerate(opts.writers):
        print(f'data writer name: {writer_name}')
        if i == 0:
            write_data(all_code, opts.bin, git_version, writer_name, True)
        elif writer_name in _writer_file_name:
            file_path = os.path.join(opts.code, _writer_file_name[writer_name])
            write_data(all_code, file_path, git_version, writer_name, False)


def default_opts(opts):
    print('/> checking arguments...')
    if not os.path.exists(opts.exceldir):
        raise Exception(f'excel dir not exists : {opts.exceldir}')

    if not opts.define:
        opts.define = 'templates/define.yml'

    if opts.language == 'cpp':
        if not opts.encoding:
            opts.encoding = 'gbk'
        if not opts.writers or len(opts.writers) == 0:
            opts.writers = ['thrift']
    elif opts.language == 'csharp':
        if not opts.encoding:
            opts.encoding = 'utf-8'
        if not opts.writers or len(opts.writers) == 0:
            opts.writers = ['bin']

    if not opts.test_data:
        opts.test_data = os.path.join(opts.exceldir, 'data.yml')

    if not opts.code:
        opts.code = f'.test{opts.language}'

    if not opts.bin:
        opts.bin = os.path.join(opts.code, 'tables.bytes')


def run(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--exceldir', type=str,
                        help='folder of excel files (xls, xlsx).')

    parser.add_argument('--subdir', type=str,
                        help='sub dir of excel files')

    parser.add_argument('--define', type=str,
                        help='file path of define')

    parser.add_argument('--encoding', type=str,
                        help='encoding of string data')

    parser.add_argument('--bin', type=str,
                        help='output binary file path.')

    parser.add_argument('--code', type=str,
                        help='output code folder path.')

    parser.add_argument('--language', type=str,
                        help='code language : csharp or cpp.')

    parser.add_argument('--cache', type=str,
                        help='cache dir')

    parser.add_argument('--git_dir', type=str,
                        help='the .git dir of config repo')

    parser.add_argument('--generate_version', action='store_true',
                        help='generate config version or not')

    parser.add_argument('--test_data', type=str,
                        help='test data')

    parser.add_argument('--writers', type=str, nargs='*',
                        help='data writers')

    parser.add_argument('--update_excel', action='store_true',
                        help='write test data to excel')
                        
    parser.add_argument('--configs', type=str,
                        help='configs to update data')
                        
    parser.add_argument('--namespace', type=str, default='Generated',
                        help='set namespace to allcode for output code.')

    opts, unparsed = parser.parse_known_args(args=args)
    default_opts(opts)
    execute(opts)


if __name__ == '__main__':
    in_args = [
        '--exceldir',
        'E:/configs',
        # 'data',
        '--language',
        'cpp',
        '--writers',
        'thrift'
    ]
	
	# run(in_args)
    run(None)
