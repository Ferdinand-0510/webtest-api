import os
import pymssql
from dotenv import load_dotenv

load_dotenv()


def create_connection():
    """
    創建與 Azure SQL Database 的連接
    """
    try:
        server = "carlweb-server.database.windows.net"
        database = "CarlWeb"
        username = "carl"
        password = os.getenv('DB_PASSWORD')

        conn = pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database,
            port='1433',
            as_dict=True,
            charset='utf8',
            timeout=30,  # 增加超時時間
            login_timeout=30  # 增加登入超時時間
        )
        print(f"成功連接到資料庫: {database}")
        return conn
    except Exception as e:
        print(f"資料庫連接錯誤: {str(e)}")
        print(f"連接詳情: server={server}, user={username}, database={database}")
        raise