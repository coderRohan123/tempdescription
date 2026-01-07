"""
History Service
Handles all database operations related to generation history
"""
from database import execute_query

def get_user_generations(user_id: str) -> list:
    """
    Get all generations for a user
    
    Args:
        user_id: User ID (string)
    
    Returns:
        List of generation dictionaries
    """
    user_id_str = str(user_id)
    
    query = """
        SELECT id, product_name, product_category, target_audience,
               user_description, target_language, image_urls, final_description,
               created_at, updated_at
        FROM generations
        WHERE user_id::text = %s AND data_status = 'A'
        ORDER BY created_at DESC
        LIMIT 50
    """
    results = execute_query(query, (user_id_str,), fetch_all=True)
    
    generations = []
    for row in results:
        generations.append({
            'id': str(row['id']),
            'product_name': row['product_name'],
            'product_category': row['product_category'],
            'target_audience': row['target_audience'],
            'user_description': row['user_description'],
            'target_language': row['target_language'],
            'image_urls': row['image_urls'] or [],
            'final_description': row['final_description'],
            'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
            'updated_at': row['updated_at'].isoformat() if row.get('updated_at') else None
        })
    
    return generations

def save_generation(user_id: str, product_name: str, product_category: str,
                    target_audience: str, user_description: str, target_language: str,
                    final_description: str, image_urls: list = None) -> dict:
    """
    Save or update a generation. Updates if product_name exists for user.
    
    Args:
        user_id: User ID (string)
        product_name: Product name (constant, used for matching)
        product_category: Product category
        target_audience: Target audience
        user_description: User description
        target_language: Target language
        final_description: Generated description
        image_urls: List of image URLs (optional)
    
    Returns:
        Dictionary with 'id' and 'updated' (boolean) keys
    """
    user_id_str = str(user_id)
    image_urls = image_urls or []
    
    # Check if generation with same product_name exists for this user
    check_query = """
        SELECT id FROM generations
        WHERE user_id::text = %s AND product_name = %s AND data_status = 'A'
    """
    existing = execute_query(check_query, (user_id_str, product_name), fetch_one=True)
    
    if existing:
        # Update existing record
        update_query = """
            UPDATE generations
            SET product_category = %s,
                target_audience = %s,
                user_description = %s,
                target_language = %s,
                image_urls = %s,
                final_description = %s,
                updated_at = now()
            WHERE id = %s AND user_id::text = %s
            RETURNING id, updated_at
        """
        result = execute_query(
            update_query,
            (
                product_category,
                target_audience,
                user_description,
                target_language,
                image_urls,
                final_description,
                existing['id'],
                user_id_str
            ),
            fetch_one=True
        )
        return {
            'id': str(result['id']),
            'updated': True
        }
    else:
        # Insert new record
        insert_query = """
            INSERT INTO generations (
                user_id, product_name, product_category, target_audience,
                user_description, target_language, image_urls, final_description
            )
            VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        """
        result = execute_query(
            insert_query,
            (
                user_id_str,
                product_name,
                product_category,
                target_audience,
                user_description,
                target_language,
                image_urls,
                final_description
            ),
            fetch_one=True
        )
        return {
            'id': str(result['id']),
            'updated': False
        }

def delete_generation(user_id: str, generation_id: str) -> bool:
    """
    Delete a generation (soft delete by setting data_status to 'D')
    
    Args:
        user_id: User ID (string)
        generation_id: Generation ID (string)
    
    Returns:
        True if deleted successfully, False if not found
    
    Raises:
        ValueError: If generation doesn't belong to user or doesn't exist
    """
    user_id_str = str(user_id)
    generation_id_str = str(generation_id)
    
    # Verify the generation belongs to the user
    check_query = """
        SELECT id FROM generations
        WHERE id::text = %s AND user_id::text = %s AND data_status = 'A'
    """
    existing = execute_query(check_query, (generation_id_str, user_id_str), fetch_one=True)
    
    if not existing:
        raise ValueError('Generation not found or access denied')
    
    # Soft delete
    delete_query = """
        UPDATE generations
        SET data_status = 'D', updated_at = now()
        WHERE id::text = %s AND user_id::text = %s
    """
    execute_query(delete_query, (generation_id_str, user_id_str))
    
    return True

