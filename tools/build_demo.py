"""Prepare a self contained, disposable demo Addon for the debugging skill."""
import argparse
import json
import subprocess
from pathlib import Path

from deploy import copy_tree, deploy

ROOT = Path(__file__).resolve().parents[1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pyreact', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / '.runtime/demo_addon')
    args = parser.parse_args()
    target = args.output.resolve()
    copy_tree(ROOT / 'examples/demo', target)
    client_package = target / 'behavior_pack/ore_demo'
    # Existing dependencies are reused on subsequent rebuilds, never replaced.
    dependency = args.pyreact.resolve() if not (client_package / 'pyreact').exists() else None
    deploy(client_package, target / 'resource_pack', dependency)
    source_commit = subprocess.check_output(['git', '-C', str(args.pyreact.resolve()), 'rev-parse', 'HEAD'], text=True).strip()
    (target / 'dependency.json').write_text(json.dumps({'PyreactMC': source_commit}, indent=2) + '\n', encoding='utf8')
    print(str(target))
