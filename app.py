# app.py
import time
from flask import Flask, jsonify, send_from_directory,session
import secrets
from flask_cors import CORS
from flask import request
import pandas as pd
import datetime
import requests
from requests.exceptions import ConnectionError
import re
import os
from collections import defaultdict
import uuid
import sys
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import bcrypt
from bs4 import BeautifulSoup
import asyncio
from datetime import datetime
from werkzeug.utils import secure_filename
from pathlib import Path  # 添加這行
from database import create_connection  # 添加這行來導入 create_connection
from dotenv import load_dotenv
# 載入環境變數
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', '0877283719e292c601be9bdf87b99a21ca96d301d4be57c7480b92506566d53b')

# 配置 CORS
CORS(app, supports_credentials=True, resources={
    r"/*": {
        "origins": [
            "https://ferdinand-0510.github.io/",  # 您的前端網域
            "https://webtest-api.onrender.com",
            "http://localhost:3000"  # 本地開發用
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# 這個客戶叫做"測試"
This_customer = '測試'

def get_This_Key():
    try:
        with create_connection() as conn_sql_server:
            with conn_sql_server.cursor() as cursor:
                cursor.execute("SELECT Uuid FROM WebLoginKey WHERE Name = ?", (This_customer,))
                row = cursor.fetchone()
                if row:
                    return row[0]
                return None  # 如果沒有找到記錄
    except Exception as e:
        print(f"Error getting key: {str(e)}")  # 正確的錯誤處理
        return None

This_key = get_This_Key()
if This_key is None:
    print("Warning: Could not get This_key")


# 註冊接口
# 註冊接口
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        print("接收到的註冊數據:", data)  # 調試用
        
        # 生成UUID
        user_uuid = uuid.uuid4()
        customer_uuid = This_key
        
        # 密碼加密
        password_hash = bcrypt.hashpw(
            data['password'].encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')

        with create_connection() as conn:
            cursor = conn.cursor()
            
            # 檢查用戶名是否已存在
            cursor.execute(
                "SELECT Id FROM Users WHERE Username = ?", 
                (data['username'],)
            )
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': '用戶名已存在'
                }), 400

            # 檢查郵箱是否已存在
            cursor.execute(
                "SELECT Id FROM Users WHERE Email = ?", 
                (data['email'],)
            )
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': '郵箱已被使用'
                }), 400

            try:
                # 插入新用戶
                sql = """
                    INSERT INTO Users (
                        Uuid, 
                        CustomerUuid,
                        Username, 
                        Email, 
                        PasswordHash,
                        Phone,
                        Status,
                        CreatedAt,
                        UpdatedAt
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
                """
                
                params = (
                    user_uuid,
                    customer_uuid,
                    data['username'],
                    data['email'],
                    password_hash,
                    data.get('phone', ''),
                    1  # 默認狀態為啟用
                )
                
                print("SQL:", sql)  # 調試用
                print("參數:", params)  # 調試用
                
                cursor.execute(sql, params)
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': '註冊成功'
                })
                
            except Exception as e:
                print(f"SQL執行錯誤: {str(e)}")  # 調試用
                conn.rollback()
                raise

    except Exception as e:
        print(f"註冊錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'註冊失敗: {str(e)}'
        }), 500
