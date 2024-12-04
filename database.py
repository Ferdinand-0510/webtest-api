import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def create_connection():
    """
    創建與 Azure SQL Database 的連接
    """
    try:
        # 從環境變數獲取連接字串
        connection_string = os.getenv('DATABASE_URL', (
            "Driver={ODBC Driver 17 for SQL Server};"
            "Server=tcp:carlweb-server.database.windows.net,1433;"
            "Database=CarlWeb;"
            "Uid=carl;"
            "Pwd=Golden3857.;"  # 請替換為您的實際密碼
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        ))
        
        # 建立連接
        conn = pyodbc.connect(connection_string)
        return conn
    except pyodbc.Error as e:
        print(f"資料庫連接錯誤: {str(e)}")
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

# 如果直接運行此文件，則執行測試
if __name__ == "__main__":
    test_connection()