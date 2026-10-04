"""Bake the complete Noto Sans SC cmap using the editor's 64 px atlas method."""
import argparse
import json
import math
import shutil
from pathlib import Path
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def build(path, license_path, latin_path=None, latin_baseline=64):
    output = ROOT / 'resource_pack/textures/pyreact_ore/type'
    output.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(str(path), 64)
    if 'fvar' in TTFont(str(path)):
        font.set_variation_by_name('Regular')
    latin = ImageFont.truetype(str(latin_path), 64) if latin_path else None
    latin_cmap = TTFont(str(latin_path)).getBestCmap() if latin_path else {}
    mapping = {}
    page = 0
    x = y = 2
    image = Image.new('RGBA', (2048, 2048), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    for code in sorted(TTFont(str(path)).getBestCmap()):
        if code < 32 or 0x7f <= code < 0xa0:
            continue
        char = chr(code)
        active_font = latin if latin and code in latin_cmap and code < 0x3000 else font
        advance = active_font.getlength(char)
        width = max(1, math.ceil(advance) + 4)
        if x + width + 2 > 2048:
            x, y = 2, y + 92
        if y + 90 > 2048:
            image.save(output / ('atlas_%03d.png' % page), optimize=True)
            page += 1
            x = y = 2
            image = Image.new('RGBA', (2048, 2048), (255, 255, 255, 0))
            draw = ImageDraw.Draw(image)
        baseline = latin_baseline if active_font is latin else 69
        draw.text((x + 1, y + baseline), char, font=active_font, fill='white', anchor='ls')
        mapping[char] = [page, x, y, width, advance]
        x += width + 4
    image.save(output / ('atlas_%03d.png' % page), optimize=True)
    (ROOT / 'oreui/_font_atlas.py').write_text(
        '# -*- coding: utf-8 -*-\n# Generated Noto Sans SC Regular and source Ore Latin glyphs.\n'
        'import json\nGLYPHS = json.loads(r\'\'\'' +
        json.dumps(mapping, ensure_ascii=True, separators=(',', ':')) + "''')\n", encoding='utf8')
    if license_path.resolve() != (output / 'OFL.txt').resolve():
        shutil.copyfile(license_path, output / 'OFL.txt')
    print('Baked %d glyphs in %d pages' % (len(mapping), page + 1), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--font', type=Path, required=True)
    parser.add_argument('--license', type=Path, required=True)
    parser.add_argument('--latin-font', type=Path)
    parser.add_argument('--latin-baseline', type=int, default=64)
    args = parser.parse_args()
    build(args.font, args.license, args.latin_font, args.latin_baseline)
