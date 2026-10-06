# -*- coding: utf-8 -*-
"""Stable texture names, metadata, and OreUI theme enums."""
from ._catalog import ASSETS, PALETTE
from ._reference_assets import ASSETS as REFERENCE_ASSETS
from ._settings_assets import ASSETS as SETTINGS_ASSETS

REFERENCE_ASSETS = dict(REFERENCE_ASSETS, **SETTINGS_ASSETS)


class OreVariant(object):
    primary = 'primary'
    secondary = 'secondary'
    neutral = 'neutral'
    destructive = 'destructive'
    realms = 'realms'


class OreState(object):
    default = 'default'
    hovered = 'hovered'
    pressed = 'pressed'
    pressed_focused = 'pressed_focused'
    focused = 'focused'
    disabled = 'disabled'
    disabled_focused = 'disabled_focused'


class OreIconName(object):
    check = 'check_white'
    checkMuted = 'check_grey'
    close = 'cross_white'
    back = 'arrow_back_white'
    search = 'magnifying_glass'
    settings = 'settings'
    world = 'world'


def asset(name):
    """Return a copy so callers cannot mutate the shared generated catalog."""
    if name not in ASSETS and name not in REFERENCE_ASSETS:
        raise ValueError('Unknown Ore asset: ' + str(name))
    metadata = dict(REFERENCE_ASSETS[name] if name in REFERENCE_ASSETS else ASSETS[name])
    if 'frames' in metadata:
        metadata['frames'] = [dict(frame) for frame in metadata['frames']]
    if 'frameDurations' in metadata:
        metadata['frameDurations'] = list(metadata['frameDurations'])
    return metadata


def texture(name):
    return asset(name)['src']


def asset_names(prefix=''):
    return sorted(name for name in list(ASSETS) + list(REFERENCE_ASSETS) if name.startswith(prefix))


def button_asset(variant, state, elevated=False):
    if variant not in (OreVariant.primary, OreVariant.secondary, OreVariant.neutral,
                       OreVariant.destructive, OreVariant.realms):
        raise ValueError('Unknown Ore button variant: ' + str(variant))
    if state not in (OreState.default, OreState.hovered, OreState.pressed,
                     OreState.focused, OreState.disabled):
        raise ValueError('Unknown Ore button state: ' + str(state))
    if state == OreState.disabled:
        return 'pressable_elevated_disabled' if elevated else 'pressable_disabled'
    suffix = state
    if variant == OreVariant.realms:
        prefix = 'realms_pressable_'
    else:
        prefix = 'pressable_'
    # Ore's raised buttons use the flat texture while pressed.
    if elevated and state != OreState.pressed:
        prefix += 'elevated_'
    if variant != OreVariant.realms:
        prefix += variant + '_'
    return prefix + suffix
