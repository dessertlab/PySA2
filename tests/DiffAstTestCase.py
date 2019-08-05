from context import diffast

import unittest
import ast, os

class DiffAstTestCase(unittest.TestCase):

  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_no_module(self):
    with self.assertRaises(Exception):
      diffast.diff(None, None)
    with self.assertRaises(Exception):
      diffast.diff(ast.Module(body=[]), ast.Str(s="Module"))

  def test_diff_tree_obj(self):
    diff_tree = diffast.diff(ast.Module(body=[]), ast.Module(body=[]))
    self.assertIn("after", dir(diff_tree))
    self.assertIn("before", dir(diff_tree))

  def test_insert_stmt(self):
    a = ast.parse("""
print a
        """)
    b = ast.parse("""
print a
print b
        """)
    diff_tree = diffast.diff(a, b)
    self.assertEquals(diff_tree.after.body[1].diff_info, 'insert')

  def test_delete_stmt(self):
    a = ast.parse("""
print a
print b
      """)
    b = ast.parse("""
print a
      """)
    diff_tree = diffast.diff(a, b)
    self.assertEquals(diff_tree.before.body[1].diff_info, 'delete')

  def test_replace_stmt(self):
    a = ast.parse("""
print a
      """)
    b = ast.parse("""
print b
      """)
    diff_tree = diffast.diff(a, b)
    diffast.diff2html(diff_tree)
    self.assertEquals(diff_tree.after.body[0].diff_info, 'update')
    self.assertEquals(diff_tree.before.body[0].values[0].diff_info, 'delete')
    self.assertEquals(diff_tree.after.body[0].values[0].diff_info, 'insert')

  def test_insert_an_if(self):
    a = ast.parse("""
print a
print b
print c
          """)
    b = ast.parse("""
print a
if a > 10:
  print b
  print c
          """)
    diff_tree = diffast.diff(a, b)
    self.assertEquals(diff_tree.after.body[1].diff_info, 'insert')
    self.assertEquals(diff_tree.before.body[1].diff_info, 'delete')
    self.assertEquals(diff_tree.after.body[1].diff_info, 'insert')

  def test_insert_a_try(self):
    a = ast.parse("""
print a
print b
print c
              """)
    b = ast.parse("""
print a
try:
  print b
  print c
except:
  print d
              """)
    diff_tree = diffast.diff(a, b)
    diffast.diff2html(diffast.diff(a, b))
    self.assertEquals(diff_tree.after.body[1].diff_info, 'insert')
    self.assertEquals(diff_tree.before.body[1].diff_info, 'delete')
    self.assertEquals(diff_tree.after.body[1].diff_info, 'insert')

  def test_diff2html(self):
    a = ast.parse("""
class Ciao():
  def hola(self):
    print "hola"
""")
    b = ast.parse("""
class Hola():
  def hola(self):
    print "hola"
""")
    os.remove("diff_tree.html")
    self.assertFalse(os.path.isfile("diff_tree.html"))
    diffast.diff2html(diffast.diff(a, b))
    self.assertTrue(os.path.isfile("diff_tree.html"))

  def test_delete_an_if(self):
    a = ast.parse("""
a = 10
print a
if a > 5:
  print "ciao"
""")
    b = ast.parse("""
a = 10
print a
print "ciao"
""")
    diffast.diff2html(diffast.diff(a, b))
    self.assertTrue(os.path.isfile("diff_tree.html"))


