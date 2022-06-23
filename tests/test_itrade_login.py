from __future__ import absolute_import
import unittest
import itrade_login


class EmptyLoginRegistryTestCase(unittest.TestCase):
    def setUp(self):
        self.reg = itrade_login.LoginRegistry()

    def tearDown(self):
        # conspicuous absence of clean-up logic
        self.reg = None

    def test_creation(self):
        self.assertIsNotNone(self.reg, "LoginRegistry creation failed.")

    def test_get_empty(self):
        self.assertIsNone(self.reg.get("any"), "Getting anything from an empty registry should return None.")

    def test_list_empty(self):
        self.assertEqual(self.reg.list(), [], "Expected empty list from empty registry.")


if __name__ == '__main__':
    unittest.main()
