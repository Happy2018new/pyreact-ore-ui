# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Reusable Ore controls composed on the supplied PyreactMC runtime."""
from functools import partial

from ..pyreact import (Component, Panel, Label, Image,
                      Style, Color,
                      FontSize, FlexDirection, AlignItems, JustifyContent,
                      ButtonState, TextAlignment, ImageAdaptionType, Position, AlignSelf, use_state)
from .assets import asset, button_asset, OreVariant, OreState, OreIconName
from .theme import OreColors, OreTone, OreSide, palette_color
from ._button import NativeOreButton, NativeOreRadioButton
from ._slider import NativeOreSlider
from ._input import NativeOreInput, NativeOreSearchInput
from ._scroll import NativeOreScrollView
from ._text import NativeOreText, NativeOreFieldText
from .typography import OreString, text_value, layout as text_layout
from ._image import NativeOreImage
from ._portal import NativeOrePortal, OreModal, modal_surface
from ._skins import state_skin, skin_image

_UNSET = object()
_STATES = {ButtonState.default: OreState.default,
           ButtonState.hover: OreState.hovered,
           ButtonState.pressed: OreState.pressed}


def _ore_modal(**props):
    return NativeOrePortal(style=Style(position=Position.absolute, left=0, top=0,
        width=0, height=0), children=OreModal(**props))


def _image_props(name, animate=False):
    metadata = asset(name)
    props = {'src': metadata['src']}
    edges = metadata.get('nineSliceData')
    if edges is not None:
        props.update(imageAdaption=ImageAdaptionType.origin_nine_slice, nineSliceData=edges)
    else:
        props['imageAdaption'] = ImageAdaptionType.filled
    if animate and 'frames' in metadata:
        props.update(frames=metadata['frames'], frameDuration=metadata['frameDuration'],
                     frameDurations=metadata.get('frameDurations'))
    elif 'frames' in metadata:
        props.update(uv=metadata['frames'][0]['uv'], uvSize=metadata['frames'][0]['uvSize'])
    return props


def _builder(names):
    states = dict((state, _image_props(name)) for state, name in names.items())

    def build(state):
        return Image(**states[state])
    return build


def _transparent_button(state):
    return Image(color=Color(0xFFFFFF00))


def _focus_outline(horizontal=0, vertical=0):
    """A persistent, non-interactive outline above native state backgrounds."""
    return Panel(key='ore_focus_outline', style=Style(
        position=Position.absolute, left=-horizontal, right=-horizontal,
        top=-vertical, bottom=-vertical, zIndex=2),
        children=[
            Image(color=OreColors.text, style=Style(position=Position.absolute,
                  left=0, top=0, width='100%', height=1)),
            Image(color=OreColors.text, style=Style(position=Position.absolute,
                  left=0, bottom=0, width='100%', height=1)),
            Image(color=OreColors.text, style=Style(position=Position.absolute,
                  left=0, top=0, width=1, height='100%')),
            Image(color=OreColors.text, style=Style(position=Position.absolute,
                  right=0, top=0, width=1, height='100%')),
        ])


@Component
def OreImage(name, style=None, animate=False, color=None, children=None, contain=None):
    metadata = asset(name)
    width, height = metadata['size']
    props = _image_props(name, animate)
    if color is not None:
        props['color'] = color
    contain = 'nineSliceData' not in metadata if contain is None else contain
    if contain:
        props.update(imageAdaption=ImageAdaptionType.filled, contain=True, sourceSize=(width, height))
        props.pop('nineSliceData', None)
    if 'frames' in metadata:
        props.update(frames=metadata['frames'], frameDuration=metadata['frameDuration'],
                     frameDurations=metadata.get('frameDurations'), playing=animate)
    return NativeOreImage(style=Style(width=width, height=height).merge(style), children=children, **props)


