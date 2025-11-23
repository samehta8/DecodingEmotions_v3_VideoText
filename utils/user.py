"""
User class for storing demographic and experience data.
"""
import random
import string

class User:
    """
    Stores demographic and experience data for a user/rater.
    User ID is randomly generated as 4 letters + 2 digits (e.g., ABCD12).
    """
    def __init__(self):
        self.user_id = ''
        self.data = {}  # Stores all questionnaire field responses
        # Legacy fields for backward compatibility
        self.gender = 'Not specified'
        self.age = 0
        self.nationality = ''
        self.player_exp = 0
        self.coach_exp = 0
        self.watch_exp = 0
        self.license = 'Not specified'

    def generate_random_user_id(self, existing_user_ids=None):
        """
        Generate a random user ID: 4 uppercase letters + 2 digits (e.g., ABCD12).
        Ensures the generated ID doesn't already exist in the system.

        Parameters:
        - existing_user_ids: List of existing user IDs to avoid duplicates

        Returns:
        - Generated user ID string
        """
        if existing_user_ids is None:
            existing_user_ids = []

        max_attempts = 1000  # Prevent infinite loop
        attempts = 0

        while attempts < max_attempts:
            # Generate 4 random uppercase letters
            letters = ''.join(random.choices(string.ascii_uppercase, k=4))
            # Generate 2 random digits
            digits = ''.join(random.choices(string.digits, k=2))
            # Combine
            new_id = letters + digits

            # Check if ID already exists
            if new_id not in existing_user_ids:
                self.user_id = new_id
                return new_id

            attempts += 1

        # Fallback if somehow we can't generate a unique ID (very unlikely)
        raise Exception("Failed to generate unique user ID after 1000 attempts")

    def set_field_value(self, field_name, value):
        """Set the value for a specific field and update User object."""
        self.data[field_name] = value

        # Update legacy fields for backward compatibility
        if field_name == 'gender':
            self.gender = value
        elif field_name == 'age':
            self.age = int(value) if value else 0
        elif field_name == 'nationality':
            self.nationality = value
        elif field_name == 'player_exp':
            self.player_exp = int(value) if value else 0
        elif field_name == 'coach_exp':
            self.coach_exp = int(value) if value else 0
        elif field_name == 'watch_exp':
            self.watch_exp = int(value) if value else 0
        elif field_name == 'license':
            self.license = value

    def to_dict(self):
        """Convert user data to dictionary for JSON export."""
        from datetime import datetime
        return {
            'user_id': self.user_id,
            'gender': self.gender,
            'age': self.age,
            'nationality': self.nationality,
            'license': self.license,
            'player_exp': self.player_exp,
            'coach_exp': self.coach_exp,
            'watch_exp': self.watch_exp,
            'saved_at': datetime.now().isoformat(timespec='seconds'),
            **self.data
        }
