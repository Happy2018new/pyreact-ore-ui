"""Compare stepped slider values with actual Ore track pixels in both input modes."""
import argparse
import json
from pathlib import Path

from PIL import Image

from live_support import find_key, nodes
from verify_atlas import AtlasVerification


class SliderSkinVerification(AtlasVerification):
    def fill(self, key, expected, name):
        control = self.native_probe(name + '-control', [key])[key]
        self.capture(name)
        with Image.open(self.output / (name + '.jpg')) as source:
            screenshot = source.convert('RGB')
        sx, sy = screenshot.width / self.screen[0], screenshot.height / self.screen[1]
        x, y = control['position']
        width, height = control['size']
        left, right = round(x * sx), round((x + width) * sx)
        center = round((y + height / 2) * sy)
        green = 0
        for column in range(left, right):
            pixels = [screenshot.getpixel((column, row)) for row in range(center - 2, center + 3)]
            green += any(g > r + 20 and g > b + 20 for r, g, b in pixels)
        fraction = green / (right - left)
        self.check(name + ' rendered fill follows value', abs(fraction - expected) < 0.12)
        return fraction

    def verify(self):
        self.mount()
        frame = next(node['layout'] for node in nodes(self.dump('initial')) if node.get('layout'))
        self.screen = [frame['width'], frame['height']]
        original = self.state()['simulated']
        measurements = []
        try:
            for touch in (False, True):
                self.set_touch(touch)
                self.mount()
                mode = 'touch' if touch else 'mouse'
                self.page('sliders')
                for value in range(5):
                    tree = self.dump(mode + '-step-target')
                    slider = next(node for node in nodes(find_key(tree, 'lab_step_slider'))
                                  if node['type'] == 'Slider')
                    self.run('simulate.py', 'slider', '--node-id', slider['id'],
                             '--value', str(value), '--settle', '0.3')
                    readback = self.native_probe(mode + '-step-value', ['lab_step_slider'])['lab_step_slider']['value']
                    self.check(mode + ' step value ' + str(value), readback == value)
                    measurements.append(dict(mode=mode, value=value,
                        fill=self.fill('lab_step_slider', value / 4, mode + '-step-' + str(value))))
                value = self.drag_slider('lab_step_slider', 0.5)
                self.check(mode + ' native step drag snaps to middle', value == 2)
                measurements.append(dict(mode=mode, value=value,
                    fill=self.fill('lab_step_slider', 0.5, mode + '-native-middle')))
                if not touch:
                    self.hover('lab_step_slider', 'slider_bar_hover')
                    self.fill('lab_step_slider', 0.5, 'mouse-step-hover')
                continuous = self.drag_slider('lab_slider', 0.8)
                self.check(mode + ' continuous drag preserved', 0.7 < continuous < 0.9)
                self.fill('lab_slider', continuous, mode + '-continuous')
                self.tap('lab_lock_slider')
                locked = self.drag_slider('lab_slider', 0.2)
                self.check(mode + ' locked slider preserved', abs(locked - continuous) < 0.001)
                self.scroll('sliders', 100)
                disabled = self.drag_slider('lab_slider_disabled', 0.2)
                self.check(mode + ' disabled slider preserved', abs(disabled - 0.65) < 0.001)
        finally:
            self.set_touch(original)
        self.mount()
        self.page('sliders')
        self.capture('current')
        return dict(ok=True, count=len(self.checks), checks=self.checks, measurements=measurements,
                    hardware_touch_tested=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', type=Path, default=Path('.runtime/repair-slider-skin'))
    args = parser.parse_args()
    verifier = SliderSkinVerification(args.session, args.owner, args.output)
    try:
        result = verifier.verify()
    except Exception as error:
        result = dict(ok=False, checks=verifier.checks, error=str(error))
    (verifier.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
