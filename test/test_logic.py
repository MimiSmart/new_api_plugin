from unittest import TestCase

from logic import Logic


class TestLogic(TestCase):
    def setUp(self):
        self.logic = Logic('test_logic.xml')

    def test_get_xml(self):
        data = ""
        with open('test_logic.xml', 'rb') as f:
            data = f.read()
        self.assertEqual(self.logic.get_xml(), data)

    def test_get_item(self):
        item = self.logic.get_item("588:240")
        self.assertIs(type(item), dict)
        self.assertIn("@addr", item)
        self.assertEqual(item['@addr'], "588:240")

    def test__find_path_2_item(self):
        keys = self.logic._find_path_2_item(self.logic.obj_logic, "item", "@addr", "588:240")
        item = self.logic.obj_logic[keys[0]]
        for key in keys[1:]:
            item = item[key]
        self.assertIs(type(item), dict)
        self.assertIn("@addr", item)
        self.assertEqual(item['@addr'], "588:240")

    def test__find_all_items(self):
        items = self.logic._find_all_items(self.logic.obj_logic, 'item')
        self.assertIs(type(items), list)
        self.assertEqual(len(items), 59)
        for item in items:
            self.assertIs(type(item), dict)
            self.assertIn("@addr", item)
