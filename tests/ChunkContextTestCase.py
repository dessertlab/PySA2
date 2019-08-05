from context import diffast, chunk_analysis

import unittest
import ast, os

class ChunkContextTestCase(unittest.TestCase):

  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_extract_insert_chunk(self):
    a = ast.parse("""
print a
print b
def foo():
  if c > b :
    print c
  print d
  print e
            """)
    b = ast.parse("""
print a
print b
def foo():
  if c > b :
    print b
    print c
  print d
  print e
  print f
            """)
    diff_tree = diffast.diff(a, b)
    chunks = diffast.extract_chunks(diff_tree)
    self.assertEquals(len(chunks), 2)


  def test_extract_delete_chunk(self):
    a = ast.parse("""
print a
print b
def foo():
  if c > b :
    print b
    print c
  print d
  print e
  print f
            """)
    b = ast.parse("""
print a
print b
def foo():
  if c > b :
    print c
  print d
  print e
            """)
    diff_tree = diffast.diff(a, b)
    diffast.diff2html(diff_tree)

    contexts = diffast.extract_chunks(diff_tree)
    self.assertEquals(len(contexts), 2)


  def test_extract_multiple_delete_chunk(self):
    a = ast.parse("""
print a
print b
if c > b :
  print b
  print c
  print d
  print e
if a > b :
  print a
""")
    b = ast.parse("""
print a
if c > b :
  print b
  print c
if a > b :
  print b
            """)
    diff_tree = diffast.diff(a, b)
    diffast.diff2html(diff_tree)
    contexts = diffast.extract_chunks(diff_tree)

    self.assertEquals(len(contexts), 3)


  def test_extract_modified_chunk(self):
    a = ast.parse("""
print a
    """)
    b = ast.parse("""
print b
    """)
    diff_tree = diffast.diff(a, b)
    diffast.diff2html(diff_tree)
    chunks = diffast.extract_chunks(diff_tree)
    for chunk in chunks:
      print chunk

  def test_extract_ctx(self):
    a = ast.parse("""
curr.get()
    """)
    b = ast.parse("""
current.get()
    """)
    diff_tree = diffast.diff(a, b)
    diffast.diff2html(diff_tree)
    chunks = diffast.extract_chunks(diff_tree)
    for chunk in chunks:
      print chunk
