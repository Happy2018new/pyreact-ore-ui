# -*- coding: utf-8 -*-
"""Copy this package alongside the host mod's existing `pyreact` package."""
from .assets import (asset, asset_names, texture, OreVariant, OreState, OreIconName,
                     button_asset)
from .theme import OreColors, OreTone, OreSide, palette_color
from .components import (OreImage, OreIcon, OreText, OreButton, OreCard, OreListItem,
                         OreTabs, OreCheckbox, OreSlider, OreProgress, OreDialog,
                         OreField, OreDropdown, OreSwitch, OreRadio, OreTag,
                         OreBadge, OreBanner, OreAccordion, OrePagination, OreDrawer, OreHelp, OreScrollView)
from .settings import (OreDivider, OreNavigationItem, OreNavigationGroup,
                       OreSettingsRow, OreSettingsSection, OreSegmentedControl,
                       OreIconButton, OreSettingsScreen, OreSettingLayout)
from .worlds import OreWorldCard

__version__ = '0.1.0'
__all__ = ['asset', 'asset_names', 'texture', 'button_asset', 'OreVariant', 'OreState',
           'OreIconName', 'OreColors', 'OreTone', 'OreSide', 'palette_color', 'OreImage', 'OreIcon', 'OreText',
           'OreButton', 'OreCard', 'OreListItem', 'OreTabs', 'OreCheckbox', 'OreSlider',
           'OreProgress', 'OreDialog', 'OreField', 'OreDropdown', 'OreSwitch', 'OreRadio',
           'OreTag', 'OreBadge', 'OreBanner', 'OreAccordion', 'OrePagination', 'OreDrawer', 'OreHelp', 'OreScrollView',
           'OreDivider', 'OreNavigationItem', 'OreNavigationGroup', 'OreSettingsRow',
           'OreSettingsSection', 'OreSegmentedControl', 'OreIconButton', 'OreSettingsScreen', 'OreSettingLayout', 'OreWorldCard']
