from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

from config import cfg

Base = declarative_base()
Base.metadata.schema = cfg.schema


class V2ServerTrojan(Base):
    __tablename__ = 'v2_server_trojan'
    __table_args__ = {'comment': 'trojan伺服器表'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='节点ID')
    group_id = Column(String(255), nullable=False, comment='节点组')
    route_id = Column(String(255), nullable=True)
    parent_id = Column(Integer, nullable=True, comment='父节点')
    tags = Column(String(255), nullable=True, comment='节点标签')
    name = Column(String(255), nullable=False, comment='节点名称')
    rate = Column(String(11), nullable=False, comment='倍率')
    host = Column(String(255), nullable=False, comment='主机名')
    port = Column(String(11), nullable=False, comment='连接端口')
    server_port = Column(Integer, nullable=False, comment='服务端口')
    network = Column(String(11), nullable=True, comment='传输方式')
    network_settings = Column(Text, nullable=True, comment='传输配置')
    allow_insecure = Column(Boolean, default=False, nullable=False, comment='是否允许不安全')
    server_name = Column(String(255), nullable=True)
    show = Column(Boolean, name='show', default=False, nullable=False, comment='是否显示')
    sort = Column(Integer, nullable=True)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)

    def to_json(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "route_id": self.route_id,
            "parent_id": self.parent_id,
            "tags": self.tags,
            "name": self.name,
            "rate": self.rate,
            "host": self.host,
            "port": self.port,
            "server_port": self.server_port,
            "network": self.network,
            "network_settings": self.network_settings,
            "allow_insecure": bool(self.allow_insecure),
            "server_name": self.server_name,
            "show": bool(self.show),
            "sort": self.sort,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }