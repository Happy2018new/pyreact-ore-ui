"""Physical clicks and lossless icon frames for the settings input regression.

This intentionally checks a few affected controls, not the component inventory.
No onClick/onChange callback is invoked by the driver. SDK scroll positioning is
used only to reveal the last ordinary action button for held-state sampling.
"""
import argparse
import json
import time
from pathlib import Path

from PIL import Image, ImageChops

from capture_navigation_animation import capture as capture_animation
from capture_settings_pixels import operate
from profile_navigation import _mount, TARGETS
from verify_seams_scroll import SeamVerification


READ = '''from ore_demo.pyreact import host,native
from ore_demo import dev_probe
from ore_demo.pyreact.primitives import ButtonPrimitive
from ore_demo.oreui.pages import PageScrollPrimitive
from ore_demo.oreui.navigation import NavigationGlintPrimitive
from ore_demo.settings_replica import ReplicaPage
h=host._ACTIVE_HOST[0]
fs=list(dev_probe._walk(h._root_fiber))
pages=[f for f in fs if isinstance(f.comp_type,PageScrollPrimitive)]
active=next(f for f in pages if f.props.get('active'))
def geometry(f):
    c=native.get_control(h,f.native_path)
    return dict(path=f.native_path,position=c.GetGlobalPosition(),size=c.GetSize())
buttons=[]
for f in dev_probe._walk(active):
    if not isinstance(f.comp_type,ButtonPrimitive):continue
    d=geometry(f)
    d.update(key=f.key,enabled=callable(f.props.get('onClick')),states={})
    for name in ('default','hover','pressed'):
        c=native.get_control(h,f.native_path+'/'+name)
        d['states'][name]=dict(visible=c.GetVisible(),skin=f.primitive_state.get('state_'+name))
    buttons.append(d)
replica=next(f for f in dev_probe._walk(active) if f.comp_type is ReplicaPage)
glints={}
for f in fs:
    if not f.key or not str(f.key).startswith('settings_page_'):continue
    g=next(c for c in dev_probe._walk(f) if isinstance(c.comp_type,NavigationGlintPrimitive))
    glints[f.key[len('settings_page_'):]]=geometry(g)
_result=dict(page=active.props['pageKey'],viewport=geometry(active),screen=native.get_screen_size(),
    buttons=buttons,values=replica.hooks[0]['value'],dialog=replica.hooks[1]['value'],glints=glints,
    scrolls={f.props['pageKey']:f.comp_type.get_scroll_position(native.get_control(h,f.native_path)) for f in pages})
'''


