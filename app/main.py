import logging

from typing import Optional
from trojan_util import DataAccessUtil
from config import cfg


from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from werkzeug.security import check_password_hash
from utils import not_blank, generate_dns_name, exits_in_servers

app = Flask(__name__)
app.secret_key = 'super_secret_key_cfy'




def update_dns_records_by_serverid(server_id, _new_host_prefix: Optional[str] = None, ws_opt_host_name: Optional[str] = None):
    """
    更新指定域名
    :param server_id: 服务器ID
    :return:
    """
    if not_blank(_new_host_prefix) and len(_new_host_prefix) != 4:
        return 'new_host_prefix must be 4'
    data = DataAccessUtil()
    server = data.get_server_by_id(server_id)
    if not server:
        logging.error('服务器ID[%s] 不存在' % server_id)
        return

    new_host_name = generate_dns_name(server, cfg.main_domain, _new_host_prefix)
    data.update_server_by_name(server, new_host_name, ws_opt_host_name)
    return new_host_name


def update_dns_records_all(ws_opt_host_name: Optional[str] = None):
    """
    更新所有dns记录
    :return:
    """
    data = DataAccessUtil()
    servers = data.get_servers()
    for server in servers:
        new_host_name = generate_dns_name(server, cfg.main_domain)
        data.update_server_by_name(server, new_host_name, ws_opt_host_name)


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
    server_id = request.form.get('id')
    prefix = request.form.get('prefix')
    ws_accelerate_url = request.form.get('ws_accelerate_url')
    ws_shared_url = request.form.get('ws_shared_url')
    ws_opt_host_name = ws_accelerate_url if not_blank(ws_accelerate_url) else ws_shared_url
    new_host_name = update_dns_records_by_serverid(server_id, prefix, ws_opt_host_name)
    flash( f" update dns {server_id} to {new_host_name} success!")
    return redirect(url_for('servers'))

@app.route('/update_all', methods=['POST'])
def update_all():
    ws_shared_url = request.form.get('ws_shared_url')
    row_ids = request.form.getlist('row_id')
    row_prefixes = request.form.getlist('row_prefix')
    row_ws_urls = request.form.getlist('row_ws_accelerate_url')

    # 校验：查询数据库，确保所有服务器存在且数据合法
    data_util = DataAccessUtil()
    db_servers = data_util.get_servers()
    db_map = {s['id']: s for s in db_servers}

    errors = []
    for i, sid in enumerate(row_ids):
        sid_int = int(sid)
        if sid_int not in db_map:
            errors.append(f"ID {sid_int} 在数据库中不存在")
            continue
        prefix = row_prefixes[i] if i < len(row_prefixes) else ''
        if not_blank(prefix) and len(prefix) != 4:
            errors.append(f"ID {sid_int} 的前缀 '{prefix}' 长度不为4")

    if errors:
        flash("校验未通过: " + "; ".join(errors))
        return redirect(url_for('servers'))

    # 校验通过，逐个更新
    success_count = 0
    for i, sid in enumerate(row_ids):
        prefix = row_prefixes[i] if i < len(row_prefixes) else ''
        ws_url = row_ws_urls[i] if i < len(row_ws_urls) else ''
        ws_opt = ws_url if not_blank(ws_url) else ws_shared_url
        result = update_dns_records_by_serverid(int(sid), prefix or None, ws_opt)
        if result:
            success_count += 1

    flash(f"更新完成: {success_count}/{len(row_ids)} 条成功")
    return redirect(url_for('servers'))

if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0",port=5000)
