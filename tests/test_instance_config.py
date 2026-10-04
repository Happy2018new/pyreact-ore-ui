"""A UI preset must not enable reload against explicit project settings."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / '.agents/skills/pyreact-debugging/scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('ore_instances', SCRIPTS / 'instances.py')
instances = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(instances)


class InstanceConfigTests(unittest.TestCase):
    def test_explicit_reload_settings_survive_ui_preset(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            executable = root / 'Minecraft.Windows.exe'
            executable.touch()
            original = dict(auto_hot_reload_mods=False, auto_hot_reload_ui=False)
            config = instances.prepare_config(root, original, str(executable), 51100, 'test', 'ui')
            self.assertFalse(config['auto_hot_reload_mods'])
            self.assertFalse(config['auto_hot_reload_ui'])
            self.assertEqual(original, dict(auto_hot_reload_mods=False, auto_hot_reload_ui=False))
            defaults = instances.prepare_config(root, {}, str(executable), 51100, 'test', 'ui')
            self.assertTrue(defaults['auto_hot_reload_mods'])
            self.assertTrue(defaults['auto_hot_reload_ui'])
