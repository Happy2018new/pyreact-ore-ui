"""Publish the reference version, sampled states and limits of pixel evidence."""
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / '.runtime/bedrock-reference'


def main(game_pixels=None):
    groups = [
        ('OreNavigationItem', 'world_edit_multiplayer', 'nav-selected-final', 'selected', [4, 964, 644, 1060]),
        ('OreNavigationItem', 'world_edit_multiplayer', 'nav-unselected-final', 'unselected', [4, 868, 644, 964]),
        ('OreSwitch', 'world_edit_multiplayer', 'switch-on-final', 'on', [1852, 124, 1972, 188]),
        ('OreSwitch', 'video', 'switch-off-final', 'off', [1852, 527, 1972, 591]),
        ('OreSegmentedControl', 'world_edit_multiplayer', 'segment-selected-final', 'selected', [1132, 400, 1552, 520]),
        ('OreSegmentedControl', 'world_edit_multiplayer', 'segment-unselected-final', 'unselected', [716, 400, 1136, 520]),
        ('OreField', 'world_edit_general', 'field-final', 'value', [720, 168, 1968, 264]),
        ('OreSlider', 'video', 'slider-final', 'thumb', [1164, 504, 1228, 568]),
        ('OreSlider', 'video', 'disabled-slider-fixed', 'disabled', None),
        ('OreNavigationItem', 'video', 'resume-nav-selected', 'selected', None),
        ('OreNavigationItem', 'video', 'resume-nav-unselected', 'unselected', None),
        ('OreSwitch', 'video', 'resume-switch-on', 'on', None),
        ('OreSlider', 'video', 'resume-slider', 'stepped_thumb', None),
        ('OreSlider', 'video', 'resume-slider-disabled', 'disabled_thumb', None),
    ]
    rows = []
    for component, page, stem, variant, box in groups:
        for state in ('default', 'hover'):
            source = REFERENCE / (stem + '-' + state + '.json')
            data = json.loads(source.read_text(encoding='utf8'))
            rows.append(dict(component=component, page=page, variant=variant, state=state,
                source=str(source.with_suffix('.png').relative_to(ROOT)).replace('\\', '/'),
                sha256=data['sha256'], client=data['client'], cursor=data['cursor'],
                version=data['version'], crop=box, reference_pixel_scale=4, input='absolute desktop pointer'))
    comparisons = json.loads((REFERENCE / 'skin-audit/result.json').read_text(encoding='utf8'))
    for row in comparisons['rows']:
        for name in ('reference', 'actual'):
            row[name] = str(Path(row[name]).relative_to(ROOT)).replace('\\', '/')
    result = dict(date='2026-10-04', executable='D:/Program/Minecraft/Minecraft.Windows.exe',
        version='1.26.5203.0', captures=rows, generated_skin_comparisons=comparisons,
        observed_pages=['settings_accessibility', 'settings_video', 'play_worlds',
                        'world_edit_general', 'world_edit_advanced', 'world_edit_multiplayer'],
        invalid_evidence='Earlier SetCursorPos-only hover captures are excluded from these state comparisons.',
        limits=['Current international GUI scaling uses segments; the user dropdown reference is from an earlier UI.',
                'Generated skin comparisons do not prove complete game UI equality.',
                'Keyboard focus, controller navigation and all pressed states are not yet covered.',
                'Dialog, world-card text, illustration and baked-font rasterization are not pixel-exact international matches.'])
    if game_pixels:
        actual = json.loads(Path(game_pixels).read_text(encoding='utf8'))
        if not actual.get('collected') or actual.get('restoration_error'):
            raise ValueError('Actual game pixel collection did not finish successfully')
        destination = ROOT / 'docs/images/pixel-audit'
        destination.mkdir(parents=True, exist_ok=True)
        for row in actual['rows']:
            for field in ('reference', 'actual'):
                source = Path(row[field])
                target = destination / (row['name'] + '-' + field + '.png')
                shutil.copyfile(source, target)
                row[field] = target.relative_to(ROOT).as_posix()
            row['source'] = Path(row['source']).relative_to(ROOT).as_posix()
        result['actual_game_comparisons'] = actual
    target = ROOT / 'docs/international-evidence.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(str(target))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--game-pixels', type=Path)
    main(parser.parse_args().game_pixels)
