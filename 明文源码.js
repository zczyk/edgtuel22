import { connect } from 'cloudflare:sockets';

////////////////////////////////////////////////////////////////////////// 配置区块 ////////////////////////////////////////////////////////////////////////
const SUB_PATH = "XiaoYeTech"; // 订阅路径，支持任意大小写字母和数字， [域名/SUB_PATH] 进入订阅页面
const V2RAY_PATH = 'v2ray';
const CLASH_PATH = 'clash';
const SUB_UUID = "550e8400-e29b-41d4-a716-446655440000"; // 订阅验证 UUID，建议修改为自己的UUID

let PREFERRED_NODES = [
    //'www.wto.org',
];  // 格式: IP(v6也可以哦)/域名:端口#节点名称  端口不填默认443 节点名称不填则使用统一名称，任何都不填使用自身域名

let PREFERRED_NODES_TXT_URL = [
  'https://raw.githubusercontent.com/ImLTHQ/edgeTunnel/refs/heads/main/Domain.txt',
];  // 优选节点 TXT 文件路径，使用 TXT 时，脚本内部填写的节点无效，两者二选一

const PROXY_ENABLED = true; // 是否启用反代功能 （总开关）
const PROXY_ADDRESS = 'ts.hpc.tw:443'; // 反代 IP 或域名，格式：地址:端口

const SOCKS5_PROXY_ENABLED = false; // 是否启用 SOCKS5 反代，启用后原始反代将失效
const SOCKS5_GLOBAL_PROXY_ENABLED = false; // 是否启用 SOCKS5 全局反代
const SOCKS5_CREDENTIALS = ''; // SOCKS5 账号信息，格式：'账号:密码@地址:端口'

const NODE_NAME = '晓夜'; // 节点名称【统一名称】
const FAKE_WEBSITE = 'www.baidu.com'; // 伪装网页，如 'www.baidu.com'

////////////////////////////////////////////////////////////////////////// 网页入口 ////////////////////////////////////////////////////////////////////////

export default {
  async fetch(request, env) {
    const upgradeHeader = request.headers.get('Upgrade');
    const url = new URL(request.url);
    const { pathname } = url;

    if (!upgradeHeader || upgradeHeader !== 'websocket') {
      // 加载优选节点
      if (PREFERRED_NODES_TXT_URL.length > 0) {
        const response = await Promise.all(PREFERRED_NODES_TXT_URL.map(url => fetch(url).then(response => response.ok ? response.text() : '')));
        const text = response.flat();
        PREFERRED_NODES = text.map(text => text.split('\n').map(line => line.trim()).filter(line => line)).flat();
      }

      if (pathname === `/${SUB_PATH}`) {
        return new Response(generateSubPage(SUB_PATH, request.headers.get('Host')), {
          status: 200,
          headers: { "Content-Type": "text/plain;charset=utf-8" },
        });
      }

      if (pathname === `/${SUB_PATH}/${V2RAY_PATH}`) {
        return new Response(generateVlessConfig(request.headers.get('Host')), {
          status: 200,
          headers: { "Content-Type": "text/plain;charset=utf-8" },
        });
      }

      if (pathname === `/${SUB_PATH}/${CLASH_PATH}`) {
        return new Response(generateClashConfig(request.headers.get('Host')), {
          status: 200,
          headers: { "Content-Type": "text/plain;charset=utf-8" },
        });
      }

      // 默认伪装网站
      url.hostname = FAKE_WEBSITE;
      url.protocol = 'https:';
      return fetch(new Request(url, request));

    } else if (upgradeHeader === 'websocket') {
      const envProxyIp = env.PROXYIP || PROXY_ADDRESS;
      const envSocks5 = env.SOCKS5 || SOCKS5_CREDENTIALS;
      const envSocks5Open = (env.SOCKS5OPEN === 'true' ? true : (env.SOCKS5OPEN === 'false' ? false : SOCKS5_PROXY_ENABLED));
      const envSocks5Global = (env.SOCKS5GLOBAL === 'true' ? true : (env.SOCKS5GLOBAL === 'false' ? false : SOCKS5_GLOBAL_PROXY_ENABLED));

      return upgradeWebSocketRequest(request, envProxyIp, envSocks5, envSocks5Open, envSocks5Global);
    }
  },
};
//////////////////////////////////////////////////////////////////////// 脚本主要架构 //////////////////////////////////////////////////////////////////////

