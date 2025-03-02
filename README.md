# edge-tunnel

这是一个基于CF Worker平台的JavaScript,在天书的基础上进行优化

本人是初学者，代码有问题欢迎指出

点个星星再走吧
[![Stargazers over time](https://starchart.cc/ImLTHQ/edge-tunnel.svg?variant=adaptive)](https://starchart.cc/ImLTHQ/edge-tunnel)

# 使用方法

请先注册GitHub和Cloudflare(下面简称CF)账号

<details>
<summary><code><strong>「 Pages部署教程(推荐) 」</strong></code></summary>

1. 部署 CF Pages:
- 在Github上先 Fork 本项目
- 在CF Pages控制台中选择`连接到 Git`后,选中`edge-tunnel`项目后，按照下面`变量说明`添加环境变量
- 点击`开始设置`

2. 使用订阅:
- 在你的Clash/V2ray客户端导入订阅地址`https://域名/订阅路径`即可
</details>

<details>
<summary><code><strong>「 Worker 部署教程 」</strong></code></summary>

1. 部署 CF Worker:
- 在Github上先Fork本项目
- 在CF Worker 控制台中创建一个新的Worker
- 在`导入存储库`中选择`edge-tunnel`,选择`构建变量`，按照下面`变量说明`添加环境变量
- 点击`保存并部署`

2. 因为部分用户无法访问CF分配的地址,建议按照`给 Pages/Workers绑定自定义域名`绑定自定义域名

3. 使用订阅:
- 在你的Clash/V2ray客户端导入订阅地址`https://域名/订阅路径`即可
</details>

<details>
<summary><code><strong>「 部署后建议做的 」</strong></code></summary>

1. 设置Github Action
- 来到你Fork的仓库
- 在`Actions`选项卡中点击`绿色按钮`
- 选择`上游同步`
- 点击`Enable workflow`
- 这是为了使你的仓库与作者的同步保持最新

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

# 变量说明

| 变量名 | 示例 | 备注 |
|-|-|-|
| SUB_PATH | `sub` | 订阅路径（支持中文） |
| SUB_UUID | `550e8400-e29b-41d4-a716-446655440000` | 用于验证的UUID |
| TXT_URL | `https://raw.githubusercontent.com/ImLTHQ/edge-tunnel/main/Domain.txt` | 优选IP的txt地址  地址之间用换行隔开  格式: 地址:端口#节点名称  端口不填默认443  节点名称不填则使用默认节点名称，任何都不填使用自身域名 |
| SUB_NAME | `节点` | 默认节点名称 |
| PROXY_IP | `ts.hpc.tw:443` | 反代IP |
| SOCKS5_GLOBAL | `false` | 启用SOCKS5全局反代 |
| SOCKS5 | `账号:密码@地址:端口` | SOCKS5 |

# 已适配客户端

Windows

- [v2rayN](https://github.com/2dust/v2rayN)
- clash（[FlClash](https://github.com/chen08209/FlClash)，[mihomo-party](https://github.com/mihomo-party-org/mihomo-party)，[clash-verge-rev](https://github.com/clash-verge-rev/clash-verge-rev)，[Clash Nyanpasu](https://github.com/keiko233/clash-nyanpasu)）

安卓

- [v2rayNG](https://github.com/2dust/v2rayNG)
- [ClashMetaForAndroid](https://github.com/MetaCubeX/ClashMetaForAndroid)

MacOS

- [v2rayN](https://github.com/2dust/v2rayN)
- clash（[FlClash](https://github.com/chen08209/FlClash)，[mihomo-party](https://github.com/mihomo-party-org/mihomo-party)）

# 更多ProxyIP

- `ProxyIP.US.CMLiussss.net` IP落地区域: 🇺🇸 美国
- `ProxyIP.SG.CMLiussss.net` IP落地区域: 🇸🇬 新加坡
- `ProxyIP.JP.CMLiussss.net` IP落地区域: 🇯🇵 日本
- `ProxyIP.HK.CMLiussss.net` IP落地区域: 🇭🇰 香港 [白嫖哥维护](https://t.me/v2rayByCf/295)
- `ProxyIP.KR.CMLiussss.net` IP落地区域: 🇰🇷 韩国
- `ProxyIP.DE.tp2024.CMLiussss.net` 🤖️GPT专用 IP落地区域: 🇩🇪 德国
- `ProxyIP.Aliyun.CMLiussss.net` IP落地区域: ☁️ 阿里云
- `ProxyIP.Oracle.CMLiussss.net` IP落地区域: ☁️ 甲骨文
- `ProxyIP.DigitalOcean.CMLiussss.net` IP落地区域: ☁️ 数码海
- `ProxyIP.Vultr.CMLiussss.net` IP落地区域: ☁️ Vultr
- `ProxyIP.Multacom.CMLiussss.net` IP落地区域: ☁️ Multacom

# 感谢
[shulng](https://github.com/shulng)，[XIU2](https://github.com/XIU2)，[zizifn](https://github.com/zizifn)，[cmliu](https://github.com/cmliu)