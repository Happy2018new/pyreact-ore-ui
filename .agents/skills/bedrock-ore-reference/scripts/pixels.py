"""Lossless crops, palette measurements and explicit pixel comparisons."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops


def compare(reference, actual, output, scale=1.0, tolerance=0, background=None):
    first = Image.open(reference).convert('RGB')
    second = Image.open(actual).convert('RGBA')
    if background:
        canvas = Image.new('RGBA', second.size, background)
        canvas.alpha_composite(second)
        second = canvas
    second = second.convert('RGB')
    original = second.size
    if scale != 1:
        second = second.resize(tuple(round(n * scale) for n in second.size), Image.Resampling.NEAREST)
    if first.size != second.size:
        raise ValueError('Crop dimensions differ: %s vs %s; specify a measured scale' % (first.size, second.size))
    delta = np.abs(np.asarray(first, dtype=np.int16) - np.asarray(second, dtype=np.int16))
    changed = delta.max(axis=2) > tolerance
    result = dict(reference=str(Path(reference).resolve()), actual=str(Path(actual).resolve()),
                  reference_size=first.size, actual_native_size=original, scale=scale,
                  native_exact=scale == 1 and bool(not delta.any()), tolerance=tolerance,
                  alpha_background=background,
                  mean_channel_error=float(delta.mean()), max_channel_error=int(delta.max()),
                  different_fraction=float(changed.mean()), compared_pixels=int(changed.size))
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    ImageChops.difference(first, second).save(output.with_suffix('.diff.png'))
    Image.blend(first, second, 0.5).save(output.with_suffix('.overlay.png'))
    output.with_suffix('.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    return result


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='op', required=True)
    crop = sub.add_parser('crop')
    crop.add_argument('source', type=Path)
    crop.add_argument('--box', nargs=4, type=int, required=True)
    crop.add_argument('--output', type=Path, required=True)
    palette = sub.add_parser('palette')
    palette.add_argument('source', type=Path)
    palette.add_argument('--top', type=int, default=12)
    diff = sub.add_parser('compare')
    diff.add_argument('reference', type=Path)
    diff.add_argument('actual', type=Path)
    diff.add_argument('--scale', type=float, default=1)
    diff.add_argument('--tolerance', type=int, default=0)
    diff.add_argument('--background')
    diff.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.op == 'compare':
        return compare(args.reference, args.actual, args.output, args.scale, args.tolerance, args.background)
    image = Image.open(args.source).convert('RGB')
    if args.op == 'palette':
        colors = sorted(image.getcolors(image.width * image.height), reverse=True)[:args.top]
        return dict(size=image.size, colors=[dict(rgb=color, pixels=count) for count, color in colors])
    x, y, right, bottom = args.box
    if not (0 <= x < right <= image.width and 0 <= y < bottom <= image.height):
        raise ValueError('Crop outside source image')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.crop(args.box).save(args.output)
    return dict(output=str(args.output.resolve()), source=str(args.source.resolve()), box=args.box)


if __name__ == '__main__':
    print(json.dumps(main(), indent=2))