# 修改登入接口
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        with create_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT Id, Uuid, Username, Email, PasswordHash, Status 
                    FROM Users 
                    WHERE Username = ? AND DeletedAt IS NULL
                """, (username,))
                
                user = cursor.fetchone()

                if user and bcrypt.checkpw(
                    password.encode('utf-8'), 
                    user.PasswordHash.encode('utf-8')
                ):
                    if user.Status != 1:
                        return jsonify({
                            'success': False,
                            'message': '帳號未啟用'
                        }), 401

                    # 更新最後登入時間
                    cursor.execute("""
                        UPDATE Users 
                        SET LastLogin = GETDATE() 
                        WHERE Id = ?
                    """, (user.Id,))
                    conn.commit()

                    # 設置session
                    session['user'] = {
                        'id': user.Id,
                        'uuid': user.Uuid,
                        'username': user.Username,
                        'email': user.Email
                    }

                    return jsonify({
                        'success': True,
                        'user': session['user']
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': '用戶名或密碼錯誤'
                    }), 401

    except Exception as e:
        print(f"登入錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': '登入失敗'
        }), 500

# 檢查 session 狀態接口
@app.route('/api/check-session', methods=['GET'])
def check_session():
    if 'user' in session:
        return jsonify({
            'loggedIn': True,
            'user': session['user']
        })
    return jsonify({'loggedIn': False})

# 登出接口
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

# 密碼驗證函數
def verify_password(password, hashed_password):
    # 這裡需要實現您的密碼驗證邏輯
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


#--------------------------------------------------------取得LoginKey資料--------------------------------------------------------
@app.route('/api/get_loginkey', methods=['GET'])
def get_loginkey():
    try:
        with create_connection() as conn_sql_server:
            with conn_sql_server.cursor() as cursor:
                cursor.execute("SELECT * FROM WebLoginKey")
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                
                # 將查詢結果轉換為字典列表
                result = []
                for row in rows:
                    result.append(dict(zip(columns, row)))
                #print("result:",result)
                return jsonify(result), 200
    except Exception as e:
        return jsonify(error=str(e)), 500
    
@app.route('/api/update_loginkey/<int:id>', methods=['PUT'])
def update_loginkey(id):
    try:
        data = request.json
        with create_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE WebLoginKey 
                    SET Name = ?, Description = ?
                    WHERE Id = ?
                """, (data['Name'], data['Description'], id))
                conn.commit()
        return jsonify({"message": "更新成功"}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500
    
@app.route('/api/delete_loginkey/<int:id>', methods=['DELETE'])
def delete_loginkey(id):
    try:
        with create_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM WebLoginKey
                    WHERE Id = ?
                """, (id,))
                conn.commit()
        return jsonify({"message": "刪除成功"}), 200
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/add_loginkey', methods=['POST'])
def add_loginkey():
    try:
        data = request.json
        #print("data:",data , ",key:" , data['LoginKey'])
        uuid1 = uuid.uuid4()
        #print("uuid:",uuid1 , ",key:" , data['LoginKey'])
        with create_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO WebLoginKey (Uuid, Name, LoginKey, Description)
                    VALUES (?, ?, ?, ?)
                """, (uuid1, data['Name'], data['LoginKey'], data['Description']))
                conn.commit()
        return jsonify({"message": "新增成功"}), 201
    except Exception as e:
        return jsonify(error=str(e)), 500
    
#--------------------------------------------------------取得LoginKey資料--------------------------------------------------------

#--------------------------------------------------------變換首頁圖片--------------------------------------------------------
# 設定上傳資料夾
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 確保上傳資料夾存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

BASE_DIR = Path(__file__).resolve().parent.parent  # webtest 資料夾

# 設定上傳資料夾
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'public', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 確保上傳資料夾存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/api/Change_HomeImg', methods=['POST'])
def Change_HomeImg():
    try:
        # 檢查是否有檔案
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '沒有檔案'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '沒有選擇檔案'}), 400
        
        if file and allowed_file(file.filename):
            try:
                # 儲存為 market.jpg
                filename = 'market.jpg'
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                print("Uploading to:", filepath)  # 調試用
                
                # 如果檔案已存在，先刪除
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                # 儲存新檔案
                file.save(filepath)
                
                # 驗證檔案是否成功保存
                if not os.path.exists(filepath):
                    raise Exception("檔案未能成功保存")
                
                # 更新資料庫
                with create_connection() as conn:
                    cursor = conn.cursor()
                    
                    # 取得表單數據
                    title = request.form.get('Title', 'HomeTitle')
                    title_img = filename
                    title_status = request.form.get('Title_Status', 1)
                    
                    # 更新或插入資料
                    cursor.execute("""
                        IF EXISTS (SELECT 1 FROM HomeData WHERE Title = ?)
                            UPDATE HomeData 
                            SET TitleImg = ?, UpdatedAt = GETDATE()
                            WHERE Title = ?
                        ELSE
                            INSERT INTO HomeData (Uuid, CustomerUuid, Title, TitleImg, Title_Status, CreatedAt, UpdatedAt)
                            VALUES (NEWID(), ?, ?, ?, ?, GETDATE(), GETDATE())
                    """, (title, title_img, title, 'default-uuid', title, title_img, title_status))
                    
                    conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': '圖片上傳成功',
                    'filename': filename
                })
                
            except Exception as e:
                print(f"檔案處理錯誤: {str(e)}")
                return jsonify({'success': False, 'error': f'檔案處理錯誤: {str(e)}'}), 500
        
        return jsonify({'success': False, 'error': '不支援的檔案類型'}), 400
        
    except Exception as e:
        print(f"上傳錯誤: {str(e)}")
        return jsonify({'success': False, 'error': f'上傳錯誤: {str(e)}'}), 500

