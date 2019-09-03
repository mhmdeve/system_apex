#!/usr/bin/env python
#
# Copyright (C) 2019 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""deapexer is a tool that prints out content of an APEX.

To print content of an APEX to stdout:
  deapexer foo.apex

To diff content of an APEX with expected whitelist:
  deapexer foo.apex foo_whitelist.txt
"""

import shutil
import subprocess
import tempfile
import os
import zipfile


class ApexImageEntry(object):

  def __init__(self, name, base_dir, permissions, is_directory=False, is_symlink=False):
    self._name = name
    self._base_dir = base_dir
    self._permissions = permissions
    self._is_directory = is_directory
    self._is_symlink = is_symlink

  @property
  def name(self):
    return self._name

  @property
  def full_path(self):
    return os.path.join(self._base_dir, self._name)

  @property
  def is_directory(self):
    return self._is_directory

  @property
  def is_symlink(self):
    return self._is_symlink

  @property
  def is_regular_file(self):
    return not self.is_directory and not self.is_symlink

  @property
  def permissions(self):
    return self._permissions

  def __str__(self):
    ret = ''
    if self._is_directory:
      ret += 'd'
    elif self._is_symlink:
      ret += 'l'
    else:
      ret += '-'

    def mask_as_string(m):
      ret = 'r' if m & 4 == 4 else '-'
      ret += 'w' if m & 2 == 2 else '-'
      ret += 'x' if m & 1 == 1 else '-'
      return ret

    ret += mask_as_string(self._permissions >> 6)
    ret += mask_as_string((self._permissions >> 3) & 7)
    ret += mask_as_string(self._permissions & 7)

    return ret + ' ' + self._name


class ApexImageDirectory(object):

  def __init__(self, path, entries, apex):
    self._path = path
    self._entries = sorted(entries, key=lambda e: e.name)
    self._apex = apex

  def list(self, is_recursive=False):
    for e in self._entries:
      yield e
      if e.is_directory and e.name != '.' and e.name != '..':
        for ce in self.enter_subdir(e).list(is_recursive):
          yield ce

  def enter_subdir(self, entry):
    return self._apex._list(self._path + '/' + entry.name)


class Apex(object):

  def __init__(self, apex):
    self._debugfs = '%s/bin/debugfs' % os.environ['ANDROID_HOST_OUT']
    self._apex = apex
    self._tempdir = tempfile.mkdtemp()
    # TODO(b/139125405): support flattened APEXes.
    with zipfile.ZipFile(self._apex, 'r') as zip_ref:
      self._payload = zip_ref.extract('apex_payload.img', path=self._tempdir)
    self._cache = {}

  def __del__(self):
    shutil.rmtree(self._tempdir)

  def __enter__(self):
    return self._list('.')

  def __exit__(self, type, value, traceback):
    pass

  def _list(self, path):
    if path in self._cache:
      return self._cache[path]
    process = subprocess.Popen([self._debugfs, '-R', 'ls -l -p %s' % path, self._payload],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True)
    stdout, _ = process.communicate()
    res = str(stdout)
    entries = []
    for line in res.split('\n'):
      if not line:
        continue
      parts = line.split('/')
      if len(parts) != 8:
        continue
      name = parts[5]
      if not name:
        continue
      bits = parts[2]
      entries.append(ApexImageEntry(name, base_dir=path, permissions=int(bits[3:], 8),
                                    is_directory=bits[1]=='4', is_symlink=bits[1]=='2'))
    return ApexImageDirectory(path, entries, self)


def main(argv):
  apex_content = []
  with Apex(argv[0]) as apex_dir:
    for e in apex_dir.list(is_recursive=True):
      if e.is_regular_file:
        apex_content.append(e.full_path)
  if len(argv) > 1:
    # diffing
    with open(argv[1], 'r') as f:
      whitelist = set([line.rstrip() for line in f.readlines()])
      diff = []
      for line in apex_content:
        if line not in whitelist:
          diff.append(line)
      if diff:
        print('%s contains following unexpected entries:\n%s' % (argv[0], '\n'.join(diff)))
        sys.exit(1)
  else:
    for line in apex_content:
      print(line)


if __name__ == '__main__':
  main(sys.argv[1:])