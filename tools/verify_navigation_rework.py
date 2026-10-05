"""Focused live checks for navigation bevels, separators and sidebar boundaries.

Run on the demo at a 2016 x 1164 client (504 x 291 logical pixels).
Captures are lossless. No other playground controls are exercised.
"""
import argparse
import json
import time
from pathlib import Path

from PIL import Image

from capture_settings_pixels import operate
from verify_settings import SettingsVerification


def fixed_boundaries(image):
    # Windows 11 rounds the client window's bottom corners. Check the straight
    # portions only; retain the entire native capture, including those corners.
    return all(image.getpixel((x, y)) == (30, 30, 31)
               for x in (0, 1, 2, 3, 668, 669, 670, 671) for y in range(100, 1148))


def check_top_shadow(runtime, session, owner, output, key):
    runtime.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host, ScrollView\n'
        'items=dev_probe.controls(["ore_settings_navigation",%r])\n'
        'scroll=items["ore_settings_navigation"]\n'
        'control=host._ACTIVE_HOST[0].GetBaseUIControl(scroll["path"])\n'
        '_result=ScrollView.scroll_to(control,scroll["scroll"]+items[%r]["position"][1]-scroll["position"][1]+1)\n'
        % (key, key), 'align-selected-under-shadow')
    time.sleep(.2)
    path = output / 'selected-under-shadow.png'
    operate(session, owner, output=path, points=[(.9, .04)])
    image = Image.open(path).convert('RGB')
    return dict(
        shadow_follows_underlying_color=all(image.getpixel((500, y)) == (30, 31, 31) for y in range(100, 104)),
        content_below_shadow=all(image.getpixel((500, y)) == (72, 73, 74) for y in range(104, 108)),
        corners_stay_opaque=all(image.getpixel((x, y)) == (30, 30, 31)
            for x in (0, 1, 2, 3, 668, 669, 670, 671) for y in range(100, 104)))


def verify(session, owner, output):
    runtime = SettingsVerification(session, owner, output)
    runtime.mount()
    if runtime.screen != [504, 291]:
        raise RuntimeError('Set the owned client to 2016x1164 before this pixel check')
    if runtime.state()['touch']:
        raise RuntimeError('Mouse mode is required for the hover comparisons')
    results = []
    captures = {}

    def capture(name, hover=None):
        points = [(.9, .04)]
        if hover:
            points.append(runtime.at(hover))
        path = output / (name + '.png')
        metadata = operate(session, owner, output=path, points=points)
        if metadata['client'][2:] != [2016, 1164]:
            raise RuntimeError('Native client size changed during the pixel check')
        controls = runtime.native_probe(name + '-controls',
            ['lab_page_overview', 'lab_page_selection', 'lab_page_buttons', 'ore_settings_navigation'])
        captures[name] = dict(image=str(path), metadata=metadata, controls=controls)
        return Image.open(path).convert('RGB'), controls

    def check(name, condition):
        results.append(dict(name=name, passed=bool(condition)))
        print(('PASS ' if condition else 'FAIL ') + name, flush=True)

    def row_pixels(image, control, selected=False, hovered=False):
        y = round(control['position'][1] * 4)
        height = round(control['size'][1] * 4)
        fill = (72, 73, 74) if selected or hovered else (49, 50, 51)
        top = [(29, 30, 31), (43, 44, 44)] if selected else [(69, 70, 71), (90, 91, 92)]
        bottom = [(90, 91, 92), (69, 70, 71)] if selected else [(43, 44, 44), (29, 30, 31)]
        expected = ([top[0]] * 2 + [top[1]] * 2 + [fill] * (height - 8) +
                    [bottom[0]] * 2 + [bottom[1]] * 2) if selected or hovered else [fill] * height
        # These columns contain no text or icon. This is a supplementary border
        # check; full rows, including text and scrollbar, remain in the captures.
        return all(image.getpixel((x, y + offset)) == color
                   for x in (4, 500, 639, 664, 667)
                   for offset, color in enumerate(expected))

    for name, hover in [('general-default', None), ('general-hover', 'lab_page_overview'),
                        ('advanced-unselected-hover', 'lab_page_selection')]:
        image, controls = capture(name, hover)
        check(name + ': selected four half-pixel bands',
              row_pixels(image, controls['lab_page_overview'], selected=True))
        check(name + ': adjacent row state', row_pixels(image, controls['lab_page_selection'],
              hovered=hover == 'lab_page_selection'))
        if hover:
            check(name + ': native hover active', controls[hover]['states']['hover']['visible'])

    runtime.tap('lab_page_selection')
    check('click changes selected page', runtime.business()['page'] == 'selection')
    for name, hover in [('advanced-default', None), ('advanced-hover', 'lab_page_selection'),
                        ('general-unselected-hover', 'lab_page_overview')]:
        image, controls = capture(name, hover)
        check(name + ': selected four half-pixel bands',
              row_pixels(image, controls['lab_page_selection'], selected=True))
        check(name + ': adjacent row state', row_pixels(image, controls['lab_page_overview'],
              hovered=hover == 'lab_page_overview'))
        if hover:
            check(name + ': native hover active', controls[hover]['states']['hover']['visible'])

    # Keep the separator and its first child away from either viewport edge.
    runtime.code("from ore_demo import dev_probe\n_result=dev_probe.reveal('ore_settings_navigation','lab_page_navigation')\n",
                 'reveal-navigation-group')
    time.sleep(.3)
    for name, hover in [('group-default', None), ('group-first-hover', 'lab_page_buttons')]:
        image, controls = capture(name, hover)
        first_y = round(controls['lab_page_buttons']['position'][1] * 4)
        check(name + ': first item visible', 112 <= first_y <= 900)
        check(name + ': four-pixel group bands reach boundary', all(
            image.getpixel((x, first_y - 8 + dy)) == color
            for x in (4, 500, 639, 664, 667)
            for dy, color in enumerate([(29, 30, 31)] * 4 + [(69, 70, 71)] * 4)))
        check(name + ': first item edge state', row_pixels(image, controls['lab_page_buttons'],
              hovered=hover is not None))
        check(name + ': continuous fixed side boundaries', fixed_boundaries(image))

    runtime.tap('lab_page_buttons')
    image, controls = capture('group-first-selected')
    check('group first item selected', runtime.business()['page'] == 'buttons')
    check('group first selected retains thin bevel', row_pixels(image, controls['lab_page_buttons'], selected=True))
    for name, passed in check_top_shadow(runtime, session, owner, output, 'lab_page_buttons').items():
        check(name, passed)
    report = dict(scope='navigation only', physical_scale=4, client=[2016, 1164],
                  boundary_sample_y=[100, 1148],
                  boundary_exclusion='Bottom 16 client pixels include the Windows 11 rounded window corners',
                  checks=results, captures=captures, passed=all(item['passed'] for item in results))
    output.mkdir(parents=True, exist_ok=True)
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    runtime.mount()
    operate(session, owner, points=[(.9, .04)])
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', type=Path, default=Path('.runtime/nav-rework/actual'))
    args = parser.parse_args()
    raise SystemExit(0 if verify(args.session, args.owner, args.output.resolve()) else 1)
