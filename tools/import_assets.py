"""Build Minecraft PNGs and a Python 2 catalog from the supplied OreUI zip.

Only actual raster files under index/assets and gameplay/assets are imported.
Files with a .png extension elsewhere are often webpack JavaScript modules.
"""
import argparse
import hashlib
import io
import json
import math
import pprint
import re
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
THEME = 'gameplay/bedrock/mge/menus/core/ui-theme/src/'


def stable_name(filename):
    stem = re.sub(r'-[0-9a-f]{16,64}$', '', Path(filename).stem)
    stem = stem.replace('@0.5x.icon', '').replace('@0.5x', '')
    stem = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', stem)
    return re.sub(r'[^a-z0-9]+', '_', stem.lower()).strip('_')


def expand_edges(values):
    if len(values) == 1:
        return values * 4
    if len(values) == 2:
        return values * 2
    if len(values) == 3:
        return values + [values[1]]
    if len(values) == 4:
        return values
    raise ValueError('Invalid CSS edge count')


def border_metadata(archive):
    result = {}
    for path in archive.namelist():
        if not path.startswith(THEME + 'components/') or not path.endswith('/index.ts'):
            continue
        text = archive.read(path).decode('utf8')
        variables = {}
        for variable, relative in re.findall(r'var (\w+) = __webpack_require__\(/\*! .*? \*/ "(.*?)"\)', text):
            source_path = 'gameplay/' + relative.removeprefix('./')
            if source_path not in archive.namelist():
                continue
            reference = archive.read(source_path).decode('utf8')
            match = re.search(r'"(assets/[^\"]+)"', reference)
            if match:
                variables[variable] = 'gameplay/' + match.group(1)
        for block in re.findall(r'borderImageProperties\)\(\{(.*?)\}\)', text, re.S):
            src = re.search(r'src:\s*(\w+)', block)
            edges = re.search(r'slice:\s*\[([^]]+)\]', block)
            if not src or not edges or src.group(1) not in variables:
                continue
            top, right, bottom, left = expand_edges([float(x.strip()) for x in edges.group(1).split(',')])
            scale = re.search(r'scale:\s*([\d.]+)', block)
            result[variables[src.group(1)]] = {
                'nine_slice': [left, right, top, bottom],
                'source_scale': float(scale.group(1)) if scale else 1,
                'theme_source': path,
            }
    return result


def animation_sheet(image):
    width, height = image.size
    count = image.n_frames
    gif_duration = getattr(image, 'info', {}).get('duration', 100)
    columns = min(count, max(1, math.ceil(math.sqrt(count))), 4096 // width)
    rows = math.ceil(count / columns) if columns else 4097
    if not columns or rows * height > 4096:
        raise ValueError('Animation exceeds a 4096x4096 Minecraft atlas')
    sheet = Image.new('RGBA', (columns * width, rows * height))
    frames = []
    durations = []
    for index in range(count):
        image.seek(index)
        uv = ((index % columns) * width, (index // columns) * height)
        sheet.paste(image.convert('RGBA'), uv)
        frames.append({'uv': uv, 'uvSize': (width, height)})
        duration = image.info.get('duration', gif_duration)
        # GIF zero-delay frames use the browser's 100ms fallback, not 1ms.
        durations.append(duration / 1000.0 if duration >= 20 else 0.1)
    return sheet, frames, durations


def import_archive(zip_path):
    output = ROOT / 'resource_pack/textures/pyreact_ore'
    output.mkdir(parents=True, exist_ok=True)
    catalog = {}
    provenance = {}
    excluded = []
    seen = {}
    with zipfile.ZipFile(zip_path) as archive:
        borders = border_metadata(archive)
        paths = sorted(n for n in archive.namelist() if n.startswith(('gameplay/assets/', 'index/assets/'))
                       and Path(n).suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif'))
        for path in paths:
            data = archive.read(path)
            digest = hashlib.sha256(data).hexdigest()
            if digest in seen:
                provenance[seen[digest]]['source_paths'].append(path)
                continue
            name = stable_name(path)
            if name in catalog:
                name += '_' + digest[:8]
            image = Image.open(io.BytesIO(data))
            metadata = {'src': 'textures/pyreact_ore/' + name, 'size': tuple(image.size)}
            if path.endswith('.gif'):
                try:
                    rendered, frames, durations = animation_sheet(image)
                except ValueError as error:
                    excluded.append({'path': path, 'reason': str(error)})
                    continue
                metadata.update(frames=frames, frameDuration=durations[0], frameDurations=durations)
            else:
                rendered = image.convert('RGBA')
                durations = None
            rendered.save(output / (name + '.png'), optimize=True)
            border = borders.get(path)
            if border:
                metadata['nineSliceData'] = tuple(border['nine_slice'])
            catalog[name] = metadata
            provenance[name] = {
                'source_paths': [path], 'source_sha256': digest,
                'output_sha256': hashlib.sha256((output / (name + '.png')).read_bytes()).hexdigest(),
                'output': 'resource_pack/textures/pyreact_ore/' + name + '.png',
                'source_size': list(image.size), 'output_size': list(rendered.size),
                'border': border, 'frame_durations': durations,
            }
            seen[digest] = name
        palette = archive.read(THEME + 'palette.ts').decode('utf8')
        colors = dict(re.findall(r"(\w+): '(#[0-9a-fA-F]{6})'", palette))
    target = ROOT / 'oreui/_catalog.py'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('# -*- coding: utf-8 -*-\n# Generated by tools/import_assets.py; do not edit.\nASSETS = ' +
                      pprint.pformat(catalog, width=110, sort_dicts=True) + '\n\nPALETTE = ' +
                      pprint.pformat({k: int(v[1:] + 'ff', 16) for k, v in colors.items()}, sort_dicts=True) + '\n', encoding='utf8')
    manifest = {'schema_version': 1, 'archive_name': zip_path.name,
                'archive_sha256': hashlib.sha256(zip_path.read_bytes()).hexdigest(),
                'imported_count': len(catalog), 'assets': provenance, 'excluded': excluded,
                'notes': ['Raster assets only; webpack code, fonts, and videos are not deployed.',
                          'GIF frames retain individual durations; delays below 20ms use the browser-compatible 100ms fallback.']}
    (ROOT / 'assets').mkdir(exist_ok=True)
    (ROOT / 'assets/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'assets': len(catalog), 'nine_sliced': sum('nineSliceData' in v for v in catalog.values()),
                      'animations': sum('frames' in v for v in catalog.values()), 'excluded': excluded}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    import_archive(args.archive.resolve())
