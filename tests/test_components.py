"""Host wrapper for genuine Python 2.7 runtime contract tests."""
import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RuntimeContractTests(unittest.TestCase):
    def test_real_python2_contracts(self):
        interpreter = os.environ.get('ORE_PYTHON2') or shutil.which('python2')
        self.assertTrue(interpreter, 'Set ORE_PYTHON2 to a Python 2.7 interpreter')
        demo = Path(os.environ.get('ORE_DEMO_PATH', ROOT / '.runtime/demo_addon'))
        self.assertTrue((demo / 'behavior_pack/ore_demo/pyreact/__init__.py').is_file(),
                        'Run tools/build_demo.py --pyreact <PyreactMC> first')
        env = dict(os.environ)
        env['ORE_TEST_BEHAVIOR'] = str(demo / 'behavior_pack')
        result = subprocess.run([interpreter, '-B', str(ROOT / 'tests/runtime_contracts.py'), '-v'],
                                env=env, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0,
                         result.stdout.decode('utf8', 'replace') + result.stderr.decode('utf8', 'replace'))


if __name__ == '__main__':
    unittest.main()
