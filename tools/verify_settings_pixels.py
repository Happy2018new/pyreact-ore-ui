"""Audit lossless game pixels against same-state international captures."""
import argparse
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image

from verify_settings import SettingsVerification
from capture_settings_pixels import operate

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / '.runtime/bedrock-reference'


def verify(session, owner, output):
    verifier = SettingsVerification(session, owner, output)
    window = json.loads(verifier.run('resize_window.py', '--list-windows'))['windows'][0]
    verifier.run('resize_window.py', '--pid', str(window['pid']), '--size', '2016x1164')
    verifier.mount()
    verifier.set_touch(False)
    spec = importlib.util.spec_from_file_location('ore_reference_pixels',
        ROOT / '.agents/skills/bedrock-ore-reference/scripts/pixels.py')
    pixels = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pixels)
    rows = []

    def control(key, child, nested=None):
        if nested:
            path = verifier.code('from ore_demo import dev_probe\n'
                'from ore_demo.pyreact import host\n'
                'from ore_demo.pyreact.primitives import ButtonPrimitive\n'
                'parent=next(f for f in dev_probe._walk(host._ACTIVE_HOST[0]._root_fiber) if f.key==%r)\n'
                'target=next(f for f in dev_probe._walk(parent) if f.key==%r)\n'
                '_result=next(f.native_path for f in dev_probe._walk(target) if isinstance(f.comp_type,ButtonPrimitive))\n'
                % (key, nested), 'pixel-nested-path')
        else:
            path = verifier.native_probe('root-' + key, [key])[key]['path']
        if child:
            path += '/' + child
        return verifier.code('from ore_demo.pyreact import host\n'
            'control=host._ACTIVE_HOST[0].GetBaseUIControl(%r)\n'
            '_result=dict(position=control.GetGlobalPosition(),size=control.GetSize(),visible=control.GetVisible())\n'
            % path, 'pixel-position')

    def reference_strip(name, source, box):
        target = verifier.output / (name + '-reference-strip.png')
        Image.open(REFERENCE / source).crop(box).save(target)
        return target

    def audit(name, key, child, reference, hover=False, strip=None, nested=None):
        verifier.code('from ore_demo import dev_probe\n_result=dev_probe.reveal(%r,%r)\n' %
            ('lab_scroll_' + verifier.current_page + '_0', key), 'pixel-reveal')
        time.sleep(.25)
        # Hidden state images can report zero geometry before hover. Hit-test
        # the owning control, then measure its newly visible state image.
        box = control(key, '', nested)
        x, y = box['position']
        width, height = box['size']
        geometry = operate(session, owner, points=[])
        client_width, client_height = geometry['client_size']
        logical_scale = client_width / float(verifier.screen[0])
        point = [(x + width / 2) * logical_scale / client_width,
                 (y + height / 2) * logical_scale / client_height]
        full = verifier.output / (name + '-full.png')
        capture = operate(session, owner, output=full, points=[(.95, .08)] + ([point] if hover else []))
        box = control(key, child, nested)
        verifier.check(name + ' native state is visible', box['visible'])
        scale = round(capture['client'][2] / verifier.screen[0])
        if abs(capture['client'][2] / verifier.screen[0] - scale) > .01:
            raise AssertionError('Unexpected native pixel scale')
        x, y = [round(n * scale) for n in box['position']]
        width, height = [round(n * scale) for n in box['size']]
        if strip:
            dx, dy, width, height = [round(n * scale) for n in strip]
            x += dx
            y += dy
        image = Image.open(full).convert('RGB')
        expected = Image.open(reference).convert('RGB')
        target = np.asarray(expected, dtype=np.int16)
        ratios = [expected.width / width, expected.height / height]
        if abs(ratios[0] - ratios[1]) > .001:
            raise AssertionError('Reference crop aspect does not match native control')
        candidates = []
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                candidate = image.crop((x + dx, y + dy, x + dx + width, y + dy + height))
                candidate = candidate.resize(expected.size, Image.Resampling.NEAREST)
                error = float(np.abs(np.asarray(candidate, dtype=np.int16) - target).mean())
                candidates.append((error, abs(dx) + abs(dy), dx, dy))
        unused, unused_distance, dx, dy = min(candidates)
        crop_box = [x + dx, y + dy, x + dx + width, y + dy + height]
        crop = verifier.output / (name + '-crop.png')
        image.crop(crop_box).save(crop)
        result = pixels.compare(reference, crop, verifier.output / name, scale=ratios[0])
        result.update(name=name, source=str(full), box=crop_box, logical_scale=scale,
            alignment_search={'radius': 2, 'offset': [dx, dy]}, native_control=box,
            scope='complete control crop' if not strip else 'explicit border or track strip; text is outside this crop')
        rows.append(result)
        print(json.dumps(dict(name=name, mean_channel_error=result['mean_channel_error'],
            max_channel_error=result['max_channel_error'], different_fraction=result['different_fraction'])), flush=True)

    result = dict(collected=False, native_exact_whole_ui=False, rows=rows,
        reference_version='1.26.5203.0',
        scope='Explicit control crops, nearest scaling and recorded alignment. No whole-page 1:1 claim.')
    try:
        verifier.page('toggles')
        for selected, key, stem, top in (
                (True, 'lab_page_toggles', 'nav-selected-final', 964),
                (False, 'lab_page_selection', 'nav-unselected-final', 868)):
            for state in ('default', 'hover'):
                name = 'navigation-%s-%s' % ('selected' if selected else 'unselected', state)
                reference = reference_strip(name, stem + '-' + state + '.png', (4, top, 16, top + 96))
                audit(name, key, state, reference, state == 'hover', strip=(0, 0, 3, 24))
        for selected, nested, stem, left in (
                (True, 'ore_segment_1', 'segment-selected-final', 1132),
                (False, 'ore_segment_0', 'segment-unselected-final', 716)):
            for state in ('default', 'hover'):
                name = 'segment-%s-%s' % ('selected' if selected else 'unselected', state)
                reference = reference_strip(name, stem + '-' + state + '.png', (left, 400, left + 8, 520))
                audit(name, 'lab_access', state, reference, state == 'hover',
                    strip=(0, 0, 2, 30), nested=nested)
        for value in ('on', 'off'):
            for state in ('default', 'hover'):
                audit('switch-' + value + '-' + state, 'lab_switch', state,
                    REFERENCE / ('skin-audit/switch_' + value + '-' + state + '.png'), state == 'hover')
            if value == 'on':
                verifier.tap('lab_switch')
        verifier.page('sliders')
        for state in ('default', 'hover'):
            audit('thumb-' + state, 'lab_slider', 'slider_box/' + state,
                REFERENCE / ('skin-audit/thumb-' + state + '.png'), state == 'hover')
        verifier.page('fields')
        for state in ('default', 'hover'):
            name = 'field-left-border-' + state
            reference = reference_strip(name, 'field-final-' + state + '.png', (720, 168, 744, 264))
            audit(name, 'lab_field', state, reference, state == 'hover', strip=(0, 0, 6, 24))
        result['collected'] = True
    except Exception as error:
        result['error'] = str(error)
    finally:
        try:
            verifier.run('resize_window.py', '--pid', str(window['pid']),
                         '--size', '%dx%d' % (window['width'], window['height']))
            verifier.mount()
            verifier.capture('preview')
        except Exception as error:
            result['restoration_error'] = str(error)
    (verifier.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    return 0 if result['collected'] and 'restoration_error' not in result else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', type=Path, default=Path('.runtime/settings-pixels'))
    args = parser.parse_args()
    raise SystemExit(verify(args.session, args.owner, args.output))