@Component
def OreIcon(name=OreIconName.check, size=12, style=None, color=None):
    width, height = asset(name)['size']
    if color is not None and name in ('member', 'operator', 'player_permissions',
                                     'information', 'add_resource_pack', 'remove_resource_pack',
                                     'chevron_up', 'chevron_down',
                                     'permission_visitor', 'permission_custom'):
        # Native sprite tint multiplies RGB; a black source cannot turn white.
        return Image(src='textures/pyreact_ore/skin/' + name + '_tintable', color=color,
                     style=Style(width=size * float(width) / height, height=size).merge(style))
    return OreImage(name=name, color=color,
                    style=Style(width=size * float(width) / height, height=size).merge(style))


@Component
def OreText(content='', style=None, color=OreColors.text, fontSize=FontSize.normal,
            textAlign=TextAlignment.left):
    return NativeOreText(style=style, content=OreString(text_value(content)), color=color, fontSize=max(7, fontSize),
                 textAlign=textAlign, shadow=False)


@Component
def OreButton(label='', variant=OreVariant.secondary, elevated=True, disabled=False,
              focused=False, onClick=None, style=None, labelStyle=None, icon=None,
              children=None):
    names = {}
    for native_state, ore_state in _STATES.items():
        if disabled:
            ore_state = OreState.disabled
        elif focused and native_state == ButtonState.default:
            ore_state = OreState.focused
        names[native_state] = button_asset(variant, ore_state, elevated)
    text_color = OreColors.darkText if variant == OreVariant.secondary else OreColors.text
    if disabled:
        text_color = OreColors.disabled
    content = children
    if content is None:
        content = [OreIcon(name=icon, size=9, style=Style(marginRight=5)) if icon else None,
                   OreText(content=label, color=text_color, fontSize=8, textAlign=TextAlignment.center,
                           style=labelStyle)]
    return NativeOreButton(
        style=Style(height=24, minWidth=36, paddingHorizontal=8,
                    flexDirection=FlexDirection.row).merge(style),
        buttonBuilder=_builder(names), onClick=None if disabled else onClick,
        children=[content, _focus_outline(8, 0) if focused and not disabled else None],
    )


@Component
def OreCard(style=None, children=None):
    return Image(color=OreColors.surface, style=Style(padding=8).merge(style), children=children)


@Component
def OreListItem(title='', description='', icon=None, selected=False, disabled=False,
                onClick=None, style=None, children=None):
    names = {}
    for state, ore_state in _STATES.items():
        if disabled:
            ore_state = OreState.disabled_focused if selected else OreState.disabled
        elif selected:
            # Hover uses the brighter texture. A separate selection outline
            # persists above the native state images through hover and press.
            if state == ButtonState.pressed:
                ore_state = OreState.pressed_focused
            elif state == ButtonState.default:
                ore_state = OreState.focused
        names[state] = 'list_item_action_' + ore_state
    content = children
    if content is None:
        content = [OreIcon(name=icon, size=14, style=Style(marginRight=7)) if icon else None,
                   Panel(style=Style(flex=1), children=[
                       OreText(content=title, color=OreColors.disabled if disabled else OreColors.text),
                       OreText(content=description, color=OreColors.muted,
                               style=Style(marginTop=3)) if description else None,
                   ])]
    return NativeOreButton(
        style=Style(width='100%', height=40 if description else 28, padding=6,
                    flexDirection=FlexDirection.row, alignItems=AlignItems.center,
                    justifyContent=JustifyContent.flex_start).merge(style),
        buttonBuilder=_builder(names), onClick=None if disabled else onClick,
        children=[content, _focus_outline(6, 6) if selected and not disabled else None],
    )


