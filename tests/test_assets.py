import hashlib
import json
import runpy
import unittest
from pathlib import Path

from PIL import Image
from tools.import_assets import animation_sheet

ROOT = Path(__file__).resolve().parents[1]
CATALOG = runpy.run_path(str(ROOT / 'oreui/_catalog.py'))['ASSETS']


class AssetTests(unittest.TestCase):
    def test_gif_zero_delay_uses_browser_timing_and_preserves_long_holds(self):
        class Source:
            size = (2, 2)
            n_frames = 3
            def seek(self, index):
                self.info = {'duration': (0, 40, 1200)[index]}
            def convert(self, mode):
                return Image.new(mode, self.size)
        unused_sheet, frames, durations = animation_sheet(Source())
        self.assertEqual(durations, [0.1, 0.04, 1.2])
        self.assertEqual(len(frames), 3)
    def test_native_input_preserves_required_state_controls(self):
        skin = json.loads((ROOT / 'resource_pack/ui/OreUI.json').read_text(encoding='utf8'))
        names = {next(iter(control)).split('@')[0] for control in skin['input@PyreactBase.input']['controls']}
        self.assertTrue({'default', 'hover', 'pressed', 'locked', 'centering_panel'} <= names)
        self.assertNotEqual(skin['slider@PyreactBase.slider']['$slider_box_layout'], 'common.slider_button_layout')
        self.assertEqual(skin['glyph@PyreactBase.image']['bilinear'], True)
        self.assertEqual(skin['input@PyreactBase.input']['$nineslice_size'], [1, 3, 1, 1])

    def test_permission_tint_masks_preserve_source_alpha(self):
        textures = ROOT / 'resource_pack/textures/pyreact_ore'
        for name in ('member', 'operator', 'player_permissions', 'permission_visitor', 'permission_custom'):
            with self.subTest(icon=name):
                source = Image.open(textures / (name + '.png')).convert('RGBA')
                mask = Image.open(textures / 'skin' / (name + '_tintable.png')).convert('RGBA')
                self.assertEqual(mask.size, source.size)
                self.assertEqual(mask.getchannel('A').tobytes(), source.getchannel('A').tobytes())
                self.assertTrue(all(pixel[:3] == (255, 255, 255) for pixel in mask.getdata()))

    def test_step_slider_markers_keep_native_factory_geometry(self):
        skin = json.loads((ROOT / 'resource_pack/ui/OreUI.json').read_text(encoding='utf8'))
        for suffix in ('', '_hover', '_progress', '_progress_hover'):
            marker = skin['slider_step' + suffix]
            self.assertEqual(marker['size'], [1, 6])
            self.assertEqual(marker['offset'], '$step_offset')
            self.assertEqual(marker['layer'], 4)
        with Image.open(ROOT / 'resource_pack/textures/pyreact_ore/skin/step.png') as texture:
            self.assertEqual(texture.size, (1, 6))
            self.assertEqual(texture.getextrema()[3], (255, 255))

    def test_catalog_matches_real_pngs_and_provenance(self):
        manifest = json.loads((ROOT / 'assets/manifest.json').read_text(encoding='utf8'))
        self.assertEqual(set(CATALOG), set(manifest['assets']))
        self.assertEqual(len(CATALOG), manifest['imported_count'])
        for name, metadata in CATALOG.items():
            with self.subTest(asset=name):
                record = manifest['assets'][name]
                path = ROOT / record['output']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record['output_sha256'])
                self.assertEqual(metadata['src'] + '.png', 'textures/pyreact_ore/' + name + '.png')
                with Image.open(path) as image:
                    self.assertEqual(image.format, 'PNG')
                    self.assertEqual(list(image.size), record['output_size'])
                    if 'nineSliceData' in metadata:
                        left, right, top, bottom = metadata['nineSliceData']
                        self.assertLessEqual(left + right, image.width)
                        self.assertLessEqual(top + bottom, image.height)
                    for frame in metadata.get('frames', []):
                        x, y = frame['uv']
                        w, h = frame['uvSize']
                        self.assertLessEqual(x + w, image.width)
                        self.assertLessEqual(y + h, image.height)
                        self.assertEqual((w, h), metadata['size'])
                if 'frames' in metadata:
                    self.assertEqual(metadata['frameDurations'], record['frame_durations'])
                    self.assertEqual(len(metadata['frames']), len(metadata['frameDurations']))


if __name__ == '__main__':
    unittest.main()
