# edge-tunnel

这是一个基于CF Pages平台的JavaScript,在天书的基础上进行优化

本人是初学者, 代码有问题欢迎指出

点个星星再走吧
[![Stargazers over time](https://starchart.cc/ImLTHQ/edge-tunnel.svg?variant=adaptive)](https://starchart.cc/ImLTHQ/edge-tunnel)

# 使用方法

请先注册`GitHub`和`Cloudflare(下面简称CF)`账号
- 在Github上先 Fork 本项目
- 在CF 控制台中选择`计算(Workers)`
- 点击`创建`, 选择`Pages`
- 点击`连接到 Git`, 选中`edge-tunnel`项目, 修改`项目名称`
- 按照下面`变量说明`添加环境变量
- 点击`保存并部署`
- 在你的Clash/V2ray客户端导入订阅地址`https://域名/订阅路径`即可

<details>
<summary><code><strong>「 部署后建议做的 」</strong></code></summary>

设置Github Action
- 来到你Fork的仓库
- 在`Actions`选项卡中点击`绿色按钮`
- 选择`上游同步`
- 点击`Enable workflow`
- 这是为了使你的仓库与作者的同步保持最新
</details>

<details>
<summary><code><strong>「 绑定自定义域名(可选) 」</strong></code></summary>

CF连接你的域名:
- 去`账户主页`,选择`域`,输入你的域名,点击`继续`
- 按照需求选择计划(免费的够用了),点击`继续`,点击`继续前往激活`,点击`确认`
- 按照CF的要求返回你的域名服务商,将你当前的DNS服务器替换为CF DNS服务器

Pages绑定自定义域名
- 点击Pages控制台的`自定义域`选项卡,点击`设置自定义域`
- 填入域名
- 点击`继续`,点击`激活域`
</details>

# 变量说明

| 变量名 | 示例 | 备注 |
|-|-|-|
| SUB_PATH | `sub` | 订阅路径（支持中文） |
| SUB_UUID | `550e8400-e29b-41d4-a716-446655440000` | 用于验证的UUID |
| TXT_URL | `https://raw.githubusercontent.com/ImLTHQ/edge-tunnel/main/Domain.txt` | 优选IP的txt地址  支持多地址  地址之间用换行隔开  格式: 地址:端口#节点名称  端口不填默认443  节点名称不填则使用默认节点名称 |
| SUB_NAME | `节点` | 默认节点名称 |
| PROXY_IP | `ts.hpc.tw:443` | 反代IP |
| SOCKS5_GLOBAL | `ture`,`false` | 启用SOCKS5全局反代 |
| SOCKS5 | `账号:密码@地址:端口` | SOCKS5 |
| FAKE_WEB | `baidu.com` | 根路径的伪装网页 |

<details>
<summary><code><strong>「 更多ProxyIP 」</strong></code></summary>

- `ts.hpc.tw:443`
- `ProxyIP.US.CMLiussss.net`
- `ProxyIP.SG.CMLiussss.net`
- `ProxyIP.JP.CMLiussss.net`
- `ProxyIP.HK.CMLiussss.net`
- `ProxyIP.KR.CMLiussss.net`
- `ProxyIP.DE.tp2024.CMLiussss.net`
- `ProxyIP.Aliyun.CMLiussss.net`
- `ProxyIP.Oracle.CMLiussss.net`
- `ProxyIP.DigitalOcean.CMLiussss.net`
- `ProxyIP.Vultr.CMLiussss.net`
- `ProxyIP.Multacom.CMLiussss.net`
</details>

<details>
<summary><code><strong>「 本项目提供的优选TXT地址 」</strong></code></summary>

- `https://raw.githubusercontent.com/ImLTHQ/edge-tunnel/main/SpeedTest/HKG.txt` 香港
- `https://raw.githubusercontent.com/ImLTHQ/edge-tunnel/main/SpeedTest/KHH.txt` 台湾
- `https://raw.githubusercontent.com/ImLTHQ/edge-tunnel/main/SpeedTest/NRT.txt` 东京
- `https://raw.githubusercontent.com/ImLTHQ/edge-tunnel/main/SpeedTest/LAX.txt` 洛杉矶
- `https://raw.githubusercontent.com/ImLTHQ/edge-tunnel/main/SpeedTest/SEA.txt` 西雅图
- `https://raw.githubusercontent.com/ImLTHQ/edge-tunnel/main/SpeedTest/SJC.txt` 圣何塞
</details>

# 已适配客户端

Windows
- [v2rayN](https://github.com/2dust/v2rayN)
- clash（[FlClash](https://github.com/chen08209/FlClash), [mihomo-party](https://github.com/mihomo-party-org/mihomo-party), [clash-verge-rev](https://github.com/clash-verge-rev/clash-verge-rev), [Clash Nyanpasu](https://github.com/keiko233/clash-nyanpasu)）

安卓
- [v2rayNG](https://github.com/2dust/v2rayNG)
- [ClashMetaForAndroid](https://github.com/MetaCubeX/ClashMetaForAndroid)

MacOS
- [v2rayN](https://github.com/2dust/v2rayN)
- clash（[FlClash](https://github.com/chen08209/FlClash), [mihomo-party](https://github.com/mihomo-party-org/mihomo-party)）

# 未来计划

- 支持sing-box

# 免责声明

本免责声明适用于 GitHub 上的 "edge-tunnel" 项目 (以下简称"本项目"), 项目链接为：`https://github.com/ImLTHQ/edge-tunnel`

<strong>用途</strong>

- 本项目仅供教育、研究和安全测试目的而设计和开发。旨在为安全研究人员、学术界人士及技术爱好者提供一个探索和实践网络通信技术的工具。

<strong>合法性</strong>

- 在下载和使用本项目代码时, 必须遵守使用者所适用的法律和规定。使用者有责任确保其行为符合所在地区的法律框架、规章制度及其他相关规定。

<strong>免责</strong>

- 作为本项目的 **二次开发作者** (以下简称“作者”), 我 **ImLTHQ** 强调本项目仅应用于合法、道德和教育目的。
- 作者不认可、不支持亦不鼓励任何形式的非法使用。如果发现本项目被用于任何非法或不道德的活动, 作者将对此强烈谴责。
- 作者对任何人或组织利用本项目代码从事的任何非法活动不承担责任。使用本项目代码所产生的任何后果, 均由使用者自行承担。
- 作者不对使用本项目代码可能引起的任何直接或间接损害负责。
- 为避免任何意外后果或法律风险, 使用者应在使用本项目代码后的 24 小时内删除代码。

通过使用本项目代码, 使用者即表示理解并同意本免责声明的所有条款。如使用者不同意这些条款, 应立即停止使用本项目。

作者保留随时更新本免责声明的权利, 且不另行通知。最新版本的免责声明将发布在本项目的 GitHub 页面上。

# 感谢
[shulng](https://github.com/shulng), [XIU2](https://github.com/XIU2), [zizifn](https://github.com/zizifn), [cmliu](https://github.com/cmliu)