@Component
def OreTabs(options, value, onChange=None, style=None, disabled=None, keyboardHints=False):
    disabled = disabled or ()
    return Panel(style=Style(width='100%', flexDirection=FlexDirection.row).merge(style), children=[
        NativeOreButton(
            key=str(index),
            style=Style(flex=1, height=24, paddingHorizontal=4, gap=4,
                        marginLeft=-1 if index else 0, flexDirection=FlexDirection.row),
            buttonBuilder=state_skin('tab', option[1] == value, option[1] in disabled,
                (2, 2, 4, 2) if option[1] == value else (2, 2, 2, 4)),
            onClick=partial(onChange, option[1]) if onChange and option[1] not in disabled else None,
            children=[Panel(style=Style(flexDirection=FlexDirection.row, gap=4,
                    alignItems=AlignItems.center, marginTop=3.5 if option[1] == value else -.5), children=[
                    OreIcon(name=option[2], size=12) if len(option) > 2 and option[2] else None,
                    OreText(content=option[0], fontSize=8, textAlign=TextAlignment.center)]),
                Image(color=OreColors.text, style=Style(position=Position.absolute,
                      bottom=1, width=24, maxWidth='65%', height=1, left='50%', marginLeft=-12)) if option[1] == value else None],
        ) for index, option in enumerate(options)
    ] + ([Panel(style=Style(position=Position.absolute, left=-5, top=6, width=12, height=12),
                    children=NativeOreButton(style=Style(width=12, height=12), buttonBuilder=_transparent_button,
                        children=OreImage(name='bracket_open', style=Style(width=10, height=10)),
                        onClick=partial(_cycle_tab, options, value, onChange, disabled, -1))),
          Panel(style=Style(position=Position.absolute, right=-5, top=6, width=12, height=12),
                    children=NativeOreButton(style=Style(width=12, height=12), buttonBuilder=_transparent_button,
                        children=OreImage(name='bracket_close', style=Style(width=10, height=10)),
                        onClick=partial(_cycle_tab, options, value, onChange, disabled, 1)))] if keyboardHints else []))


def _cycle_tab(options, value, onChange, disabled, direction):
    values = [option[1] for option in options if option[1] not in disabled]
    if onChange and values:
        index = values.index(value) if value in values else 0
        onChange(values[(index + direction) % len(values)])


@Component
def OreCheckbox(value=_UNSET, defaultValue=False, onChange=None, disabled=False,
                style=None):
    internal, set_internal = use_state(bool(defaultValue))
    controlled = value is not _UNSET
    checked = bool(value) if controlled else internal

    def change():
        next_value = not checked
        if not controlled:
            set_internal(next_value)
        if onChange is not None:
            onChange(next_value)

    return OreButton(variant=OreVariant.primary if checked else OreVariant.neutral,
                     elevated=False, disabled=disabled, onClick=change,
                     style=Style(width=16, height=16, minWidth=16, paddingHorizontal=0).merge(style),
                     children=OreIcon(name=OreIconName.check, size=8) if checked else Panel())


@Component
def OreSlider(value=_UNSET, defaultValue=0.5, steps=1, onChange=None, disabled=False,
              style=None, tickLabels=None):
    """Ore-sized wrapper around the host slider primitive."""
    steps = max(1, int(steps))
    upper = 1.0 if steps == 1 else float(steps - 1)

    def normalize(number):
        number = max(0.0, min(upper, float(number)))
        return int(number + 0.5) if steps > 1 else number

    internal, set_internal = use_state(normalize(defaultValue))
    controlled = value is not _UNSET
    current = normalize(value) if controlled else normalize(internal)

    def change(next_value):
        if disabled:
            return
        next_value = normalize(next_value)
        if not controlled:
            set_internal(next_value)
        if onChange is not None and not disabled:
            onChange(next_value)

    slider = Panel(style=Style(width='100%', height=16, minWidth=40,
        flexDirection=FlexDirection.row).merge(style), children=NativeOreSlider(
        value=current,
        steps=steps,
        disabled=disabled,
        onChange=None if disabled else change,
        # The native engine places the thumb centre at both ends. Inset its
        # input range by half a thumb; the native skin extends the track back.
        style=Style(flex=1, height='100%', marginHorizontal=8, opacity=1.0),
    ))
    if tickLabels is None:
        return slider
    count = len(tickLabels)
    return Panel(style=Style(width='100%').merge(style), children=[slider,
        Panel(style=Style(width='100%', height=12), children=Panel(
            style=Style(position=Position.absolute, left=8, right=8, height=12), children=[
            OreText(content=str(label), fontSize=8, textAlign=TextAlignment.center,
                style=Style(position=Position.absolute, left=str(100.0 * index / max(1, count - 1)) + '%',
                            top=0, width=16, marginLeft=-8))
            for index, label in enumerate(tickLabels)]))])


