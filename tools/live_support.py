"""Functional + real-pointer acceptance through the installed debugging skill."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.agents/skills/pyreact-debugging/scripts'
PLAYGROUND_PAGES = ('按钮', '选项', '滑块', '反馈', '资源', '弹窗')


def nodes(tree):
    yield tree
    for child in tree.get('children', []):
        yield from nodes(child)


def find_key(tree, key):
    matches = [n for n in nodes(tree) if n.get('key') == key]
    if len(matches) != 1:
        raise AssertionError('Expected one key %s, got %s' % (key, len(matches)))
    return matches[0]


def labels(tree):
    return [n['props'].get('content') for n in nodes(tree) if n['type'] == 'Label']


class RuntimeTools:
    def __init__(self, session, owner, output):
        self.route = [sys.executable, '-X', 'utf8', str(SCRIPTS / 'instances.py'), 'exec',
                      '--session', session, '--owner', owner, '--']
        self.output = output.resolve()
        self.output.mkdir(parents=True, exist_ok=True)
        self.checks = []

    def run(self, script, *args):
        environment = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
        result = subprocess.run(self.route + [script] + list(args), cwd=ROOT,
                                capture_output=True, text=True, encoding='utf8', env=environment, timeout=45)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        return result.stdout

    def dump(self, name):
        path = self.output / (name + '.json')
        self.run('get_ui_tree.py', '--output', str(path), '--quiet')
        return json.loads(path.read_text(encoding='utf8'))['tree']

    def click(self, key):
        return self.run('simulate.py', 'click', '--key', key, '--settle', '0.25')

    def click_label(self, label):
        return self.run('simulate.py', 'click', '--label', label, '--settle', '0.25')

    def check(self, label, condition):
        if not condition:
            raise AssertionError(label)
        self.checks.append(label)

    def _pointer_input(self, tree, key, action, name, capture=False):
        target = find_key(tree, key)
        control = next(n for n in nodes(target) if n['type'] in ('Button', 'Slider'))
        frame = control['layout']
        screen = next(n for n in nodes(tree) if n.get('layout'))['layout']
        at = [(frame['x'] + frame['width'] / 2) / screen['width'],
              (frame['y'] + frame['height'] / 2) / screen['height']]
        if action == 'move':
            steps = [{'do': 'move', 'at': at}, {'do': 'wait', 'ms': 350}]
        else:
            steps = [{'do': 'click', 'at': at}, {'do': 'wait', 'ms': 250}]
        args = {'op': '/run', 'args': {'steps': steps, 'budget_ms': 2000}}
        path = self.output / (name + '.json')
        path.write_text(json.dumps(args), encoding='utf8')
        windows = json.loads(self.run('resize_window.py', '--list-windows'))['windows']
        if len(windows) != 1:
            raise RuntimeError('Expected one window belonging to this bound game')
        window = windows[0]
        # Activate only the bound game just before real input. Preserve its size
        # and origin. Captured input still checks focus and can reject safely.
        self.run('resize_window.py', '--pid', str(window['pid']), '--size',
                 '%dx%d' % (window['width'], window['height']), '--no-center', '--settle', '0')
        result = self.run('mcdk.py', 'call', 'mc_input', '--args-file', str(path))
        (self.output / (name + '-result.json')).write_text(result, encoding='utf8')
        if capture:
            self.run('mcdk.py', 'capture', '--output', str(self.output / (name + '.jpg')))
        return result

    def pointer(self, tree, key):
        return self._pointer_input(tree, key, 'click', 'pointer-' + key, capture=False)

    def click_at(self, at, name):
        args = {'op': '/run', 'args': {'steps': [
            {'do': 'click', 'at': at}, {'do': 'wait', 'ms': 300}], 'budget_ms': 2000}}
        path = self.output / (name + '.json')
        path.write_text(json.dumps(args), encoding='utf8')
        windows = json.loads(self.run('resize_window.py', '--list-windows'))['windows']
        if len(windows) != 1:
            raise RuntimeError('Expected one window belonging to this bound game')
        window = windows[0]
        self.run('resize_window.py', '--pid', str(window['pid']), '--size',
                 '%dx%d' % (window['width'], window['height']), '--no-center', '--settle', '0')
        result = self.run('mcdk.py', 'call', 'mc_input', '--args-file', str(path))
        (self.output / (name + '-result.json')).write_text(result, encoding='utf8')
        return result

    def hover(self, tree, key, name):
        return self._pointer_input(tree, key, 'move', name, capture=True)

    def drag(self, tree, key, start=0.25, end=0.8, name=None):
        target = find_key(tree, key)
        slider = next(n for n in nodes(target) if n['type'] == 'Slider')
        frame = slider['layout']
        screen = next(n for n in nodes(tree) if n.get('layout'))['layout']
        y = (frame['y'] + frame['height'] / 2) / screen['height']
        at_start = [(frame['x'] + frame['width'] * start) / screen['width'], y]
        at_end = [(frame['x'] + frame['width'] * end) / screen['width'], y]
        args = {'op': '/run', 'args': {'steps': [
            {'do': 'drag', 'from': at_start, 'to': at_end, 'segments': 8},
            {'do': 'wait', 'ms': 400}], 'budget_ms': 3000}}
        name = name or ('drag-' + key)
        path = self.output / (name + '.json')
        path.write_text(json.dumps(args), encoding='utf8')
        windows = json.loads(self.run('resize_window.py', '--list-windows'))['windows']
        if len(windows) != 1:
            raise RuntimeError('Expected one window belonging to this bound game')
        window = windows[0]
        self.run('resize_window.py', '--pid', str(window['pid']), '--size',
                 '%dx%d' % (window['width'], window['height']), '--no-center', '--settle', '0')
        result = self.run('mcdk.py', 'call', 'mc_input', '--args-file', str(path))
        (self.output / (name + '-result.json')).write_text(result, encoding='utf8')
        return result

    def edge_score(self, tree, key, image_name):
        target = find_key(tree, key)
        control = next(n for n in nodes(target) if n['type'] in ('Button', 'Slider'))
        frame = control['layout']
        screen = next(n for n in nodes(tree) if n.get('layout'))['layout']
        image = Image.open(self.output / image_name).convert('RGB')
        scale_x = image.width / float(screen['width'])
        scale_y = image.height / float(screen['height'])
        left = max(0, int(frame['x'] * scale_x))
        right = min(image.width - 1, int((frame['x'] + frame['width']) * scale_x))
        top = max(0, int(frame['y'] * scale_y))
        bottom = min(image.height - 1, int((frame['y'] + frame['height']) * scale_y))
        pixels = []
        for x in range(left, right + 1):
            for y in (top, bottom):
                pixels.append(max((image.getpixel((x, max(0, min(image.height - 1, y + delta))))
                                   for delta in range(-2, 3)), key=sum))
        for y in range(top, bottom + 1):
            for x in (left, right):
                pixels.append(max((image.getpixel((max(0, min(image.width - 1, x + delta)), y))
                                   for delta in range(-2, 3)), key=sum))
        return sum(1 for pixel in pixels if sum(pixel) > 600)

    def native_probe(self, name, keys):
        source = self.output / (name + '.py')
        source.write_text(
            'from ore_demo import dev_probe\n_result = dev_probe.controls(%r)\n' % keys,
            encoding='utf8')
        raw = self.run('mcdk.py', 'exec', str(source))
        result = json.loads(raw)
        (self.output / (name + '.json')).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
        return result

