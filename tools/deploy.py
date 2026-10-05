"""Copy Ore into an existing client package and merge Pyreact's UI registration."""
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_EXTRA = frozenset(('settings', 'world', 'general_icon', 'advanced_icon',
    'multiplayer_icon', 'accessibility', 'ui_menu_worlds_tab', 'ui_menu_server_tab',
    'realms', 'grass_block', 'member', 'operator', 'player_permissions',
    'edit', 'world_demo_screen_big', 'information', 'friends', 'resource_packs_icon',
    'minecraft_texture_pack', 'steve_thumb', 'alex_thumb', 'ari_thumb', 'kai_thumb',
    'efe_thumb', 'sunny_thumb', 'magnifying_glass', 'add_resource_pack', 'remove_resource_pack',
    'icon_alex', 'no_player_profile'))


def core_assets(manifest):
    return {name for name, record in manifest['assets'].items() if name in CORE_EXTRA or
            any(path.startswith('gameplay/assets/') for path in record['source_paths'])}


def copy_tree(source, destination):
    shutil.copytree(source, destination, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))


def deploy(client_package, resource_pack, pyreact_root=None, asset_set='all'):
    if pyreact_root:
        if not (pyreact_root / 'pyreact/__init__.py').is_file():
            raise ValueError('--pyreact must point to a PyreactMC repository')
        if (client_package / 'pyreact').exists():
            raise ValueError('Pyreact already exists; omit --pyreact to preserve the host runtime')
    elif not (client_package / 'pyreact/__init__.py').is_file():
        raise ValueError('Expected sibling pyreact package; install Pyreact or pass --pyreact')
    defs_path = resource_pack / 'ui/_ui_defs.json'
    defs = json.loads(defs_path.read_text(encoding='utf-8-sig')) if defs_path.exists() else {'ui_defs': []}
    if not isinstance(defs.get('ui_defs'), list):
        raise ValueError('_ui_defs.json must contain an ui_defs array')
    template_path = resource_pack / 'ui/PyreactBase.json'
    if not template_path.exists() and not pyreact_root:
        raise ValueError('Install the host PyreactBase.json in the resource pack first')
    client_package.mkdir(parents=True, exist_ok=True)
    if pyreact_root:
        copy_tree(pyreact_root / 'pyreact', client_package / 'pyreact')
        for filename in ('LICENSE', 'NOTICE'):
            shutil.copyfile(pyreact_root / filename, client_package / 'pyreact' / filename)
        template_path.parent.mkdir(parents=True, exist_ok=True)
        if not template_path.exists():
            shutil.copyfile(pyreact_root / 'jsonui/PyreactBase.json', template_path)
    copy_tree(ROOT / 'oreui', client_package / 'oreui')
    copy_tree(ROOT / 'resource_pack/textures/pyreact_ore/type', resource_pack / 'textures/pyreact_ore/type')
    copy_tree(ROOT / 'resource_pack/textures/pyreact_ore/skin', resource_pack / 'textures/pyreact_ore/skin')
    copy_tree(ROOT / 'resource_pack/textures/pyreact_ore/reference', resource_pack / 'textures/pyreact_ore/reference')
    shutil.copyfile(ROOT / 'resource_pack/ui/OreUI.json', resource_pack / 'ui/OreUI.json')
    template = json.loads(template_path.read_text(encoding='utf-8-sig'))
    controls = template['rootBase']['controls']
    for suffix, target in [('glyph', 'glyph'), ('field_text', 'field_text'), ('input', 'input'),
                          ('search_input', 'search_input'), ('step', 'step'), ('slider', 'slider'), ('scroll', 'scroll'),
                          ('navigation', 'navigation')]:
        name = 'ore_' + suffix + '_tmpl@OreUI.' + target
        if not any(name in entry for entry in controls):
            controls.append({name: {}})
    template_path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    if asset_set == 'all':
        copy_tree(ROOT / 'resource_pack/textures/pyreact_ore', resource_pack / 'textures/pyreact_ore')
    else:
        manifest = json.loads((ROOT / 'assets/manifest.json').read_text(encoding='utf8'))
        names = core_assets(manifest)
        for name, record in manifest['assets'].items():
            if name not in names:
                continue
            destination = resource_pack / 'textures/pyreact_ore' / (name + '.png')
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / record['output'], destination)
    for filename in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
        shutil.copyfile(ROOT / filename, client_package / 'oreui' / filename)
    if 'ui/PyreactBase.json' not in defs['ui_defs']:
        defs['ui_defs'].append('ui/PyreactBase.json')
    if 'ui/OreUI.json' not in defs['ui_defs']:
        defs['ui_defs'].append('ui/OreUI.json')
    defs_path.parent.mkdir(parents=True, exist_ok=True)
    defs_path.write_text(json.dumps(defs, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'client_package': str(client_package), 'resource_pack': str(resource_pack),
                      'ore_package': str(client_package / 'oreui')}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--client-package', type=Path, required=True)
    parser.add_argument('--resource-pack', type=Path, required=True)
    parser.add_argument('--pyreact', type=Path)
    parser.add_argument('--assets', choices=('all', 'core'), default='all',
                        help='core deploys gameplay controls/icons/keyboard legends; all deploys the full catalog')
    args = parser.parse_args()
    deploy(args.client_package.resolve(), args.resource_pack.resolve(),
           args.pyreact.resolve() if args.pyreact else None, args.assets)