async function upgradeWebSocketRequest(request, envProxyIp, envSocks5, envSocks5Open, envSocks5Global) {
  const webSocketPair = new WebSocketPair();
  const [client, webSocket] = Object.values(webSocketPair);
  webSocket.accept();

  const encodedTarget = request.headers.get('sec-websocket-protocol');
  const decodedTarget = decodeBase64(encodedTarget);
  const { tcpSocket, initialData } = await parseVLHeader(decodedTarget, envProxyIp, envSocks5, envSocks5Open, envSocks5Global);

  establishPipeline(webSocket, tcpSocket, initialData);

  return new Response(null, { status: 101, webSocket: client });
}

function decodeBase64(encoded) {
  const base64String = encoded.replace(/-/g, '+').replace(/_/g, '/');
  const decodedString = atob(base64String);
  return Uint8Array.from(decodedString, (c) => c.charCodeAt(0)).buffer;
}

async function parseVLHeader(vlData, envProxyIp, envSocks5, envSocks5Open, envSocks5Global) {
  if (verifyUUID(new Uint8Array(vlData.slice(1, 17))) !== SUB_UUID) {
    return null;
  }

  const dataLocation = new Uint8Array(vlData)[17];
  const portStartIndex = 18 + dataLocation + 1;
  const portBuffer = vlData.slice(portStartIndex, portStartIndex + 2);
  const targetPort = new DataView(portBuffer).getUint16(0);
  const addressStartIndex = portStartIndex + 2;
  const addressTypeBuffer = new Uint8Array(vlData.slice(addressStartIndex, addressStartIndex + 1));
  const addressType = addressTypeBuffer[0];

  let addressLength = 0;
  let targetAddress = '';
  let addressInfoStartIndex = addressStartIndex + 1;

  switch (addressType) {
    case 1:
      addressLength = 4;
      targetAddress = new Uint8Array(vlData.slice(addressInfoStartIndex, addressInfoStartIndex + addressLength)).join('.');
      break;
    case 2:
      addressLength = new Uint8Array(vlData.slice(addressInfoStartIndex, addressInfoStartIndex + 1))[0];
      addressInfoStartIndex += 1;
      targetAddress = new TextDecoder().decode(vlData.slice(addressInfoStartIndex, addressInfoStartIndex + addressLength));
      break;
    case 3:
      addressLength = 16;
      const dataView = new DataView(vlData.slice(addressInfoStartIndex, addressInfoStartIndex + addressLength));
      const ipv6Parts = [];
      for (let i = 0; i < 8; i++) { ipv6Parts.push(dataView.getUint16(i * 2).toString(16)); }
      targetAddress = ipv6Parts.join(':');
      break;
  }

  const initialData = vlData.slice(addressInfoStartIndex + addressLength);
  let tcpSocket;

  if (PROXY_ENABLED && envSocks5Open && envSocks5Global) {
    tcpSocket = await createSocks5Socket(addressType, targetAddress, targetPort, envProxyIp, envSocks5);
    return { tcpSocket, initialData };
  } else {
    try {
      tcpSocket = connect({ hostname: targetAddress, port: targetPort });
      await tcpSocket.opened;
    } catch {
      if (PROXY_ENABLED) {
        if (envSocks5Open) {
          tcpSocket = await createSocks5Socket(addressType, targetAddress, targetPort, envProxyIp, envSocks5);
        } else {
          let [proxyHost, proxyPort] = envProxyIp.split(':');
          tcpSocket = connect({ hostname: proxyHost, port: proxyPort || targetPort });
        }
      }
    } finally {
      return { tcpSocket, initialData };
    }
  }
}

function verifyUUID(arr, offset = 0) {
  const uuid = (
    formatUUID[arr[offset + 0]] + formatUUID[arr[offset + 1]] + formatUUID[arr[offset + 2]] + formatUUID[arr[offset + 3]] + "-" +
    formatUUID[arr[offset + 4]] + formatUUID[arr[offset + 5]] + "-" +
    formatUUID[arr[offset + 6]] + formatUUID[arr[offset + 7]] + "-" +
    formatUUID[arr[offset + 8]] + formatUUID[arr[offset + 9]] + "-" +
    formatUUID[arr[offset + 10]] + formatUUID[arr[offset + 11]] + formatUUID[arr[offset + 12]] + formatUUID[arr[offset + 13]] + formatUUID[arr[offset + 14]] + formatUUID[arr[offset + 15]]
  ).toLowerCase();
  return uuid;
}

