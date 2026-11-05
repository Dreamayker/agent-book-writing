import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "order_runner", SCRIPTS / "replay_cases.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class EnvironmentBoundaryTest(unittest.TestCase):
    def test_business_command_does_not_inherit_api_credentials(self):
        with tempfile.TemporaryDirectory() as scratch:
            output = Path(scratch) / "output.txt"
            with patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "test-sentinel",
                    "ORDER_TEST_SECRET": "test-sentinel",
                },
            ):
                result = runner.capture(
                    [
                        sys.executable,
                        "-c",
                        "import os; print('OPENAI_API_KEY' in os.environ, 'ORDER_TEST_SECRET' in os.environ)",
                    ],
                    scratch,
                    output,
                )
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(output.read_text().strip(), "False False")


if __name__ == "__main__":
    unittest.main()
