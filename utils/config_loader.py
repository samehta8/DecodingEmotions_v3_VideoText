"""
Configuration loader for YAML files.
"""
import yaml
import os

def load_config():
    """Load main configuration from config.yaml."""
    config_path = 'config/config.yaml'
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"{config_path} not found")

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    return config

def load_questionnaire_fields(config):
    """Load questionnaire fields from configured file."""
    questionnaire_file = config['settings'].get(
        'questionnaire_fields_file',
        'config/questionnaire_fields.yaml'
    )

    if not os.path.exists(questionnaire_file):
        print(f"[WARNING] {questionnaire_file} not found, using empty questionnaire fields")
        return []

    with open(questionnaire_file, 'r') as file:
        all_fields = yaml.safe_load(file)
        if all_fields is None:
            return []

    # Filter only active fields
    return [field for field in all_fields if field.get('active', False)]

def load_rating_scales(config):
    """
    Load rating scales and groups from configured file.

    Returns a dictionary with:
    - 'scales': list of active rating scales
    - 'groups': list of rating scale groups
    - 'group_requirements': dict mapping group_id to required number of ratings
    """
    rating_scales_file = config['settings'].get(
        'rating_scales_file',
        'config/rating_scales.yaml'
    )

    if not os.path.exists(rating_scales_file):
        print(f"[WARNING] {rating_scales_file} not found, using empty rating scales")
        return {'scales': [], 'groups': [], 'group_requirements': {}}

    with open(rating_scales_file, 'r') as file:
        data = yaml.safe_load(file)
        if data is None:
            return {'scales': [], 'groups': [], 'group_requirements': {}}

    # Check if this is the old format (list of scales) or new format (dict with groups and scales)
    if isinstance(data, list):
        # Old format: data is directly a list of scales
        print("[INFO] Using legacy rating scales format (list of scales)")
        all_scales = data
        groups = []
        group_requirements = {}
    else:
        # New format: data is a dict with 'groups' and 'scales' keys
        # Parse groups
        groups = data.get('groups', [])
        group_requirements = {}

        for group in groups:
            group_id = group.get('id')
            number_of_ratings = group.get('number_of_ratings', 0)
            error_msg = group.get('error_msg', '')
            if group_id:
                group_requirements[group_id] = {
                    'number_of_ratings': number_of_ratings,
                    'error_msg': error_msg,
                    'title': group.get('title', group_id)
                }

        # Parse scales
        all_scales = data.get('scales', [])
        if all_scales is None:
            all_scales = []

    # Filter only active scales
    active_scales = [scale for scale in all_scales if scale.get('active', False)]

    # Validate group requirements
    _validate_group_requirements(active_scales, groups, group_requirements)

    return {
        'scales': active_scales,
        'groups': groups,
        'group_requirements': group_requirements
    }

def _validate_group_requirements(scales, groups, group_requirements):
    """
    Validate that group requirements are reasonable.
    Issues warnings if number_of_ratings > number of scales in group.
    """
    # Count scales per group
    group_scale_counts = {}
    for scale in scales:
        group_id = scale.get('group')
        if group_id:
            group_scale_counts[group_id] = group_scale_counts.get(group_id, 0) + 1

    # Check each group
    for group_id, group_info in group_requirements.items():
        required_ratings = group_info['number_of_ratings']
        scale_count = group_scale_counts.get(group_id, 0)

        if scale_count == 0:
            print(f"[WARNING] Rating scale group '{group_id}' has no active scales assigned to it")
        elif required_ratings > scale_count:
            group_title = group_info['title']
            print(f"[WARNING] Rating scale group '{group_title}' (id: {group_id}) requires {required_ratings} ratings but only has {scale_count} scales. All scales in this group will be required.")
            # Update to require all scales
            group_requirements[group_id]['number_of_ratings'] = scale_count
