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
from typing import List, Tuple, Union

import aiohttp
import async_timeout
from tqdm import tqdm

# Constants and Defaults
BUFFER_SIZE = 1024
DEFAULT_URL = "https://cf.xiu2.xyz/url"
DEFAULT_TIMEOUT = 10  # seconds
DEFAULT_DISABLE_DOWNLOAD = False
DEFAULT_TEST_NUM = 10
DEFAULT_MIN_SPEED = 0.0  # MB/s
DEFAULT_ROUTINES = 200
DEFAULT_PORT = 443
DEFAULT_PING_TIMES = 4
DEFAULT_OUTPUT = "result.csv"
MAX_DELAY = 9999  # ms
MIN_DELAY = 0  # ms
MAX_LOSS_RATE = 1.0

# Global Variables (with defaults)
URL = DEFAULT_URL
TIMEOUT = DEFAULT_TIMEOUT
DISABLE = DEFAULT_DISABLE_DOWNLOAD
TEST_COUNT = DEFAULT_TEST_NUM
MIN_SPEED = DEFAULT_MIN_SPEED
ROUTINES = DEFAULT_ROUTINES
TCP_PORT = DEFAULT_PORT
PING_TIMES = DEFAULT_PING_TIMES
OUTPUT = DEFAULT_OUTPUT
PRINT_NUM = 10
INPUT_MAX_DELAY = MAX_DELAY
INPUT_MIN_DELAY = MIN_DELAY
INPUT_MAX_LOSS_RATE = MAX_LOSS_RATE
TEST_ALL = False
IP_FILE = "ip.txt"
IP_TEXT = ""
HTTPING = False
HTTPING_STATUS_CODE = 0
HTTPING_CF_COLO = ""
HTTPING_CF_COLOMAP = None
VERSION = "0.0.1"  # Replace with actual version
VERSION_NEW = ""

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Utility Functions ---


def is_ipv4(ip_str: str) -> bool:
    """Checks if a string is a valid IPv4 address."""
    try:
        socket.inet_pton(socket.AF_INET, ip_str)
        return True
    except socket.error:
        return False


def is_ipv6(ip_str: str) -> bool:
    """Checks if a string is a valid IPv6 address."""
    try:
        socket.inet_pton(socket.AF_INET6, ip_str)
        return True
    except socket.error:
        return False


def check_update():
    """Placeholder for version check."""
    global VERSION_NEW
    try:
        with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async def fetch_version():
                async with session.get("https://api.xiu2.xyz/ver/cloudflarespeedtest.txt") as resp:
                    if resp.status == 200:
                        return await resp.text()
                    return None
            new_version = asyncio.run(fetch_version())
            if new_version and new_version.strip() != VERSION:
                VERSION_NEW = new_version.strip()
    except Exception:
        pass


def no_print_result() -> bool:
    """Checks if the result printing is disabled."""
    return PRINT_NUM == 0


def no_output() -> bool:
    """Checks if the output to file is disabled."""
    return not OUTPUT or OUTPUT.strip() == ""


async def get_dial_context(ip: str, port: int) -> asyncio.Protocol:
    """Creates a connection to the target with a specific source IP."""

    class CustomProtocol(asyncio.Protocol):
        def __init__(self, on_con_lost):
            self._on_con_lost = on_con_lost
        def connection_made(self, transport):
            self.transport = transport
        def connection_lost(self, exc):
            self._on_con_lost.set_result(True)

    def protocol_factory():
        return CustomProtocol(asyncio.Future())

    loop = asyncio.get_event_loop()
    on_con_lost = loop.create_future()
    try:
        transport, protocol = await loop.create_connection(protocol_factory, host=ip, port=port)
        return protocol
    except Exception as e:
        logging.error(f"Connection error to {ip}:{port}: {e}")
        return None


# --- IP Address Handling ---
def init_rand_seed():
    """Initializes the random seed."""
    random.seed(time.time())


def rand_ip_end_with(num: int) -> int:
    """Generates a random number for the last octet of an IP."""
    if num == 0:
        return 0
    return random.randint(0, num - 1)


