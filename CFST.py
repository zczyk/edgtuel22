import asyncio
import csv
import ipaddress
import logging
import math
import os
import random
import re
import socket
import struct
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

import aiohttp
import async_timeout
from ewma import EWMA

VERSION = "0.0.1"  # 替换为实际版本
VERSION_NEW = ""

# -------------------- 配置参数 --------------------
ROUTINES = 200
TCP_PORT = 443
PING_TIMES = 4
TEST_COUNT = 10
DOWNLOAD_TIME = 10
URL = "https://cf.xiu2.xyz/url"
HTTPING = False
HTTPING_STATUS_CODE = 0
HTTPING_CF_COLO = ""
MAX_DELAY = 9999
MIN_DELAY = 0
MAX_LOSS_RATE = 1.0
MIN_SPEED = 0.0
PRINT_NUM = 10
IP_FILE = "ip.txt"
IP_TEXT = ""
OUTPUT = "result.csv"
DISABLE = False
TEST_ALL = False

INPUT_MAX_DELAY = MAX_DELAY
INPUT_MIN_DELAY = MIN_DELAY
INPUT_MAX_LOSS_RATE = MAX_LOSS_RATE
TIMEOUT = DOWNLOAD_TIME
HTTPING_CF_COLOMAP = None

# -------------------- 常量 --------------------
BUFFER_SIZE = 1024
TCP_CONNECT_TIMEOUT = 1
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36"

# -------------------- 日志配置 --------------------
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# -------------------- 辅助函数 --------------------
def is_ipv4(ip_str: str) -> bool:
    return "." in ip_str


def rand_ip_end_with(num: int) -> int:
    if num == 0:
        return 0
    return random.randint(0, num - 1)


def format_speed(speed: float) -> str:
    if speed >= 1024 * 1024:
        return f"{speed / 1024 / 1024:.2f} MB/s"
    elif speed >= 1024:
        return f"{speed / 1024:.2f} KB/s"
    else:
        return f"{speed:.2f} B/s"


def check_update():
    global VERSION_NEW
    try:
        with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async def fetch():
                async with session.get("https://api.xiu2.xyz/ver/cloudflarespeedtest.txt") as resp:
                    if resp.status == 200:
                        return await resp.text()
                    else:
                        logging.warning(f"Failed to check for updates: {resp.status}")
                        return None
            body = asyncio.run(fetch())
            if body and body.strip() != VERSION:
                VERSION_NEW = body.strip()
    except Exception as e:
        logging.warning(f"Failed to check for updates: {e}")


# -------------------- 数据结构 --------------------
class PingData:
    def __init__(self, ip: ipaddress.IPAddress):
        self.ip = ip
        self.sended = 0
        self.received = 0
        self.delay = 0.0  # 毫秒


class CloudflareIPData:
    def __init__(self, ping_data: PingData):
        self.ping_data = ping_data
        self.loss_rate = 0.0
        self.download_speed = 0.0

    def get_loss_rate(self) -> float:
        if self.loss_rate == 0:
            ping_lost = self.ping_data.sended - self.ping_data.received
            self.loss_rate = ping_lost / self.ping_data.sended if self.ping_data.sended else 0.0
        return self.loss_rate

    def to_string_list(self) -> List[str]:
        return [
            str(self.ping_data.ip),
            str(self.ping_data.sended),
            str(self.ping_data.received),
            f"{self.get_loss_rate():.2f}",
            f"{self.ping_data.delay:.2f}",
            f"{self.download_speed / 1024 / 1024:.2f}",
        ]


