# astrbot_plugin_nowhere · 乌有乡

乌有乡（Nowhere）的非官方 AstrBot 移植版。AI 不是在文字里假装旅行，而是调用原版运行时，在真实地球坐标上开门、行走、观察环境、收听电台、询问地方、标记地点、等待时间、携带纪念品并寄回明信片。

## 安装

在 AstrBot WebUI 的插件管理中通过仓库地址安装：

`https://github.com/Yussica1026/astrbot_plugin_nowhere`

首次安装会下载原作所需的地理、天文与科学计算依赖，耗时可能较长。要求 Python 3.11+、AstrBot 4.17+。

## 使用

插件注册 `nowhere_travel` Agent 工具。正常聊天时可以直接对 AI 说“打开乌有乡的门，自己旅行一会儿”“继续上次的旅程”“看看周围并寄张明信片”，AI 会自行调用工具。

手动指令：

- `/nowhere` 或 `/nowhere 状态`
- `/nowhere 开门 北京`
- `/nowhere 走 N 2`
- `/nowhere 观察`
- `/nowhere 继续`
- `/nowhere 收听`
- `/nowhere 标记 河边`
- `/nowhere 明信片 今天走到了有风的地方。`

旅程存档位于 AstrBot 的 `data/plugin_data/astrbot_plugin_nowhere/`，更新插件不会覆盖。

## 原作与许可

- 原作：旋复（yuyixuanfu）
- 原项目：[yuyixuanfu/nowhere](https://github.com/yuyixuanfu/nowhere)
- 许可：CC BY-NC 4.0（署名—非商业性使用 4.0 国际）
- 本仓库是非官方 AstrBot 适配；`vendor/nowhere/` 保留原作 Python 源码、数据与测试。

仅限非商业使用。原作及所含第三方数据的许可边界以原项目文件为准。
