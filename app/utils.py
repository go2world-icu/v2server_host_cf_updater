import json
import logging
import binascii
from datetime import datetime
from typing import Optional, TypeGuard


def is_blank(s):
    return s is None or s == ''

def not_blank(s: Optional[str]) -> TypeGuard[str]:
    return s is not None and s != ''

def calc_crc32(text):
    """
      计算字符串的CRC32校验值。
      Args:
        text: 要计算校验值的字符串。
      Returns:
        字符串的CRC32校验值（无符号整数）。
    """
    crc32 = binascii.crc32(text.encode('utf-8'))
    return f'{crc32:08x}'


def exits_in_servers(servers, host):
    for server in servers:
        if server['host'] == host:
            return server
    return None


def parse_network_settings(network_settings: Optional[str]) -> dict:
    """
    解析 network_settings JSON 字符串，返回结构化的字典。

    JSON 格式示例:
        {"path":"/ws-chat-001?ed=2048","headers":{"Host":"us01f2-xxx.the-best-airfield.com"}}

    返回格式:
        {
            "path": "/ws-chat-001?ed=2048",
            "host": "us01f2-xxx.the-best-airfield.com",
            "headers": {"Host": "us01f2-xxx.the-best-airfield.com"}
        }
    解析失败或为空时返回空字典 {}，方便调用方安全地链式调用 .get()。
    """
    if not network_settings:
        return {}
    try:
        data = json.loads(network_settings)
        path = data.get("path")
        headers = data.get("headers", {}) or {}
        host = headers.get("Host")
        return {
            "path": path,
            "host": host,
            "headers": headers,
        }
    except (json.JSONDecodeError, TypeError) as e:
        logging.error("解析 network_settings 失败: %s, 原始值: %s", e, network_settings)
        return {}

def get_server_host(server):
    dns_host_name = server['host']
    if server['network'] == 'ws':
        network_data = parse_network_settings(server['network_settings'])
        host = network_data.get("host")
        if not host:
            logging.error('ws节点[%s]的network_settings中host为空，跳过更新' % server['host'])
            return ""
        dns_host_name = host
    return dns_host_name


def generate_dns_name(server, main_domain: str, _new_host_prefix: Optional[str] = None):
    """
    生成dns名称
    :param main_domain: 主域名
    :param server: 服务器信息
    :param _new_host_prefix: 传入前缀，不传取数据库里当前的域名前缀
    :return: prefix + current_date_str + crc16(prefix+current_date_str) + main_domain
    """
    current_date = datetime.now()
    current_date_str = current_date.strftime('%Y%m%d%H%M%S')
    if not_blank(_new_host_prefix):
        prefix = _new_host_prefix
    else:
        dns_host_name = get_server_host(server)
        prefix = dns_host_name[0:4]
        
    if 'tcp' == server['network']:
        prefix = prefix + 'f1'
    elif 'ws' == server['network']:
        prefix = prefix + 'f2'
    else:
        prefix = prefix + 'f3'
        
    new_host = prefix + '-' + current_date_str
    new_host = new_host + '-' + calc_crc32(new_host) + '.' + main_domain
    return new_host