def run(session, owner, output):
    output.mkdir(parents=True, exist_ok=True)
    r = SeamVerification(session, owner, output)
    report = dict(scope='settings physical input and visible navigation animations', checks=[])

    def check(name, passed, **details):
        report['checks'].append(dict(name=name, passed=bool(passed), **details))
        report['passed'] = all(c['passed'] for c in report['checks'])
        (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf8')
        print(('PASS ' if passed else 'FAIL ') + name, flush=True)
        if not passed:
            raise AssertionError(name)

    def read():
        return r.code(READ, 'read-interactions')

    def point(target, screen):
        x, y = target['position']; w, h = target['size']
        return [(x + w / 2) / screen[0], (y + h / 2) / screen[1]]

    def click(target, data):
        # Re-enter after a mount so the engine recomputes the native hit target.
        operate(session, owner, points=[[.5, .04], point(target, data['screen'])], click=True)

    def select(page, animate=False):
        target = r.code(TARGETS, 'navigation-targets')['targets'][page]
        if not target['visible']:
            raise AssertionError('Navigation target is outside the sidebar viewport')
        before = read()
        if animate:
            icon = before['glints'][page]
            client = operate(session, owner)['client_size']
            # SDK dimensions can be rounded by a logical pixel. This test uses
            # an integer GUI scale and crops inside the icon's outer border.
            viewport = r.code('from ore_demo.pyreact import native\n'
                'g=native.clientApi.GetEngineCompFactory().CreateGame(native.clientApi.GetLevelId())\n'
                '_result=g.GetScreenViewInfo()', 'viewport')
            ratios = [viewport[i] / before['screen'][i] for i in (0, 1)]
            scale = round(sum(ratios) / 2)
            if not scale or any(abs(ratio - scale) > .03 for ratio in ratios):
                raise AssertionError('Visible-frame check requires an integer GUI scale')
            x, y = icon['position']; w, h = icon['size']
            box = [round(x * scale) + 4, round(y * scale) + 4,
                   round((x + w) * scale) - 4, round((y + h) * scale) - 4]
            if not (box[2] <= client[0] and box[3] <= client[1]):
                raise AssertionError('Animation crop falls outside the actual client')
            replay = sum(c['name'] == page + ': animation changes actual pixels' for c in report['checks'])
            folder = output / ('animation-%s-%d' % (page, replay))
            capture_animation(session, folder, target['position'], box, owner)
            frames = json.loads((folder / 'frames.json').read_text('utf8'))['frames']
            unique = len({f['sha256'] for f in frames})
            # Crop contains only the icon. Selection background and hover cannot
            # produce the required intermediate glint frames.
            check(page + ': animation changes actual pixels', unique >= 4, unique_frames=unique)
            first = Image.open(folder / frames[0]['file']).convert('RGB')
            last = Image.open(folder / frames[-1]['file']).convert('RGB')
            check(page + ': animation returns to the base icon', ImageChops.difference(first, last).getbbox() is None)
        else:
            operate(session, owner, points=[[.5, .04], target['position']], click=True)
        result = read()
        check('physical navigation to ' + page, result['page'] == page)
        return result

    def switch_twice(page):
        before = read()
        target = next(b for b in before['buttons'] if b['enabled'] and
                      'switch_' in b['states']['default']['skin'][2])
        original_skin = target['states']['default']['skin']
        click(target, before)
        after = read()
        changed = next(b for b in after['buttons'] if b['path'] == target['path'])
        check(page + ': switch changes value and native skin',
              before['values'] != after['values'] and original_skin != changed['states']['default']['skin'])
        operate(session, owner, output=output / (page + '-switch-on.png'))
        click(changed, after)
        restored = read()
        check(page + ': second click restores value', restored['values'] == before['values'])
        return target

    def hold(target, name):
        before = read()
        path = target['path']
        def observe(unused):
            data = read()
            button = next(b for b in data['buttons'] if b['path'] == path)
            return dict(states=button['states'],values=data['values'],dialog=data['dialog'])
        sample = operate(session, owner, output=output / (name + '.png'),
            sample=dict(at=point(target, before['screen']), away=[.5, .04], observe=observe))
        states = sample['states']
        actual = {k:v['observation']['runtime'] for k,v in states.items()}
        check(name + ': native hover and held states', actual['hover']['states']['hover']['visible']
            and actual['pressed']['states']['pressed']['visible']
            and actual['pressed-held']['states']['pressed']['visible'])
        check(name + ': cancelled press changes no value or dialog', all(
            state['values'] == before['values'] and state['dialog'] == before['dialog'] for state in actual.values()))
        check(name + ': mouse released', sample['mouse_released'])

    operate(session, owner)
    _mount(r)
    first = read()
    switch = switch_twice('accessibility')
    hold(switch, 'accessibility-switch')
    select('keyboard', animate=True)
    switch_twice('keyboard')
    select('touch', animate=True)
    data = read()
    disabled = next(b for b in data['buttons'] if not b['enabled'])
    click(disabled, data)
    unchanged = read()
    check('disabled action remains inactive', data['values'] == unchanged['values'] and unchanged['dialog'] is None)
    segment = next(b for b in data['buttons'] if b['key'] == 'ore_segment_1' and b['enabled'])
    hold(segment, 'touch-segment')
    click(segment, read())
    check('touch segment changes selection', read()['values'] != data['values'])
    select('accessibility')
    returned = read()
    check('cached page retains native path and edited values',
          returned['viewport']['path'] == first['viewport']['path'] and returned['values'] == first['values'])
    switch_twice('accessibility-returned')
    select('keyboard', animate=True)  # Replay after returning to a retained page.
    select('general')
    r.code(READ.replace('_result=dict(page=',
        'active.comp_type.scroll_to_percent(native.get_control(h,active.native_path),100)\n_result=dict(page='), 'reveal-action')
    time.sleep(.3)
    data = read()
    top = data['viewport']['position'][1]
    bottom = top + data['viewport']['size'][1]
    button = next(b for b in reversed(data['buttons']) if b['enabled']
        and 'button_secondary' in b['states']['default']['skin'][2]
        and b['position'][1] >= top and b['position'][1] + b['size'][1] <= bottom)
    hold(button, 'general-action')
    click(button, read())
    opened = read()
    check('ordinary button opens its dialog on release', opened['dialog'] is not None)
    operate(session, owner, output=output / 'action-dialog.png')
    close = next(b for b in opened['buttons'] if b['key'] == 'ore_dialog_close')
    click(close, opened)
    check('dialog close button responds', read()['dialog'] is None)
    select('touch')
    operate(session, owner, output=output / 'final.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', required=True, type=Path)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    run(args.session, args.owner, args.output)
