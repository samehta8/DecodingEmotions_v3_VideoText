"""
Data persistence functions for saving and loading user data and ratings.
Implements flexible storage strategy based on config: local, online, or both.
"""
import json
import os
import streamlit as st
from datetime import datetime
from utils.gsheets_manager import (
    append_rating_to_gsheets,
    get_rated_videos_for_user_from_gsheets,
    append_user_to_gsheets,
    user_exists_in_gsheets
)

def save_user_data(user):
    """
    Save user demographic data based on configured storage_mode.

    Storage modes:
    - "local": Save to local JSON only
    - "online": Save to Google Sheets only
    - "both": Save to both Google Sheets and local JSON

    Parameters:
    - user: User object with user_id and demographic data

    Returns:
    - True if at least one save method successful, False if all fail
    """
    # Get user data dictionary
    user_data = user.to_dict()

    # Get storage mode from config
    config = st.session_state.get('config', {})
    storage_mode = config.get('settings', {}).get('storage_mode', 'both')

    # Track success of each write method
    gsheets_success = False
    local_json_success = False

    # ONLINE: Write to Google Sheets
    if storage_mode in ['online', 'both']:
        try:
            gsheets_success = append_user_to_gsheets(user_data, worksheet="users")
            if gsheets_success:
                print(f"[INFO] ✓ User data saved to Google Sheets: {user.user_id}")
        except Exception as e:
            print(f"[WARNING] Google Sheets write failed for user data: {e}")

    # LOCAL: Write to local JSON file
    if storage_mode in ['local', 'both']:
        try:
            os.makedirs('user_data', exist_ok=True)
            filename = f"{user.user_id}.json"
            path = os.path.join('user_data', filename)

            with open(path, 'w') as f:
                json.dump(user_data, f, indent=2)

            local_json_success = True
            print(f"[INFO] ✓ User data saved to local JSON: {filename}")
        except Exception as e:
            print(f"[WARNING] Local JSON write failed for user data: {e}")

    # Return True if at least one method succeeded
    success = gsheets_success or local_json_success
    if success:
        return True
    else:
        print(f"[ERROR] CRITICAL: All storage methods failed for user {user.user_id}")
        return False

def save_rating(user_id, action_id, scale_values):
    """
    Save rating data based on configured storage_mode.

    Storage modes:
    - "local": Save to local JSON only
    - "online": Save to Google Sheets only
    - "both": Save to both Google Sheets and local JSON

    Parameters:
    - user_id: User identifier
    - action_id: Action/video identifier
    - scale_values: Dictionary of scale titles to values

    Returns:
    - True if at least one save method successful, False if all fail
    """
    # Build rating data
    rating_data = {
        'user_id': user_id,
        'id': action_id
    }

    # Add each scale's value
    for title, value in scale_values.items():
        # Use title as key (sanitized for JSON compatibility)
        key = title.lower().replace(' ', '_')
        rating_data[key] = value

    # Get storage mode from config
    config = st.session_state.get('config', {})
    storage_mode = config.get('settings', {}).get('storage_mode', 'both')

    # Track success of each write method
    gsheets_success = False
    local_json_success = False

    # ONLINE: Write to Google Sheets
    if storage_mode in ['online', 'both']:
        try:
            gsheets_success = append_rating_to_gsheets(rating_data, worksheet="ratings")
            if gsheets_success:
                print(f"[INFO] ✓ Rating saved to Google Sheets: {user_id}_{action_id}")
        except Exception as e:
            print(f"[WARNING] Google Sheets write failed: {e}")

    # LOCAL: Write to local JSON file
    if storage_mode in ['local', 'both']:
        try:
            os.makedirs('user_ratings', exist_ok=True)
            filename = os.path.join('user_ratings', f"{user_id}_{action_id}.json")
            with open(filename, 'w') as f:
                json.dump(rating_data, f, indent=2)
            local_json_success = True
            print(f"[INFO] ✓ Rating saved to local JSON: {user_id}_{action_id}.json")
        except Exception as e:
            print(f"[WARNING] Local JSON write failed: {e}")

    # Return True if at least one method succeeded
    success = gsheets_success or local_json_success
    if success:
        return True
    else:
        print(f"[ERROR] CRITICAL: All storage methods failed for {user_id}_{action_id}")
        return False

