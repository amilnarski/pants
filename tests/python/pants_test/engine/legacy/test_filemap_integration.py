# coding=utf-8
# Copyright 2016 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.base.file_system_project_tree import FileSystemProjectTree
from pants_test.pants_run_integration_test import PantsRunIntegrationTest


class FilemapIntegrationTest(PantsRunIntegrationTest):
  PATH_PREFIX = 'testprojects/tests/python/pants/file_sets/'
  TEST_EXCLUDE_FILES = {
    'a.py', 'aa.py', 'aaa.py', 'ab.py', 'aabb.py', 'test_a.py',
    'dir1/a.py', 'dir1/aa.py', 'dir1/aaa.py',
    'dir1/ab.py', 'dir1/aabb.py', 'dir1/dirdir1/a.py', 'dir1/dirdir1/aa.py', 'dir1/dirdir1/ab.py'
  }

  def setUp(self):
    super(FilemapIntegrationTest, self).setUp()

    project_tree = FileSystemProjectTree(os.path.abspath(self.PATH_PREFIX), ['BUILD', '.*'])
    scan_set = set()

    def should_ignore(file):
      return file.endswith('.pyc')

    for root, dirs, files in project_tree.walk(''):
      scan_set.update({os.path.join(root, f) for f in files if not should_ignore(f)})

    self.assertEquals(scan_set, self.TEST_EXCLUDE_FILES)

  def _mk_target(self, test_name):
    return '{}:{}'.format(self.PATH_PREFIX, test_name)

  def _extract_exclude_output(self, test_name):
    stdout_data = self.do_command('filemap',
                                  self._mk_target(test_name),
                                  success=True).stdout_data

    return {s.split(' ')[0].replace(self.PATH_PREFIX, '')
            for s in stdout_data.split('\n') if s.startswith(self.PATH_PREFIX)}

  def test_testprojects(self):
    self.do_command('filemap', 'testprojects::', success=True)

  def test_python_sources(self):
    run = self.do_command('filemap',
                          'testprojects/src/python/sources',
                          success=True)
    self.assertIn('testprojects/src/python/sources/sources.py', run.stdout_data)

  def test_exclude_invalid_string(self):
    build_path = os.path.join(self.PATH_PREFIX, 'BUILD.invalid')
    build_content = '''python_library(name='exclude_strings_disallowed',
                                      sources=rglobs('*.py', exclude='aa.py'))'''

    with self.temporary_file_content(build_path, build_content):
      pants_run = self.do_command('filemap',
                                  self._mk_target('exclude_strings_disallowed'),
                                  success=False)
      self.assertRegexpMatches(pants_run.stderr_data,
                               r'Excludes of type `.*` are not supported')

  def test_exclude_list_of_strings(self):
    test_out = self._extract_exclude_output('exclude_list_of_strings')
    self.assertEquals(self.TEST_EXCLUDE_FILES - {'aaa.py', 'dir1/aaa.py'},
                      test_out)

  def test_exclude_globs(self):
    test_out = self._extract_exclude_output('exclude_globs')
    self.assertEquals(self.TEST_EXCLUDE_FILES - {'aabb.py', 'dir1/dirdir1/aa.py'},
                      test_out)

  def test_exclude_strings(self):
    test_out = self._extract_exclude_output('exclude_strings')
    self.assertEquals(self.TEST_EXCLUDE_FILES - {'aa.py', 'ab.py'},
                      test_out)

  def test_exclude_set(self):
    test_out = self._extract_exclude_output('exclude_set')
    self.assertEquals(self.TEST_EXCLUDE_FILES - {'aaa.py', 'a.py'},
                      test_out)

  def test_exclude_rglobs(self):
    test_out = self._extract_exclude_output('exclude_rglobs')
    self.assertEquals(self.TEST_EXCLUDE_FILES - {'ab.py', 'aabb.py', 'dir1/ab.py', 'dir1/aabb.py', 'dir1/dirdir1/ab.py'},
                      test_out)

  def test_exclude_zglobs(self):
    test_out = self._extract_exclude_output('exclude_zglobs')
    self.assertEquals(self.TEST_EXCLUDE_FILES - {'ab.py', 'aabb.py', 'dir1/ab.py', 'dir1/aabb.py', 'dir1/dirdir1/ab.py'},
                      test_out)

  def test_exclude_composite(self):
    test_out = self._extract_exclude_output('exclude_composite')
    self.assertEquals(self.TEST_EXCLUDE_FILES -
                      {'a.py', 'aaa.py', 'dir1/a.py', 'dir1/dirdir1/a.py'},
                      test_out)

  def test_implicit_sources(self):
    test_out = self._extract_exclude_output('implicit_sources')
    self.assertEquals({'a.py', 'aa.py', 'aaa.py', 'aabb.py', 'ab.py'},
                      test_out)

    test_out = self._extract_exclude_output('test_with_implicit_sources')
    self.assertEquals({'test_a.py'}, test_out)