class IPRanges:
    """Manages IP address ranges and generation."""

    def __init__(self):
        self.ips: List[ipaddress.IPv4Address,ipaddress.IPv6Address] = []
        self.mask: str = ""
        self.first_ip: Union[ipaddress.IPv4Address,ipaddress.IPv6Address] = None  # type: ignore
        self.ip_network: Union[ipaddress.IPv4Network,ipaddress.IPv6Network] = None  # type: ignore

    def fix_ip(self, ip_str: str) -> str:
        """Adds a subnet mask to a single IP address if it's missing."""
        if "/" not in ip_str:
            if is_ipv4(ip_str):
                self.mask = "/32"
            elif is_ipv6(ip_str):
                self.mask = "/128"
            else:
                raise ValueError(f"Invalid IP address: {ip_str}")
            ip_str += self.mask
        else:
            self.mask = ip_str[ip_str.index("/") :]
        return ip_str

    def parse_cidr(self, ip_str: str):
        """Parses a CIDR notation IP address string."""
        try:
            ip_str = self.fix_ip(ip_str)
            self.ip_network = ipaddress.ip_network(ip_str, strict=False)
            self.first_ip = self.ip_network.network_address
        except ValueError as e:
            logging.error(f"ParseCIDR error: {e}")
            raise

    def append_ip(self, ip: Union[ipaddress.IPv4Address,ipaddress.IPv6Address]):
        """Appends an IP address to the list."""
        self.ips.append(ip)

    def choose_ipv4(self):
        """Chooses IPv4 addresses based on the settings."""
        if self.mask == "/32":
            self.append_ip(self.first_ip)
        else:
            min_ip = int(self.first_ip) & int(ipaddress.IPv4Address("255.255.255.0"))
            hosts = 256 - int(ipaddress.IPv4Address("255.255.255.255")) + int(ipaddress.IPv4Address(self.ip_network.netmask))
            if TEST_ALL:
                for i in range(int(hosts)):
                    self.append_ip(ipaddress.IPv4Address(min_ip + i))
            else:
                self.append_ip(ipaddress.IPv4Address(min_ip + rand_ip_end_with(int(hosts))))

    def choose_ipv6(self):
        """Chooses IPv6 addresses based on the settings."""
        if self.mask == "/128":
            self.append_ip(self.first_ip)
        else:
            for ip_int in range(int(self.first_ip), int(self.first_ip) + 256): # type: ignore
                self.append_ip(ipaddress.IPv6Address(ip_int))

