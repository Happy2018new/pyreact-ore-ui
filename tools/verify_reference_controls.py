"""Whole-control acceptance with fixed endpoints, text and surrounding pixels."""
import argparse
import importlib.util
import json
import time
from pathlib import Path

from PIL import Image
from verify_settings import SettingsVerification
from capture_settings_pixels import operate

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('ore_pixels',
    ROOT / '.agents/skills/bedrock-ore-reference/scripts/pixels.py')
pixels = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pixels)


def verify(session, owner, output, cases, only):
    verifier = SettingsVerification(session, owner, output)
    rows = []
    result = dict(collected=False, visual_pass=False, scope='Complete native controls with text and outer margin', rows=rows)
    window = json.loads(verifier.run('resize_window.py', '--list-windows'))['windows'][0]
    try:
        verifier.run('resize_window.py', '--pid', str(window['pid']), '--size', '2016x1172')
        verifier.mount()
        verifier.set_touch(False)
        for case in cases:
            if only and case['kind'] not in only:
                continue
            verifier.code('from ore_demo.pyreact import navigator\n'
                'from ore_demo.reference_fixture import OreReferenceFixture\n'
                'navigator.reset(OreReferenceFixture(kind=%r,selected=%r,disabled=%r))\n_result=True\n'
                % (case['kind'], case.get('selected', True), case.get('disabled', False)), 'mount-reference')
            time.sleep(.4)
            box = verifier.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host,native\n'
                'fiber=next(f for f in dev_probe._walk(host._ACTIVE_HOST[0]._root_fiber) if f.key==%r)\n'
                'control=host._ACTIVE_HOST[0].GetBaseUIControl(fiber.native_path)\n'
                '_result=dict(position=control.GetGlobalPosition(),size=control.GetSize(),logical_screen=native.get_screen_size())\n'
                % case.get('bounds_key', 'reference_bounds'), 'reference-box')
            scale = 4
            actual_box = pixels.logical_box(box['position'], box['size'], scale, margin=1)
            geometry = operate(session, owner, points=[])
            if abs(geometry['client_size'][0] / box['logical_screen'][0] - scale) > .005:
                raise ValueError('Native scale does not match reference scale 4')
            for state in case['states']:
                points = [(.95, .8), (.9, .2)]
                if state.get('hover'):
                    x, y = state['hover']
                    points.append(((box['position'][0] + x) * scale / geometry['client_size'][0],
                                   (box['position'][1] + y) * scale / geometry['client_size'][1]))
                stem = case['name'] + '-' + state['name']
                full = verifier.output / (stem + '-full.png')
                capture = operate(session, owner, output=full, points=points)
                actual = verifier.output / (stem + '-actual.png')
                reference = verifier.output / (stem + '-reference.png')
                pixels.checked_crop(full, actual_box).save(actual)
                source = ROOT / state['source']
                pixels.checked_crop(source, state['box']).save(reference)
                row = dict(name=stem, kind=case['kind'], actual_box=actual_box,
                    reference_box=state['box'], native_geometry=box, capture=capture,
                    reference_source=str(source), includes_text=True, margin_logical=1)
                try:
                    row.update(pixels.compare(reference, actual, verifier.output / stem))
                except ValueError as error:
                    row.update(within_tolerance=False, dimension_error=str(error),
                        actual_native_size=Image.open(actual).size, reference_size=Image.open(reference).size)
                rows.append(row)
                print(json.dumps({key:row[key] for key in ('name','within_tolerance')}, ensure_ascii=False), flush=True)
        result['collected'] = True
        result['visual_pass'] = bool(rows) and all(row['within_tolerance'] for row in rows)
    except Exception as error:
        result['error'] = str(error)
    finally:
        try:
            verifier.run('resize_window.py', '--pid', str(window['pid']), '--size', '%dx%d' % (window['width'],window['height']))
            verifier.mount()
        except Exception as error:
            result['restoration_error'] = str(error)
        (verifier.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2),encoding='utf8')
    return 0 if result['visual_pass'] and 'restoration_error' not in result else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', type=Path, default=Path('.runtime/reference-controls'))
    parser.add_argument('--cases', type=Path, default=ROOT / 'tools/reference_cases.json')
    parser.add_argument('--only', nargs='+')
    args=parser.parse_args()
    raise SystemExit(verify(args.session,args.owner,args.output,json.loads(args.cases.read_text(encoding='utf8')),args.only))