# 提供靜態檔案訪問
@app.route('/images/<filename>')
def uploaded_file(filename):
    try:
        response = send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        print(f"檔案訪問錯誤: {str(e)}")
        return jsonify({'error': '檔案不存在'}), 404
#--------------------------------------------------------變換首頁圖片--------------------------------------------------------


#--------------------------------------------------------取得首頁標題資料--------------------------------------------------------
@app.route('/api/get_title', methods=['GET'])
def get_title():
    try:
        title = get_title_logic()
        return jsonify(Title=title), 200
    except Exception as e:
        return jsonify(error=str(e)), 500
    
def get_title_logic():
    try:
        with create_connection() as conn_sql_server:
            with conn_sql_server.cursor() as cursor:
                cursor.execute("SELECT Title FROM HomeData WHERE Title_Status = 1 and CustomerUuid = ?", (This_key,))
                row = cursor.fetchone()
                return row[0] if row else ""

    except Exception as e:
        print(f"Error fetching title: {e}")
        return ""
    
with app.app_context():
    Now_Home_Title = get_title_logic()

@app.route('/api/save_HomeData', methods=['POST'])
def save_HomeData():
    try:
        
        data = request.get_json()
        title = data.get("Title")
        customer_uuid = This_key
        title_img = data.get("TitleImg", "")
        title_status = data.get("Title_Status", 1)
        #print("Now_Home_Title:",Now_Home_Title , ",title:",title , ",customer_uuid:",customer_uuid)
        if not title:
            return jsonify(error="Title is required"), 400

        with create_connection() as conn_sql_server:
            with conn_sql_server.cursor() as cursor:
                # Check if title exists
                cursor.execute("SELECT Id FROM HomeData WHERE Title = ? and CustomerUuid = ?", (Now_Home_Title,customer_uuid))
                row = cursor.fetchone() 
                if row:
                    print("row123")     
                    # Update existing entry
                    cursor.execute("""
                        UPDATE HomeData
                        SET Title = ?, UpdatedAt = GETDATE()
                        WHERE Title = ? and CustomerUuid = ?
                    """, (title, Now_Home_Title,customer_uuid))
                else:
                    # Insert new entry
                    cursor.execute("""
                        INSERT INTO HomeData (Uuid, CustomerUuid, Title, TitleImg, Title_Status, CreatedAt, UpdatedAt)
                        VALUES (NEWID(), ?, ?, ?, ?, GETDATE(), GETDATE())
                    """, (customer_uuid, title, title_img, title_status))
                print("row456")     
                conn_sql_server.commit()
        return jsonify(message="Success"), 200

    except Exception as e:
        return jsonify(error=str(e)), 500
#--------------------------------------------------------取得首頁標題資料--------------------------------------------------------


