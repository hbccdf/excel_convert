# python 3
# -*- coding: utf_8 -*-

import os
import subprocess
from zipfile import ZipFile


def get_cache_file(cache_dir):
    return cache_dir + "/version.txt"


def get_git_revision_hash(git_dir, reversion):
    hash = subprocess.check_output(['git', f'--git-dir={git_dir}/.git', 'rev-parse', f'HEAD~{reversion}'])
    return bytes.decode(hash).strip('\n')


def get_git_revision_branch(git_dir):
    branch = subprocess.check_output(['git', f'--git-dir={git_dir}/.git', 'rev-parse', "--abbrev-ref", 'HEAD'])
    return bytes.decode(branch).strip('\n')


def get_git_revision_commit_datetime(git_dir, reversion):
    commit_time = subprocess.check_output(['git', f'--git-dir={git_dir}/.git', 'log', '-1', '--format=%ci', f'HEAD~{reversion}'])
    return bytes.decode(commit_time).strip('\n')


def git_archive_reversion(git_dir, reversion, output_file):
    subprocess.check_call(['git', f'--git-dir={git_dir}/.git', 'archive', '--format=zip', '-o', f'{output_file}', f'HEAD~{reversion}'])


def git_is_dirty(git_dir):
    output = subprocess.check_output(['git', f'--git-dir={git_dir}/.git', 'status', '--short'])
    output = bytes.decode(output).strip()
    return output != ''


class GitVersion:
    def __init__(self, git_dir, reversion):
        self.git_dir = git_dir
        self.reversion = reversion

        self.archive_path = ''
        self.archive_file = ''
        self.extract_path = ''

        self.IsDirty = False

        if not self.git_dir:
            self._init()
            return

        self.Hash = get_git_revision_hash(git_dir, reversion)
        self._Branch = get_git_revision_branch(git_dir)
        self._CommitTime = get_git_revision_commit_datetime(git_dir, reversion)
        if reversion == 0:
            self.IsDirty = git_is_dirty(git_dir)

        self.Version = f'{self._Branch} | {self.Hash} | {self._CommitTime}'
        self.CodeHash = 'No'

        self.FullVersion = ''

    def _init(self):
        self.Hash = 'No'
        self._Branch = 'No'
        self._CommitTime = 'No'
        self.Version = 'No'
        self.CodeHash = 'No'
        self.FullVersion = 'No'

    def set_code_hash(self, code_hash):
        self.CodeHash = code_hash
        self.FullVersion = f'{self.CodeHash};{self.Version}'

    def archive_reversion(self, output_dir):
        output_file = output_dir + '/archived.zip'
        self.archive_path = output_dir
        self.archive_file = output_file
        self.extract_path = self.archive_path + '/archived'

        self.remove_files()
        git_archive_reversion(self.git_dir, self.reversion, output_file)

    def extract_files(self):
        with ZipFile(self.archive_file, 'r') as zip_ref:
            zip_ref.extractall(self.extract_path)

    def remove_files(self):
        if not os.path.exists(self.extract_path):
            return

        files = os.listdir(self.extract_path)
        for f in files:
            file_path = os.path.join(self.extract_path, f)
            if os.path.isfile(file_path) and '.xls' in f:
                os.remove(file_path)

        os.rmdir(self.extract_path)
        if os.path.exists(self.archive_file):
            os.remove(self.archive_file)


class VersionCache:
    def __init__(self, cache_dir):
        self.checked_hash = None
        self.checked_version = None
        self.version = None
        self.code_hash = None

        self._cache_dir = cache_dir
        self._load_cache()

    def _load_cache(self):
        if not self._cache_dir:
            return
        cache_version_file = os.path.join(self._cache_dir, 'version.txt')
        if not os.path.exists(cache_version_file):
            return

        with open(cache_version_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                strs = line.split('=')
                if len(strs) < 2:
                    continue

                key = strs[0].strip()
                val = strs[1].strip()

                if key == 'checked_hash':
                    self.checked_hash = val
                elif key == 'checked_version':
                    self.checked_version = val
                elif key == 'version':
                    self.version = val
                elif key == 'code_hash':
                    self.code_hash = val

    def save_cache(self, first_version, git_version):
        if not git_version or not first_version:
            return

        print('save cache')
        self.checked_hash = first_version.Hash
        self.checked_version = first_version.Version
        self.code_hash = git_version.CodeHash
        self.version = git_version.Version

        cache_version_file = os.path.join(self._cache_dir, 'version.txt')
        with open(cache_version_file, 'w') as f:
            f.write(f'checked_hash={self.checked_hash}\nchecked_version={self.checked_version}\n'
                    f'code_hash={self.code_hash}\nversion={self.version}')


class GitRef:
    def __init__(self, git_dir, max_revision, cache_dir):
        self.git_dir = git_dir
        self.first_version = None
        self.git_version = None
        self.prev_version = None
        self.max_revision = max_revision
        self.reversion = 0
        self.is_end = self.reversion >= self.max_revision
        self.cache_version = VersionCache(cache_dir)
        self.versions = []

        if not self.git_dir:
            self.git_version = GitVersion(None, 0)
            return

        self.read_version(self.reversion)

    def save_cache(self):
        prev_git_version = self.get_prev_git_version()
        self.cache_version.save_cache(self.first_version, prev_git_version)

    def read_version(self, reversion):
        if not self.git_dir or self.is_end:
            return
        try:
            self.prev_version = self.git_version
            self.git_version = GitVersion(self.git_dir, reversion)
            self.versions.append(self.git_version)
            self.reversion = reversion
        except Exception:
            self.is_end = True

        if not self.is_end:
            self.is_end = self.reversion >= self.max_revision

    def read_prev_version(self):
        self.read_version(self.reversion + 1)

    def set_code_hash(self, code_hash):
        self.git_version.set_code_hash(code_hash)

        if self.is_end:
            return

        if not self.first_version and not self.git_version.IsDirty:
            self.first_version = self.git_version

        if self.git_version.Hash == self.cache_version.checked_hash:
            self.is_end = True
            if not self.git_version.IsDirty or self.git_version.CodeHash == self.cache_version.code_hash:
                self.git_version = GitVersion(None, 0)
                self.git_version.Version = self.cache_version.version
                self.git_version.set_code_hash(self.cache_version.code_hash)
                if not self.hash_changed():
                    self.prev_version = self.git_version

    def hash_changed(self):
        if not self.prev_version or not self.git_version:
            return False

        if self.prev_version.CodeHash == '':
            return False

        if self.git_version.CodeHash == '':
            return False

        return self.prev_version.CodeHash != self.git_version.CodeHash

    def archive_reversion(self, output_dir):
        if self.git_version:
            self.git_version.archive_reversion(output_dir)

    def extract_files(self):
        if self.git_version:
            self.git_version.extract_files()

    def version(self):
        if self.git_version:
            return self.git_version.Version

        return 'No'

    def cur_git_version(self):
        return self.git_version

    def get_prev_git_version(self):
        if self.prev_version:
            return self.prev_version

        return self.git_version
