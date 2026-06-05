import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


DB_NAME = "careerMate.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tool_type TEXT NOT NULL,
            input_text TEXT NOT NULL,
            result_text TEXT NOT NULL,
            score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_filename TEXT NOT NULL,
            saved_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unknown_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def register_user(name, email, password):
    conn = get_connection()
    cursor = conn.cursor()

    hashed_password = generate_password_hash(password)

    try:
        cursor.execute("""
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
        """, (name, email, hashed_password))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email, password
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[3], password):
        return {
            "id": user[0],
            "name": user[1],
            "email": user[2]
        }

    return None


def save_chat_history(user_id, user_message, bot_response):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_history (user_id, user_message, bot_response)
        VALUES (?, ?, ?)
    """, (user_id, user_message, bot_response))

    conn.commit()
    conn.close()


def get_user_chat_history(user_id, search_query=None):
    conn = get_connection()
    cursor = conn.cursor()

    if search_query:
        keyword = f"%{search_query}%"
        cursor.execute("""
            SELECT id, user_message, bot_response, created_at
            FROM chat_history
            WHERE user_id = ?
            AND (user_message LIKE ? OR bot_response LIKE ?)
            ORDER BY id DESC
        """, (user_id, keyword, keyword))
    else:
        cursor.execute("""
            SELECT id, user_message, bot_response, created_at
            FROM chat_history
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,))

    chats = cursor.fetchall()
    conn.close()
    return chats


def get_all_chat_history(search_query=None):
    conn = get_connection()
    cursor = conn.cursor()

    if search_query:
        keyword = f"%{search_query}%"
        cursor.execute("""
            SELECT chat_history.id, users.name, users.email,
                   chat_history.user_message, chat_history.bot_response,
                   chat_history.created_at
            FROM chat_history
            JOIN users ON chat_history.user_id = users.id
            WHERE users.name LIKE ?
            OR users.email LIKE ?
            OR chat_history.user_message LIKE ?
            OR chat_history.bot_response LIKE ?
            ORDER BY chat_history.id DESC
        """, (keyword, keyword, keyword, keyword))
    else:
        cursor.execute("""
            SELECT chat_history.id, users.name, users.email,
                   chat_history.user_message, chat_history.bot_response,
                   chat_history.created_at
            FROM chat_history
            JOIN users ON chat_history.user_id = users.id
            ORDER BY chat_history.id DESC
        """)

    chats = cursor.fetchall()
    conn.close()
    return chats


def delete_chat_by_id(chat_id, user_id=None, is_admin=False):
    conn = get_connection()
    cursor = conn.cursor()

    if is_admin:
        cursor.execute("DELETE FROM chat_history WHERE id = ?", (chat_id,))
    else:
        cursor.execute(
            "DELETE FROM chat_history WHERE id = ? AND user_id = ?",
            (chat_id, user_id)
        )

    conn.commit()
    conn.close()


def clear_user_chat_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()


def clear_all_chat_history():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM chat_history")

    conn.commit()
    conn.close()


def save_unknown_question(user_id, question):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO unknown_questions (user_id, question)
        VALUES (?, ?)
    """, (user_id, question))

    conn.commit()
    conn.close()


def get_user_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email, created_at
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM chat_history WHERE user_id = ?", (user_id,))
    chat_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tool_results WHERE user_id = ?", (user_id,))
    tool_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM uploaded_resumes WHERE user_id = ?", (user_id,))
    resume_count = cursor.fetchone()[0]

    conn.close()

    return user, chat_count, tool_count, resume_count


def get_total_users_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_admin_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chat_history")
    total_chats = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tool_results")
    total_tools = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM uploaded_resumes")
    total_resumes = cursor.fetchone()[0]

    conn.close()

    return {
        "total_users": total_users,
        "total_chats": total_chats,
        "total_tools": total_tools,
        "total_resumes": total_resumes
    }


def save_tool_result(user_id, tool_type, input_text, result_text, score=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tool_results (user_id, tool_type, input_text, result_text, score)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, tool_type, input_text, result_text, score))

    conn.commit()
    result_id = cursor.lastrowid
    conn.close()

    return result_id


def get_user_tool_results(user_id, tool_type=None):
    conn = get_connection()
    cursor = conn.cursor()

    if tool_type:
        cursor.execute("""
            SELECT id, tool_type, input_text, result_text, score, created_at
            FROM tool_results
            WHERE user_id = ? AND tool_type = ?
            ORDER BY id DESC
        """, (user_id, tool_type))
    else:
        cursor.execute("""
            SELECT id, tool_type, input_text, result_text, score, created_at
            FROM tool_results
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,))

    results = cursor.fetchall()
    conn.close()
    return results


def get_tool_result_by_id(result_id, user_id=None, is_admin=False):
    conn = get_connection()
    cursor = conn.cursor()

    if is_admin:
        cursor.execute("""
            SELECT id, tool_type, input_text, result_text, score, created_at
            FROM tool_results
            WHERE id = ?
        """, (result_id,))
    else:
        cursor.execute("""
            SELECT id, tool_type, input_text, result_text, score, created_at
            FROM tool_results
            WHERE id = ? AND user_id = ?
        """, (result_id, user_id))

    result = cursor.fetchone()
    conn.close()
    return result


def save_uploaded_resume(user_id, original_filename, saved_filename, file_path):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO uploaded_resumes (user_id, original_filename, saved_filename, file_path)
        VALUES (?, ?, ?, ?)
    """, (user_id, original_filename, saved_filename, file_path))

    conn.commit()
    conn.close()


def get_user_uploaded_resumes(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, original_filename, saved_filename, file_path, created_at
        FROM uploaded_resumes
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    resumes = cursor.fetchall()
    conn.close()
    return resumes


def get_uploaded_resume_by_id(resume_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, original_filename, saved_filename, file_path, created_at
        FROM uploaded_resumes
        WHERE id = ? AND user_id = ?
    """, (resume_id, user_id))

    resume = cursor.fetchone()
    conn.close()
    return resume


def delete_uploaded_resume_by_id(resume_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM uploaded_resumes
        WHERE id = ? AND user_id = ?
    """, (resume_id, user_id))

    conn.commit()
    conn.close()