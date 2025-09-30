import sqlite3
import bcrypt
from datetime import datetime
from typing import Optional, Dict, List
import json

class Database:
    def __init__(self, db_path: str = "trading_analyzer.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    last_login TIMESTAMP,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    deriv_token TEXT,
                    account_balances TEXT,
                    performance_metrics TEXT
                )
            """)
            
            # Create default admin user if not exists
            cursor.execute("SELECT * FROM users WHERE email = ?", ("williamsamoe2023@gmail.com",))
            if not cursor.fetchone():
                # Hash the password
                password = "12345678"
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
                
                cursor.execute("""
                    INSERT INTO users (email, name, password_hash, role, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "williamsamoe2023@gmail.com",
                    "Admin",
                    password_hash,
                    "admin",
                    datetime.now(),
                    True
                ))
            
            conn.commit()

    def create_user(self, email: str, name: str, password: str, role: str = "user") -> bool:
        """Create a new user"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user exists
                cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    return False
                
                # Hash password
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
                
                # Create user
                cursor.execute("""
                    INSERT INTO users (email, name, password_hash, role, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (email, name, password_hash, role, datetime.now(), True))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    def verify_user(self, email: str, password: str) -> Optional[Dict]:
        """Verify user credentials"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if not user:
                return None
            
            # Check password - user[2] is already bytes, no need to encode
            if bcrypt.checkpw(password.encode('utf-8'), user[2]):
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = ? WHERE email = ?",
                    (datetime.now(), email)
                )
                conn.commit()
                
                # Return user data
                return {
                    'email': user[0],
                    'name': user[1],
                    'role': user[3],
                    'is_active': user[6],
                    'deriv_token': json.loads(user[7]) if user[7] else None,
                    'account_balances': json.loads(user[8]) if user[8] else None,
                    'performance_metrics': json.loads(user[9]) if user[9] else None
                }
            
            return None

    def update_user(self, email: str, updates: Dict) -> bool:
        """Update user information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build update query
                update_fields = []
                values = []
                
                if 'name' in updates:
                    update_fields.append("name = ?")
                    values.append(updates['name'])
                
                if 'password' in updates:
                    salt = bcrypt.gensalt()
                    password_hash = bcrypt.hashpw(updates['password'].encode('utf-8'), salt)
                    update_fields.append("password_hash = ?")
                    values.append(password_hash)
                
                if 'role' in updates:
                    update_fields.append("role = ?")
                    values.append(updates['role'])
                
                if 'is_active' in updates:
                    update_fields.append("is_active = ?")
                    values.append(updates['is_active'])
                
                if 'deriv_token' in updates:
                    update_fields.append("deriv_token = ?")
                    values.append(json.dumps(updates['deriv_token']))
                
                if 'account_balances' in updates:
                    update_fields.append("account_balances = ?")
                    values.append(json.dumps(updates['account_balances']))
                
                if 'performance_metrics' in updates:
                    update_fields.append("performance_metrics = ?")
                    values.append(json.dumps(updates['performance_metrics']))
                
                if not update_fields:
                    return False
                
                # Add email to values
                values.append(email)
                
                # Execute update
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE email = ?"
                cursor.execute(query, values)
                conn.commit()
                
                return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    def get_user(self, email: str) -> Optional[Dict]:
        """Get user information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if not user:
                return None
            
            return {
                'email': user[0],
                'name': user[1],
                'role': user[3],
                'created_at': user[4],
                'last_login': user[5],
                'is_active': user[6],
                'deriv_token': json.loads(user[7]) if user[7] else None,
                'account_balances': json.loads(user[8]) if user[8] else None,
                'performance_metrics': json.loads(user[9]) if user[9] else None
            }

    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            
            return [{
                'email': user[0],
                'name': user[1],
                'role': user[3],
                'created_at': user[4],
                'last_login': user[5],
                'is_active': user[6],
                'deriv_token': json.loads(user[7]) if user[7] else None,
                'account_balances': json.loads(user[8]) if user[8] else None,
                'performance_metrics': json.loads(user[9]) if user[9] else None
            } for user in users]

# Create global database instance
db = Database() 