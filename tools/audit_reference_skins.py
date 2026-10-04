"""Compare recorded international control pixels with generated raster skins."""
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / '.runtime/bedrock-reference'


def main():
    spec = importlib.util.spec_from_file_location('ore_reference_pixels',
        ROOT / '.agents/skills/bedrock-ore-reference/scripts/pixels.py')
    pixels = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pixels)
    output = REFERENCE / 'skin-audit'
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    controls = [('switch-on-final', 'switch_on', (1852, 124)),
                ('switch-off-final', 'switch_off', (1852, 528)),
                ('slider-final', 'thumb', (1164, 504))]
    for capture, skin, approximate in controls:
        for state in ('default', 'hover'):
            source = REFERENCE / (capture + '-' + state + '.png')
            texture = ROOT / ('resource_pack/textures/pyreact_ore/skin/' + skin + '_' + state + '.png')
            image = Image.open(source).convert('RGB')
            expected = Image.open(texture).convert('RGBA')
            canvas = Image.new('RGBA', expected.size, '#48494a')
            canvas.alpha_composite(expected)
            expected = canvas.convert('RGB').resize((expected.width * 4, expected.height * 4), Image.Resampling.NEAREST)
            desired = np.asarray(expected, dtype=np.int16)
            candidates = []
            for dy in range(-8, 9):
                for dx in range(-8, 9):
                    x, y = approximate[0] + dx, approximate[1] + dy
                    delta = np.abs(np.asarray(image.crop((x, y, x + expected.width, y + expected.height)), dtype=np.int16) - desired)
                    candidates.append((float(delta.mean()), abs(dx) + abs(dy), dx, dy))
            error, unused, dx, dy = min(candidates)
            x, y = approximate[0] + dx, approximate[1] + dy
            box = [x, y, x + expected.width, y + expected.height]
            crop = output / (skin + '-' + state + '.png')
            image.crop(box).save(crop)
            result = pixels.compare(crop, texture, output / (skin + '-' + state), scale=4, background='#48494a')
            result.update(component=skin, state=state, source=str(source.relative_to(ROOT)), box=box,
                alignment_search={'radius': 8, 'offset': [dx, dy]}, scope='reference versus generated skin; no text or icons excluded')
            rows.append(result)
    result = dict(client_version='1.26.5203.0', reference_pixel_scale=4,
        scope='Generated skins only. Actual game rendering is a separate comparison.', rows=rows)
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps([dict(component=row['component'], state=row['state'], box=row['box'],
        mean_channel_error=row['mean_channel_error'], different_fraction=row['different_fraction']) for row in rows], indent=2))


if __name__ == '__main__':
    main()
