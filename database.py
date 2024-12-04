import os
import pymssql
from dotenv import load_dotenv
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def create_connection():
    """
    创建与 Azure SQL Database 的连接
    """
    server = "carlweb-server.database.windows.net"
    database = "CarlWeb"
    username = "carl"
    password = os.getenv('DB_PASSWORD')

    try:
        # 打印详细的连接信息（不包含密码）
        logger.info(f"尝试连接到服务器: {server}, 数据库: {database}, 用户: {username}")

        conn = pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database,
            port='1433',
            as_dict=True,
            charset='utf8',
            tds_version='7.4',
            encrypt=True
        )

        logger.info(f"成功连接到数据库: {database}")
        return conn

    except pymssql.Error as e:
        # 更详细的错误日志
        logger.error(f"数据库连接错误: {e}")
        logger.error(f"连接详情: server={server}, user={username}, database={database}")
        
        # 根据错误类型给出具体建议
        if "Login failed" in str(e):
            logger.error("登录失败，请检查用户名和密码是否正确")
        elif "connection failed" in str(e):
            logger.error("无法建立连接，请检查服务器地址和网络设置")
        
        raise