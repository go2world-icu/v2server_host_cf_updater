import logging

from trojan_util import DataAccessUtil
from config import cfg
from datetime import datetime
import binascii
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key_cfy'


def is_blank(s):
    return s is None or s == ''

def not_blank(s):
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


def generate_dns_content(server, main_domain: str, _new_host_prefix: str = None):
    """
    生成dns名称
    :param main_domain: 主域名
    :param server: 服务器信息
    :param _new_host_prefix: 传入前缀，不传取数据库里当前的域名前缀
    :return: prefix + current_date_str + crc16(prefix+current_date_str) + main_domain
    """
    current_date = datetime.now()
    current_date_str = current_date.strftime('%Y%m%d%H%M%S')
    if is_blank(_new_host_prefix):
        _new_host_prefix = server['host'][0:4]
    if 'tcp' == server['network']:
        _new_host_prefix = _new_host_prefix + 'f1'
    elif 'ws' == server['network']:
        _new_host_prefix = _new_host_prefix + 'f2'
    else:
        _new_host_prefix = _new_host_prefix + 'f3'
    new_host = _new_host_prefix + '-' + current_date_str
    new_host = new_host + '-' + calc_crc32(new_host) + '.' + main_domain
    return new_host

def update_dns_records_by_name(update_host, _new_host_prefix: str = None):
    """
    更新指定域名
    :param update_host: 待更新域名名称
    :return:
    """
    if not_blank(_new_host_prefix) and len(_new_host_prefix) != 4:
        return 'new_host_prefix must be 4'
    data = DataAccessUtil()
    servers = data.get_servers()
    server = exits_in_servers(servers, update_host)
    if server is None:
        logging.error('待更新主机dns[%s] 不存在' % update_host)
        return

    new_host_name = generate_dns_content(server, cfg.main_domain,_new_host_prefix)
    data.update_server_by_name(server, new_host_name)
    return new_host_name


def update_dns_records_all():
    """
    更新所有dns记录
    :return:
    """
    data = DataAccessUtil()
    servers = data.get_servers()
    for server in servers:
        new_host_name = generate_dns_content(server, cfg.main_domain)
        data.update_server_by_name(server, new_host_name)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_hashed_password = cfg.users.get(username)
        if user_hashed_password and check_password_hash(user_hashed_password, password):
            session['logged_in'] = True
            return redirect(url_for('servers'))
        else:
            error = '用户名或密码错误'
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('servers'))

@app.route("/servers", methods=['GET'])
def servers():
    if session.get('logged_in'):
        data = DataAccessUtil()
        servers = data.get_servers()
        servers.sort(key=lambda item: item["sort"])
        return render_template(
            "servers.html",
            servers=servers
        )
    else:
        return redirect(url_for('login'))


@app.route('/update_row', methods=['POST'])
def update_row():
    host = request.form.get('host')
    prefix = request.form.get('prefix')
    new_host_name = update_dns_records_by_name(host,prefix)
    flash( f" update dns {host} to {new_host_name} success!")
    return redirect(url_for('servers'))


if __name__ == "__main__":
    # app.debug = True
    app.run(host="0.0.0.0",port=5000)
