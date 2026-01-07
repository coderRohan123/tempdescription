import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432'),
            dbname=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD')
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute a database query and return results"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            
            if fetch_one:
                result = cursor.fetchone()
                # Convert to dict if result exists
                if result:
                    columns = [desc[0] for desc in cursor.description]
                    result = dict(zip(columns, result))
            elif fetch_all:
                results = cursor.fetchall()
                # Convert to list of dicts
                columns = [desc[0] for desc in cursor.description]
                result = [dict(zip(columns, row)) for row in results]
            else:
                result = None
            
            conn.commit()
            return result
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Database query error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

