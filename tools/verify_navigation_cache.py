"""Targeted retained-page checks against a bound development client."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops
from verify_seams_scroll import SeamVerification
from capture_settings_pixels import operate
from profile_navigation import _mount

WALK = '''from ore_demo.pyreact import host,native
from ore_demo import dev_probe
from ore_demo.oreui.pages import PageScrollPrimitive
from ore_demo.settings_replica import ReplicaPage
h=host._ACTIVE_HOST[0]
fs=list(dev_probe._walk(h._root_fiber))
pages=[f for f in fs if isinstance(f.comp_type,PageScrollPrimitive)]
active=next(f for f in pages if f.props.get('active'))
control=h.GetBaseUIControl(active.native_path)
'''
STATE = WALK + '''_result=dict(active=active.props['pageKey'],path=active.native_path,
    pages=[f.props['pageKey'] for f in pages],size=control.GetSize(),position=control.GetGlobalPosition(),
    parent=native.get_size(h,active.native_parent_path),
    scrolls=dict((f.props['pageKey'],f.comp_type.get_scroll_position(h.GetBaseUIControl(f.native_path))) for f in pages),
    values=dict((f.props['page'],f.hooks[0]['value']) for f in fs if f.comp_type is ReplicaPage))
'''


def run(session, owner, output):
    output.mkdir(parents=True, exist_ok=True)
    r = SeamVerification(session, owner, output)
    checks = []
    def check(name, passed, **data):
        checks.append(dict(name=name, passed=bool(passed), **data))
        (output / 'report.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), 'utf8')
        print(('PASS ' if passed else 'FAIL ') + name, flush=True)
    def select(page):
        r.code('from ore_demo.pyreact import host\nfrom ore_demo import dev_probe\n'
            'f=next(f for f in dev_probe._walk(host._ACTIVE_HOST[0]._root_fiber) if f.key==%r)\n'
            'f.props["onClick"]()\n_result=True' % ('settings_page_' + page), 'select-' + page)
        time.sleep(.3)
    operate(session, owner)
    _mount(r)
    select('keyboard')
    r.code(WALK + '''from ore_demo.oreui import OreSwitch
f=next(f for f in dev_probe._walk(active) if f.comp_type is OreSwitch and not f.props.get('disabled'))
f.props['onChange'](not f.props['value'])
_result=True''', 'change-keyboard')
    time.sleep(.25)
    first = r.code(STATE, 'keyboard-before')
    operate(session, owner, points=[[.5, .015]], output=output / 'before.png')
    r.code(WALK + '_result=active.comp_type.scroll_to_percent(control,70)', 'scroll-keyboard')
    time.sleep(.2)
    scrolled = r.code(STATE, 'keyboard-scrolled')
    check('keyboard scroll reaches content', scrolled['scrolls']['keyboard'] > 50)
    select('controller')
    select('touch')
    select('keyboard')
    after = r.code(STATE, 'keyboard-return')
    check('visited page reuses native controls', after['path'] == first['path'])
    check('return resets scroll and keeps edited values', after['scrolls']['keyboard'] == 0
          and after['values']['keyboard'] == first['values']['keyboard'])
    time.sleep(.7)
    operate(session, owner, points=[[.5, .015]], output=output / 'after.png')
    before_image = Image.open(output / 'before.png').convert('RGB')
    after_image = Image.open(output / 'after.png').convert('RGB')
    # Content starts to the right of the sidebar. Exclude debug FPS and glints.
    crop = (int(before_image.width * .34), 125, before_image.width - 4, before_image.height - 4)
    difference = ImageChops.difference(before_image.crop(crop), after_image.crop(crop))
    check('retained page pixels match before switching', difference.getbbox() is None, crop=crop)
    select('touch')
    saved = r.code(STATE, 'before-wheel')
    operate(session, owner, steps=[dict(do='scroll', at=[.7, .6], amount=-1), dict(do='wait', ms=300)])
    wheeled = r.code(STATE, 'after-wheel')
    check('wheel reaches active page only', wheeled['scrolls']['touch'] > 0
          and all(wheeled['scrolls'][k] == v for k,v in saved['scrolls'].items() if k != 'touch'),
          before=saved['scrolls'], after=wheeled['scrolls'])
    resize = [sys.executable, '.agents/skills/pyreact-debugging/scripts/instances.py', 'exec',
        '--session', str(session), '--owner', owner, '--', 'resize_window.py', '--size']
    original_size = operate(session, owner)['client_size']
    try:
        subprocess.run(resize + ['1600x1000'], check=True, capture_output=True)
        select('keyboard')
        resized = r.code(STATE, 'resized-keyboard')
        check('hidden page relayouts after resize', resized['size'] == resized['parent']
              and resized['size'] != first['size'], before=first['size'], after=resized['size'])
    finally:
        subprocess.run(resize + ['%sx%s' % tuple(original_size)], check=True, capture_output=True)
    for page in ('touch','controller','video','audio','general','account','storage','creator','language'):
        select(page)
    evicted = r.code(STATE, 'after-eviction')
    check('page retention is bounded', len(evicted['pages']) == 8 and 'keyboard' not in evicted['pages'])
    select('keyboard')
    restored = r.code(STATE, 'after-remount')
    check('evicted page restores saved values', restored['path'] != first['path']
          and restored['values']['keyboard'] == first['values']['keyboard'])
    r.code('from ore_demo.pyreact import navigator,host\n'
        'host._ore_cache_test_host=host._ACTIVE_HOST[0]\nnavigator.clear()\n_result=True', 'close')
    time.sleep(.2)
    leftovers = r.code('from ore_demo.pyreact import host\nh=host._ore_cache_test_host\n'
        '_result=dict(animations=len(h._animation_frames),buttons=len(h._button_handlers))\n'
        'del host._ore_cache_test_host', 'cleanup')
    check('closed settings leave no active handlers', not leftovers['animations'] and not leftovers['buttons'])
    _mount(r)
    select('touch')
    operate(session, owner, output=output / 'final.png')
    if not all(c['passed'] for c in checks):
        raise AssertionError('Targeted navigation checks failed; inspect report.json')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--session', required=True, type=Path)
    p.add_argument('--owner', required=True)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    run(a.session, a.owner, a.output)
