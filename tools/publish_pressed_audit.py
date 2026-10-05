"""Publish fixed-coordinate game pixel comparisons, including residual error.

No alignment search, text mask, or resizing is used. Coordinates were measured
at GUI scale 4 in Bedrock 1.26.5203.0 and the 504 x 291 logical fixture.
"""
import argparse
import hashlib
import json
from pathlib import Path

from verify_component_boundaries import pixels

ROOT = Path(__file__).resolve().parents[1]

# Whole controls with one logical pixel outside; joined groups keep neighbors.
# Reference scrollbars and key hints remain in the images even if overlapping.
CASES = [
    ('primary', 'primary-button', 'primary-00', [892,220,1412,324], [28,156,548,260]),
    ('secondary', 'secondary-confirm', 'secondary-00', [568,686,1456,790], [28,156,916,260]),
    ('segment-selected', 'segment-selected', 'segments-00', [715,364,1980,492], [28,156,1293,284]),
    ('segment-middle', 'segment-middle', 'segments-01', [715,364,1980,492], [28,156,1293,284]),
    ('segment-last', 'segment-last', 'segments-02', [715,364,1980,492], [28,156,1293,284]),
    ('tab-unselected', 'pack-tab-unselected', 'tabs-00', [695,236,2004,340], [28,156,1337,260]),
    ('tab-selected', 'pack-tab-selected', 'tabs-01', [695,236,2004,340], [28,156,1337,260]),
    ('navigation-unselected', 'nav-unselected', 'navigation-00', [0,456,675,752], [28,156,703,452]),
    ('navigation-selected', 'nav-selected', 'navigation-01', [0,456,675,752], [28,156,703,452]),
    ('pack-group', 'pack-group', 'group-00', [695,348,2004,452], [28,156,1337,260]),
    ('pack-details', 'pack-details', 'packs-01', [695,348,2004,736], [28,156,1337,544]),
    ('pack-action', 'pack-action', 'packs-02', [695,348,2004,736], [28,156,1337,544]),
    ('player-profile', 'player-profile', 'players-00', [1308,740,1956,1032], None),
    ('player-options', 'player-options', 'players-01', [1308,740,1956,1032], None),
    ('switch-off', 'switch-off', 'switch-00', [1856,196,1984,268], [28,156,156,228]),
    ('switch-on', 'switch-on', 'switch-selected-00', [1856,324,1984,396], [28,156,156,228]),
    ('switch-disabled', 'switch-disabled', 'switch-disabled-00', [1856,936,1984,1008], [28,156,156,228]),
    ('slider', 'slider-middle', 'slider-reference-00', [720,500,1980,572], [28,156,1288,228]),
    ('dropdown-close', 'dropdown-close', 'dropdown-open-01', [532,284,1492,884], 'dropdown'),
    ('dropdown-option', 'dropdown-option6', 'dropdown-open-03', [532,284,1492,884], 'dropdown'),
    ('action-menu-close', 'action-menu-close', 'menu-00', [532,250,1492,918], 'menu'),
    ('world-edit', 'world-edit', 'worlds-02', [36,680,660,824], 'world'),
]


def publish(reference, actual, output):
    output.mkdir(parents=True, exist_ok=True)
    report = dict(scale=4, comparison_scale=1, tolerance=0,
        scope='Full controls including content, borders, outside margin and adjacent joined controls',
        acceptance='native_exact; residual differences are never a visual pass', rows=[])
    inventory = json.loads((actual / 'report.json').read_text(encoding='utf8'))
    interaction=dict(passed=inventory['passed'],target_count=len(inventory['rows']),rows=[
        dict(name=row['name'],case=row['case'],checks=row['checks'],passed=row['passed'],
             changed_neighbor_pixels=row['states'].get('changed_neighbor_pixels'),
             inside_release=row['states'].get('inside_release'),
             input_held=row['states']['states']['pressed']['mouse_left_down_before'],
             input_released=row['states']['mouse_released']) for row in inventory['rows']])
    (output/'interaction-report.json').write_text(json.dumps(interaction,ensure_ascii=False,indent=2),encoding='utf8')
    lookup = {row['name']: row for row in inventory['rows']}
    for name, ref, test, ref_box, actual_box in CASES:
        if test not in lookup:
            continue
        if actual_box is None:
            # PlayerGroup heading is outside this two-row specimen. Derive
            # the outer border from the first profile, never from image error.
            item = lookup['players-00']['target']
            x,y = item['position']
            left,top = round((x-2)*4), round((y-2)*4)
            actual_box = [left,top,left+648,top+292]
        elif actual_box=='world':
            item=lookup[test]['target'];x,y=item['position']
            actual_box=pixels.logical_box((x-121,y-1),(154,34),4,margin=1)
        elif actual_box in ('dropdown','menu'):
            dropdown=actual_box=='dropdown'
            item=lookup['dropdown-open-01' if dropdown else 'menu-00']['target']
            x,y=item['position']
            actual_box=pixels.logical_box((x-215,y-3),
                                          (238,148 if dropdown else 165),4,margin=1)
        for state in ('default','hover','pressed'):
            ref_source = reference / (ref+'-'+state+'.png')
            actual_source = actual / (test+'-'+state+'.png')
            if not ref_source.exists() or not actual_source.exists():
                continue
            stem = name+'-'+state
            first,second = output/(stem+'-reference.png'),output/(stem+'-actual.png')
            pixels.checked_crop(ref_source,ref_box).save(first)
            pixels.checked_crop(actual_source,actual_box).save(second)
            result = pixels.compare(first,second,output/stem)
            result['reference'] = first.name
            result['actual'] = second.name
            result.update(name=name,state=state,reference_box=ref_box,actual_box=actual_box,
                reference_capture=ref_source.name,actual_capture=actual_source.name,
                reference_sha256=hashlib.sha256(ref_source.read_bytes()).hexdigest(),
                actual_sha256=hashlib.sha256(actual_source.read_bytes()).hexdigest())
            for label,source in (('reference_evidence',ref_source),('actual_evidence',actual_source)):
                meta=json.loads(source.with_suffix('.json').read_text(encoding='utf8'))
                result[label]={k:meta.get(k) for k in ('pid','exe','version','created','client','cursor',
                    'timestamp','mouse_left_down_before','mouse_left_down_after')}
                result[label]['hold_ms']=meta.get('observation',{}).get('hold_ms')
                probe=meta.get('observation',{}).get('runtime')
                if probe:
                    result[label]['native_states']={s:probe[s] for s in ('default','hover','pressed') if s in probe}
            report['rows'].append(result)
            (output/(stem+'.json')).write_text(json.dumps(result,indent=2),encoding='utf8')
            print('%s %.3f%% different' % (stem,result['different_fraction']*100))
    report['native_exact'] = bool(report['rows']) and all(r['native_exact'] for r in report['rows'])
    (output/'comparison.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--reference',type=Path,default=ROOT/'.runtime/pressed-audit/reference')
    parser.add_argument('--actual',type=Path,default=ROOT/'.runtime/pressed-audit/acceptance')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/images/pressed-states')
    args=parser.parse_args()
    result=publish(args.reference,args.actual,args.output)
    if not result['native_exact']:
        print('NOT EXACT: comparison artifacts published; residual differences remain.')
    raise SystemExit(0 if result['native_exact'] else 1)
