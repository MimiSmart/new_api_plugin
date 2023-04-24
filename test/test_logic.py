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
        self.assertIn("addr", item)
        self.assertEqual(item['addr'], "588:240")

    def test__find_path_2_item(self):
        keys = self.logic._find_path_2_item(self.logic.obj_logic, "item", "addr", "588:240")
        item = self.logic.obj_logic[keys[0]]
        for key in keys[1:]:
            item = item[key]
        self.assertIs(type(item), dict)
        self.assertIn("addr", item)
        self.assertEqual(item['addr'], "588:240")

    def test__find_all_items(self):
        items = self.logic._find_all_items(self.logic.obj_logic, 'item')
        self.assertIs(type(items), list)
        self.assertEqual(len(items), 59)
        for item in items:
            self.assertIs(type(item), dict)
            self.assertIn("addr", item)

    def test_set_item(self):
        response = self.logic.set_item('write', 'item', 'Setup',
                                       {'name': 'test item', 'addr': '999:99'})
        self.assertEqual(response, {'message': 'Write successfully', 'type': 'response'})
        keys = self.logic._find_path_2_item(self.logic.obj_logic, "item", "addr", "999:99")
        self.assertNotEqual(len(keys),0)

        items = self.logic._find_all_items(self.logic.obj_logic, 'item')
        self.assertIn({'name': 'test item', 'addr': '999:99'}, items)

        response = self.logic.set_item('append', 'item', 'Setup', {'test': 'test', 'addr': '999:99'})
        self.assertEqual(response, {'type': 'response', 'message': 'Append successfully'})
        item = self.logic.obj_logic
        for key in keys:
            item = item[key]
        self.assertIn('test', item)


        response = self.logic.set_item('remove', 'item', 'Setup', {'addr': '999:99', 'test': ''})
        item = self.logic.obj_logic
        for key in keys:
            item = item[key]
        self.assertEqual(response, {'type': 'response', 'message': 'Removed successfully'})
        self.assertNotIn('test', item)
