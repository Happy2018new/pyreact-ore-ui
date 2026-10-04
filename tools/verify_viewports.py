"""Inspect native layout and real taps at desktop and phone-like window sizes."""
import argparse
import json
import time
from pathlib import Path

from verify_atlas import AtlasVerification, PAGES
from live_support import ROOT, nodes, find_key
from verify_visual_repair import PROBE


def verify(session, owner, output):
    verifier = AtlasVerification(session, owner, output)
    window = json.loads(verifier.run('resize_window.py', '--list-windows'))['windows'][0]
    original = verifier.state()['simulated']
    sizes = []
    verifier.mount()
    tree = verifier.dump('initial')
    frame = next(node['layout'] for node in nodes(tree) if node.get('layout'))
    verifier.screen = [frame['width'], frame['height']]
    try:
        verifier.set_touch(True)
        for name, width, height in [('landscape', 1200, 540), ('portrait', 1008, 1440), ('compact', 504, 800)]:
            resize = json.loads(verifier.run('resize_window.py', '--pid', str(window['pid']),
                                '--size', '%dx%d' % (width, height)))
            sizes.append({'name': name, 'requested': [width, height], 'resize': resize})
            time.sleep(0.4)
            verifier.mount()
            tree = verifier.dump(name + '-initial')
            frame = next(node['layout'] for node in nodes(tree) if node.get('layout'))
            verifier.screen = [frame['width'], frame['height']]
            sizes[-1]['logical'] = verifier.screen
            narrow = verifier.screen[0] < 360 or verifier.screen[0] < verifier.screen[1]
            for page in PAGES:
                if narrow:
                    verifier.tap('lab_catalogue')
                    directory_tree = verifier.dump(name + '-directory-open')
                    directory = find_key(directory_tree, 'lab_directory')
                    verifier.check(name + ' directory opens', directory['props']['visible'])
                    target = find_key(directory_tree, 'lab_page_' + page)
                    control = next(node for node in nodes(target) if node['type'] == 'Button')
                    frame = control['layout']
                    verifier.tap_at([(frame['x'] + frame['width'] / 2) / verifier.screen[0],
                                     (frame['y'] + frame['height'] / 2) / verifier.screen[1]],
                                    name + '-page-' + page)
                    verifier.current_page = page
                else:
                    verifier.page(page)
                tree = verifier.dump(name + '-' + page)
                verifier.check(name + ' mounts ' + page, bool(find_key(tree, 'lab_page_title')))
                overflowing = []
                for node in nodes(tree):
                    layout = node.get('layout')
                    if node['type'] == 'Label' and layout and (
                            layout['x'] < -1 or layout['x'] + layout['width'] > verifier.screen[0] + 1):
                        overflowing.append(node['props'].get('content'))
                verifier.check(name + ' text horizontal bounds ' + page, not overflowing)
                geometry = verifier.code(PROBE, name + '-geometry-' + page)
                verifier.check(name + ' native glyph and image geometry ' + page,
                               not geometry['text_errors'] and not geometry['image_errors'])
                if page in ('buttons', 'selection', 'cards', 'fields', 'dropdowns', 'messages', 'media'):
                    verifier.capture(name + '-' + page)
                if page == 'buttons':
                    before = verifier.event_count()
                    verifier.tap('lab_primary_raised')
                    verifier.check(name + ' native touch tap', verifier.event_count() == before + 1)
                    verifier.scroll('buttons', 12)
                    verifier.capture(name + '-states')
                if page == 'fields':
                    verifier.tap('lab_name_clear')
                    verifier.capture(name + '-field-cleared')
                    verifier.check(name + ' native clear input',
                                   verifier.native_probe('cleared', ['lab_name'])['lab_name']['text'] == '')
                    verifier.tap('lab_name')
                    verifier.input([{'do': 'text', 'value': 'PhoneAtlas'}, {'do': 'key', 'keys': 'enter'},
                                    {'do': 'wait', 'ms': 200}], name + '-input')
                    verifier.check(name + ' native single-line input',
                                   verifier.native_probe('field', ['lab_name'])['lab_name']['text'] == 'PhoneAtlas')
                if page == 'messages':
                    section = next(node for node in nodes(tree) if node['type'] == 'Section'
                                   and node['props'].get('title') == '消息横幅')
                    frame = next(node['layout'] for node in nodes(section) if node.get('layout'))
                    tags = [next(child['layout'] for child in nodes(node) if child.get('layout'))
                            for node in nodes(section) if node['type'] in ('OreTag', 'OreBadge')]
                    verifier.check(name + ' tags stay inside section', len(tags) == 5 and
                                   all(tag['y'] + tag['height'] <= frame['y'] + frame['height'] for tag in tags))
                if page == 'dialogs':
                    for key in ('lab_open_dialog', 'lab_open_progress', 'lab_open_menu', 'lab_open_warning'):
                        verifier.tap(key)
                        verifier.check(name + ' opens ' + key,
                                       find_key(verifier.dump(name + '-' + key), 'lab_dialog')['props']['visible'])
                        bounds = verifier.native_probe('dialog-bounds', ['ore_dialog_surface'])['ore_dialog_surface']
                        x, y = bounds['position']
                        w, h = bounds['size']
                        verifier.check(name + ' bounds ' + key, x >= 11.9 and y >= 11.9 and
                                       x + w <= verifier.screen[0] - 11.9 and y + h <= verifier.screen[1] - 11.9)
                        if key in ('lab_open_dialog', 'lab_open_warning'):
                            verifier.capture(name + '-' + key)
                        verifier.tap('ore_dialog_close')
            if narrow:
                verifier.tap('lab_catalogue')
                tree = verifier.dump(name + '-directory-open-final')
                verifier.check(name + ' directory reopens', find_key(tree, 'lab_directory')['props']['visible'])
                verifier.capture(name + '-directory')
                verifier.tap('ore_drawer_close')
                verifier.check('narrow directory close', not find_key(verifier.dump('closed'), 'lab_directory')['props']['visible'])
        result = {'ok': True, 'count': len(verifier.checks), 'checks': verifier.checks,
                  'sizes': sizes, 'hardware_touch_tested': False}
    except Exception as error:
        result = {'ok': False, 'checks': verifier.checks, 'error': str(error), 'sizes': sizes}
    finally:
        try:
            verifier.run('resize_window.py', '--pid', str(window['pid']),
                         '--size', '%dx%d' % (window['width'], window['height']))
            verifier.mount()
            frame = next(node['layout'] for node in nodes(verifier.dump('restored')) if node.get('layout'))
            verifier.screen = [frame['width'], frame['height']]
            verifier.set_touch(original)
        except RuntimeError as error:
            result['ok'] = False
            result['restoration_error'] = str(error)
    result['count'] = len(verifier.checks)
    (verifier.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', type=Path, default=ROOT / '.runtime/acceptance-viewports')
    args = parser.parse_args()
    raise SystemExit(verify(args.session, args.owner, args.output))