const formatUUID = [];
for (let i = 0; i < 256; ++i) { formatUUID.push((i + 256).toString(16).slice(1)); }

async function establishPipeline(webSocket, tcpSocket, initialData, tcpBuffer = [], wsBuffer = []) {
  const tcpWriter = tcpSocket.writable.getWriter();
  await webSocket.send(new Uint8Array([0, 0]).buffer); // 发送 WS 握手认证信息

  tcpSocket.readable.pipeTo(new WritableStream({
    async write(chunk) {
      wsBuffer.push(chunk);
      const wsData = wsBuffer.shift();
      webSocket.send(wsData);
    }
  }));

  const wsDataStream = new ReadableStream({
    async start(controller) {
      if (initialData) { controller.enqueue(initialData); initialData = null }
      webSocket.addEventListener('message', (event) => { controller.enqueue(event.data) });
      webSocket.addEventListener('close', () => { controller.close() });
      webSocket.addEventListener('error', () => { controller.close() });
    }
  });

  wsDataStream.pipeTo(new WritableStream({
    async write(chunk) {
      tcpBuffer.push(chunk)
      const tcpData = tcpBuffer.shift();
      tcpWriter.write(tcpData)
    },
  }));
}
////////////////////////////////////////////////////////////////////////// SOCKS5 部分 //////////////////////////////////////////////////////////////////////
async function createSocks5Socket(addressType, targetAddress, targetPort, envProxyIp, envSocks5) {
  const { username, password, hostname, port } = await parseSocks5Credentials(envSocks5);
  const socket = connect({ hostname, port });
  try {
    await socket.opened;
  } catch (e) {
    return new Response('SOCKS5 连接失败', { status: 400 });
  }

  const writer = socket.writable.getWriter();
  const reader = socket.readable.getReader();
  const encoder = new TextEncoder();

  // SOCKS5 认证请求
  const socksGreeting = new Uint8Array([5, 2, 0, 2]); // 支持无认证和用户名/密码认证
  await writer.write(socksGreeting);
  let response = (await reader.read()).value;

  if (response[1] === 0x02) { // 需要用户名/密码认证
    if (!username || !password) {
      return closeAndReject(writer, reader, socket, 'SOCKS5 认证失败,缺少账号密码');
    }
    const authRequest = new Uint8Array([
      1, username.length, ...encoder.encode(username), password.length, ...encoder.encode(password),
    ]);
    await writer.write(authRequest);
    response = (await reader.read()).value;
    if (response[0] !== 0x01 || response[1] !== 0x00) {
      return closeAndReject(writer, reader, socket, 'SOCKS5 认证失败');
    }
  }

  // SOCKS5 连接请求
  let convertedAddress;
  switch (addressType) {
    case 1: // IPv4
      convertedAddress = new Uint8Array([1, ...targetAddress.split('.').map(Number)]);
      break;
    case 2: // 域名
      convertedAddress = new Uint8Array([3, targetAddress.length, ...encoder.encode(targetAddress)]);
      break;
    case 3: // IPv6
      convertedAddress = new Uint8Array([4, ...targetAddress.split(':').flatMap(x => [parseInt(x.slice(0, 2), 16), parseInt(x.slice(2), 16)])]);
      break;
    default:
      return closeAndReject(writer, reader, socket, 'SOCKS5 地址类型错误');
  }

  const socksRequest = new Uint8Array([5, 1, 0, ...convertedAddress, targetPort >> 8, targetPort & 0xff]);
  await writer.write(socksRequest);
  response = (await reader.read()).value;
  if (response[0] !== 0x05 || response[1] !== 0x00) {
    return closeAndReject(writer, reader, socket, 'SOCKS5 连接失败')
  }

  writer.releaseLock();
  reader.releaseLock();
  return socket;
}
async function closeAndReject(writer, reader, socket, message) {
  writer.releaseLock();
  reader.releaseLock();
  socket.close();
  return new Response(message, { status: 400 });
}
async function parseSocks5Credentials(socks5String) {
  const [latter, former] = socks5String.split("@").reverse();
  let username = null, password = null, hostname = null, port = null;

  if (former) {
    const formers = former.split(":");
    username = formers[0];
    password = formers[1];
  }

  const latters = latter.split(":");
  port = Number(latters.pop());
  hostname = latters.join(":");

  return { username, password, hostname, port };
}
////////////////////////////////////////////////////////////////////////// 订阅页面 ////////////////////////////////////////////////////////////////////////

