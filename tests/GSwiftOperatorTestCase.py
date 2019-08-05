from context import diffast, chunk_analysis

import unittest
import ast, os

class GSwiftOperatorTestCase(unittest.TestCase):

  def setUp(self):
    pass

  def tearDown(self):
    for key in sorted(self.c):
      print "%s: %s" % (self.c[key], key)


  def _get_chunks(self, a, b):
    a = ast.parse(a)
    b = ast.parse(b)
    diff_tree = diffast.diff(a, b)
    chunks = diffast.extract_chunks(diff_tree)
    for chunk in chunks:
      print '*'
      print chunk
      print '*'

    return chunks, diff_tree.before, diff_tree.after

  def test_omfc(self):
    chunks, before, after= self._get_chunks("""
a = 10
    ""","""
a = 10
f(a, 1, 'ciao')
    """)

    self.c= chunk_analysis.extract_features(chunks[0])

  def test_omviv(self):
    chunks, before, after= self._get_chunks("""
b = 4
    ""","""
b = 4
a = b
    """)

    self.c= chunk_analysis.extract_features(chunks[0])

  def test_omvae(self):
    chunks, before, after = self._get_chunks("""
a = 10
        """, """
a = 10
a = b + 5
        """)

    self.c= chunk_analysis.extract_features(chunks[0])

  def test_omia(self):
    chunks, before, after = self._get_chunks("""
a = f()
b = a + 1
        """, """
a = f()
if a:
  b = a + 1
        """)

    self.c= chunk_analysis.extract_features(chunks[0])

  def test_omieb(self):
    chunks, before, after = self._get_chunks("""
a = f()
        """, """
if a:
  b = a + 1
else:
  a = f()
        """)

    self.c= chunk_analysis.extract_features(chunks[0])

  def test_omlac(self):
    chunks, before, after = self._get_chunks("""
if a and b:
  f(a,b,c)
        """, """
if a and b and c:
  f(a,b,c) 
        """)

    self.c= chunk_analysis.extract_features(chunks[0])

  def test_omlpa(self):
    chunks, before, after = self._get_chunks("""
def largest_number(l):
  if l.size == 0:
    return None
  for item in l:
    if item > largest:
      largest = item
  return largest
def ciao():
  pass
        """, """
def largest_number(l):
  if l.size == 0:
    return None
  print "largest number in a list of", l.size, "elements"
  largest = l[0]
  for item in l:
    if item > largest:
      largest = item
  return largest
def ciao():
  pass
        """)

    self.c= chunk_analysis.extract_features(chunks[0])

  def test_owpfv(self):
    chunks, before, after = self._get_chunks("""
f(a, b, c)
        """, """
f(a, b, d)
        """)

    self.c = chunk_analysis.extract_features(chunks[0])

  def test_missing_nested_if(self):
    chunks, before, after = self._get_chunks("""
f(a, b, c)
            """, """
if a:
  if b:
    f(a, b, c)
            """)

    self.c = chunk_analysis.extract_features(chunks[0])