def get_all_existing_user_ids():
    """
    Get all existing user IDs from the system.
    Tries both Google Sheets and local JSON, combines results.

    Returns:
    - List of all unique user IDs
    """
    user_ids = set()

    # Try Google Sheets first
    try:
        from utils.gsheets_manager import get_all_user_ids_from_gsheets
        gsheets_ids = get_all_user_ids_from_gsheets(worksheet="users")
        user_ids.update(gsheets_ids)
        print(f"[INFO] Retrieved {len(gsheets_ids)} user IDs from Google Sheets")
    except Exception as e:
        print(f"[WARNING] Failed to get user IDs from Google Sheets: {e}")

    # Also check local JSON files
    try:
        if os.path.exists('user_data'):
            for filename in os.listdir('user_data'):
                if filename.endswith('.json'):
                    user_id = filename.replace('.json', '')
                    user_ids.add(user_id)
            print(f"[INFO] Found {len(user_ids)} total unique user IDs")
    except Exception as e:
        print(f"[WARNING] Failed to get user IDs from local files: {e}")

    return list(user_ids)

def user_exists(user_id):
    """
    Check if a user_id exists in the system (case-insensitive).
    Tries Google Sheets first (primary), falls back to local JSON (backup).

    Parameters:
    - user_id: User identifier to check

    Returns:
    - True if user has at least one rating file, False otherwise
    """
    # PRIMARY: Try Google Sheets first
    try:
        if user_exists_in_gsheets(user_id, worksheet="users"):
            print(f"[INFO] User {user_id} found in Google Sheets")
            return True
    except Exception as e:
        print(f"[WARNING] Failed to check user existence in Google Sheets: {e}")

    # FALLBACK: Check local JSON files (case-insensitive)
    try:
        if not os.path.exists('user_data'):
            return False

        # Check in user_data folder (primary storage for user info) - case insensitive
        user_id_lower = user_id.lower()
        for filename in os.listdir('user_data'):
            if filename.endswith('.json'):
                file_user_id = filename.replace('.json', '').lower()
                if file_user_id == user_id_lower:
                    print(f"[INFO] User {user_id} found in local JSON files")
                    return True

        # Also check user_ratings as fallback - case insensitive
        if not os.path.exists('user_ratings'):
            return False

        user_ratings_files = os.listdir('user_ratings')
        for f in user_ratings_files:
            if '_' in f and f.endswith('.json'):
                file_user_id = f.split('_')[0].lower()
                if file_user_id == user_id_lower:
                    print(f"[INFO] User {user_id} found in local JSON files")
                    return True

        return False
    except Exception as e:
        print(f"[ERROR] Failed to check user existence in both sources: {e}")
        return False

def get_rated_videos_for_user(user_id):
    """
    Get list of video IDs already rated by a user (case-insensitive).
    Tries Google Sheets first (primary), falls back to local JSON (backup).

    Parameters:
    - user_id: User identifier

    Returns:
    - List of action IDs (without .mp4 extension)
    """
    # PRIMARY: Try Google Sheets first
    try:
        gsheets_ids = get_rated_videos_for_user_from_gsheets(user_id, worksheet="ratings")
        if gsheets_ids:
            print(f"[INFO] Retrieved {len(gsheets_ids)} rated videos from Google Sheets for user {user_id}")
            return gsheets_ids
    except Exception as e:
        print(f"[WARNING] Failed to get rated videos from Google Sheets: {e}")

    # FALLBACK: Use local JSON files (case-insensitive)
    try:
        if not os.path.exists('user_ratings'):
            return []

        files = os.listdir('user_ratings')
        rated_ids = []
        user_id_lower = user_id.lower()

        for f in files:
            if f.endswith('.json') and '_' in f:
                # Extract user_id from filename (case-insensitive match)
                file_user_id = f.split('_')[0].lower()
                if file_user_id == user_id_lower:
                    # Extract action_id from filename: {user_id}_{action_id}.json
                    parts = f.replace('.json', '').split('_', 1)
                    if len(parts) > 1:
                        action_id = parts[1]
                        rated_ids.append(action_id)

        print(f"[INFO] Retrieved {len(rated_ids)} rated videos from JSON backup for user {user_id}")
        return rated_ids
    except Exception as e:
        print(f"[ERROR] Failed to get rated videos from both sources: {e}")
        return []
