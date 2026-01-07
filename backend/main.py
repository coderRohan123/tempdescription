"""
Main Application Entry Point
Central routing and API endpoint definitions
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
from auth import (
    create_user, get_user_by_username, get_user_by_email,
    verify_password, generate_access_token, generate_refresh_token,
    verify_token, verify_refresh_token, revoke_refresh_token,
    get_user_by_id
)
from gemini_service import generate_product_description, translate_description
from history import get_user_generations, save_generation, delete_generation

app = Flask(__name__)
CORS(app, supports_credentials=True)

# =========================
# AUTHENTICATION MIDDLEWARE
# =========================
def token_required(f):
    """Decorator to require JWT token for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated

# =========================
# HEALTH CHECK
# =========================
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK'})

# =========================
# AUTHENTICATION ENDPOINTS
# =========================
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        if get_user_by_username(username):
            return jsonify({'error': 'Username already exists'}), 400
        
        if get_user_by_email(email):
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create user
        user = create_user(username, email, password)
        if not user:
            return jsonify({'error': 'Failed to create user'}), 500
        
        # Convert user_id to string (handles UUID objects from psycopg3)
        user_id_str = str(user['user_id'])
        
        # Generate tokens
        access_token = generate_access_token(user_id_str, user['username'])
        refresh_token = generate_refresh_token(user_id_str)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'user_id': user_id_str,
                'username': user['username'],
                'email': user['email']
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Get user
        user = get_user_by_username(username)
        if not user:
            print(f"Login failed: User '{username}' not found")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        password_valid = verify_password(password, user['password_hash'])
        if not password_valid:
            print(f"Login failed: Invalid password for user '{username}'")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Convert user_id to string (handles UUID objects from psycopg3)
        user_id_str = str(user['user_id'])
        
        # Generate tokens
        access_token = generate_access_token(user_id_str, user['username'])
        refresh_token = generate_refresh_token(user_id_str)
        
        print(f"Login successful for user '{username}'")
        return jsonify({
            'message': 'Login successful',
            'user': {
                'user_id': user_id_str,
                'username': user['username'],
                'email': user['email']
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'An error occurred during login. Please try again.'}), 500

@app.route('/api/auth/refresh', methods=['POST'])
def refresh():
    try:
        data = request.json
        refresh_token_value = data.get('refresh_token')
        
        if not refresh_token_value:
            return jsonify({'error': 'Refresh token is required'}), 400
        
        # Verify refresh token
        payload = verify_refresh_token(refresh_token_value)
        if not payload:
            return jsonify({'error': 'Invalid or expired refresh token'}), 401
        
        # Get user (ensure user_id is a string)
        user_id_str = str(payload['user_id'])
        user = get_user_by_id(user_id_str)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate new access token
        user_id_for_token = str(user['user_id'])
        access_token = generate_access_token(user_id_for_token, user['username'])
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        print(f"Refresh token error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout endpoint - doesn't require authentication to allow cleanup even with expired tokens"""
    try:
        data = request.json or {}
        refresh_token_value = data.get('refresh_token')
        
        # Try to revoke refresh token if provided (optional, don't fail if it's invalid)
        if refresh_token_value:
            try:
                revoke_refresh_token(refresh_token_value)
            except Exception as e:
                # Don't fail logout if token revocation fails (token might already be expired/invalid)
                print(f"Note: Could not revoke refresh token (may already be invalid): {str(e)}")
        
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except Exception as e:
        print(f"Logout error: {str(e)}")
        # Still return success since we want to clear client-side storage
        return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    try:
        user_id = request.current_user['user_id']
        user_id_str = str(user_id)  # Ensure it's a string
        user = get_user_by_id(user_id_str)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'user_id': str(user['user_id']),
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at'].isoformat() if user.get('created_at') else None
            }
        }), 200
        
    except Exception as e:
        print(f"Get current user error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =========================
# GENERATION ENDPOINTS
# =========================
@app.route('/api/generate-description', methods=['POST'])
def generate_description():
    """Generate product description using Gemini AI"""
    try:
        data = request.json
        product_name = data.get('product_name', '').strip()
        product_category = data.get('product_category', '').strip()
        target_audience = data.get('target_audience', '').strip()
        user_description = data.get('user_description', '').strip()
        target_language = data.get('target_language', 'English').strip()
        
        # Support both single image (backward compatibility) and multiple images
        image_data = data.get('image', '')
        images_data = data.get('images', [])
        
        # If images array is provided, use it; otherwise fall back to single image
        if images_data and isinstance(images_data, list) and len(images_data) > 0:
            image_list = images_data
        elif image_data:
            image_list = [image_data]
        else:
            image_list = []
        
        # Generate description using Gemini service
        description = generate_product_description(
            product_name=product_name,
            product_category=product_category,
            target_audience=target_audience,
            user_description=user_description,
            target_language=target_language,
            images=image_list
        )
        
        return jsonify({
            'description': description
        })
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error in generate_description: {str(e)}")
        return jsonify({'error': str(e)}), 500


# =========================
# HISTORY ENDPOINTS
# =========================
@app.route('/api/generations', methods=['GET'])
@token_required
def get_generations():
    """Get user's generation history"""
    try:
        user_id = request.current_user['user_id']
        generations = get_user_generations(user_id)
        return jsonify({'generations': generations}), 200
        
    except Exception as e:
        print(f"Get generations error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generations/save', methods=['POST'])
@token_required
def save_generation_endpoint():
    """Save or update a generation. Updates if product_name exists for user."""
    try:
        user_id = request.current_user['user_id']
        data = request.json
        
        product_name = data.get('product_name', '').strip()
        product_category = data.get('product_category', '').strip()
        target_audience = data.get('target_audience', '').strip()
        user_description = data.get('user_description', '').strip()
        target_language = data.get('target_language', 'English').strip()
        final_description = data.get('final_description', '').strip()
        image_urls = data.get('image_urls', [])
        
        if not product_name or not final_description:
            return jsonify({'error': 'Product name and description are required'}), 400
        
        result = save_generation(
            user_id=user_id,
            product_name=product_name,
            product_category=product_category,
            target_audience=target_audience,
            user_description=user_description,
            target_language=target_language,
            final_description=final_description,
            image_urls=image_urls
        )
        
        message = 'Generation updated successfully' if result['updated'] else 'Generation saved successfully'
        status_code = 200 if result['updated'] else 201
        
        return jsonify({
            'message': message,
            'id': result['id'],
            'updated': result['updated']
        }), status_code
        
    except Exception as e:
        print(f"Save generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/generations/<generation_id>', methods=['DELETE'])
@token_required
def delete_generation_endpoint(generation_id):
    """Delete a generation (soft delete by setting data_status to 'D')"""
    try:
        user_id = request.current_user['user_id']
        delete_generation(user_id, generation_id)
        return jsonify({'message': 'Generation deleted successfully'}), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        print(f"Delete generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/translate-description', methods=['POST'])
def translate_description_endpoint():
    """Translate a product description to multiple languages"""
    try:
        data = request.json
        description = data.get('description', '').strip()
        target_languages = data.get('languages', [])
        
        if not description:
            return jsonify({'error': 'Description is required'}), 400
        
        if not target_languages or not isinstance(target_languages, list) or len(target_languages) == 0:
            return jsonify({'error': 'At least one target language is required'}), 400
        
        if len(target_languages) > 3:
            return jsonify({'error': 'Maximum 3 languages allowed'}), 400
        
        # Translate using Gemini service
        translations = translate_description(description, target_languages)
        
        return jsonify({
            'translations': translations
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error in translate_description: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)

