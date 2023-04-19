import json
import unittest

import requests


class TestRest(unittest.TestCase):
    config = None

    def setUp(self) -> None:
        with open('../config') as f:
            self.config = json.load(f)

    def test_get_item(self):
        response = requests.post("http://127.0.0.1:" + str(self.config['rest_port']) + "/item/get",
                                 json={"addr": "588:250"})
        response = response.json()
        self.assertIs(type(response), dict)
        self.assertIn("@addr", response)
        self.assertEqual(response['@addr'], "588:250")

