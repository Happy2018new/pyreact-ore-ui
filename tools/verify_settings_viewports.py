"""Native layout and directory regression for the current settings playground."""
import argparse
import json
import time
from pathlib import Path

from live_support import nodes, find_key
from verify_settings import SettingsVerification, PAGES
from verify_visual_repair import PROBE


def verify(session, owner, output, pages=PAGES):
    verifier = SettingsVerification(session, owner, output)
    window = json.loads(verifier.run('resize_window.py', '--list-windows'))['windows'][0]
    original = verifier.state()['simulated']
    sizes = []
    result = dict(ok=False)
    try:
        verifier.mount()
        verifier.set_touch(True)
        for name, width, height in (('landscape', 1200, 540), ('portrait', 1008, 1440), ('compact', 540, 800)):
            resized = json.loads(verifier.run('resize_window.py', '--pid', str(window['pid']),
                '--size', '%dx%d' % (width, height)))
            time.sleep(.4)
            verifier.mount()
            narrow = verifier.screen[0] < 320 or verifier.screen[0] < verifier.screen[1]
            sizes.append(dict(name=name, requested=[width, height], logical=verifier.screen, resize=resized))
            for page in pages:
                if narrow:
                    verifier.tap('ore_settings_menu')
                    tree = verifier.dump(name + '-directory-' + page)
                    verifier.check(name + ' directory opens ' + page,
                        find_key(tree, 'ore_settings_directory')['props']['visible'])
                    verifier.code('from ore_demo import dev_probe\n_result=dev_probe.reveal(%r,%r)\n' %
                        ('ore_settings_directory_scroll', 'lab_page_' + page), 'reveal-directory')
                    verifier.tap('lab_page_' + page)
                    verifier.current_page = page
                    if page != 'overview':
                        verifier.check(name + ' directory closes after navigation ' + page,
                            not find_key(verifier.dump('directory-closed'), 'ore_settings_directory')['props']['visible'])
                    else:
                        verifier.tap('ore_drawer_close')
                else:
                    verifier.page(page)
                tree = verifier.dump(name + '-' + page)
                verifier.check(name + ' page ' + page, verifier.business()['page'] == page)
                overflow = [n['props'].get('content') for n in nodes(tree) if n['type'] == 'Label'
                    and n.get('layout') and (n['layout']['x'] < -1 or
                    n['layout']['x'] + n['layout']['width'] > verifier.screen[0] + 1)]
                verifier.check(name + ' horizontal text bounds ' + page, not overflow)
                geometry = verifier.code(PROBE, name + '-geometry-' + page)
                verifier.check(name + ' glyph and image geometry ' + page,
                    not geometry['text_errors'] and not geometry['image_errors'])
                if page == 'toggles':
                    group = find_key(tree, 'lab_radio')
                    frame = next(node['layout'] for node in nodes(group) if node.get('layout'))
                    options = [find_key(group, 'ore_radio_' + option)['layout']
                               for option in ('survival', 'creative', 'adventure')]
                    verifier.check(name + ' radio rows fit before divider',
                        all(option['y'] >= frame['y'] and option['y'] + option['height'] <=
                            frame['y'] + frame['height'] + .1 for option in options))
                if page in ('overview', 'selection', 'sliders', 'fields', 'dropdowns', 'media'):
                    verifier.capture(name + '-' + page)
                if page == 'dropdowns':
                    verifier.tap('lab_dropdown')
                    probe = verifier.native_probe('menu-bounds', ['ore_dropdown_surface'])['ore_dropdown_surface']
                    x, y = probe['position']
                    w, h = probe['size']
                    verifier.check(name + ' dropdown fits screen', x >= 0 and y >= 0 and
                        x + w <= verifier.screen[0] + .1 and y + h <= verifier.screen[1] + .1)
                    verifier.capture(name + '-dropdown-open')
                    verifier.tap('ore_dropdown_close')
                if page == 'dialogs':
                    for key in ('lab_open_dialog', 'lab_open_progress', 'lab_open_warning'):
                        verifier.tap(key)
                        probe = verifier.native_probe('dialog-bounds', ['ore_dialog_surface'])['ore_dialog_surface']
                        x, y = probe['position']
                        w, h = probe['size']
                        verifier.check(name + ' dialog fits ' + key, x >= 11.9 and y >= 11.9 and
                            x + w <= verifier.screen[0] - 11.9 and y + h <= verifier.screen[1] - 11.9)
                        verifier.tap('ore_dialog_close')
                if page == 'social':
                    verifier.tap('lab_open_friends')
                    for key in ('ore_friends_surface', 'ore_friends_search'):
                        probe = verifier.native_probe('social-bounds-' + key, [key])[key]
                        x, y = probe['position']
                        w, h = probe['size']
                        verifier.check(name + ' social bounds ' + key, x >= 0 and y >= 0 and
                            x + w <= verifier.screen[0] + .1 and y + h <= verifier.screen[1] + .1)
                    verifier.capture(name + '-friends')
                    verifier.tap_at(verifier.scoped_at('lab_player_0', 'ore_player_options',
                        within='ore_friends_surface'), name + '-player-options')
                    verifier.check(name + ' player options open', verifier.business()['overlay'] == 'friend_options')
                    probe = verifier.native_probe('social-action-bounds', ['ore_action_surface'])['ore_action_surface']
                    x, y = probe['position']
                    w, h = probe['size']
                    verifier.check(name + ' action menu fits screen', x >= 0 and y >= 0 and
                        x + w <= verifier.screen[0] + .1 and y + h <= verifier.screen[1] + .1)
                    verifier.capture(name + '-player-actions')
                    verifier.tap('ore_action_close')
                    verifier.check(name + ' action close is above friends drawer',
                        verifier.business()['overlay'] == 'drawer')
                    verifier.tap_at(verifier.scoped_at('lab_player_0', 'ore_player_options', within='ore_friends_surface'),
                        name + '-reopen-player-options')
                    before = verifier.event_count()
                    verifier.tap('ore_action_0')
                    verifier.check(name + ' player action returns once',
                        verifier.event_count() == before + 1 and verifier.business()['overlay'] == 'drawer')
                    verifier.tap('ore_friends_close')
                    verifier.check(name + ' friends closes', verifier.business()['overlay'] is None)
            verifier.capture(name + '-last-page')
        result['ok'] = True
    except Exception as error:
        result['error'] = str(error)
    finally:
        try:
            verifier.run('resize_window.py', '--pid', str(window['pid']),
                         '--size', '%dx%d' % (window['width'], window['height']))
            verifier.mount()
            verifier.set_touch(original)
            verifier.mount()
            verifier.capture('preview')
        except Exception as error:
            result.update(ok=False, restoration_error=str(error))
    result.update(checks=verifier.checks, count=len(verifier.checks), sizes=sizes,
                  pages=pages, hardware_touch_tested=False)
    (verifier.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', type=Path, default=Path('.runtime/settings-viewports'))
    parser.add_argument('--pages', nargs='+', choices=PAGES, default=PAGES)
    args = parser.parse_args()
    raise SystemExit(verify(args.session, args.owner, args.output, args.pages))