@Component
def OreScrollView(style=None, children=None, showScrollbar=True):
    """Host scrolling template with a bounded range for nested scroll regions."""
    return NativeOreScrollView(style=style, showScrollbar=showScrollbar,
        children=Panel(style=Style(width='100%'), children=children))


@Component
def OreProgress(value=0, style=None, color=OreColors.primary):
    progress = max(0.0, min(1.0, float(value)))
    return Image(color=OreColors.raised, style=Style(height=5, width='100%').merge(style),
                 children=Image(color=color, style=Style(width=str(progress * 100) + '%', height='100%')))


@Component
def OreDialog(visible=False, title='', message='', confirmLabel='确定', onConfirm=None,
              onClose=None, children=None, confirmVariant=OreVariant.primary):
    from ..pyreact import native
    screen = native.get_screen_size() if visible else (320, 210)
    width = min(260, screen[0] - 24)
    height = min(220, screen[1] - 24)
    return _ore_modal(visible=visible, onClick=onClose,
                 style=Style(alignItems=AlignItems.center, justifyContent=JustifyContent.center),
                 children=[Image(color=Color(0x00000099), style=Style(
                     position=Position.absolute, left=0, top=0, width='100%', height='100%')),
                     modal_surface(key='ore_dialog_surface',
                     style=Style(width=width, maxHeight=height),
                     children=Image(color=OreColors.surface, style=Style(width='100%', flex=1, padding=1), children=[
                     Image(color=OreColors.raised, style=Style(width='100%', height=32, paddingHorizontal=8,
                         flexDirection=FlexDirection.row, alignItems=AlignItems.center), children=[
                         OreText(content=title, fontSize=10, style=Style(flex=1)),
                         NativeOreButton(key='ore_dialog_close', buttonBuilder=state_skin('icon', slices=(0, 0, 0, 0)),
                             style=Style(width=20, height=20), onClick=onClose,
                             children=OreIcon(name=OreIconName.close, size=8)),
                     ]),
                     OreScrollView(style=Style(width='100%', flex=1, minHeight=0), children=Panel(
                         style=Style(width='100%', padding=10, gap=8), children=[
                             OreText(content=message, color=OreColors.muted, style=Style(width=width - 28)) if message else None,
                             children,
                         ])),
                     Panel(style=Style(width='100%', padding=8, flexDirection=FlexDirection.row, gap=5), children=[
                         OreButton(label='取消', onClick=onClose, style=Style(flex=1)),
                        OreButton(key='ore_dialog_confirm', label=confirmLabel, variant=confirmVariant,
                                   onClick=onConfirm, style=Style(flex=1)),
                     ]),
                     ]))])


