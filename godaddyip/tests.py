#!/usr/bin/env python3

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from godaddyip.__main__ import Config, previous_value, store_value


class TestGodaddyIp(unittest.TestCase):
    def test_config_load(self) -> None:
        tests_src_path = Path(__file__).parent
        unittest_config_path = tests_src_path / "unittest.yml"
        config = Config(unittest_config_path)
        self.assertEqual("unittest", config["arecord"])

    def test_store_previous_value(self) -> None:
        with TemporaryDirectory() as td:
            td_path = Path(td)
            store_value(td_path, "unittest", "unittest")
            self.assertEqual(
                "unittest",
                previous_value(td_path, "unittest"),
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
