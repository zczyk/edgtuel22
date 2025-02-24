# edge-tunnel
这是一个基于CF Worker平台的JavaScript,在原版的基础上简化并添加了对客户端的识别,不依赖外部订阅转换

# 使用方法
动手点个星星吧。我真的很需要！！！

<details>
<summary><code><strong>「 Pages部署教程(推荐) 」</strong></code></summary>

1. 部署 CF Pages:
- 在Github上先 Fork 本项目
- 在CF Pages控制台中选择`连接到 Git`后,选中`edge-tunnel`项目后点击`开始设置`

2. 使用订阅:
- 在你的Clash/V2ray客户端导入订阅地址`https://CF分配的域名/sub`即可
</details>

<details>
<summary><code><strong>「 Worker 部署教程 」</strong></code></summary>

1. 部署 CF Worker:
- 在Github上先Fork本项目
- 在CF Worker 控制台中创建一个新的Worker
- 在`导入存储库`中选择`edge-tunnel`,点击`保存并部署`

2. 因为部分用户无法访问CF分配的地址,建议按照下面的教程绑定自定义域名
</details>

<details>
<summary><code><strong>「 给 Pages/Workers绑定自定义域名 」</strong></code></summary>

1. CF连接你的域名:
- 去`账户主页`,选择`域`,输入你的域名,点击`继续`
- 按照需求选择计划(免费的够用了),点击`继续`,点击`继续前往激活`,点击`确认`
- 按照CF的要求返回你的域名服务商,将你当前的DNS服务器替换为CF DNS服务器

2. Worker绑定自定义域名
- 点击Worker控制台的`设置`选项卡,在`域和路由`那一栏点`添加`,选择`自定义域`
- 填入你的自定义域名
- 点击`添加域`

3. Pages绑定自定义域名
- 点击Pages控制台的`自定义域`选项卡,点击`设置自定义域`
- 填入你的自定义域名
- 点击`继续`,点击`激活域`
</details>

# Star 星星走起
[![Stargazers over time](https://starchart.cc/ImLTHQ/edge-tunnel.svg?variant=adaptive)](https://starchart.cc/ImLTHQ/edge-tunnel)

# 已适配客户端
# Windows
- [v2rayN](https://github.com/2dust/v2rayN)
- clash.meta（[FlClash](https://github.com/chen08209/FlClash)，[mihomo-party](https://github.com/mihomo-party-org/mihomo-party)，[clash-verge-rev](https://github.com/clash-verge-rev/clash-verge-rev)，[Clash Nyanpasu](https://github.com/keiko233/clash-nyanpasu)）
# 安卓
- [v2rayNG](https://github.com/2dust/v2rayNG)
- clash.meta（[ClashMetaForAndroid](https://github.com/MetaCubeX/ClashMetaForAndroid)，[FlClash](https://github.com/chen08209/FlClash)）
### MacOS
- [v2rayN](https://github.com/2dust/v2rayN)
- clash.meta（[FlClash](https://github.com/chen08209/FlClash)，[mihomo-party](https://github.com/mihomo-party-org/mihomo-party)）

# 感谢
[shulng](https://github.com/shulng)，[XIU2](https://github.com/XIU2)

# 免责声明
本免责声明适用于 GitHub 上的 “edge-tunnel” 项目（以下简称“本项目”）,项目链接为:https://github.com/ImLTHQ/edge-tunnel

用途

本项目仅供教育、研究和安全测试目的而设计和开发。旨在为安全研究人员、学术界人士及技术爱好者提供一个探索和实践网络通信技术的工具。

合法性

在下载和使用本项目代码时,必须遵守使用者所适用的法律和规定。使用者有责任确保其行为符合所在地区的法律框架、规章制度及其他相关规定。