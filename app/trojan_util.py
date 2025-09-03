import logging

from cloudflare.types.dns.record_list_params import Name
from sqlalchemy import create_engine
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker
from config import cfg
from model import V2ServerTrojan
from cloudflare import Cloudflare
from datetime import datetime
from dateutil.relativedelta import relativedelta


class DataAccessUtil:
    def __init__(self):
        engine = create_engine(cfg.mysql_url, echo=True)
        self.Session = sessionmaker(bind=engine)
        self.zone_id = cfg.zone_id
        self.client = Cloudflare(api_token=cfg.api_token)

    def get_servers(self):
        session = self.Session()
        try:
            servers = session.query(V2ServerTrojan).all()
            users_json = [server.to_json() for server in servers]
            session.commit()
            return users_json
        except Exception as e:
            logging.error('*** Exception in get_users: %s' % e)
            session.rollback()
            raise
        finally:
            session.close()

    def _update_db_dns(self, server, new_host_name, content):
        proxied = True
        if server['network'] == 'tcp':
            proxied = False
        # 2. 更新数据库记录（更新host,ws节点记得改network_settings）
        session = self.Session()
        try:
            stmt = (
                update(V2ServerTrojan)
                .where(V2ServerTrojan.id == server['id'])
                .values(host=new_host_name)
            )
            if server['network'] == 'ws':
                network_settings = '{"path":"\/ws-chat-001?ed=2048","headers":{"Host":"%s"}}' % new_host_name
                stmt = stmt.values(network_settings=network_settings)
            # 执行更新
            session.execute(stmt)
            session.commit()
            # 3. 用老记录创建新的dns记录(修改备注的更新时间为当前时间、生成新的host)
            self.client.dns.records.create(
                zone_id=self.zone_id,
                name=new_host_name,
                content=content,
                proxied=proxied,
                type='A',
            )

        except Exception as e:
            logging.error('更新服务器[%s]发生异常： %s' % (server['host'], e))
            session.rollback()
            raise
        finally:
            session.close()

    def _del_cf_dns(self, same_proxied_hosts):
        """
        删除same_proxied_hosts中超过一个月的记录
        :param same_proxied_hosts: 同一个节点的域名列表
        :return:
        """
        if len(same_proxied_hosts) < 2:
            logging.error('旧域名记录数小于2, 跳过删除')
            return
        before_month = datetime.now() - relativedelta(days=20)
        for n in same_proxied_hosts[1:]:
            sub_domain_array = n.name.split('.')[0].split('-')
            if len(sub_domain_array) != 3:
                logging.error('旧域名[%s]不是新的规则域名记录，手动确认删除，跳过' % n.name)
                continue
            old_date_str = sub_domain_array[1]
            old_date = datetime.strptime(old_date_str, "%Y%m%d%H%M%S")
            if old_date > before_month:
                logging.error('旧域名[%s]时间未超过20天，跳过' % n.name)
                continue
            self.client.dns.records.delete(
                zone_id=self.zone_id,
                dns_record_id=n.id
            )
            logging.info('删除域名[%s]记录' % n.name)

    def update_server_by_name(self, server, new_host_name):
        """
        1、查询server['host']的dns记录, 不存在则返回
        2. 更新数据库记录（更新host,ws节点记得改network_settings）
        3. 复制该记录并创建新的dns记录
        4. 删除old_host中超过一个月的记录
        2.3在同一个事物中
        :param server: 数据库中服务器信息
        :param new_host_name: 新的域名信息
        :return:
        """
        # 1、查询server['host']的前8位dns记录, 不存在则返回 ,获取主机ip
        old_host = self.client.dns.records.list(
            zone_id=self.zone_id,
            type="A",
            name=Name(startswith=server['host'][0:4]),
            order="name"
        )
        if len(old_host.result) == 0:
            logging.error('没有名叫[%s]的dns记录, 跳过更新' % server['host'])
            return
        content = old_host.result[0].content

        # 2. 更新数据库记录（更新host,ws节点记得改network_settings）
        # 3. 创建新的dns记录
        self._update_db_dns(server, new_host_name, content)
        logging.info('新增域名[%s]记录' % new_host_name)

        # 4. 删除old_host中超过一个月的记录
        same_proxied_hosts = [n for n in old_host.result if n.name[0:6] == new_host_name[0:6]]
        self._del_cf_dns(same_proxied_hosts)

