"""Rasterize the Ore CSS bevels and register scoped native input templates."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'resource_pack/textures/pyreact_ore/skin'
TEX = 'textures/pyreact_ore/skin/'
NS = 'OreUI'


def input_controls():
    geometry = {'size': ['default', 'default'], 'min_size': ['100% - 2px', 0],
                'offset': [-1, 0], 'anchor_from': 'right_middle', 'anchor_to': 'right_middle'}
    display = dict(geometry, bindings=[
        {'binding_type': '$text_edit_box_content_binding_type',
         'binding_condition': '$text_edit_box_binding_condition',
         'binding_collection_name': '$text_edit_box_grid_collection_name',
         'binding_name': '$text_edit_box_content_binding_name', 'binding_name_override': '#item_name'},
        {'binding_name': '#newline_refresh'},
        {'binding_type': 'view', 'source_property_name': '#text_edit_selected', 'target_property_name': '#alpha'},
    ])
    return [{'centering_panel': {'type': 'panel', 'size': ['100%', '100%'], 'controls': [
        {'clipper_panel': {'type': 'panel', 'size': ['100% - 16px', '100% - 8px'],
            'clips_children': True, 'controls': [
                {'display_text@common.text_edit_box_label': display},
                {'visibility_panel': {'type': 'panel', 'controls': [
                    {'place_holder_control@common.text_edit_box_place_holder_label': dict(geometry)}],
                    'bindings': [{'binding_type': 'view', 'source_control_name': 'display_text',
                        'source_property_name': "(#item_name = '')", 'target_property_name': '#visible',
                        'resolve_sibling_scope': True}]}},
            ]}},
    ]}}, {'default@PyreactBase.edit_box_background_default': {}},
        {'hover@PyreactBase.edit_box_background_hover': {}},
        {'pressed@PyreactBase.edit_box_background_hover': {}},
        {'locked@PyreactBase.edit_box_background_default': {}}]


def bevel(name, fill, edge='#1e1e1f', top='#e6e8eb', bottom='#58585a', size=(12, 12)):
    image = Image.new('RGBA', size, edge)
    draw = ImageDraw.Draw(image)
    w, h = size
    draw.rectangle((1, 1, w - 2, h - 2), fill=fill)
    draw.line((1, 1, w - 2, 1), fill=top)
    draw.rectangle((1, h - 3, w - 2, h - 2), fill=bottom)
    image.save(OUT / (name + '.png'))


def patch(texture, size=('100%', '100%'), slices=(2, 2, 2, 3)):
    return {'type': 'image', 'texture': TEX + texture, 'size': list(size),
            'nineslice_size': list(slices), 'keep_ratio': False}


def reflected(fill, top, bottom, size=(16, 16), raised=True, edge='#1e1e1f'):
    image = Image.new('RGBA', size, edge)
    draw = ImageDraw.Draw(image)
    w, h = size
    base = h - 4 if raised else h - 2
    draw.rectangle((1, 1, w - 2, h - 2), fill=fill)
    draw.line((1, 1, w - 2, 1), fill=top)
    draw.line((1, 1, 1, base), fill=top)
    draw.line((1, base, w - 2, base), fill=bottom)
    draw.line((w - 2, 1, w - 2, base), fill=bottom)
    if raised:
        draw.rectangle((1, h - 3, w - 2, h - 2), fill='#58585a')
    # Reflection borders meet with two half-alpha edges in Gameface.
    corners = {'#d0d1d4': '#f4f4f5', '#b1b2b5': '#f9f9f9', '#8c8d90': '#acadaf', '#3c8527': '#72a763'}
    corner = corners.get(fill, top)
    draw.point((w - 2, 1), fill=corner)
    draw.point((1, base), fill=corner)
    return image


def control_skins():
    for state, fill, top, bottom in (
            ('default', '#d0d1d4', '#ecedee', '#e3e3e5'),
            ('hover', '#b1b2b5', '#eff0f0', '#e0e0e1'),
            ('pressed', '#b1b2b5', '#eff0f0', '#e0e0e1'),
            ('disabled', '#b1b2b5', '#eff0f0', '#e0e0e1')):
        reflected(fill, top, bottom, edge='#58585a' if state == 'disabled' else '#1e1e1f').save(OUT / ('thumb_' + state + '.png'))
        reflected(fill, top, bottom).save(OUT / ('segment_' + state + '.png'))
        for selected in (False, True):
            image = Image.new('RGBA', (30, 16))
            draw = ImageDraw.Draw(image)
            active = selected and state != 'disabled'
            track = reflected('#3c8527' if active else '#8c8d90',
                              '#639d52' if active else '#a3a4a6',
                              '#4f913c' if active else '#97989b', size=(30, 14), raised=False)
            image.paste(track, (0, 2))
            if selected:
                draw.rectangle((7, 6, 7, 11), fill='#ffffff' if active else '#58585a')
            else:
                draw.rectangle((19, 6, 24, 11), outline='#242425')
                draw.point((19, 6), fill='#8c8d90')
                draw.point((24, 6), fill='#8c8d90')
                draw.point((19, 11), fill='#8c8d90')
                draw.point((24, 11), fill='#8c8d90')
            thumb = Image.open(OUT / ('thumb_' + state + '.png'))
            image.paste(thumb, (14 if selected else 0, 0))
            image.save(OUT / ('switch_%s_%s.png' % ('on' if selected else 'off', state)))
        selected = reflected('#3c8527' if state != 'disabled' else '#58585a',
                             '#639d52', '#4f913c', raised=False)
        shifted = Image.new('RGBA', (16, 16))
        shifted.paste(selected.resize((16, 14), Image.Resampling.NEAREST), (0, 2))
        ImageDraw.Draw(shifted).line((0, 0, 0, 15), fill='#1e1e1f')
        ImageDraw.Draw(shifted).line((15, 0, 15, 15), fill='#1e1e1f')
        shifted.save(OUT / ('segment_selected_' + state + '.png'))
        for selected in (False, True):
            fill_nav = '#48494a' if selected or state in ('hover', 'pressed') else '#313233'
            image = Image.new('RGBA', (4, 4), fill_nav)
            if selected or state in ('hover', 'pressed'):
                draw = ImageDraw.Draw(image)
                draw.line((0, 0, 3, 0), fill='#1e1e1f' if selected else '#5a5b5c')
                draw.line((0, 3, 3, 3), fill='#5a5b5c' if selected else '#1e1e1f')
            image.save(OUT / ('navigation' + ('_selected' if selected else '') + '_' + state + '.png'))
            tab_fill = '#313233' if selected else '#58585a' if state == 'hover' else '#48494a'
            reflected(tab_fill, '#707071', '#5a5b5c', raised=False).save(
                OUT / ('tab' + ('_selected' if selected else '') + '_' + state + '.png'))
        Image.new('RGBA', (1, 1), '#58585a' if state == 'hover' else '#313233' if state == 'pressed' else (0, 0, 0, 0)).save(OUT / ('icon_' + state + '.png'))
    Image.open(OUT / 'thumb_default.png').save(OUT / 'thumb.png')
    Image.open(OUT / 'thumb_disabled.png').save(OUT / 'thumb_locked.png')
    reflected('#8c8d90', '#a3a4a6', '#97989b', (8, 6), False).save(OUT / 'track.png')
    reflected('#3c8527', '#639d52', '#4f913c', (8, 6), False).save(OUT / 'progress.png')
    Image.open(OUT / 'progress.png').save(OUT / 'progress_hover.png')
    reflected('#48494a', '#707071', '#5a5b5c', raised=False).save(OUT / 'dropdown_header.png')
    for name in ('input', 'input_hover'):
        image = Image.new('RGBA', (8, 8), '#1e1e1f')
        draw = ImageDraw.Draw(image)
        draw.rectangle((1, 1, 6, 6), fill='#313233')
        draw.rectangle((1, 1, 6, 2), fill='#242425')
        image.save(OUT / (name + '.png'))


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ('member', 'operator', 'player_permissions', 'permission_visitor', 'permission_custom'):
        source = Image.open(OUT.parent / (name + '.png')).convert('RGBA')
        mask = Image.new('RGBA', source.size, '#ffffff')
        mask.putalpha(source.getchannel('A'))
        mask.save(OUT / (name + '_tintable.png'))
    bevel('input', '#313233', top='#1e1e1f', bottom='#58585a')
    bevel('input_hover', '#313233', edge='#ffffff', top='#1e1e1f', bottom='#58585a')
    bevel('track', '#1e1e1f', top='#1e1e1f', bottom='#58585a')
    bevel('progress', '#3c8527', top='#6cc349', bottom='#2a641c')
    bevel('progress_hover', '#52a535', top='#86d562', bottom='#3c8527')
    bevel('thumb', '#d0d1d4')
    bevel('thumb_hover', '#e6e8eb', edge='#ffffff')
    bevel('thumb_locked', '#8b8b8e')
    bevel('scroll_thumb', '#e6e8eb', size=(8, 12))
    Image.new('RGBA', (1, 1)).save(OUT / 'transparent.png')
    Image.new('RGBA', (1, 6), '#1e1e1f').save(OUT / 'step.png')
    control_skins()
    for state in ('default', 'hover'):
        strip = Image.new('RGBA', (8, 6), '#3c8527')
        for y, color in ((0, '#1e1e1f'), (1, '#639d52'), (4, '#4f913c'), (5, '#1e1e1f')):
            ImageDraw.Draw(strip).line((0, y, 7, y), fill=color)
        strip.save(OUT / ('progress' + ('_hover' if state == 'hover' else '') + '.png'))
    reflected('#b1b2b5', '#eff0f0', '#e0e0e1', (8, 6), False, '#8c8d90').save(OUT / 'track_disabled.png')
    skin = {'namespace': NS, 'glyph@PyreactBase.image': {'bilinear': True},
            'field_text@PyreactBase.label': {'bindings': [{'binding_type': 'view',
                'source_control_name': 'display_text', 'source_property_name': '(not #text_edit_selected)',
                'target_property_name': '#visible', 'resolve_sibling_scope': True}]},
            'input@PyreactBase.input': {'$edit_box_default_texture': TEX + 'input',
                # JSON orders cuts left, top, right, bottom; the SDK API uses
                # left, right, top, bottom instead.
                '$edit_box_hover_texture': TEX + 'input_hover', '$nineslice_size': [1, 3, 1, 1],
                '$place_holder_text': '', '$font_scale_factor': 1.0,
                '$text_box_text_color': [1, 1, 1], 'controls': input_controls()},
            'scroll_thumb': patch('scroll_thumb'),
            'scroll_track': patch('track'),
            'scroll@PyreactBase.scrollBase': {'$scroll_size': [6, '100%'],
                '$scroll_size_touch': [6, '100%'],
                '$scroll_box_mouse_image_control': NS + '.scroll_thumb',
                '$scroll_box_touch_image_control': NS + '.scroll_thumb',
                '$scroll_track_image_control': NS + '.scroll_track'},
            'slider@PyreactBase.slider': {'$slider_box_size': [16, 16]}}
    slider = skin['slider@PyreactBase.slider']
    for state in ('default', 'hover'):
        names = ('slider_background', 'slider_progress') if state == 'default' else ('slider_background_hover', 'slider_progress_hover')
        skin['slider_bar_' + state] = {'type': 'image', 'texture': TEX + 'transparent',
            'size': ['100%', '100%'], 'controls': [{'sizing_panel': {'type': 'panel',
                'size': ['100%', '100%'], 'controls': [
                    {names[0] + '@OreUI.background_' + state: {'layer': 1}},
                    {names[1] + '@OreUI.progress_' + state: {'clip_direction': 'left', 'clip_pixelperfect': False, 'layer': 3}},
                ]}}]}
    slider['controls'] = [
        {'slider_box@common.slider_box': {'$slider_box_layout': '$slider_box_layout',
            '$slider_box_size': '$slider_box_size', '$slider_track_button': '$slider_name'}},
        {'slider_bar_default@OreUI.slider_bar_default': {}},
        {'slider_bar_hover@OreUI.slider_bar_hover': {'visible': False}},
    ]
    for state in ('default', 'hover'):
        for kind, texture in [('background', 'track'), ('progress', 'progress' + ('_hover' if state == 'hover' else ''))]:
            name = kind + '_' + state
            skin[name] = patch(texture, ('100%', 6), (2, 2, 2, 2))
            if kind == 'progress':
                skin[name] = dict(type='image', texture=TEX + 'progress' + ('_hover' if state == 'hover' else ''),
                                  size=['100%', 6], keep_ratio=False)
            slider['$' + name + '_control'] = NS + '.' + name
    for suffix, texture in [('', 'thumb'), ('_hover', 'thumb_hover'), ('_locked', 'thumb_locked'), ('_indent', 'thumb_hover')]:
        name = 'slider_box' + suffix
        skin[name] = patch(texture, slices=(2, 2, 2, 4))
        slider['$slider_box' + suffix + '_layout'] = NS + '.' + name
    for suffix, texture in [('', 'track'), ('_hover', 'track'), ('_progress', 'progress'), ('_progress_hover', 'progress_hover')]:
        name = 'slider_step' + suffix
        skin[name] = dict(type='image', texture=TEX + 'step', size=[1, 6],
                          layer=4, offset='$step_offset')
    slider['$slider_step_factory_control_ids'] = dict(
        ('slider_step' + suffix, '@' + NS + '.slider_step' + suffix)
        for suffix in ('', '_hover', '_progress', '_progress_hover'))
    output = ROOT / 'resource_pack/ui/OreUI.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(skin, indent=2) + '\n', encoding='utf8')


if __name__ == '__main__':
    build()