# -------------------- IP地址处理 --------------------
class IPRanges:
    def __init__(self):
        self.ips: List[ipaddress.IPAddress] = []
        self.mask = ""
        self.first_ip: ipaddress.IPAddress = None
        self.ip_network: ipaddress.IPNetwork = None

    def fix_ip(self, ip_str: str) -> str:
        if "/" not in ip_str:
            if is_ipv4(ip_str):
                self.mask = "/32"
            else:
                self.mask = "/128"
            ip_str += self.mask
        else:
            self.mask = ip_str[ip_str.index("/") :]
        return ip_str

    def parse_cidr(self, ip_str: str):
        try:
            self.ip_network = ipaddress.ip_network(self.fix_ip(ip_str), strict=False)
            self.first_ip = self.ip_network[0]
        except ValueError as e:
            logging.error(f"ParseCIDR error: {e}")
            sys.exit(1)

    def append_ipv4(self, ip_int: int):
        self.append_ip(ipaddress.IPv4Address(ip_int))

    def append_ip(self, ip: ipaddress.IPAddress):
        self.ips.append(ip)

    def choose_ipv4(self):
        if self.mask == "/32":
            self.append_ip(self.first_ip)
        else:
            min_ip = int(self.first_ip) & int(self.ip_network.netmask)
            hosts = int(self.ip_network.hostmask)

            if TEST_ALL:
                for i in range(hosts + 1):
                    self.append_ipv4(min_ip + i)
            else:
                self.append_ipv4(min_ip + rand_ip_end_with(hosts + 1))

    def choose_ipv6(self):
        if self.mask == "/128":
            self.append_ip(self.first_ip)
        else:
            network_address = int(self.first_ip)
            max_hosts = self.ip_network.num_addresses

            if TEST_ALL:
                for i in range(max_hosts):
                    self.append_ip(ipaddress.IPv6Address(network_address + i))
            else:
                random_offset = random.randint(0, max_hosts - 1)
                self.append_ip(ipaddress.IPv6Address(network_address + random_offset))

    def load_ip_ranges(self) -> List[ipaddress.IPAddress]:
        if IP_TEXT:
            ips = IP_TEXT.split(",")
            for ip_str in ips:
                ip_str = ip_str.strip()
                if not ip_str:
                    continue
                self.parse_cidr(ip_str)
                if is_ipv4(ip_str):
                    self.choose_ipv4()
                else:
                    self.choose_ipv6()
        else:
            try:
                with open(IP_FILE, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        self.parse_cidr(line)
                        if is_ipv4(line):
                            self.choose_ipv4()
                        else:
                            self.choose_ipv6()
            except FileNotFoundError:
                logging.error(f"IP file not found: {IP_FILE}")
                sys.exit(1)

        return self.ips


def load_ip_ranges() -> List[ipaddress.IPAddress]:
    ranges = IPRanges()
    return ranges.load_ip_ranges()


# -------------------- TCP Ping --------------------
async def tcp_ping(ip: ipaddress.IPAddress) -> Tuple[bool, float]:
    start_time = time.time()
    try:
        if is_ipv4(str(ip)):
            full_address = f"{ip}:{TCP_PORT}"
        else:
            full_address = f"[{ip}]:{TCP_PORT}"
        
        with socket.socket(socket.AF_INET if is_ipv4(str(ip)) else socket.AF_INET6, socket.SOCK_STREAM) as sock:
            sock.settimeout(TCP_CONNECT_TIMEOUT)
            await asyncio.get_running_loop().sock_connect(sock, (str(ip), TCP_PORT))  # Use sock_connect for async
        duration = time.time() - start_time
        return True, duration * 1000  # 返回毫秒
    except Exception:
        return False, 0.0


# -------------------- HTTP Ping --------------------
async def httping(ip: ipaddress.IPAddress, session: aiohttp.ClientSession) -> Tuple[int, float]:
    try:
        # 首先访问一次获得 HTTP 状态码 及 Cloudflare Colo
        async with async_timeout.timeout(2):
            try:
                if is_ipv4(str(ip)):
                    full_address = f"{ip}:{TCP_PORT}"
                else:
                    full_address = f"[{ip}]:{TCP_PORT}"
                
                conn = socket.create_connection((str(ip), TCP_PORT), timeout=TCP_CONNECT_TIMEOUT)
                conn.close()

                headers = {"User-Agent": DEFAULT_USER_AGENT}
                async with session.head(URL, headers=headers, allow_redirects=False) as resp:
                    if HTTPING_STATUS_CODE == 0 or not 100 <= HTTPING_STATUS_CODE <= 599:
                        if resp.status not in (200, 301, 302):
                            return 0, 0.0
                    elif resp.status != HTTPING_STATUS_CODE:
                        return 0, 0.0

                    colo = None
                    if HTTPING_CF_COLO:
                        cf_ray = resp.headers.get("CF-RAY")
                        x_amz_cf_pop = resp.headers.get("x-amz-cf-pop")
                        server = resp.headers.get("Server")

                        if server == "cloudflare" and cf_ray:
                            colo = re.search(r"[A-Z]{3}", cf_ray)
                            colo = colo.group(0) if colo else None
                        elif x_amz_cf_pop:
                            colo = re.search(r"[A-Z]{3}", x_amz_cf_pop)
                            colo = colo.group(0) if colo else None

                        if colo and HTTPING_CF_COLOMAP and colo not in HTTPING_CF_COLOMAP:
                            return 0, 0.0

            except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
                return 0, 0.0

        success = 0
        total_delay = 0.0
        for _ in range(PING_TIMES):
            try:
                start_time = time.time()
                headers = {"User-Agent": DEFAULT_USER_AGENT, "Connection": "close" if _ == PING_TIMES - 1 else "keep-alive"}
                async with session.head(URL, headers=headers, allow_redirects=False) as resp:
                    await resp.read()  # 确保读取响应以释放连接
                    if resp.status != 200:
                        continue
                    success += 1
                    total_delay += (time.time() - start_time) * 1000
            except (aiohttp.ClientError, asyncio.TimeoutError, OSError):
                continue

        return success, total_delay

    except asyncio.TimeoutError:
        return 0, 0.0


# -------------------- 延迟测试 --------------------
async def check_connection(ip: ipaddress.IPAddress, session: aiohttp.ClientSession) -> Tuple[int, float]:
    if HTTPING:
        return await httping(ip, session)
    else:
        success = 0
        total_delay = 0.0
        for _ in range(PING_TIMES):
            ok, delay = await tcp_ping(ip)
            if ok:
                success += 1
                total_delay += delay
        return success, total_delay


async def tcping_handler(
    ip: ipaddress.IPAddress, queue: asyncio.Queue, results: List[CloudflareIPData], lock: asyncio.Lock
):
    async with aiohttp.ClientSession() as session:
        recv, total_delay = await check_connection(ip, session)
        if recv > 0:
            data = PingData(ip)
            data.sended = PING_TIMES
            data.received = recv
            data.delay = total_delay / recv

            async with lock:
                results.append(CloudflareIPData(data))
        await queue.put(True)  # Signal completion


async def run_ping(ips: List[ipaddress.IPAddress]) -> List[CloudflareIPData]:
    results: List[CloudflareIPData] = []
    queue = asyncio.Queue(maxsize=ROUTINES)
    lock = asyncio.Lock()

    # 初始化队列，填满
    for _ in range(ROUTINES):
        await queue.put(True)

    tasks = []
    for ip in ips:
        await queue.get()  # 等待一个完成信号
        task = asyncio.create_task(tcping_handler(ip, queue, results, lock))
        tasks.append(task)

    await asyncio.gather(*tasks)
    return results


# -------------------- 下载速度测试 --------------------
async def download_handler(ip: ipaddress.IPAddress, session: aiohttp.ClientSession) -> float:
    try:
        if is_ipv4(str(ip)):
            full_address = f"{ip}:{TCP_PORT}"
        else:
            full_address = f"[{ip}]:{TCP_PORT}"
        conn = socket.create_connection((str(ip), TCP_PORT), timeout=TCP_CONNECT_TIMEOUT)
        conn.close()

        headers = {"User-Agent": DEFAULT_USER_AGENT}
        time_start = time.time()
        time_end = time_start + TIMEOUT
        content_read = 0
        time_slice = TIMEOUT / 100
        time_counter = 1
        last_content_read = 0
        next_time = time_start + time_slice * time_counter
        ewma = EWMA()

        async with session.get(URL, headers=headers, allow_redirects=True) as response:
            if response.status != 200:
                return 0.0
            content_length = int(response.headers.get("Content-Length", -1))
            buffer = bytearray(BUFFER_SIZE)
            
            async for chunk in response.content.iter_chunked(BUFFER_SIZE):
                current_time = time.time()
                if current_time > next_time:
                    time_counter += 1
                    next_time = time_start + time_slice * time_counter
                    ewma.add(content_read - last_content_read)
                    last_content_read = content_read
                if current_time > time_end:
                    break
                
                buffer_read = len(chunk)
                content_read += buffer_read
            
            if content_length != -1 and content_length != content_read:
                last_time_slice = time_start + time_slice * (time_counter - 1)
                ewma.add((content_read - last_content_read) / ((current_time - last_time_slice) / time_slice))
        
        return ewma.value / (TIMEOUT / 120)
    
    except Exception as e:
        return 0.0


async def test_download_speed(ip_set: List[CloudflareIPData]) -> List[CloudflareIPData]:
    if DISABLE:
        return ip_set
    if not ip_set:
        logging.info("延迟测速结果 IP 数量为 0，跳过下载测速。")
        return []

    test_num = min(TEST_COUNT, len(ip_set))
    logging.info(f"开始下载测速（下限：{MIN_SPEED:.2f} MB/s, 数量：{TEST_COUNT}, 队列：{test_num}）")
    
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(download_handler(item.ping_data.ip, session)) for item in ip_set[:test_num]]
        speeds = await asyncio.gather(*tasks)

    speed_set = []
    for i, speed in enumerate(speeds):
        ip_set[i].download_speed = speed
        if speed >= MIN_SPEED * 1024 * 1024:
            speed_set.append(ip_set[i])
            if len(speed_set) == TEST_COUNT:
                break

    if not speed_set:
        speed_set = ip_set

    speed_set.sort(key=lambda x: x.download_speed, reverse=True)
    return speed_set


