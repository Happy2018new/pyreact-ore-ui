"""Publish portable, lossless control references and their capture provenance."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'tools/reference_cases.json'
OUTPUT = ROOT / 'docs/images/reference/native'


def publish():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    cases = json.loads(CASES.read_text('utf8'))
    for case in cases:
        for state in case['states']:
            source = ROOT / state['source']
            if state.get('provenance'):
                continue
            metadata = json.loads(source.with_suffix('.json').read_text('utf8'))
            box = state['box']
            image = Image.open(source)
            if not (0 <= box[0] < box[2] <= image.width and 0 <= box[1] < box[3] <= image.height):
                raise ValueError('Reference crop outside source: ' + state['source'])
            target = OUTPUT / (case['name'] + '-' + state['name'] + '.png')
            crop = image.crop(box)
            crop.save(target)
            state['provenance'] = dict(capture=source.name,
                capture_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                capture_crop=box, reference_scale=4, margin_logical=1,
                version=metadata['version'], client=metadata['client'][2:],
                cursor=metadata['cursor'], timestamp=metadata['timestamp'],
                crop_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
            state['source'] = target.relative_to(ROOT).as_posix()
            state['box'] = [0, 0, crop.width, crop.height]
    CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print('Published %d complete-control states without resizing or masks' %
          sum(len(case['states']) for case in cases))


if __name__ == '__main__':
    publish()