def load_ip_ranges() -> List[ipaddress.IPv4Address,ipaddress.IPv6Address]:
    """Loads IP ranges from file or command line."""
    ranges = IPRanges()
    if IP_TEXT:
        ips = [ip.strip() for ip in IP_TEXT.split(",") if ip.strip()]
        for ip_str in ips:
            try:
                ranges.parse_cidr(ip_str)
                if is_ipv4(ip_str):
                    ranges.choose_ipv4()
                elif is_ipv6(ip_str):
                    ranges.choose_ipv6()
            except ValueError as e:
                logging.error(f"Error processing IP {ip_str}: {e}")
    else:
        try:
            with open(IP_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            ranges.parse_cidr(line)
                            if is_ipv4(line):
                                ranges.choose_ipv4()
                            elif is_ipv6(line):
                                ranges.choose_ipv6()
                        except ValueError as e:
                            logging.error(f"Error processing line {line}: {e}")
        except FileNotFoundError:
            logging.error(f"IP file not found: {IP_FILE}")
            sys.exit(1)
    return ranges.ips


# --- Data Structures ---
class PingData:
    """Stores ping data for an IP address."""

    def __init__(self, ip: Union[ipaddress.IPv4Address,ipaddress.IPv6Address]):
        self.ip: Union[ipaddress.IPv4Address,ipaddress.IPv6Address] = ip
        self.sended: int = 0
        self.received: int = 0
        self.delay: float = 0.0  # Milliseconds

    def __repr__(self):
        return f"PingData(ip={self.ip}, sended={self.sended}, received={self.received}, delay={self.delay:.2f})"

class CloudflareIPData:
    """Stores Cloudflare IP data with ping and download speed."""

    def __init__(self, ping_data: PingData):
        self.ping_data: PingData = ping_data
        self.loss_rate: float = 0.0
        self.download_speed: float = 0.0  # Bytes per second

    def get_loss_rate(self) -> float:
        """Calculates the packet loss rate."""
        if self.loss_rate == 0:
            ping_lost = self.ping_data.sended - self.ping_data.received
            self.loss_rate = ping_lost / self.ping_data.sended if self.ping_data.sended > 0 else 0.0
        return self.loss_rate

    def to_string_list(self) -> List[str]:
        """Converts the data to a list of strings for CSV output."""
        return [
            str(self.ping_data.ip),
            str(self.ping_data.sended),
            str(self.ping_data.received),
            f"{self.get_loss_rate():.2f}",
            f"{self.ping_data.delay:.2f}",
            f"{self.download_speed / 1024 / 1024:.2f}",  # MB/s
        ]

    def __repr__(self):
        return f"CloudflareIPData(ping_data={self.ping_data}, loss_rate={self.loss_rate:.2f}, download_speed={self.download_speed:.2f})"


# --- Sorting ---
class SortByPing(list):
    """Sorts a list of CloudflareIPData by ping delay and loss rate."""

    def __lt__(self, other):
        if self.get_loss_rate() != other.get_loss_rate():
            return self.get_loss_rate() < other.get_loss_rate()
        return self.ping_data.delay < other.ping_data.delay


class SortByDownloadSpeed(list):
    """Sorts a list of CloudflareIPData by download speed."""

    def __lt__(self, other):
        return self.download_speed > other.download_speed

# --- HTTPing Implementation ---

class HTTPing:
    """Performs HTTP ping to measure latency."""

    OUT_REGEXP = re.compile(r"[A-Z]{3}")

    def __init__(self, ip: Union[ipaddress.IPv4Address,ipaddress.IPv6Address]):
        self.ip: Union[ipaddress.IPv4Address,ipaddress.IPv6Address] = ip
        self.httping_status_code: int = HTTPING_STATUS_CODE
        self.httping_cf_colomap = HTTPING_CF_COLOMAP

    async def httping(self) -> Tuple[int, float]:
        """Performs a single HTTP ping attempt."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2),connector=aiohttp.TCPConnector(ssl=False)) as session:

                # First request to get HTTP status code and Cloudflare Colo
                async def initial_request():
                    try:
                        async with session.head(URL,allow_redirects=False) as resp:
                            # Check HTTP status code
                            if self.httping_status_code == 0 or not 100 <= self.httping_status_code <= 599:
                                valid_status = resp.status in [200, 301, 302]
                            else:
                                valid_status = resp.status == self.httping_status_code

                            if not valid_status:
                                return 0, 0.0

                            # Match Cloudflare Colo if specified
                            if HTTPING_CF_COLO:
                                cf_ray = resp.headers.get("CF-RAY", "") if resp.headers.get("Server") == "cloudflare" else resp.headers.get("x-amz-cf-pop", "")
                                colo = self.get_colo(cf_ray)
                                if not colo:
                                    return 0, 0.0

                            return resp.status, 0.0
                    except Exception as e:
                        logging.error(f"Error in initial request: {e}")
                        return 0, 0.0

                status_code, _ = await initial_request()
                if status_code == 0:
                    return 0, 0.0

                # Loop for latency measurement
                success = 0
                total_delay = 0.0
                for _ in range(PING_TIMES):
                    try:
                        start_time = time.time()
                        async with session.head(URL,allow_redirects=False) as resp:
                            await resp.read()  # Ensure the response is fully read
                            duration = (time.time() - start_time) * 1000  # in milliseconds
                            success += 1
                            total_delay += duration
                    except Exception as e:
                        logging.error(f"Error in latency measurement loop: {e}")
                        continue

                return success, total_delay

        except Exception as e:
            logging.error(f"HTTPing error: {e}")
            return 0, 0.0

    def get_colo(self, b: str) -> str:
        """Extracts and matches the airport code."""
        if not b:
            return ""

        out = self.OUT_REGEXP.search(b)
        if not out:
            return ""

        colo = out.group(0)
        if not self.httping_cf_colomap or colo in self.httping_cf_colomap:
            return colo

        return ""

# --- TCP Ping Implementation ---

async def tcp_ping(ip: Union[ipaddress.IPv4Address,ipaddress.IPv6Address], port: int) -> Tuple[bool, float]:
    """Performs a TCP ping to a given IP and port."""
    start_time = time.time()
    try:
        # loop = asyncio.get_event_loop()
        # await asyncio.wait_for(loop.create_connection(lambda: asyncio.Protocol(), str(ip), port), timeout=1)
        protocol = await get_dial_context(str(ip), port)

        if protocol:
            return True, (time.time() - start_time) * 1000  # in milliseconds
        else:
            return False, 0.0
    except Exception:
        return False, 0.0

# --- Main Ping Logic ---
async def check_connection(ip: Union[ipaddress.IPv4Address,ipaddress.IPv6Address]) -> Tuple[int, float]:
    """Checks the connection to an IP address using either TCP or HTTP ping."""
    if HTTPING:
        httping = HTTPing(ip)
        return await httping.httping()
    else:
        successes = 0
        total_delay = 0.0
        for _ in range(PING_TIMES):
            ok, delay = await tcp_ping(ip, TCP_PORT)
            if ok:
                successes += 1
                total_delay += delay
        return successes, total_delay

async def ping_handler(ip: Union[ipaddress.IPv4Address,ipaddress.IPv6Address], progress_bar: tqdm, results: list):
    """Handles the ping operation for a single IP address."""
    successes, total_delay = await check_connection(ip)
    if successes > 0:
        avg_delay = total_delay / successes
        ping_data = PingData(ip)
        ping_data.sended = PING_TIMES
        ping_data.received = successes
        ping_data.delay = avg_delay
        results.append(CloudflareIPData(ping_data))
    progress_bar.update(1)

async def run_pings(ips: List[ipaddress.IPv4Address,ipaddress.IPv6Address]) -> List[CloudflareIPData]:
    """Runs pings on a list of IP addresses concurrently."""
    results = []
    with tqdm(total=len(ips), desc="Pinging IPs", unit="IP") as progress_bar:
        tasks = [ping_handler(ip, progress_bar, results) for ip in ips]
        await asyncio.gather(*tasks)
    return results

# --- Download Speed Test ---
async def download_handler(ip: Union[ipaddress.IPv4Address,ipaddress.IPv6Address]) -> float:
    """Tests the download speed from a given IP address."""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT),connector=aiohttp.TCPConnector(ssl=False)) as session:
            start_time = time.time()
            total_bytes = 0
            try:
                async with session.get(URL) as response:
                    if response.status != 200:
                        logging.warning(f"Download failed for {ip}: HTTP {response.status}")
                        return 0.0

                    async for chunk in response.content.iter_chunked(BUFFER_SIZE):
                        total_bytes += len(chunk)
                        if time.time() - start_time > TIMEOUT:
                            break
            except Exception as e:
                logging.error(f"Download error for {ip}: {e}")
                return 0.0

            duration = time.time() - start_time
            if duration > 0:
                return total_bytes / duration
            else:
                return 0.0
    except Exception as e:
        logging.error(f"Session error for {ip}: {e}")
        return 0.0


async def test_download_speed(ping_data: List[CloudflareIPData]) -> List[CloudflareIPData]:
    """Tests download speed for a list of IP addresses."""
    if DISABLE:
        return ping_data

    if not ping_data:
        logging.info("No IPs to test download speed.")
        return []

    test_num = min(TEST_COUNT, len(ping_data))
    if test_num < TEST_COUNT:
        global TEST_COUNT
        TEST_COUNT = test_num

    logging.info(f"Testing download speed (Min: {MIN_SPEED:.2f} MB/s, Count: {TEST_COUNT}, Queue: {test_num})")

    with tqdm(total=test_num, desc="Testing Download Speed", unit="IP") as progress_bar:
        async def test_ip(ip_data: CloudflareIPData):
            speed = await download_handler(ip_data.ping_data.ip)
            ip_data.download_speed = speed
            progress_bar.update(1)
            return ip_data

        tasks = [test_ip(ip_data) for ip_data in ping_data[:test_num]]
        speed_data = await asyncio.gather(*tasks)

    # Filter by minimum speed
    speed_data = [data for data in speed_data if data.download_speed >= MIN_SPEED * 1024 * 1024]

    if not speed_data:
        logging.warning("No IPs met the minimum speed requirement.")
        speed_data = ping_data

    speed_data.sort(key=lambda x: x.download_speed, reverse=True)
    return speed_data

# --- CSV Output ---
def export_csv(data: List[CloudflareIPData]):
    """Exports the data to a CSV file."""
    if no_output() or not data:
        return

    try:
        with open(OUTPUT, "w", newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(["IP Address", "Sent", "Received", "Loss Rate", "Avg Delay", "Download Speed (MB/s)"])
            for item in data:
                writer.writerow(item.to_string_list())
        logging.info(f"Complete test results written to {OUTPUT}")
    except Exception as e:
        logging.error(f"Error writing to CSV file: {e}")


def print_results(data: List[CloudflareIPData]):
    """Prints the results to the console."""
    if no_print_result():
        return

    if not data:
        logging.info("No results to print.")
        return

    print_num = min(PRINT_NUM, len(data))
    head_format = "%-18s%-8s%-8s%-8s%-10s%-15s"
    data_format = "%-18s%-8s%-8s%-8s%-10s%-15s"

    if any(len(str(item.ping_data.ip)) > 15 for item in data[:print_num]):
        head_format = "%-42s%-8s%-8s%-8s%-10s%-15s"
        data_format = "%-42s%-8s%-8s%-8s%-10s%-15s"

    print(head_format % ("IP Address", "Sent", "Received", "Loss Rate", "Avg Delay", "Download Speed (MB/s)"))
    for item in data[:print_num]:
        print(data_format % tuple(item.to_string_list()))

    if not no_output():
        print(f"\nComplete test results written to {OUTPUT} file, can be viewed using Notepad/Spreadsheet software.")


# --- Argument Parsing (Simplified) ---
def parse_arguments():
    """Parses command-line arguments (simplified)."""
    import argparse

    parser = argparse.ArgumentParser(description="Cloudflare Speed Test")

    # Core Parameters
    parser.add_argument("-n", "--routines", type=int, default=DEFAULT_ROUTINES, help="Number of ping threads")
    parser.add_argument("-t", "--ping-times", type=int, default=DEFAULT_PING_TIMES, help="Number of pings per IP")
    parser.add_argument("-dn", "--test-count", type=int, default=DEFAULT_TEST_NUM, help="Number of IPs to test download speed")
    parser.add_argument("-dt", "--timeout", type=int, default=DEFAULT_TIMEOUT, help="Download timeout in seconds")
    parser.add_argument("-tp", "--tcp-port", type=int, default=DEFAULT_PORT, help="TCP port to test")
    parser.add_argument("-url", "--url", type=str, default=DEFAULT_URL, help="URL to use for download speed test")

    # HTTPing Mode
    parser.add_argument("--httping", action="store_true", help="Enable HTTP ping mode")
    parser.add_argument("--httping-code", type=int, default=0, help="Valid HTTP status code for HTTPing")
    parser.add_argument("--cfcolo", type=str, default="", help="Match specific Cloudflare regions (airport codes)")

    # Filtering Options
    parser.add_argument("-tl", "--max-delay", type=int, default=MAX_DELAY, help="Maximum average delay in ms")
    parser.add_argument("-tll", "--min-delay", type=int, default=MIN_DELAY, help="Minimum average delay in ms")
    parser.add_argument("-tlr", "--max-loss-rate", type=float, default=MAX_LOSS_RATE, help="Maximum packet loss rate (0.00-1.00)")
    parser.add_argument("-sl", "--min-speed", type=float, default=DEFAULT_MIN_SPEED, help="Minimum download speed in MB/s")

    # Output Options
    parser.add_argument("-p", "--print-num", type=int, default=PRINT_NUM, help="Number of results to print")
    parser.add_argument("-f", "--ip-file", type=str, default=IP_FILE, help="File containing IP ranges")
    parser.add_argument("-ip", "--ip-text", type=str, default="", help="IP ranges as comma-separated string")
    parser.add_argument("-o", "--output", type=str, default=DEFAULT_OUTPUT, help="Output CSV file")

    # Other Options
    parser.add_argument("--dd", "--disable-download", action="store_true", help="Disable download speed test")
    parser.add_argument("--allip", action="store_true", help="Test all IPs in a range")
    parser.add_argument("-v", "--version", action="store_true", help="Print version and check for updates")
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit")

    args = parser.parse_args()

    global ROUTINES, PING_TIMES, TEST_COUNT, TIMEOUT, TCP_PORT, URL
    global HTTPING, HTTPING_STATUS_CODE, HTTPING_CF_COLO
    global INPUT_MAX_DELAY, INPUT_MIN_DELAY, INPUT_MAX_LOSS_RATE, MIN_SPEED
    global PRINT_NUM, IP_FILE, IP_TEXT, OUTPUT
    global DISABLE, TEST_ALL
    global HTTPING_CF_COLOMAP

    ROUTINES = args.routines
    PING_TIMES = args.ping_times
    TEST_COUNT = args.test_count
    TIMEOUT = args.timeout
    TCP_PORT = args.tcp_port
    URL = args.url

    HTTPING = args.httping
    HTTPING_STATUS_CODE = args.httping_code
    HTTPING_CF_COLO = args.cfcolo

    INPUT_MAX_DELAY = args.max_delay
    INPUT_MIN_DELAY = args.min_delay
    INPUT_MAX_LOSS_RATE = args.max_loss_rate
    MIN_SPEED = args.min_speed

    PRINT_NUM = args.print_num
    IP_FILE = args.ip_file
    IP_TEXT = args.ip_text
    OUTPUT = args.output

    DISABLE = args.disable_download
    TEST_ALL = args.allip

    if HTTPING_CF_COLO:
        HTTPING_CF_COLOMAP = set(HTTPING_CF_COLO.upper().split(","))
    else:
        HTTPING_CF_COLOMAP = None

    if MIN_SPEED > 0 and INPUT_MAX_DELAY == MAX_DELAY:
        logging.warning("Using --min-speed without --max-delay is not recommended.")

# --- Main ---
async def main():
    """Main function to run the speed test."""
    parse_arguments()
    init_rand_seed()

    print(f"# XIU2/CloudflareSpeedTest {VERSION}\n")

    ips = load_ip_ranges()

    if HTTPING:
        print(f"Starting latency test (Mode: HTTP, Port: {TCP_PORT}, Range: {INPUT_MIN_DELAY} ~ {INPUT_MAX_DELAY} ms, Loss: {INPUT_MAX_LOSS_RATE:.2f})")
    else:
        print(f"Starting latency test (Mode: TCP, Port: {TCP_PORT}, Range: {INPUT_MIN_DELAY} ~ {INPUT_MAX_DELAY} ms, Loss: {INPUT_MAX_LOSS_RATE:.2f})")

    ping_data = await run_pings(ips)

    # Filtering
    ping_data.sort(key=lambda x: x.get_loss_rate())
    ping_data = [v for v in ping_data if v.ping_data.delay <= INPUT_MAX_DELAY]
    ping_data = [v for v in ping_data if v.ping_data.delay >= INPUT_MIN_DELAY]
    ping_data = [v for v in ping_data if v.get_loss_rate() <= INPUT_MAX_LOSS_RATE]

    # Download Speed Test
    speed_data = await test_download_speed(ping_data)

    export_csv(speed_data)
    print_results(speed_data)

    if VERSION_NEW:
        print(f"\n*** New version [{VERSION_NEW}] found! Please update at [https://github.com/XIU2/CloudflareSpeedTest] ***\n")

    # Optional: Add a pause on Windows
    if sys.platform == "win32" and not no_print_result():
        input("Press Enter or Ctrl+C to exit.")

if __name__ == "__main__":
    asyncio.run(main())