"""Regression for strict crop accounting and overflow visibility."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / '.agents/skills/bedrock-ore-reference/scripts/pixels.py'
SPEC = importlib.util.spec_from_file_location('ore_pixels', SCRIPT)
pixels = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pixels)


class PixelAccountingTests(unittest.TestCase):
    def test_fractional_adjacent_boxes_share_the_same_edge(self):
        first = pixels.logical_box((.125, 0), (10.25, 3), 4)
        second = pixels.logical_box((10.375, 0), (10.25, 3), 4)
        self.assertEqual(first[2], second[0])
        self.assertEqual(first, (1, 0, 42, 12))

    def test_outer_margin_includes_protrusions(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            reference = Image.new('RGB', (12, 12), '#48494a')
            reference.save(base / 'ref.png')
            actual = reference.copy()
            actual.putpixel((0, 0), (30, 30, 31))
            actual.save(base / 'actual.png')
            result = pixels.compare(base / 'ref.png', base / 'actual.png', base / 'audit')
            self.assertFalse(result['within_tolerance'])
            self.assertEqual(result['changed_bounds'], [0, 0, 1, 1])
            self.assertEqual(result['compared_pixels'], 144)

    def test_size_mismatch_is_not_automatically_resized(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            Image.new('RGB', (10, 10)).save(base / 'ref.png')
            Image.new('RGB', (11, 10)).save(base / 'actual.png')
            with self.assertRaisesRegex(ValueError, 'dimensions differ'):
                pixels.compare(base / 'ref.png', base / 'actual.png', base / 'audit')
            with self.assertRaisesRegex(ValueError, 'outside source'):
                pixels.checked_crop(base / 'ref.png', (-1, 0, 9, 10))

    def test_invalid_scale_is_rejected(self):
        for scale in (0, -1, float('nan')):
            with self.assertRaises(ValueError):
                pixels.logical_box((0, 0), (1, 1), scale)
