# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
from .pyreact import runtime_init, navigator
from .gallery import OreGallery
from .playground import OrePlayground

ClientSystem = clientApi.GetClientSystemCls()


class OreDemoClientSystem(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        runtime_init(self, debug=True)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'UiInitFinished', self, self.on_ui_init)
        self.ListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                            'OnKeyPressInGame', self, self.on_key)

    def on_ui_init(self, _=None):
        self.open_playground()

    def open_gallery(self):
        if navigator.depth == 0:
            navigator.push(OreGallery)

    def open_playground(self):
        if navigator.depth == 0:
            navigator.push(OrePlayground)

    def on_key(self, args):
        key = str(clientApi.GetMinecraftEnum().KeyBoardType.KEY_F8)
        if args.get('key') == key and args.get('isDown') == '0':
            self.open_playground()

    def Destroy(self):
        self.UnListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                              'UiInitFinished', self, self.on_ui_init)
        self.UnListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
                              'OnKeyPressInGame', self, self.on_key)
