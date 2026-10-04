"""Publish complete-control errors and scoped behavior results without runtime paths."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish(audit, behavior, output, client_version, engine_version):
    source = json.loads((audit / 'result.json').read_text(encoding='utf8'))
    cases = json.loads((ROOT / 'tools/reference_cases.json').read_text(encoding='utf8'))
    provenance = {case['name'] + '-' + state['name']: state['provenance']
                  for case in cases for state in case['states']}
    target = output.parent / 'images/reference/audit'
    target.mkdir(parents=True, exist_ok=True)
    rows = []
    metrics = ('native_exact', 'exact', 'within_tolerance', 'mean_channel_error',
               'max_channel_error', 'different_fraction', 'compared_pixels',
               'changed_bounds', 'reference_size', 'actual_native_size',
               'resampled', 'alignment', 'tolerance', 'dimension_error')
    for original in source['rows']:
        name = original['name']
        row = {key: original[key] for key in metrics if key in original}
        row.update(name=name, kind=original['kind'], actual_box=original['actual_box'],
                   includes_text=original['includes_text'], margin_logical=original['margin_logical'],
                   native_geometry=original['native_geometry'],
                   actual_capture=dict(client_size=original['capture']['client'][2:],
                       cursor=original['capture']['cursor'], timestamp=original['capture']['timestamp'],
                       full_capture_sha256=original['capture']['sha256']),
                   provenance=provenance[name], images={})
        for suffix in ('-reference.png', '-actual.png', '.pair.png', '.diff.png', '.overlay.png'):
            path = audit / (name + suffix)
            if path.is_file():
                destination = target / path.name
                shutil.copy2(path, destination)
                row['images'][suffix] = dict(path=destination.relative_to(ROOT).as_posix(),
                                            sha256=sha256(destination))
        rows.append(row)
    results = []
    for entry in behavior:
        label, path = entry.split('=', 1)
        batch = json.loads((Path(path) / 'result.json').read_text(encoding='utf8'))
        result = {key: batch[key] for key in ('ok', 'count', 'checks', 'error',
                  'hardware_touch_tested', 'pages') if key in batch}
        result.update(name=label, source_batch=Path(path).name)
        if 'sizes' in batch:
            result['sizes'] = [{key: size[key] for key in ('name', 'requested', 'logical')}
                               for size in batch['sizes']]
        results.append(result)
    reference_versions = sorted({row['provenance']['version'] for row in rows})
    report = dict(reference_versions=reference_versions, development_client=client_version,
        game_file_version=engine_version,
        acceptance='Exact original RGB pixels, complete control, text/icons and one logical pixel around it',
        collected=source['collected'], visual_pass=source['visual_pass'],
        native_scale=4, state_count=len(rows), states=rows, behavior=results)
    runtime_sources = list((ROOT / 'oreui').glob('*.py')) + [ROOT / 'resource_pack/ui/OreUI.json']
    report['runtime_source_sha256'] = {path.relative_to(ROOT).as_posix(): sha256(path)
                                     for path in sorted(runtime_sources)}
    for key in ('error', 'restoration_error'):
        if key in source:
            report[key] = source[key]
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(dict(output=str(output), visual_pass=report['visual_pass'], states=len(rows)), ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--audit', required=True, type=Path)
    parser.add_argument('--client-version', required=True, help='Development client distribution version')
    parser.add_argument('--engine-version', required=True, help='Verified game executable file version')
    parser.add_argument('--behavior', nargs='*', default=[], help='label=directory entries containing result.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/validation-latest.json')
    args = parser.parse_args()
    publish(args.audit, args.behavior, args.output, args.client_version, args.engine_version)
