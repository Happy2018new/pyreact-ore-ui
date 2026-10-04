"""Publish native-resolution screenshots from the owned demo instance."""
import argparse
import json
from pathlib import Path

from PIL import Image

from capture_settings_pixels import operate
from verify_settings import SettingsVerification


def capture(session, owner, output):
    verifier = SettingsVerification(session, owner, Path('.runtime/settings-gallery'))
    window = json.loads(verifier.run('resize_window.py', '--list-windows'))['windows'][0]
    output.mkdir(parents=True, exist_ok=True)

    def publish(name, png=False):
        source = verifier.output / (name + '.png')
        operate(session, owner, output=source, points=[(.95, .8), (.95, .08)])
        target = output / (name + ('.png' if png else '.jpg'))
        image = Image.open(source)
        image.save(target, **({} if png else dict(quality=95, subsampling=0)))
        print(str(target.resolve()), flush=True)

    try:
        verifier.set_touch(False)
        verifier.mount()
        for page in ('overview', 'toggles', 'sliders', 'fields', 'navigation', 'containers', 'dropdowns', 'social'):
            verifier.page(page)
            publish('settings-' + page)
        verifier.page('toggles')
        verifier.code("from ore_demo import dev_probe\n_result=dev_probe.reveal('lab_scroll_toggles_0','ore_radio_survival')\n",
            'gallery-radio')
        # Reveal the last row as well so the captured group includes its divider.
        verifier.code("from ore_demo import dev_probe\n_result=dev_probe.reveal('lab_scroll_toggles_0','ore_radio_adventure')\n",
            'gallery-radio-last')
        publish('settings-radio', png=True)
        verifier.page('dropdowns')
        verifier.tap('lab_dropdown')
        publish('settings-dropdown', png=True)
        verifier.tap('ore_dropdown_close')
        verifier.page('social')
        verifier.tap('lab_open_friends')
        publish('settings-friends', png=True)
        verifier.tap_at(verifier.scoped_at('lab_player_0', 'ore_player_options', within='ore_friends_surface'),
            'gallery-player-options')
        publish('settings-player-actions', png=True)
        verifier.tap('ore_action_close')
        verifier.tap('ore_friends_close')
        verifier.run('resize_window.py', '--pid', str(window['pid']), '--size', '1008x1440')
        verifier.mount()
        publish('settings-portrait')
    finally:
        verifier.run('resize_window.py', '--pid', str(window['pid']),
                     '--size', '%dx%d' % (window['width'], window['height']))
        verifier.mount()
        publish('settings-overview')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', type=Path, default=Path('docs/images'))
    args = parser.parse_args()
    capture(args.session, args.owner, args.output)
