from context import diffast
from context import chunk_analysis

import unittest
import ast, os
import pickle


# https://review.openstack.org/#/c/570741/2/manila/share/drivers/quobyte/quobyte.py
class ActualChangesTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_contexts_quobyte(self):
        with open(os.path.join("change_522209", "before_quobyte.py"), "r") as f:
            self.faulty_tree = ast.parse(f.read())
        with open(os.path.join("change_522209", "after_quobyte.py"), "r") as f:
            self.fixed_tree = ast.parse(f.read())

        diff_tree = diffast.diff(self.faulty_tree, self.fixed_tree)
        diffast.diff2html(diff_tree)
        chunks = diffast.extract_chunks(diff_tree)

        self.assertEquals(len(chunks), 4)

    def test_contexts_jsonrpc(self):
        with open(os.path.join("change_522209", "before_jsonrpc.py"), "r") as f:
            self.faulty_tree = ast.parse(f.read())
        with open(os.path.join("change_522209", "after_jsonrpc.py"), "r") as f:
            self.fixed_tree = ast.parse(f.read())

        diff_tree = diffast.diff(self.faulty_tree, self.fixed_tree)
        diffast.diff2html(diff_tree)
        chunks = diffast.extract_chunks(diff_tree)

        self.assertEquals(len(chunks), 4)

    def test_contexts_notifier(self):
        with open(os.path.join("change_569845", "before_notifier.py"), "r") as f:
            self.faulty_tree = ast.parse(f.read())
        with open(os.path.join("change_569845", "after_notifier.py"), "r") as f:
            self.fixed_tree = ast.parse(f.read())

        diff_tree = diffast.diff(self.faulty_tree, self.fixed_tree)
        diffast.diff2html(diff_tree)
        chunks = diffast.extract_chunks(diff_tree)

        self.assertEquals(len(chunks), 4)

    def test_contexts_driver(self):
        with open(os.path.join("change_570160", "before_driver.py"), "r") as f:
            self.faulty_tree = ast.parse(f.read())
        with open(os.path.join("change_570160", "after_driver.py"), "r") as f:
            self.fixed_tree = ast.parse(f.read())

        diff_tree = diffast.diff(self.faulty_tree, self.fixed_tree)
        diffast.diff2html(diff_tree)
        chunks = diffast.extract_chunks(diff_tree)

        self.assertEquals(len(chunks), 1)

    # def test_contexts_openstackcloud(self):
    #
    #   with open(os.path.join("change_567234", "before_openstackcloud.py"), "r") as f:
    #     self.faulty_tree = ast.parse(f.read())
    #   with open(os.path.join("change_567234", "after_openstackcloud.py"), "r") as f:
    #     self.fixed_tree = ast.parse(f.read())
    #
    #   diff_tree = diffast.diff(self.faulty_tree, self.fixed_tree)
    #   diffast.diff2html(diff_tree)
    #   chunks = diffast.extract_chunks(diff_tree)
    #
    #   self.assertEquals(len(chunks), 405)
    #   #print len(pickle.dumps(chunks[0]))

    def test_contexts_kolla_client(self):
        with open(os.path.join("change_566719", "before_client.py"), "r") as f:
            self.faulty_tree = ast.parse(f.read())
        with open(os.path.join("change_566719", "after_client.py"), "r") as f:
            self.fixed_tree = ast.parse(f.read())

        diff_tree = diffast.diff(self.faulty_tree, self.fixed_tree)
        diffast.diff2html(diff_tree)
        chunks = diffast.extract_chunks(diff_tree)

        self.assertEquals(len(chunks), 3)

    def test_539508_nova_virt_ironic_driver(self):
        with open(os.path.join("change_539508", "before_driver.py"), "r") as f:
            self.faulty_tree = ast.parse(f.read())
        with open(os.path.join("change_539508", "after_driver.py"), "r") as f:
            self.fixed_tree = ast.parse(f.read())

        diff_tree = diffast.diff(self.faulty_tree, self.fixed_tree)
        diffast.diff2html(diff_tree)
        chunks = diffast.extract_chunks(diff_tree)

        self.assertEquals(len(chunks), 1)

    def test_567271_nova_compute_resource_tracker(self):
        with open(os.path.join("change_567271", "before_resource_tracker.py"), "r") as f:
            self.faulty_tree = ast.parse(f.read())
        with open(os.path.join("change_567271", "after_resource_tracker.py"), "r") as f:
            self.fixed_tree = ast.parse(f.read())

        diff_tree = diffast.diff(self.faulty_tree, self.fixed_tree)
        diffast.diff2html(diff_tree)
        chunks = diffast.extract_chunks(diff_tree)

        for c in chunks:
            print c
        self.assertEquals(len(chunks), 1)