@Component
def OreField(label='', value=_UNSET, defaultValue='', onChange=None, disabled=False,
             placeholder='', style=None, search=False):
    """Ore framed text input with controlled and uncontrolled modes."""
    internal, set_internal = use_state(defaultValue)
    controlled = value is not _UNSET

    def change(next_value):
        if disabled:
            return
        if not controlled:
            set_internal(next_value)
        if onChange is not None:
            onChange(next_value)

    props = {
        'style': Style(width='100%', height=24),
        'onChange': None if disabled else change,
        'disabled': disabled,
        'value': value if controlled else internal,
        'children': NativeOreFieldText(content=OreString(text_value((value if controlled else internal) or placeholder)),
            fontSize=8, color=OreColors.disabled if disabled else OreColors.muted
                if not (value if controlled else internal) else OreColors.text, textAlign=TextAlignment.left, singleLine=True,
            style=Style(width='100%', height=16, marginTop=3.5, marginLeft=.75)),
    }
    return Panel(style=Style(width='100%', gap=5).merge(style), children=[
        OreText(content=label, color=OreColors.muted) if label else None,
        (NativeOreSearchInput if search else NativeOreInput)(**props),
    ])


@Component
def OreDropdown(options=None, value=_UNSET, defaultValue=_UNSET, onChange=None,
                placeholder='请选择', disabled=False, style=None, title='请选择'):
    options = options or []
    internal, set_internal = use_state(defaultValue if defaultValue is not _UNSET else None)
    opened, set_opened = use_state(False)
    current = internal if value is _UNSET else value
    label = next((text for text, item in options if item == current), placeholder)

    def choose(item):
        if disabled:
            return
        if value is _UNSET:
            set_internal(item)
        set_opened(False)
        if onChange:
            onChange(item)

    return Panel(style=Style(width='100%').merge(style), children=[
        OreButton(key='ore_dropdown_trigger', disabled=disabled,
                  style=Style(width='100%', height=24), onClick=partial(set_opened, True), children=[
            OreText(content=label, color=OreColors.darkText, style=Style(flex=1)),
            OreIcon(name='chevron_down', size=4, color=OreColors.darkText),
        ]),
        _ore_modal(visible=opened and not disabled, onClick=partial(set_opened, False),
            style=Style(alignItems=AlignItems.center, justifyContent=JustifyContent.center), children=[
                Image(color=Color(0x000000B3), style=Style(position=Position.absolute,
                    left=0, top=0, width='100%', height='100%')),
                modal_surface(key='ore_dropdown_surface',
                    # Outer border, header and the list's bottom separator
                    # need 27 units. A 26-unit budget scrolls even three rows.
                    style=Style(width=240, maxWidth='90%', height=27 + min(5, len(options)) * 24), children=
                    Image(color=Color(0x1E1E1FFF), style=Style(width='100%', height='100%', padding=1), children=[
                        Image(
                            src='textures/pyreact_ore/skin/dropdown_header',
                            imageAdaption=ImageAdaptionType.origin_nine_slice, nineSliceData=(2, 2, 2, 2),
                            style=Style(width='100%', height=24, paddingHorizontal=5,
                            flexDirection=FlexDirection.row, alignItems=AlignItems.center), children=[
                                OreText(content=title, fontSize=8, style=Style(position=Position.absolute,
                                    left=24, right=24, top=6), textAlign=TextAlignment.center),
                                NativeOreButton(key='ore_dropdown_close',
                                    buttonBuilder=state_skin('icon', slices=(0, 0, 0, 0)),
                                    style=Style(position=Position.absolute, right=3, top=2, width=20, height=20), onClick=partial(set_opened, False),
                                    children=OreIcon(name=OreIconName.close, size=8)),
                            ]),
                        Image(color=Color(0x8C8D90FF), style=Style(width='100%', flex=1, paddingHorizontal=1, paddingBottom=1),
                            children=OreScrollView(showScrollbar=len(options) > 5, style=Style(width='100%', flex=1), children=Panel(style=Style(width='100%'), children=[
                            NativeOreButton(key='ore_option_' + str(index),
                                buttonBuilder=partial(_menu_row, index), style=Style(width='100%', height=24,
                                    paddingHorizontal=8, flexDirection=FlexDirection.row, alignItems=AlignItems.center),
                                onClick=partial(choose, item), children=[
                                    OreText(content=text, fontSize=8, style=Style(flex=1)),
                                    OreIcon(name=OreIconName.check, size=9) if item == current else None,
                                    Image(color=Color(0x8C8D90FF), style=Style(position=Position.absolute,
                                        left=-8, right=-8, height=1, bottom=0)) if index < len(options) - 1 else None,
                                ]) for index, (text, item) in enumerate(options)]))),
                    ])),
            ]),
    ])


