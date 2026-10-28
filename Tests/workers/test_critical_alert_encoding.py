import sys
import unittest
from unittest.mock import MagicMock
import os

# Adjust path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

class TestEncodingFix(unittest.TestCase):
    def test_reconfigure_missing(self):
        # Mock sys.stdout to NOT have reconfigure
        original_stdout = sys.stdout
        sys.stdout = MagicMock(spec=[]) # Empty spec, no methods

        try:
            # We need to import the module.
            import importlib
            import api_agents.workers.critical_alert.critical_alert as ca
            importlib.reload(ca)
        except AttributeError as e:
             self.fail(f"Import crashed due to missing attribute: {e}")
        except Exception as e:
            if "stdout" in str(e):
                self.fail(f"Import crashed with stdout error: {e}")
        finally:
            sys.stdout = original_stdout

    def test_reconfigure_raises(self):
        # Mock sys.stdout to HAVE reconfigure but it raises
        original_stdout = sys.stdout
        sys.stdout = MagicMock()
        sys.stdout.reconfigure.side_effect = Exception("Boom")

        try:
            import importlib
            import api_agents.workers.critical_alert.critical_alert as ca
            importlib.reload(ca)
        except Exception as e:
            self.fail(f"Import crashed when reconfigure raised: {e}")
        finally:
            sys.stdout = original_stdout

if __name__ == '__main__':
    unittest.main()
