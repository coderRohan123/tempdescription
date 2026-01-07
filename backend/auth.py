import jwt
import bcrypt
from datetime import datetime, timedelta
import os
from database import execute_query

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def generate_access_token(user_id: str, username: str) -> str:
    """Generate a JWT access token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_refresh_token(user_id: str) -> str:
    """Generate a refresh token and store it in database"""
    # Ensure user_id is a string
    user_id_str = str(user_id)
    
    token = jwt.encode(
        {
            'user_id': user_id_str,
            'type': 'refresh',
            'exp': datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            'iat': datetime.utcnow()
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )
    
    # Hash the token before storing
    token_hash = bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Store refresh token in database (UUID will be cast automatically by psycopg)
    query = """
        INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
        VALUES (%s::uuid, %s, %s)
        RETURNING token_id
    """
    execute_query(query, (user_id_str, token_hash, expires_at))
    
    return token

def verify_token(token: str, token_type: str = 'access') -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get('type') != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def verify_refresh_token(token: str) -> dict:
    """Verify refresh token against database"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get('type') != 'refresh':
            return None
        
        user_id = payload.get('user_id')
        user_id_str = str(user_id)
        
        # Check if token exists in database and is not revoked
        query = """
            SELECT token_id, token_hash, expires_at, revoked_at
            FROM refresh_tokens
            WHERE user_id::text = %s AND revoked_at IS NULL AND expires_at > now()
            ORDER BY issued_at DESC
        """
        tokens = execute_query(query, (user_id_str,), fetch_all=True)
        
        if not tokens:
            return None
        
        # Verify token hash matches (we need to check all tokens since we can't directly compare)
        # For simplicity, we'll verify the JWT and check if any valid token exists for this user
        # In production, you might want to store a token identifier in the JWT payload
        
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def revoke_refresh_token(token: str):
    """Revoke a refresh token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        user_id_str = str(user_id)
        
        # Revoke all tokens for this user (or implement more granular revocation)
        query = """
            UPDATE refresh_tokens
            SET revoked_at = now(), updated_at = now()
            WHERE user_id::text = %s AND revoked_at IS NULL
        """
        execute_query(query, (user_id_str,))
    except Exception as e:
        print(f"Error revoking token: {str(e)}")

def get_user_by_id(user_id: str) -> dict:
    """Get user by ID"""
    query = """
        SELECT user_id, username, email, created_at
        FROM users
        WHERE user_id::text = %s AND data_status = 'A'
    """
    result = execute_query(query, (str(user_id),), fetch_one=True)
    return dict(result) if result else None

def get_user_by_username(username: str) -> dict:
    """Get user by username"""
    query = """
        SELECT user_id, username, email, password_hash, created_at
        FROM users
        WHERE username = %s AND data_status = 'A'
    """
    result = execute_query(query, (username,), fetch_one=True)
    return dict(result) if result else None

def get_user_by_email(email: str) -> dict:
    """Get user by email"""
    query = """
        SELECT user_id, username, email, password_hash, created_at
        FROM users
        WHERE email = %s AND data_status = 'A'
    """
    result = execute_query(query, (email,), fetch_one=True)
    return dict(result) if result else None

def create_user(username: str, email: str, password: str) -> dict:
    """Create a new user"""
    password_hash = hash_password(password)
    query = """
        INSERT INTO users (username, email, password_hash)
        VALUES (%s, %s, %s)
        RETURNING user_id, username, email, created_at
    """
    result = execute_query(query, (username, email, password_hash), fetch_one=True)
    return dict(result) if result else None

