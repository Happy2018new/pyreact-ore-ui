# 设计参考

当前控件以本机国际版 Bedrock 1.26.5203.0 的原生截图为准。用户提供的图片补充了旧版下拉菜单及好友面板。版本不同的截图不用于宣称原像素一致。

2026-10-04 读取 [中文 Minecraft Wiki 的 Ore UI 页面](https://zh.minecraft.wiki/w/Ore_UI)，页面列出的设计系统图覆盖按钮状态、复选框、单选、下拉、滑块、开关、输入框、页签和标签，示例页面还包含游戏列表、存档编辑和好友界面。它们适合研究组件类别和页面结构，不能替代同版本的实际状态采集。研究用图未打包为运行时资源。

菱形单选的形状与源 ZIP 的 RadioBox CSS 对照：外框为旋转 45 度的正方形，选中时显示较小的反光方形。原先的圆形文本示意已替换，default、hover、pressed 与 disabled 有独立皮肤。当前未获得本机同版本的 native 单选裁切，形状研究和游戏命中检查不能代替逐像素验收。

- [File:Ore_UI.png](https://zh.minecraft.wiki/w/File:Ore_UI.png)
- [File:Ore_UI_Design_System.png](https://zh.minecraft.wiki/w/File:Ore_UI_Design_System.png)
- [File:Ore_UI_Design_System_Updated.png](https://zh.minecraft.wiki/w/File:Ore_UI_Design_System_Updated.png)
- [单选状态设计](https://zh.minecraft.wiki/w/File:Ore_UI_Design_System_-_Radio_Button_State.png)
- [标签变体设计](https://zh.minecraft.wiki/w/File:Ore_UI_Design_System_-_Tag_Variant.png)
- [Ore UI开发者页面板块](https://zh.minecraft.wiki/w/File:Ore_UI_Developer_Pages.png)
- [成就菜单的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:AchievementsMenuBE_Simplified.png)
- [选择世界菜单的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:Play_Menu_All_Worlds_Tab_(empty)_Simplified.png)
- [选择世界菜单内Realms标签页的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:Ore_UI_-_Play_Screen_Realms_Tab_(Bedrock).png)
- [选择世界菜单内服务器标签页的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:Featured_Servers_Simplified.png)
- [创建新世界内“通用”标签页的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:Create_new_world_General_Simplified.png)
- [编辑世界菜单内“通用”标签页的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:Edit_world_General_Simplified.png)
- [使用Ore UI的“社交”抽屉式菜单](https://zh.minecraft.wiki/w/File:Ore_UI_-_Game_Menu_-_Social_Tab_Screen_Menu_%22People%22_Tab_(Bedrock)_Simplified.png)
- [在床上入睡屏幕的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:Ore_UI_-_Sleep_Screen_Menu_(Bedrock)_Simplified.png)
- [在生存模式和冒险模式下死亡菜单的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:Bedrock_Death_Scene_1.20.51.png)
- [在极限模式下死亡后游戏结束菜单的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:BE_hardcore_death_screen_Simplified.png)
- [档案菜单的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:Ore_UI_-_Profile_Screen_Menu_(Bedrock)_Simplified.png)
- [搜索玩家界面的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:Search_for_Players_Screen_Menu_BE_OreUI_Simplified.png)
- [收件箱界面的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:Ore_UI_-_Inbox_Screen_Menu_(Bedrock)_Simplified.png)
- [控制模式屏幕菜单中触摸设置的Ore UI翻新版本（基岩版26.10前）](https://zh.minecraft.wiki/w/File:Ore_UI_-_Settings_Touch_-_Control_Mode_Screen_Menu_(Bedrock)_Simplified.png)
- [玩家权限菜单的Ore UI翻新版本：基岩版1.21.70.22](https://zh.minecraft.wiki/w/File:Ore_UI_-_Player_Permissions_Screen_Menu_(Bedrock)_Simplified.png)
- [断开连接界面的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:Disconnected_Screen_BE_OreUI_Simplified.png)
- [设置菜单的Ore UI翻新版本](https://zh.minecraft.wiki/w/File:OreUI_Settings_screenshot.jpg)
- [开发中的Ore UI成就界面](https://zh.minecraft.wiki/w/File:OreUI_development_achievements.jpg)