# -------------------- 结果处理 --------------------
def export_csv(data: List[CloudflareIPData]):
    if not OUTPUT or not data:
        return

    try:
        with open(OUTPUT, "w", newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(["IP 地址", "已发送", "已接收", "丢包率", "平均延迟", "下载速度 (MB/s)"])
            writer.writerows([d.to_string_list() for d in data])
        logging.info(f"完整测速结果已写入 {OUTPUT} 文件。")
    except Exception as e:
        logging.error(f"创建文件[{OUTPUT}]失败：{e}")


def print_results(data: List[CloudflareIPData]):
    if PRINT_NUM == 0:
        return

    if not data:
        logging.info("完整测速结果 IP 数量为 0，跳过输出结果。")
        return

    headFormat = "%-16s%-5s%-5s%-5s%-6s%-11s"
    dataFormat = "%-18s%-8s%-8s%-8s%-10s%-15s"
    for i in range(min(PRINT_NUM, len(data))):
        if len(str(data[i].ping_data.ip)) > 15:
            headFormat = "%-40s%-5s%-5s%-5s%-6s%-11s"
            dataFormat = "%-42s%-8s%-8s%-8s%-10s%-15s"
            break

    print(headFormat % ("IP 地址", "已发送", "已接收", "丢包率", "平均延迟", "下载速度 (MB/s)"))
    for i in range(min(PRINT_NUM, len(data))):
        print(dataFormat % tuple(data[i].to_string_list()))

    if OUTPUT:
        print(f"\n完整测速结果已写入 {OUTPUT} 文件，可使用记事本/表格软件查看。\n")


# -------------------- 过滤和排序 --------------------
def filter_delay(data: List[CloudflareIPData]) -> List[CloudflareIPData]:
    if INPUT_MAX_DELAY == MAX_DELAY and INPUT_MIN_DELAY == MIN_DELAY:
        return data
    return [
        v
        for v in data
        if INPUT_MIN_DELAY <= v.ping_data.delay <= INPUT_MAX_DELAY
    ]


def filter_loss_rate(data: List[CloudflareIPData]) -> List[CloudflareIPData]:
    if INPUT_MAX_LOSS_RATE >= MAX_LOSS_RATE:
        return data
    return [v for v in data if v.get_loss_rate() <= INPUT_MAX_LOSS_RATE]


# -------------------- 主函数 --------------------
async def main():
    global ROUTINES, TCP_PORT, PING_TIMES, TEST_COUNT, DOWNLOAD_TIME, URL, HTTPING, HTTPING_STATUS_CODE, HTTPING_CF_COLO
    global MAX_DELAY, MIN_DELAY, MAX_LOSS_RATE, MIN_SPEED, PRINT_NUM, IP_FILE, IP_TEXT, OUTPUT, DISABLE, TEST_ALL
    global INPUT_MAX_DELAY, INPUT_MIN_DELAY, INPUT_MAX_LOSS_RATE, TIMEOUT, HTTPING_CF_COLOMAP

    import argparse

    parser = argparse.ArgumentParser(
        description=f"CloudflareSpeedTest {VERSION}\n测试 Cloudflare CDN 所有 IP 的延迟和速度，获取最快 IP (IPv4+IPv6)！\nhttps://github.com/XIU2/CloudflareSpeedTest",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-n",
        type=int,
        default=200,
        help="延迟测速线程；越多延迟测速越快，性能弱的设备 (如路由器) 请勿太高；(默认 200 最多 1000)",
    )
    parser.add_argument(
        "-t", type=int, default=4, help="延迟测速次数；单个 IP 延迟测速的次数；(默认 4 次)"
    )
    parser.add_argument(
        "-dn",
        type=int,
        default=10,
        help="下载测速数量；延迟测速并排序后，从最低延迟起下载测速的数量；(默认 10 个)",
    )
    parser.add_argument(
        "-dt",
        type=int,
        default=10,
        help="下载测速时间；单个 IP 下载测速最长时间，不能太短；(默认 10 秒)",
    )
    parser.add_argument(
        "-tp",
        type=int,
        default=443,
        help="指定测速端口；延迟测速/下载测速时使用的端口；(默认 443 端口)",
    )
    parser.add_argument(
        "-url",
        type=str,
        default="https://cf.xiu2.xyz/url",
        help="指定测速地址；延迟测速(HTTPing)/下载测速时使用的地址，默认地址不保证可用性，建议自建；",
    )
    parser.add_argument(
        "-httping",
        action="store_true",
        help="切换测速模式；延迟测速模式改为 HTTP 协议，所用测试地址为 [-url] 参数；(默认 TCPing)",
    )
    parser.add_argument(
        "-httping-code",
        type=int,
        default=0,
        help="有效状态代码；HTTPing 延迟测速时网页返回的有效 HTTP 状态码，仅限一个；(默认 200 301 302)",
    )
    parser.add_argument(
        "-cfcolo",
        type=str,
        default="",
        help="匹配指定地区；地区名为当地机场三字码，英文逗号分隔，仅 HTTPing 模式可用；(默认 所有地区)",
    )
    parser.add_argument(
        "-tl",
        type=int,
        default=9999,
        help="平均延迟上限；只输出低于指定平均延迟的 IP，各上下限条件可搭配使用；(默认 9999 ms)",
    )
    parser.add_argument(
        "-tll",
        type=int,
        default=0,
        help="平均延迟下限；只输出高于指定平均延迟的 IP；(默认 0 ms)",
    )
    parser.add_argument(
        "-tlr",
        type=float,
        default=1.0,
        help="丢包几率上限；只输出低于/等于指定丢包率的 IP，范围 0.00~1.00，0 过滤掉任何丢包的 IP；(默认 1.00)",
    )
    parser.add_argument(
        "-sl",
        type=float,
        default=0.0,
        help="下载速度下限；只输出高于指定下载速度的 IP，凑够指定数量 [-dn] 才会停止测速；(默认 0.00 MB/s)",
    )
    parser.add_argument(
        "-p",
        type=int,
        default=10,
        help="显示结果数量；测速后直接显示指定数量的结果，为 0 时不显示结果直接退出；(默认 10 个)",
    )
    parser.add_argument(
        "-f",
        type=str,
        default="ip.txt",
        help="IP段数据文件；如路径含有空格请加上引号；支持其他 CDN IP段；(默认 ip.txt)",
    )
    parser.add_argument(
        "-ip",
        type=str,
        default="",
        help="指定IP段数据；直接通过参数指定要测速的 IP 段数据，英文逗号分隔；(默认 空)",
    )
    parser.add_argument(
        "-o",
        type=str,
        default="result.csv",
        help='写入结果文件；如路径含有空格请加上引号；值为空时不写入文件 [-o ""]；(默认 result.csv)',
    )
    parser.add_argument(
        "-dd",
        action="store_true",
        help="禁用下载测速；禁用后测速结果会按延迟排序 (默认按下载速度排序)；(默认 启用)",
    )
    parser.add_argument(
        "-allip",
        action="store_true",
        help="测速全部的IP；对 IP 段中的每个 IP (仅支持 IPv4) 进行测速；(默认 每个 /24 段随机测速一个 IP)",
    )
    parser.add_argument("-v", action="store_true", help="打印程序版本 + 检查版本更新")
    args = parser.parse_args()

    ROUTINES = args.n
    TCP_PORT = args.tp
    PING_TIMES = args.t
    TEST_COUNT = args.dn
    DOWNLOAD_TIME = args.dt
    URL = args.url
    HTTPING = args.httping
    HTTPING_STATUS_CODE = args.httping_code
    HTTPING_CF_COLO = args.cfcolo
    MAX_DELAY = args.tl
    MIN_DELAY = args.tll
    MAX_LOSS_RATE = args.tlr
    MIN_SPEED = args.sl
    PRINT_NUM = args.p
    IP_FILE = args.f
    IP_TEXT = args.ip
    OUTPUT = args.o
    DISABLE = args.dd
    TEST_ALL = args.allip

    INPUT_MAX_DELAY = MAX_DELAY
    INPUT_MIN_DELAY = MIN_DELAY
    INPUT_MAX_LOSS_RATE = MAX_LOSS_RATE
    TIMEOUT = DOWNLOAD_TIME
    HTTPING_CF_COLOMAP = (
        set(HTTPING_CF_COLO.upper().split(",")) if HTTPING_CF_COLO else None
    )
    
    if MIN_SPEED > 0 and MAX_DELAY == 9999:
        print("[小提示] 在使用 [-sl] 参数时，建议搭配 [-tl] 参数，以避免因凑不够 [-dn] 数量而一直测速...")
    
    random.seed()

    print(f"# XIU2/CloudflareSpeedTest {VERSION} \n")

    if args.v:
        print(VERSION)
        print("检查版本更新中...")
        check_update()
        if VERSION_NEW:
            print(
                f"*** 发现新版本 [{VERSION_NEW}]！请前往 [https://github.com/XIU2/CloudflareSpeedTest] 更新！ ***"
            )
        else:
            print(f"当前为最新版本 [{VERSION}]！")
        return

    ips = load_ip_ranges()
    
    # 延迟测速
    if HTTPING:
        print(f"开始延迟测速（模式：HTTP, 端口：{TCP_PORT}, 范围：{MIN_DELAY} ~ {MAX_DELAY} ms, 丢包：{MAX_LOSS_RATE:.2f})")
    else:
        print(f"开始延迟测速（模式：TCP, 端口：{TCP_PORT}, 范围：{MIN_DELAY} ~ {MAX_DELAY} ms, 丢包：{MAX_LOSS_RATE:.2f})")
    
    ping_data = await run_ping(ips)

    # 过滤延迟/丢包
    ping_data = filter_delay(ping_data)
    ping_data = filter_loss_rate(ping_data)
    ping_data.sort(key=lambda x: (x.get_loss_rate(), x.ping_data.delay))

    # 下载测速
    speed_data = await test_download_speed(ping_data)

    export_csv(speed_data)
    print_results(speed_data)
    
    if VERSION_NEW:
        print(
            f"\n*** 发现新版本 [{VERSION_NEW}]！请前往 [https://github.com/XIU2/CloudflareSpeedTest] 更新！ ***\n"
        )

if __name__ == "__main__":
    asyncio.run(main())
    if sys.platform == "win32" and PRINT_NUM != 0:
        input("按下 回车键 或 Ctrl+C 退出。")