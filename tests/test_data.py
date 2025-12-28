import os
import sys
import unittest
from textwrap import dedent

sys.path.insert(0, os.path.abspath('./src/sphinxnotes'))

from data.data import Field

class TestFieldParser(unittest.TestCase):

    # ==========================
    # Basic Types
    # ==========================
    
    def test_basic_scalar(self):
        f = Field.from_str('int')
        self.assertEqual(f.parse('123'), 123)
        
        f = Field.from_str('bool')
        self.assertTrue(f.parse('true'))
        self.assertTrue(f.parse('y'))
        self.assertFalse(f.parse('false'))

    # ==========================
    # Container Forms
    # ==========================

    def test_list_default_sep(self):
        # Your default list sep is ',' (comma)
        f = Field.from_str('list of int')
        self.assertEqual(f.parse('1, 2, 3'), [1, 2, 3])

    def test_words_form(self):
        # words sep is ' ' (arbitrary whitespace)
        f = Field.from_str('words of str')
        self.assertEqual(f.parse('a   b\tc'), ['a', 'b', 'c'])

    def test_lines_form(self):
        # lines sep is '\n'
        f = Field.from_str('lines of int')
        self.assertEqual(f.parse('1\n2\n3'), [1, 2, 3])

    # ==========================
    # Modifiers
    # ==========================

    def test_sep_by_override(self):
        # Override default comma with pipe
        f = Field.from_str("list of int, sep by '|'")
        self.assertEqual(f.parse('1|2|3'), [1, 2, 3])

    def test_sep_by_implies_list(self):
        # 'sep by' without form implies list
        f = Field.from_str("int, sep by ';'")
        self.assertEqual(f.parse('1; 2; 3'), [1, 2, 3])

    def test_required(self):
        f = Field.from_str('int, req')
        self.assertTrue(f.required)
        with self.assertRaisesRegex(ValueError, 'field is required'):
            f.parse('')
        with self.assertRaisesRegex(ValueError, 'field is required'):
            f.parse(None)

    # ==========================
    # Parsing Logic
    # ==========================

    def test_empty_input(self):
        # Optional scalar -> None
        self.assertIsNone(Field.from_str('int').parse(''))
        # Optional list -> []
        self.assertEqual(Field.from_str('list of int').parse(''), [])

    def test_quoted_separator(self):
        # Test quoted separator parsing in DSL
        f = Field.from_str("list of str, sep by ','")
        self.assertEqual(f.parse('a,b,c'), ['a', 'b', 'c'])

    def test_escaped_separator(self):
        # Test escaping \n in DSL
        f = Field.from_str(r"list of str, sep by '\n'")
        self.assertEqual(f.parse('a\nb'), ['a', 'b'])

    # ==========================
    # Errors
    # ==========================

    def test_unsupported_modifier(self):
        with self.assertRaisesRegex(ValueError, 'unsupported type'):
            Field.from_str('list of unknown')
            
        with self.assertRaisesRegex(ValueError, 'unknown modifier'):
            Field.from_str('int, random_mod')

if __name__ == '__main__':
    unittest.main()
