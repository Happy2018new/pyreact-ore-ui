# -*- coding: utf-8 -*-
from mod.common.mod import Mod
import mod.client.extraClientApi as clientApi


@Mod.Binding(name='PyreactOreDemo', version='0.1.0')
class PyreactOreDemoMod(object):
    @Mod.InitClient()
    def init_client(self):
        clientApi.RegisterSystem('PyreactOreDemo', 'Client', 'ore_demo.client_system.OreDemoClientSystem')
