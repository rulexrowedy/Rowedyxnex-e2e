import sqlite3
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
import os
import json

DB_PATH = Path(__file__).parent / 'sessions.db'
ENCRYPTION_KEY_FILE = Path(__file__).parent / '.encryption_key'

def get_encryption_key():
    """Get or create encryption key for cookie storage"""
    if ENCRYPTION_KEY_FILE.exists():
        with open(ENCRYPTION_KEY_FILE, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(ENCRYPTION_KEY_FILE, 'wb') as f:
            f.write(key)
        return key

ENCRYPTION_KEY = get_encryption_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

def init_db():
    """Initialize database with tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            chat_id TEXT,
            name_prefix TEXT,
            delay INTEGER DEFAULT 30,
            cookies_encrypted TEXT,
            messages TEXT,
            status TEXT DEFAULT 'inactive',
            message_count INTEGER DEFAULT 0,
            profile_name TEXT,
            profile_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            log_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_name TEXT UNIQUE,
            chat_id TEXT,
            name_prefix TEXT,
            delay INTEGER DEFAULT 30,
            cookies_encrypted TEXT,
            messages TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def encrypt_data(data):
    """Encrypt data for secure storage"""
    if not data:
        return None
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    """Decrypt data"""
    if not encrypted_data:
        return ""
    try:
        return cipher_suite.decrypt(encrypted_data.encode()).decode()
    except:
        return ""

def save_session(task_id, chat_id, name_prefix, delay, cookies, messages, profile_name=None, profile_id=None):
    """Save a session to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    encrypted_cookies = encrypt_data(cookies)
    
    try:
        cursor.execute('''
            INSERT INTO sessions (task_id, chat_id, name_prefix, delay, cookies_encrypted, messages, status, profile_name, profile_id)
            VALUES (?, ?, ?, ?, ?, ?, 'running', ?, ?)
        ''', (task_id, chat_id, name_prefix, delay, encrypted_cookies, messages, profile_name, profile_id))
        conn.commit()
    except sqlite3.IntegrityError:
        cursor.execute('''
            UPDATE sessions 
            SET chat_id = ?, name_prefix = ?, delay = ?, cookies_encrypted = ?, 
                messages = ?, status = 'running', profile_name = ?, profile_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
        ''', (chat_id, name_prefix, delay, encrypted_cookies, messages, profile_name, profile_id, task_id))
        conn.commit()
    
    conn.close()

def update_session_status(task_id, status, message_count=None):
    """Update session status"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if message_count is not None:
        cursor.execute('''
            UPDATE sessions 
            SET status = ?, message_count = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
        ''', (status, message_count, task_id))
    else:
        cursor.execute('''
            UPDATE sessions 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
        ''', (status, task_id))
    
    conn.commit()
    conn.close()

def update_profile_info(task_id, profile_name, profile_id):
    """Update profile info for a session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE sessions 
        SET profile_name = ?, profile_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE task_id = ?
    ''', (profile_name, profile_id, task_id))
    
    conn.commit()
    conn.close()

def get_session(task_id):
    """Get session by task ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT task_id, chat_id, name_prefix, delay, cookies_encrypted, messages, status, message_count, profile_name, profile_id
        FROM sessions WHERE task_id = ?
    ''', (task_id,))
    
    session = cursor.fetchone()
    conn.close()
    
    if session:
        return {
            'task_id': session[0],
            'chat_id': session[1] or '',
            'name_prefix': session[2] or '',
            'delay': session[3] or 30,
            'cookies': decrypt_data(session[4]),
            'messages': session[5] or '',
            'status': session[6] or 'inactive',
            'message_count': session[7] or 0,
            'profile_name': session[8],
            'profile_id': session[9]
        }
    return None

def get_all_sessions():
    """Get all sessions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT task_id, chat_id, name_prefix, delay, cookies_encrypted, messages, status, message_count, profile_name, profile_id
        FROM sessions ORDER BY created_at DESC
    ''')
    
    sessions = cursor.fetchall()
    conn.close()
    
    result = []
    for session in sessions:
        result.append({
            'task_id': session[0],
            'chat_id': session[1] or '',
            'name_prefix': session[2] or '',
            'delay': session[3] or 30,
            'cookies': decrypt_data(session[4]),
            'messages': session[5] or '',
            'status': session[6] or 'inactive',
            'message_count': session[7] or 0,
            'profile_name': session[8],
            'profile_id': session[9]
        })
    
    return result

def delete_session(task_id):
    """Delete a session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM session_logs WHERE task_id = ?', (task_id,))
    cursor.execute('DELETE FROM sessions WHERE task_id = ?', (task_id,))
    
    conn.commit()
    conn.close()

def add_log(task_id, log_message):
    """Add a log entry for a session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO session_logs (task_id, log_message)
        VALUES (?, ?)
    ''', (task_id, log_message))
    
    conn.commit()
    conn.close()

def get_logs(task_id, limit=100):
    """Get logs for a session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT log_message, created_at FROM session_logs 
        WHERE task_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (task_id, limit))
    
    logs = cursor.fetchall()
    conn.close()
    
    return [{'message': log[0], 'timestamp': log[1]} for log in reversed(logs)]

def clear_old_logs(task_id, keep_count=500):
    """Clear old logs keeping only the most recent ones"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM session_logs 
        WHERE task_id = ? AND id NOT IN (
            SELECT id FROM session_logs 
            WHERE task_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        )
    ''', (task_id, task_id, keep_count))
    
    conn.commit()
    conn.close()

def save_config(config_name, chat_id, name_prefix, delay, cookies, messages):
    """Save a reusable configuration"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    encrypted_cookies = encrypt_data(cookies)
    
    try:
        cursor.execute('''
            INSERT INTO saved_configs (config_name, chat_id, name_prefix, delay, cookies_encrypted, messages)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (config_name, chat_id, name_prefix, delay, encrypted_cookies, messages))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        cursor.execute('''
            UPDATE saved_configs 
            SET chat_id = ?, name_prefix = ?, delay = ?, cookies_encrypted = ?, 
                messages = ?, updated_at = CURRENT_TIMESTAMP
            WHERE config_name = ?
        ''', (chat_id, name_prefix, delay, encrypted_cookies, messages, config_name))
        conn.commit()
        return True
    finally:
        conn.close()

def get_saved_configs():
    """Get all saved configurations"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT config_name, chat_id, name_prefix, delay, cookies_encrypted, messages FROM saved_configs')
    configs = cursor.fetchall()
    conn.close()
    
    result = []
    for config in configs:
        result.append({
            'config_name': config[0],
            'chat_id': config[1] or '',
            'name_prefix': config[2] or '',
            'delay': config[3] or 30,
            'cookies': decrypt_data(config[4]),
            'messages': config[5] or ''
        })
    
    return result

def delete_saved_config(config_name):
    """Delete a saved configuration"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM saved_configs WHERE config_name = ?', (config_name,))
    
    conn.commit()
    conn.close()

init_db()
