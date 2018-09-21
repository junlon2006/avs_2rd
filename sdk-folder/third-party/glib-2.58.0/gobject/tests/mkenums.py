#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright © 2018 Endless Mobile, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301  USA

"""Integration tests for glib-mkenums utility."""

import collections
import os
import subprocess
import tempfile
import textwrap
import unittest

import taptestrunner


Result = collections.namedtuple('Result', ('info', 'out', 'err', 'subs'))


class TestMkenums(unittest.TestCase):
    """Integration test for running glib-mkenums.

    This can be run when installed or uninstalled. When uninstalled, it
    requires G_TEST_BUILDDIR and G_TEST_SRCDIR to be set.

    The idea with this test harness is to test the glib-mkenums utility, its
    handling of command line arguments, its exit statuses, and its handling of
    various C source codes. In future we could split the core glib-mkenums
    parsing and generation code out into a library and unit test that, and
    convert this test to just check command line behaviour.
    """

    def setUp(self):
        self.timeout_seconds = 10  # seconds per test
        self.tmpdir = tempfile.TemporaryDirectory()
        os.chdir(self.tmpdir.name)
        print('tmpdir:', self.tmpdir.name)
        if 'G_TEST_BUILDDIR' in os.environ:
            self.__mkenums = \
                os.path.join(os.environ['G_TEST_BUILDDIR'], '..',
                             'glib-mkenums')
        else:
            self.__mkenums = os.path.join('/', 'usr', 'bin', 'glib-mkenums')
        print('mkenums:', self.__mkenums)

    def tearDown(self):
        self.tmpdir.cleanup()

    def runMkenums(self, *args):
        argv = [self.__mkenums]
        argv.extend(args)
        print('Running:', argv)

        env = os.environ.copy()
        env['LC_ALL'] = 'C.UTF-8'
        print('Environment:', env)

        info = subprocess.run(argv, timeout=self.timeout_seconds,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              env=env)
        info.check_returncode()
        out = info.stdout.decode('utf-8').strip()
        err = info.stderr.decode('utf-8').strip()

        # Known substitutions for standard boilerplate
        subs = {
            'standard_top_comment':
                'This file is generated by glib-mkenums, do not modify '
                'it. This code is licensed under the same license as the '
                'containing project. Note that it links to GLib, so must '
                'comply with the LGPL linking clauses.',
            'standard_bottom_comment': 'Generated data ends here'
        }

        result = Result(info, out, err, subs)

        print('Output:', result.out)
        return result

    def runMkenumsWithTemplate(self, template_contents, *args):
        with tempfile.NamedTemporaryFile(dir=self.tmpdir.name,
                                         suffix='.template') as template_file:
            # Write out the template.
            template_file.write(template_contents.encode('utf-8'))
            print(template_file.name + ':', template_contents)
            template_file.flush()

            return self.runMkenums('--template', template_file.name, *args)

    def runMkenumsWithAllSubstitutions(self, *args):
        '''Run glib-mkenums with a template which outputs all substitutions.'''
        template_contents = '''
/*** BEGIN file-header ***/
file-header
/*** END file-header ***/

/*** BEGIN file-production ***/
file-production
filename: @filename@
basename: @basename@
/*** END file-production ***/

/*** BEGIN enumeration-production ***/
enumeration-production
EnumName: @EnumName@
enum_name: @enum_name@
ENUMNAME: @ENUMNAME@
ENUMSHORT: @ENUMSHORT@
ENUMPREFIX: @ENUMPREFIX@
type: @type@
Type: @Type@
TYPE: @TYPE@
/*** END enumeration-production ***/

/*** BEGIN value-header ***/
value-header
EnumName: @EnumName@
enum_name: @enum_name@
ENUMNAME: @ENUMNAME@
ENUMSHORT: @ENUMSHORT@
ENUMPREFIX: @ENUMPREFIX@
type: @type@
Type: @Type@
TYPE: @TYPE@
/*** END value-header ***/

/*** BEGIN value-production ***/
value-production
VALUENAME: @VALUENAME@
valuenick: @valuenick@
valuenum: @valuenum@
type: @type@
Type: @Type@
TYPE: @TYPE@
/*** END value-production ***/

/*** BEGIN value-tail ***/
value-tail
EnumName: @EnumName@
enum_name: @enum_name@
ENUMNAME: @ENUMNAME@
ENUMSHORT: @ENUMSHORT@
ENUMPREFIX: @ENUMPREFIX@
type: @type@
Type: @Type@
TYPE: @TYPE@
/*** END value-tail ***/

/*** BEGIN comment ***/
comment
comment: @comment@
/*** END comment ***/

/*** BEGIN file-tail ***/
file-tail
/*** END file-tail ***/
'''
        return self.runMkenumsWithTemplate(template_contents, *args)

    def runMkenumsWithHeader(self, h_contents, encoding='utf-8'):
        with tempfile.NamedTemporaryFile(dir=self.tmpdir.name,
                                         suffix='.h') as h_file:
            # Write out the header to be scanned.
            h_file.write(h_contents.encode(encoding))
            print(h_file.name + ':', h_contents)
            h_file.flush()

            # Run glib-mkenums with a template which outputs all substitutions.
            result = self.runMkenumsWithAllSubstitutions(h_file.name)

            # Known substitutions for generated filenames.
            result.subs.update({
                'filename': h_file.name,
                'basename': os.path.basename(h_file.name),
            })

            return result

    def assertSingleEnum(self, result, enum_name_camel, enum_name_lower,
                         enum_name_upper, enum_name_short, enum_prefix,
                         type_lower, type_camel, type_upper,
                         value_name, value_nick, value_num):
        """Assert that out (from runMkenumsWithHeader()) contains a single
           enum and value matching the given arguments."""
        subs = dict({
            'enum_name_camel': enum_name_camel,
            'enum_name_lower': enum_name_lower,
            'enum_name_upper': enum_name_upper,
            'enum_name_short': enum_name_short,
            'enum_prefix': enum_prefix,
            'type_lower': type_lower,
            'type_camel': type_camel,
            'type_upper': type_upper,
            'value_name': value_name,
            'value_nick': value_nick,
            'value_num': value_num,
        }, **result.subs)

        self.assertEqual('''
comment
comment: {standard_top_comment}


file-header
file-production
filename: {filename}
basename: {basename}
enumeration-production
EnumName: {enum_name_camel}
enum_name: {enum_name_lower}
ENUMNAME: {enum_name_upper}
ENUMSHORT: {enum_name_short}
ENUMPREFIX: {enum_prefix}
type: {type_lower}
Type: {type_camel}
TYPE: {type_upper}
value-header
EnumName: {enum_name_camel}
enum_name: {enum_name_lower}
ENUMNAME: {enum_name_upper}
ENUMSHORT: {enum_name_short}
ENUMPREFIX: {enum_prefix}
type: {type_lower}
Type: {type_camel}
TYPE: {type_upper}
value-production
VALUENAME: {value_name}
valuenick: {value_nick}
valuenum: {value_num}
type: {type_lower}
Type: {type_camel}
TYPE: {type_upper}
value-tail
EnumName: {enum_name_camel}
enum_name: {enum_name_lower}
ENUMNAME: {enum_name_upper}
ENUMSHORT: {enum_name_short}
ENUMPREFIX: {enum_prefix}
type: {type_lower}
Type: {type_camel}
TYPE: {type_upper}
file-tail

comment
comment: {standard_bottom_comment}
'''.format(**subs).strip(), result.out)

    def test_help(self):
        """Test the --help argument."""
        result = self.runMkenums('--help')
        self.assertIn('usage: glib-mkenums', result.out)

    def test_no_args(self):
        """Test running with no arguments at all."""
        result = self.runMkenums()
        self.assertEqual('', result.err)
        self.assertEquals('''/* {standard_top_comment} */


/* {standard_bottom_comment} */'''.format(**result.subs),
                          result.out.strip())

    def test_empty_template(self):
        """Test running with an empty template and no header files."""
        result = self.runMkenumsWithTemplate('')
        self.assertEqual('', result.err)
        self.assertEquals('''/* {standard_top_comment} */


/* {standard_bottom_comment} */'''.format(**result.subs),
                          result.out.strip())

    def test_no_headers(self):
        """Test running with a complete template, but no header files."""
        result = self.runMkenumsWithAllSubstitutions()
        self.assertEqual('', result.err)
        self.assertEquals('''
comment
comment: {standard_top_comment}


file-header
file-tail

comment
comment: {standard_bottom_comment}
'''.format(**result.subs).strip(), result.out)

    def test_empty_header(self):
        """Test an empty header."""
        result = self.runMkenumsWithHeader('')
        self.assertEqual('', result.err)
        self.assertEqual('''
comment
comment: {standard_top_comment}


file-header
file-tail

comment
comment: {standard_bottom_comment}
'''.format(**result.subs).strip(), result.out)

    def test_enum_name(self):
        """Test typedefs with an enum and a typedef name. Bug #794506."""
        h_contents = '''
        typedef enum _SomeEnumIdentifier {
          ENUM_VALUE
        } SomeEnumIdentifier;
        '''
        result = self.runMkenumsWithHeader(h_contents)
        self.assertEqual('', result.err)
        self.assertSingleEnum(result, 'SomeEnumIdentifier',
                              'some_enum_identifier', 'SOME_ENUM_IDENTIFIER',
                              'ENUM_IDENTIFIER', 'SOME', 'enum', 'Enum',
                              'ENUM', 'ENUM_VALUE', 'value', '0')

    def test_non_utf8_encoding(self):
        """Test source files with non-UTF-8 encoding. Bug #785113."""
        h_contents = '''
        /* Copyright © La Peña */
        typedef enum {
          ENUM_VALUE
        } SomeEnumIdentifier;
        '''
        result = self.runMkenumsWithHeader(h_contents, encoding='iso-8859-1')
        self.assertIn('WARNING: UnicodeWarning: ', result.err)
        self.assertSingleEnum(result, 'SomeEnumIdentifier',
                              'some_enum_identifier', 'SOME_ENUM_IDENTIFIER',
                              'ENUM_IDENTIFIER', 'SOME', 'enum', 'Enum',
                              'ENUM', 'ENUM_VALUE', 'value', '0')

    def test_reproducible(self):
        """Test builds are reproducible regardless of file ordering.
        Bug #691436."""
        template_contents = 'template'

        h_contents1 = '''
        typedef enum {
          FIRST,
        } Header1;
        '''

        h_contents2 = '''
        typedef enum {
          SECOND,
        } Header2;
        '''

        with tempfile.NamedTemporaryFile(dir=self.tmpdir.name,
                                         suffix='1.h') as h_file1, \
                tempfile.NamedTemporaryFile(dir=self.tmpdir.name,
                                            suffix='2.h') as h_file2:
            # Write out the headers.
            h_file1.write(h_contents1.encode('utf-8'))
            h_file2.write(h_contents2.encode('utf-8'))

            h_file1.flush()
            h_file2.flush()

            # Run glib-mkenums with the headers in one order, and then again
            # in another order.
            result1 = self.runMkenumsWithTemplate(template_contents,
                                                  h_file1.name, h_file2.name)
            self.assertEqual('', result1.err)

            result2 = self.runMkenumsWithTemplate(template_contents,
                                                  h_file2.name, h_file1.name)
            self.assertEqual('', result2.err)

            # The output should be the same.
            self.assertEqual(result1.out, result2.out)

    def test_no_nick(self):
        """Test trigraphs with a desc but no nick. Issue #1360."""
        h_contents = '''
        typedef enum {
          GEGL_SAMPLER_NEAREST = 0,   /*< desc="nearest"      >*/
        } GeglSamplerType;
        '''
        result = self.runMkenumsWithHeader(h_contents)
        self.assertEqual('', result.err)
        self.assertSingleEnum(result, 'GeglSamplerType',
                              'gegl_sampler_type', 'GEGL_SAMPLER_TYPE',
                              'SAMPLER_TYPE', 'GEGL', 'enum', 'Enum',
                              'ENUM', 'GEGL_SAMPLER_NEAREST', 'nearest', '0')

    def test_filename_basename_in_fhead_ftail(self):
        template_contents = '''
/*** BEGIN file-header ***/
file-header
filename: @filename@
basename: @basename@
/*** END file-header ***/

/*** BEGIN comment ***/
comment
comment: @comment@
/*** END comment ***/

/*** BEGIN file-tail ***/
file-tail
filename: @filename@
basename: @basename@
/*** END file-tail ***/'''
        result = self.runMkenumsWithTemplate(template_contents)
        self.assertEqual(
            textwrap.dedent(
                '''
                WARNING: @filename@ used in file-header section.
                WARNING: @basename@ used in file-header section.
                WARNING: @filename@ used in file-tail section.
                WARNING: @basename@ used in file-tail section.
                ''').strip(),
            result.err)
        self.assertEqual('''
comment
comment: {standard_top_comment}


file-header
filename: @filename@
basename: @basename@
file-tail
filename: @filename@
basename: @basename@

comment
comment: {standard_bottom_comment}
'''.format(**result.subs).strip(), result.out)


if __name__ == '__main__':
    unittest.main(testRunner=taptestrunner.TAPTestRunner())
