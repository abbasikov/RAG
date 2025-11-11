import sqlite3
from typing import Dict, List, Optional

class UserDatabase:
    def __init__(self, db_path: str = "user_data.db"):
        """Initialize SQLite database for user data storage"""
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Store only user data (name, email, income)
        # Conversation history is managed by OpenAI's Conversations API
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                name TEXT,
                email TEXT,
                income TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_complete BOOLEAN DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()

    def create_session(self, session_id: str) -> bool:
        """Create a new user session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO users (session_id, data_complete)
                VALUES (?, 0)
            ''', (session_id,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False

    def update_user_data(self, session_id: str, name: str = None,
                        email: str = None, income: str = None) -> bool:
        """Update user data for a session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build dynamic update query
            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)

            if email is not None:
                updates.append("email = ?")
                params.append(email)

            if income is not None:
                updates.append("income = ?")
                params.append(income)

            if not updates:
                return False

            params.append(session_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE session_id = ?"

            cursor.execute(query, params)

            # Check if all data is collected
            cursor.execute('''
                SELECT name, email, income FROM users WHERE session_id = ?
            ''', (session_id,))

            row = cursor.fetchone()
            if row and all(row):
                cursor.execute('''
                    UPDATE users SET data_complete = 1 WHERE session_id = ?
                ''', (session_id,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating user data: {e}")
            return False

    def get_user_data(self, session_id: str) -> Optional[Dict]:
        """Get user data for a session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT name, email, income, collected_at, data_complete
                FROM users WHERE session_id = ?
            ''', (session_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "session_id": session_id,
                    "name": row[0],
                    "email": row[1],
                    "income": row[2],
                    "collected_at": row[3],
                    "data_complete": bool(row[4])
                }
            return None
        except Exception as e:
            print(f"Error getting user data: {e}")
            return None

    def is_data_complete(self, session_id: str) -> bool:
        """Check if all user data has been collected"""
        user_data = self.get_user_data(session_id)
        if not user_data:
            return False

        return (user_data.get("name") and
                user_data.get("email") and
                user_data.get("income"))

    def get_all_complete_users(self) -> List[Dict]:
        """Get all users with complete data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT session_id, name, email, income, collected_at
                FROM users
                WHERE data_complete = 1
                ORDER BY collected_at DESC
            ''')

            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "session_id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "income": row[3],
                    "collected_at": row[4]
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error getting complete users: {e}")
            return []
