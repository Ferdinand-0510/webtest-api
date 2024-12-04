import os
import pymssql
from dotenv import load_dotenv

load_dotenv()


def create_connection():
    """
    創建與 Azure SQL Database 的連接
    """
    try:
        # Azure SQL Database 連接參數
        server = "carlweb-server.database.windows.net"
        database = "CarlWeb"
        username = "carl"
        password = os.getenv('DB_PASSWORD')  # 從環境變數獲取密碼

        # 使用 pymssql 建立連接
        conn = pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database,
            port='1433',
            as_dict=True,  # 返回字典格式的結果
            charset='utf8'  # 設置字符編碼
        )

        print(f"成功連接到資料庫: {database}")  # 調試用
        return conn

    except Exception as e:
        print(f"資料庫連接錯誤: {str(e)}")
        print(f"連接詳情: server={server}, user={username}, database={database}")  # 調試用
        raise


def test_connection():
    """
    測試資料庫連接是否成功
    """
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        print("資料庫連接成功！")
        conn.close()
        return True
    except Exception as e:
        print(f"連接測試失敗: {str(e)}")
        return False


if __name__ == "__main__":
    test_connection()