def _menu_row(index, state):
    color = Color(0x58585AFF)
    if state == ButtonState.hover:
        color = Color(0x48494AFF)
    elif state == ButtonState.pressed:
        color = OreColors.background
    return Image(color=color)


@Component
def OreSwitch(value=_UNSET, defaultValue=False, onChange=None, disabled=False,
              label='', style=None):
    internal, set_internal = use_state(bool(defaultValue))
    current = internal if value is _UNSET else bool(value)

    def change():
        if disabled:
            return
        if value is _UNSET:
            set_internal(not current)
        if onChange:
            onChange(not current)

    def builder(state):
        suffix = 'disabled' if disabled else state
        return Image(src='textures/pyreact_ore/skin/switch_%s_%s' % ('on' if current else 'off', suffix))

    control = NativeOreButton(style=Style(width=30, height=16),
        onClick=None if disabled else change, buttonBuilder=builder)
    return Panel(style=Style(flexDirection=FlexDirection.row,
                             alignItems=AlignItems.center, gap=6).merge(style), children=[
        control,
        OreText(content=label, color=OreColors.disabled if disabled else OreColors.text)
        if label else None,
    ])


@Component
def OreRadio(options, value, onChange, disabled=None, style=None):
    """Diamond radio indicators with a full-row native hit area."""
    disabled = disabled or []
    children = []
    for label, option in options:
        selected = option == value
        is_disabled = option in disabled
        children.append(NativeOreRadioButton(key='ore_radio_' + str(option),
            buttonBuilder=state_skin('radio_on' if selected else 'radio_off', disabled=is_disabled,
                slices=(0, 0, 0, 0)), onClick=None if is_disabled else partial(onChange, option),
            style=Style(width='100%', height=28, minHeight=28, paddingLeft=22,
                flexDirection=FlexDirection.row, justifyContent=JustifyContent.flex_start),
            children=OreText(content=label, fontSize=8, color=OreColors.disabled if is_disabled else OreColors.text)))
    return Panel(style=Style(width='100%').merge(style), children=children)


@Component
def OreTag(label='', color=None, style=None):
    """Compact status tag built from the Ore palette."""
    color = color or OreColors.primary
    unused, widths = text_layout(text_value(label), 7)
    return Image(color=color, style=Style(height=16, width=max(widths) + 12, paddingHorizontal=6,
                 alignSelf=AlignSelf.flex_start, alignItems=AlignItems.center,
                 justifyContent=JustifyContent.center).merge(style),
                 children=OreText(content=label, fontSize=7,
                                  textAlign=TextAlignment.center))


@Component
def OreBadge(label='', color=None, style=None):
    """Small counter/status badge."""
    unused, widths = text_layout(text_value(label), 7)
    return Image(color=color or OreColors.destructive,
                 style=Style(width=max(18, max(widths) + 10), height=16, alignSelf=AlignSelf.flex_start, alignItems=AlignItems.center,
                             justifyContent=JustifyContent.center).merge(style),
                 children=OreText(content=label, fontSize=7,
                                  textAlign=TextAlignment.center))


