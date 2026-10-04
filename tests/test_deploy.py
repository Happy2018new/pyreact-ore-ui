"""Verify consumer installation preserves the host and ships native skins."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.deploy import deploy


class DeploymentTests(unittest.TestCase):
    def test_repeat_core_install_preserves_host_templates_and_definitions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client = root / 'behavior_pack/client'
            resources = root / 'resource_pack'
            (client / 'pyreact').mkdir(parents=True)
            (client / 'pyreact/__init__.py').write_text('# Existing host\n', encoding='utf8')
            (resources / 'ui').mkdir(parents=True)
            template = {'namespace': 'PyreactBase', 'rootBase': {
                'controls': [{'custom_tmpl@MyMod.widget': {'size': [7, 9]}}]}}
            definitions = {'ui_defs': ['ui/MyMod.json', 'ui/PyreactBase.json'], 'host_metadata': 42}
            (resources / 'ui/PyreactBase.json').write_text(json.dumps(template), encoding='utf8')
            (resources / 'ui/_ui_defs.json').write_text(json.dumps(definitions), encoding='utf8')
            with contextlib.redirect_stdout(io.StringIO()):
                deploy(client, resources, asset_set='core')
                first = (resources / 'ui/PyreactBase.json').read_bytes()
                deploy(client, resources, asset_set='core')
            self.assertEqual(first, (resources / 'ui/PyreactBase.json').read_bytes())
            current = json.loads(first)
            self.assertEqual(current['rootBase']['controls'][0], template['rootBase']['controls'][0])
            self.assertEqual(len(current['rootBase']['controls']), 8)
            current_defs = json.loads((resources / 'ui/_ui_defs.json').read_text(encoding='utf8'))
            self.assertEqual(current_defs['host_metadata'], 42)
            self.assertEqual(current_defs['ui_defs'], ['ui/MyMod.json', 'ui/PyreactBase.json', 'ui/OreUI.json'])
            self.assertEqual((client / 'pyreact/__init__.py').read_text(), '# Existing host\n')
            self.assertTrue((client / 'oreui/_text.py').is_file())
            self.assertTrue((resources / 'ui/OreUI.json').is_file())
            self.assertEqual(len(list((resources / 'textures/pyreact_ore/type').glob('atlas_*.png'))), 50)
            self.assertTrue((resources / 'textures/pyreact_ore/type/OFL.txt').is_file())
            for name in ('input', 'thumb', 'track', 'scroll_thumb', 'switch_on_default'):
                self.assertTrue((resources / ('textures/pyreact_ore/skin/' + name + '.png')).is_file(), name)
            for name in ('general_icon', 'advanced_icon', 'member', 'operator', 'player_permissions',
                         'edit', 'world_demo_screen_big', 'ui_menu_worlds_tab', 'icon_alex',
                         'no_player_profile', 'bracket_open', 'bracket_close'):
                self.assertTrue((resources / ('textures/pyreact_ore/' + name + '.png')).is_file(), name)
            for name in ('reference_social', 'reference_friends', 'reference_team', 'reference_steve_face'):
                self.assertTrue((resources / ('textures/pyreact_ore/reference/' + name + '.png')).is_file(), name)
