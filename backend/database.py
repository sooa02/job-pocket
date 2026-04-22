import pymysql
import json
import os

DB_CONFIG = {
    'host': os.getenv('RDB_URL'),
    'port': 3306,
    'user': os.getenv('MYSQL_RDB_USER'),
    'password': os.getenv('MYSQL_RDB_PASSWORD'),
    'db': 'job_pocket_rdb',
    'charset': 'utf8mb4'    
}

# DB 연결을 생성하는 헬퍼 함수
def get_connection():
    config = DB_CONFIG
    return pymysql.connect(
        **config,
        cursorclass=pymysql.cursors.DictCursor # 결과를 딕셔너리 형태로 받기 위해 추가
    )


def get_user(email: str):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            # MySQL은 플레이스홀더로 %s를 사용합니다.
            sql = 'SELECT username, password, email, resume_data FROM users WHERE email = %s'
            c.execute(sql, (email,))
            user = c.fetchone()
            # DictCursor를 사용하므로 tuple이 아닌 dict 형태(또는 None)로 반환됩니다.
            # 만약 튜플 형태를 유지해야 한다면 cursorclass 설정을 빼거나 아래처럼 반환하세요.
            if user:
                return (user['username'], user['password'], user['email'], user['resume_data'])
            return None
    finally:
        conn.close()

def add_user_via_web(name, password_hash, email, resume_data=None):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            c.execute('SELECT email FROM users WHERE email = %s', (email,))
            if c.fetchone():
                return False, "이미 가입된 이메일입니다."
            
            resume_json_str = json.dumps(resume_data, ensure_ascii=False) if resume_data else "{}"
            sql = 'INSERT INTO users (username, password, email, resume_data) VALUES (%s, %s, %s, %s)'
            c.execute(sql, (name, password_hash, email, resume_json_str))
            conn.commit()
            return True, "회원가입 성공"
    except Exception as e:
        return False, f"오류 발생: {e}"
    finally:
        conn.close()

def update_password(email, new_password_hash):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            sql = 'UPDATE users SET password = %s WHERE email = %s'
            c.execute(sql, (new_password_hash, email))
            success = c.rowcount > 0
            conn.commit()
            return success
    finally:
        conn.close()

def update_resume_data(email, resume_data):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            resume_json_str = json.dumps(resume_data, ensure_ascii=False)
            sql = 'UPDATE users SET resume_data = %s WHERE email = %s'
            c.execute(sql, (resume_json_str, email))
            success = c.rowcount > 0
            conn.commit()
            return success
    finally:
        conn.close()

def save_chat_message(email, role, content):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            sql = 'INSERT INTO chat_history (email, role, content) VALUES (%s, %s, %s)'
            c.execute(sql, (email, role, content))
            conn.commit()
    finally:
        conn.close()

def load_chat_history(email):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            sql = 'SELECT role, content FROM chat_history WHERE email = %s ORDER BY created_at ASC'
            c.execute(sql, (email,))
            rows = c.fetchall() # DictCursor이므로 [{"role": "...", "content": "..."}, ...] 형태로 바로 나옵니다.
            return rows
    finally:
        conn.close()

def delete_chat_history(email):
    conn = get_connection()
    try:
        with conn.cursor() as c:
            sql = 'DELETE FROM chat_history WHERE email = %s'
            c.execute(sql, (email,))
            conn.commit()
    finally:
        conn.close()