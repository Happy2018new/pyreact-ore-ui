"""Export the reusable package separately from the demo/runtime/agent skills."""
import argparse
import json
import zipfile
from pathlib import Path
from deploy import core_assets

ROOT = Path(__file__).resolve().parents[1]


def package(output, asset_set):
    manifest = json.loads((ROOT / 'assets/manifest.json').read_text(encoding='utf8'))
    names = set(manifest['assets'])
    if asset_set == 'core':
        names = core_assets(manifest)
    paths = [p for p in (ROOT / 'oreui').glob('*.py')]
    paths += [ROOT / manifest['assets'][name]['output'] for name in sorted(names)]
    paths += [ROOT / 'resource_pack/ui/OreUI.json']
    paths += list((ROOT / 'resource_pack/textures/pyreact_ore/type').glob('*'))
    paths += list((ROOT / 'resource_pack/textures/pyreact_ore/skin').glob('*'))
    paths += [ROOT / p for p in ('README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'assets/manifest.json',
                                  'tools/deploy.py')]
    paths += [p for p in (ROOT / 'docs').rglob('*') if p.is_file() and
              p.suffix in ('.md', '.json', '.jpg', '.png')]
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in paths:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr('package.json', json.dumps({'version': '0.1.0', 'asset_set': asset_set,
                                                    'assets': len(names), 'pyreact': 'external sibling dependency'}, indent=2))
    print(json.dumps({'archive': str(output), 'assets': len(names), 'bytes': output.stat().st_size}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--assets', choices=('core', 'all'), default='core')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    package(args.output or ROOT / ('dist/pyreact-ore-ui-0.1.0-' + args.assets + '.zip'), args.assets)
