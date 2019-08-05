import sys, unittest

from DiffAstTestCase import DiffAstTestCase
from ChunkContextTestCase import ChunkContextTestCase
from ActualChangesTestCase import ActualChangesTestCase
from GSwiftOperatorTestCase import GSwiftOperatorTestCase

if __name__ == "__main__":
  my_suite = unittest.TestLoader().loadTestsFromTestCase(DiffAstTestCase)
  result = unittest.TextTestRunner(verbosity=3).run(my_suite)
  if not result.wasSuccessful():
    sys.exit(1)

  my_suite = unittest.TestLoader().loadTestsFromTestCase(ChunkContextTestCase)
  result = unittest.TextTestRunner(verbosity=3).run(my_suite)
  if not result.wasSuccessful():
    sys.exit(2)

  my_suite = unittest.TestLoader().loadTestsFromTestCase(ActualChangesTestCase)
  result = unittest.TextTestRunner(verbosity=3).run(my_suite)
  if not result.wasSuccessful():
    sys.exit(3)

  my_suite = unittest.TestLoader().loadTestsFromTestCase(GSwiftOperatorTestCase)
  result = unittest.TextTestRunner(verbosity=3).run(my_suite)
  if not result.wasSuccessful():
    sys.exit(4)