function generateSubPage(subPath, hostName) {
  return `
v2ray的：https://${hostName}/${subPath}/${V2RAY_PATH}
Clash的：https://${hostName}/${subPath}/${CLASH_PATH}
`;
}

function generateVlessConfig(hostName) {
  if (PREFERRED_NODES.length === 0) {
    PREFERRED_NODES = [`${hostName}:443`];
  }
  return PREFERRED_NODES.map(node => {
    const [mainPart] = node.split("@");
    const [addressPort, nodeName = NODE_NAME] = mainPart.split("#");
    const [address, portStr] = addressPort.split(":");
    const port = portStr ? Number(portStr) : 443;
    return `vless://${SUB_UUID}@${address}:${port}?encryption=none&security=tls&sni=${hostName}&type=ws&host=${hostName}&path=%2F%3Fed%3D2560#${nodeName}`;
  }).join("\n");
}
function generateClashConfig(hostName) {
  if (PREFERRED_NODES.length === 0) {
    PREFERRED_NODES = [`${hostName}:443`];
  }
  const generateNodes = (nodes) => {
    return nodes.map(node => {
      const [mainPart] = node.split("@");
      const [addressPort, nodeName = NODE_NAME] = mainPart.split("#");
      const [address, portStr] = addressPort.split(":");
      const port = portStr ? Number(portStr) : 443;
      const cleanAddress = address.replace(/^\[(.+)\]$/, '$1');
      return {
        nodeConfig: `- name: ${nodeName}
  type: vless
  server: ${cleanAddress}
  port: ${port}
  uuid: ${SUB_UUID}
  udp: false
  tls: true
  sni: ${hostName}
  network: ws
  ws-opts:
    path: "/?ed=2560"
    headers:
      Host: ${hostName}`,
        proxyConfig: `    - ${nodeName}`
      };
    });
  };

  const nodeConfigs = generateNodes(PREFERRED_NODES).map(node => node.nodeConfig).join("\n");
  const proxyConfigs = generateNodes(PREFERRED_NODES).map(node => node.proxyConfig).join("\n");

  return `
dns:
  nameserver:
    - 1.1.1.1
    - 2606:4700:4700::1111
    - 8.8.8.8
    - 2001:4860:4860::8888
  fallback:
    - 223.5.5.5
    - 2400:3200::1
proxies:
${nodeConfigs}
proxy-groups:
- name: 🚀 节点选择
  type: select
  proxies:
    - ♻️ 自动选择
    - 🔯 故障转移
${proxyConfigs}
- name: ♻️ 自动选择
  type: url-test
  url: https://www.google.com/generate_204
  interval: 150
  tolerance: 50
  proxies:
${proxyConfigs}
- name: 🔯 故障转移
  type: fallback
  health-check:
    enable: true
    interval: 300
    url: https://www.google.com/generate_204
  proxies:
${proxyConfigs}
- name: 漏网之鱼
  type: select
  proxies:
    - DIRECT
    - 🚀 节点选择
rules:
- GEOIP,LAN,DIRECT,no-resolve #局域网IP直连规则
- GEOSITE,cn,DIRECT #国内域名直连规则
- GEOIP,CN,DIRECT,no-resolve #国内IP直连规则
- DOMAIN-SUFFIX,cn,DIRECT #cn域名直连规则
- GEOSITE,gfw,🚀 节点选择 #GFW域名规则
- GEOSITE,google,🚀 节点选择 #GOOGLE域名规则
- GEOIP,GOOGLE,🚀 节点选择,no-resolve #GOOGLE IP规则
- GEOSITE,netflix,🚀 节点选择 #奈飞域名规则
- GEOIP,NETFLIX,🚀 节点选择,no-resolve #奈飞IP规则
- GEOSITE,telegram,🚀 节点选择 #TG域名规则
- GEOIP,TELEGRAM,🚀 节点选择,no-resolve #TG IP规则
- GEOSITE,openai,🚀 节点选择 #GPT规则
- GEOSITE,category-ads-all,REJECT #简单广告过滤规则
- MATCH,漏网之鱼
`;
}