@Component
def OreBanner(message='', tone=OreTone.info, onClose=None, style=None):
    """Dismissible feedback banner with success/warning/error tones."""
    colors = {'info': OreColors.surface, 'success': OreColors.primary,
              'warning': palette_color('orange30'), 'error': OreColors.destructive}
    return Image(color=colors.get(tone, OreColors.surface),
                 style=Style(width='100%', minHeight=28, paddingHorizontal=8,
                             paddingVertical=4,
                             flexDirection=FlexDirection.row, alignItems=AlignItems.center,
                             gap=6).merge(style),
                 children=[OreText(content=message, style=Style(flex=1)),
                           NativeOreButton(key='ore_banner_close', buttonBuilder=state_skin('icon', slices=(0, 0, 0, 0)),
                                     onClick=onClose, style=Style(width=20, height=20),
                                     children=OreIcon(name=OreIconName.close, size=8)) if onClose else
                           # Reserve the minimum row height in the host measure pass.
                           Panel(style=Style(width=0, height=20))])


@Component
def OreAccordion(title='', expanded=False, onToggle=None, children=None, style=None):
    """Expandable Ore panel; the header remains a normal touch button."""
    return Panel(style=Style(width='100%', gap=4).merge(style), children=[
        OreButton(label=title, icon='chevron_down' if expanded else 'chevron_right', variant=OreVariant.neutral,
                  elevated=False, onClick=onToggle, style=Style(width='100%')),
        Panel(style=Style(width='100%', padding=6, visible=expanded), children=children)
        if expanded else None,
    ])


@Component
def OrePagination(page=1, pages=1, onChange=None, style=None):
    """Previous/next paging controls with disabled edge states."""
    pages = max(1, int(pages))
    page = max(1, min(pages, int(page)))
    def change(next_page):
        if onChange is not None and 1 <= next_page <= pages and next_page != page:
            onChange(next_page)
    return Panel(style=Style(flexDirection=FlexDirection.row, gap=5,
                             alignItems=AlignItems.center).merge(style), children=[
        OreButton(key='ore_page_previous', icon='chevron_left', variant=OreVariant.neutral, elevated=False,
                  style=Style(width=24, minWidth=24),
                  disabled=page <= 1, onClick=partial(change, page - 1)),
        OreText(content='第 %d 页，共 %d 页' % (page, pages), style=Style(minWidth=64),
                textAlign=TextAlignment.center),
        OreButton(key='ore_page_next', icon='chevron_right', variant=OreVariant.neutral, elevated=False,
                  style=Style(width=24, minWidth=24),
                  disabled=page >= pages, onClick=partial(change, page + 1)),
    ])


@Component
def OreDrawer(visible=False, title='', onClose=None, side=OreSide.right, children=None):
    """Full-height side panel with the same input shield as OreDialog."""
    return _ore_modal(visible=visible, onClick=onClose,
                 style=Style(justifyContent=JustifyContent.center,
                             alignItems=AlignItems.flex_start if side == 'left'
                             else AlignItems.flex_end), children=[
        Image(color=Color(0x00000099), style=Style(position=Position.absolute,
              left=0, top=0, width='100%', height='100%')),
        modal_surface(key='ore_drawer_surface',
                        style=Style(width=200, maxWidth='85%', height='100%'),
                        children=OreCard(style=Style(width='100%', height='100%', gap=8), children=[
            Panel(style=Style(flexDirection=FlexDirection.row, gap=5,
                              alignItems=AlignItems.center), children=[
                OreText(content=title, style=Style(flex=1)),
                NativeOreButton(key='ore_drawer_close', buttonBuilder=state_skin('icon', slices=(0, 0, 0, 0)),
                          onClick=onClose, style=Style(width=20, height=20),
                          children=OreIcon(name=OreIconName.close, size=8)),
            ]),
            children,
        ])),
    ])


@Component
def OreHelp(label='说明', message='', style=None):
    """A tap-accessible help bubble; never requires hover to reveal its message."""
    visible, set_visible = use_state(False)
    return Panel(style=Style(width='100%', gap=4).merge(style), children=[
        OreButton(key='ore_help_trigger', label=label, elevated=False,
                  onClick=partial(set_visible, not visible)),
        OreCard(style=Style(width='100%', padding=6), children=OreText(
            content=message, color=OreColors.muted, style=Style(width='100%')))
        if visible else None,
    ])