#--------------------------------------------------------取得最新資料--------------------------------------------------------
@app.route('/api/get_HomeNews', methods=['GET'])
def get_HomeNews():
    try:
        news = get_HomeNews_logic()
        return jsonify({"news": news}), 200  # 包裝在 news 鍵中
    except Exception as e:
        print(f"獲取新聞錯誤: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_HomeNews_logic():
    try:
        with create_connection() as conn_sql_server:
            with conn_sql_server.cursor() as cursor:
                cursor.execute("SELECT * FROM News WHERE Customer_Uuid = ? AND Deleted_At IS NULL ORDER BY Created_At DESC", (This_key,))
                columns = [column[0] for column in cursor.description]
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    row_dict = {}
                    for i, column in enumerate(columns):
                        value = row[i]
                        # 處理不同類型的數據
                        if isinstance(value, bytes):
                            row_dict[column] = value.decode('utf-8', errors='ignore')
                        elif isinstance(value, datetime):
                            row_dict[column] = value.isoformat()
                        elif column == 'Publish_Date' and value:
                            # 特別處理 Publish_Date
                            try:
                                if isinstance(value, str) and '\x00' in value:
                                    # 處理特殊格式的日期
                                    row_dict[column] = datetime.now().isoformat()
                                else:
                                    row_dict[column] = value.isoformat() if isinstance(value, datetime) else str(value)
                            except Exception as e:
                                print(f"日期處理錯誤: {str(e)}")
                                row_dict[column] = None
                        else:
                            row_dict[column] = value
                    result.append(row_dict)
                
                print("處理後的結果:", result)
                return result
    except Exception as e:
        print(f"獲取新聞邏輯錯誤: {str(e)}")
        raise
with app.app_context():
    Now_HomeNews = get_HomeNews_logic()

@app.route('/api/add_news', methods=['POST'])
def add_news():
    try:
        data = request.json
        print("接收到的新聞數據:", data)  # 調試用
        
        # 驗證必要欄位
        if not data.get('title') or not data.get('content'):
            return jsonify({
                'success': False,
                'message': '標題和內容為必填項目'
            }), 400

        # 處理發布日期
        try:
            publish_date = datetime.fromisoformat(data['publishDate'].replace('Z', '+00:00'))
        except Exception as e:
            print(f"日期解析錯誤: {str(e)}")
            return jsonify({
                'success': False,
                'message': '日期格式不正確'
            }), 400

        news_uuid = str(uuid.uuid4())
        
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO News (
                    Uuid, 
                    Customer_Uuid,
                    Title,
                    Content,
                    Publish_Date,
                    Status,
                    Created_At,
                    Updated_At
                ) VALUES (?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """, (
                news_uuid,
                This_key,
                data['title'],
                data['content'],
                publish_date,
                data['status']
            ))
            conn.commit()
            
        return jsonify({
            'success': True,
            'message': '新增成功'
        })
    except Exception as e:
        print(f"新增新聞錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'新增失敗: {str(e)}'
        }), 500

@app.route('/api/update_news/<int:id>', methods=['PUT'])
def update_news(id):
    try:
        data = request.json
        print("接收到的更新數據:", data)  # 調試用

        # 處理日期格式
        try:
            # 將日期字符串轉換為 datetime 對象
            publish_date = datetime.fromisoformat(data['Publish_Date'].replace('Z', '+00:00'))
        except Exception as e:
            print(f"日期轉換錯誤: {str(e)}")
            # 如果轉換失敗，使用當前時間
            publish_date = datetime.now()

        with create_connection() as conn:
            cursor = conn.cursor()
            
            # SQL 查詢使用參數化查詢
            sql = """
                UPDATE News 
                SET Title = ?,
                    Content = ?,
                    Publish_Date = ?,
                    Status = ?,
                    Updated_At = GETDATE()
                WHERE Id = ?
            """
            
            params = (
                data['Title'],
                data['Content'],
                publish_date,  # 使用轉換後的日期
                data['Status'],
                id
            )
            
            print("SQL:", sql)  # 調試用
            print("參數:", params)  # 調試用
            
            cursor.execute(sql, params)
            conn.commit()
            
        return jsonify({
            'success': True, 
            'message': '更新成功'
        })
    except Exception as e:
        print(f"更新新聞錯誤: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'更新失敗: {str(e)}'
        }), 500

@app.route('/api/delete_news/<int:id>', methods=['DELETE'])
def delete_news(id):
    try:
        print(f"嘗試刪除新聞 ID: {id}")  # 調試用
        with create_connection() as conn:
            cursor = conn.cursor()
            
            # 先檢查新聞是否存在
            cursor.execute("SELECT Id FROM News WHERE Id = ? AND Deleted_At IS NULL", (id,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': '找不到該新聞或已被刪除'
                }), 404

            # 執行軟刪除
            cursor.execute("""
                UPDATE News 
                SET Deleted_At = GETDATE(),
                    Status = 0
                WHERE Id = ? AND Deleted_At IS NULL
            """, (id,))
            
            # 確認更新成功
            if cursor.rowcount == 0:
                raise Exception("刪除操作未影響任何行")
                
            conn.commit()
            print(f"成功刪除新聞 ID: {id}")  # 調試用
            
        return jsonify({
            'success': True, 
            'message': '刪除成功'
        })
    except Exception as e:
        print(f"刪除新聞錯誤: {str(e)}")  # 調試用
        return jsonify({
            'success': False, 
            'message': f'刪除失敗: {str(e)}'
        }), 500
#--------------------------------------------------------取得最新資料--------------------------------------------------------

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy"}), 200
#--------------------------------------------------------取得XX資料--------------------------------------------------------
#--------------------------------------------------------取得XX資料--------------------------------------------------------
#--------------------------------------------------------取得XX資料--------------------------------------------------------
#--------------------------------------------------------取得XX資料--------------------------------------------------------

    
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)