"""Publish fixed native-pixel comparisons for this scoped repair.

Whole specimens stay unmasked. Exact edge/icon assertions are supplemental,
with their bounds and purpose recorded separately; they never imply that an
entire component (including its baked glyphs) is identical.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw
from verify_component_boundaries import pixels, ROOT


def publish(source, output):
    output.mkdir(parents=True, exist_ok=True)
    report = dict(scale=4, resampled=False, alignment='fixed measured bounds; no shift search',
                  comparisons=[], checks=[])

    def compare(name, reference, reference_box, actual, actual_box, purpose, exact=False):
        paths = []
        sources = []
        for side, filename, box in [('reference', reference, reference_box), ('actual', actual, actual_box)]:
            path = source / filename
            destination = output / (name + '-' + side + '.png')
            pixels.checked_crop(path, box).save(destination)
            paths.append(destination)
            sources.append(dict(side=side, file=filename, box=box,
                client_size=list(Image.open(path).size), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            metadata = path.with_suffix('.json')
            if metadata.exists():
                capture = json.loads(metadata.read_text(encoding='utf8'))
                sources[-1]['capture'] = {key: capture[key] for key in (
                    'version', 'timestamp', 'client', 'mouse_left_down_before', 'mouse_left_down_after')
                    if key in capture}
                observation = capture.get('observation') or {}
                sources[-1]['capture']['state'] = observation.get('state')
                sources[-1]['capture']['hold_ms'] = observation.get('hold_ms')
        result = pixels.compare(*paths, output / name)
        # Public evidence stays portable; original source coordinates and hashes
        # above identify the unmodified runtime PNGs.
        result['reference'] = paths[0].name
        result['actual'] = paths[1].name
        result.update(name=name, purpose=purpose, sources=sources,
                      differing_pixels=round(result['different_fraction'] * result['compared_pixels']))
        (output / (name + '.json')).write_text(json.dumps(result, indent=2), encoding='utf8')
        report['comparisons'].append(result)
        if exact:
            report['checks'].append(dict(name=name, passed=result['native_exact'],
                                         scope=purpose, differing_pixels=result['differing_pixels']))
        return result

    for state in ('default', 'hover', 'pressed'):
        back_ref = 'reference/header-back-' + state + '.png'
        back_actual = 'header-verified/header-0-' + state + '.png'
        social_ref = 'reference/header-social-' + state + '.png'
        social_actual = 'header-verified/header-1-' + state + '.png'
        compare('back-' + state, back_ref, [0, 0, 96, 96], back_actual, [0, 160, 96, 256],
                'Complete back button including arrow and surrounding header', exact=True)
        compare('social-' + state, social_ref, [1743, 0, 2021, 96],
                social_actual, [1743, 160, 2021, 256], 'Complete social button, text and separator')
        compare('header-' + state, social_ref, [0, 0, 2021, 100],
                social_actual, [0, 160, 2021, 260],
                'Complete header including title, both buttons and four pixels below it')
        compare('header-face-' + state, social_ref, [0, 0, 2021, 96],
                social_actual, [0, 160, 2021, 256],
                'Whole header without the page background below it; glyph differences remain included')
        compare('social-frame-' + state, social_ref, [1743, 0, 2021, 16],
                social_actual, [1743, 160, 2021, 176],
                'Supplement: full social width above the icon; feedback bounds and separator', exact=True)
        compare('social-icon-' + state, social_ref, [1791, 16, 1848, 68],
                social_actual, [1791, 176, 1848, 228],
                'Supplement: social icon and its immediate background', exact=True)
        compare('header-depth-' + state, social_ref, [0, 80, 2021, 96],
                social_actual, [0, 240, 2021, 256],
                'Supplement: bottom of face, reflection row and lower depth', exact=True)

    compare('segment-corner-before', 'reference/segment-middle.png', [1124, 360, 1156, 400],
            'before/segment-middle.png', [438, 152, 470, 192],
            'Supplement: original selected-left joint, anchored to this joint rather than the group origin')
    compare('segment-corner-after', 'reference/segment-middle.png', [1124, 360, 1156, 400],
            'after/segments-1-1-default.png', [438, 152, 470, 192],
            'Supplement: repaired selected-left joint at the same anchor', exact=True)
    for state in ('default', 'hover', 'pressed'):
        compare('segment-group-' + state, 'reference/segment-selected-middle-' + state + '.png',
                [715, 364, 1980, 492], 'after/segments-1-1-' + state + '.png', [28, 156, 1293, 284],
                'Entire three-choice group and margin, anchored to the outer group')
    compare('tabs-group', 'reference/tabs-middle.png', [24, 108, 2000, 212],
            'final/tabs-1-1-default.png', [16, 156, 1992, 260],
            'Entire world tab group, keyboard hints and surrounding pixels; backdrop differs')
    for name, ref, ab, rb, value in [
            ('friends', 'friends-open', [148, 176, 276, 256], [1408, 148, 1536, 228], 0),
            ('team', 'team', [500, 176, 628, 256], [1760, 148, 1888, 228], 1)]:
        compare(name + '-icon', 'reference/' + ref + '.png', rb,
                'final/icons-%d-%d-default.png' % (value, value), ab,
                'Supplement: selected icon, underline and immediate surrounding pixels', exact=True)
        compare(name + '-group', 'reference/' + ref + '.png', [1272, 128, 2020, 232],
                'final/icons-%d-%d-default.png' % (value, value), [12, 156, 760, 260],
                'Both icon tabs, keyboard hints and outer margin; containing panel differs')
    compare('world-seam', 'reference/start.png', [184, 682, 216, 702],
            'after/world-0-default.png', [176, 516, 208, 536],
            'Supplement: preview/name seam, one black row followed by one reflection row', exact=True)

    # Preserve complete world cards even though their preview content/height
    # differ. Do not resize these specimens to manufacture an equal-size diff.
    for side, file, box in [
            ('reference', 'reference/start.png', [36, 332, 660, 822]),
            ('actual', 'after/world-0-default.png', [28, 156, 652, 656])]:
        pixels.checked_crop(source / file, box).save(output / ('world-full-' + side + '.png'))
    report['world_full'] = dict(reference_size=[624, 490], actual_size=[624, 500],
        comparison='Not compared: preview height and image content differ; only the shared seam is in scope')

    for name, file in [('friends', 'friends-after/report.json'),
                       ('joined', 'final/report.json'), ('header', 'header-verified/report.json')]:
        data = json.loads((source / file).read_text(encoding='utf8'))
        if name == 'joined':
            # This batch also contains a superseded header iteration. The
            # header-verified batch below is the final implementation.
            data['checks'] = [row for row in data['checks'] if not row['name'].startswith('header-')]
        report['checks'].extend(dict(name=name + ': ' + row['name'], passed=row['passed'])
                                for row in data['checks'])
        # Retain numeric transition samples, but omit absolute runtime paths.
        (output / (name + '-runtime.json')).write_text(json.dumps(dict(
            passed=data['passed'], dimensions=data.get('dimensions'), checks=data['checks'],
            transitions=data.get('transitions', [])), ensure_ascii=False, indent=2), encoding='utf8')

    board = Image.new('RGB', (832, 356), '#28292a')
    draw = ImageDraw.Draw(board)
    draw.text((12, 8), 'Back: reference | Pyreact          Social: reference | Pyreact', fill='white')
    for row, state in enumerate(('default', 'hover', 'pressed')):
        y = 30 + row * 108
        draw.text((8, y + 4), state, fill='white')
        board.paste(Image.open(output / ('back-' + state + '.pair.png')), (68, y))
        board.paste(Image.open(output / ('social-' + state + '.pair.png')), (264, y))
    # Width includes complete paired social specimens.
    board.save(output / 'header-states.png')
    report['passed'] = all(row['passed'] for row in report['checks'])
    report['full_native_exact'] = all(row['native_exact'] for row in report['comparisons'])
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(dict(passed=report['passed'], checks=len(report['checks']),
        failed=[r['name'] for r in report['checks'] if not r['passed']],
        full_native_exact=report['full_native_exact']), indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=ROOT / '.runtime/seams-scroll')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/images/seams-scroll')
    args = parser.parse_args()
    raise SystemExit(0 if publish(args.source, args.output)['passed'] else 1)
