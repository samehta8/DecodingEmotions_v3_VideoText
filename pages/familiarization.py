"""
Familiarization trials page - Practice rating interface.
Displays familiarization videos with rating scales but doesn't save data.
Always shows the same 3 videos for all users.
"""
import streamlit as st
import streamlit.components.v1 as components
import os
import pandas as pd
import base64

from utils.config_loader import load_rating_scales
from utils.video_rating_display import display_video_rating_interface
from utils.gdrive_manager import get_all_video_filenames, get_video_path

def display_video_with_mode(video_file_path, playback_mode='loop', video_width=None, enable_auto_advance=False):
    """
    Display video with specified playback mode.

    Parameters:
    - video_file_path: Path to the video file
    - playback_mode: 'loop' or 'once'
        - 'loop': Autoplay, loop enabled, controls visible
        - 'once': Play for 2 seconds, then stop at black first frame
    - video_width: Width of video in pixels
    - enable_auto_advance: If True, trigger Streamlit rerun when video ends
    """
    if not os.path.exists(video_file_path):
        st.error(f"Video file not found: {video_file_path}")
        return

    if playback_mode == 'loop':
        if video_width:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.video(video_file_path, autoplay=True, loop=True)
        else:
            st.video(video_file_path, autoplay=True, loop=True)

    elif playback_mode == 'once':
        with open(video_file_path, 'rb') as f:
            video_bytes = f.read()
        video_base64 = base64.b64encode(video_bytes).decode()

        if video_width:
            if isinstance(video_width, str) and '%' in video_width:
                width_style = f"width: {video_width};"
            else:
                width_style = f"width: {video_width}px;"
        else:
            width_style = "max-width: 100%;"

        video_html = f"""
        <div style="width: 100%; height: 100vh; display: flex; align-items: center; justify-content: center; background: transparent;">
            <video
                id="main-video-fam"
                autoplay
                muted
                style="{width_style} max-height: 85vh; height: auto; object-fit: contain;"
            >
                <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        <style>
            video::-webkit-media-controls {{
                display: none !important;
            }}
            video::-webkit-media-controls-enclosure {{
                display: none !important;
            }}
        </style>
        <script>
            const video = document.getElementById('main-video-fam');
            
            video.addEventListener('timeupdate', function() {{
                if (video.currentTime >= 2.0) {{
                    video.pause();
                    video.currentTime = 0;
                }}
            }});
        </script>
        """
        components.html(video_html, height=700)

    else:
        st.video(video_file_path)


def _validate_familiarization_ratings(scale_values):
    """
    Validate that all required ratings are provided for familiarization trials.
    Checks both individual required scales and group requirements.

    Returns:
        List of error messages (empty if validation passes)
    """
    errors = []

    # Check individually required scales (not in groups)
    required_scales = st.session_state.get('required_scales', [])
    missing_scales = [
        title for title in required_scales
        if scale_values.get(title) is None or scale_values.get(title) == ''
    ]

    if missing_scales:
        errors.append(f"Required fields: {', '.join(missing_scales)}")

    # Check group requirements
    group_requirements = st.session_state.get('group_requirements', {})
    rating_scales = st.session_state.get('rating_scales', [])

    for group_id, group_info in group_requirements.items():
        required_count = group_info['number_of_ratings']
        error_msg = group_info.get('error_msg', '')
        group_title = group_info.get('title', group_id)

        # Find all scales in this group
        group_scales = [
            scale for scale in rating_scales
            if scale.get('group') == group_id
        ]

        # Count how many scales in this group have been changed
        changed_count = 0
        for scale in group_scales:
            title = scale.get('title')
            value = scale_values.get(title)

            # Check if value exists and is not empty
            if value is None or value == '':
                continue

            # For sliders, check if value has been changed from initial position
            if scale.get('type') == 'slider':
                initial_state = scale.get('initial_state', 'low')
                slider_min = scale.get('slider_min', 0)
                slider_max = scale.get('slider_max', 100)

                # Calculate initial value based on initial_state
                if initial_state == 'low':
                    initial_value = slider_min
                elif initial_state == 'high':
                    initial_value = slider_max
                else:  # center
                    initial_value = (slider_min + slider_max) / 2

                # Count as changed if value is different from initial
                if value != initial_value:
                    changed_count += 1
            else:
                # For discrete and text types, any non-empty value counts as changed
                changed_count += 1

        if changed_count < required_count:
            # Use custom error message if provided, otherwise use default
            if error_msg:
                errors.append(error_msg)
            else:
                errors.append(
                    f"Group '{group_title}': Please rate at least {required_count} emotions "
                    f"(currently {changed_count}/{required_count})"
                )

    return errors

def show():
    """Display the familiarization trials screen."""
    user = st.session_state.user
    config = st.session_state.config

    if not config:
        st.error("Configuration not loaded. Please restart the application.")
        return

    # Initialize familiarization state
    if 'familiarization_initialized' not in st.session_state:
        initialize_familiarization(config)

    # Check if there are videos to show
    if not st.session_state.get('familiarization_videos'):
        st.title("⚠️ Familiarization Videos Not Found")
        st.error(f"""
        No familiarization videos found in the configured directory.

        **Current path in config:** `{config['paths'].get('familiarization_video_path', 'videos_familiarization')}`

        **Current working directory:** `{os.getcwd()}`

        Please check:
        1. The familiarization_video_path in config.yaml is correct
        2. The directory exists and contains .mp4 files
        3. The path is correct relative to the app's working directory
        """)

        if st.button("◀️ Back to Pre-Familiarization", use_container_width=True):
            st.session_state.page = 'pre_familiarization'
            st.session_state.familiarization_initialized = False
            st.rerun()
        return

    # Load current video
    current_video_index = st.session_state.get('familiarization_video_index', 0)
    videos = st.session_state.familiarization_videos

    if current_video_index >= len(videos):
        # All familiarization videos completed - navigate to post-familiarization screen
        st.session_state.page = 'post_familiarization'
        st.session_state.familiarization_initialized = False
        st.rerun()
        return

    current_video = videos[current_video_index]

    # Get display mode from config
    display_mode = config['settings'].get('display_mode', 'combined')

    if display_mode == 'separate':
        # Sequential flow: video screen -> rating screen
        # Initialize screen state for current video if not exists
        if 'familiarization_current_screen' not in st.session_state:
            st.session_state.familiarization_current_screen = 'video'

        if st.session_state.familiarization_current_screen == 'video':
            # Display video screen
            display_familiarization_video_screen(current_video, config)
        else:
            # Display rating screen
            display_familiarization_rating_screen(current_video, config)
    else:
        # Combined mode: video and ratings side-by-side (original behavior)
        display_familiarization_interface(current_video, config)

def initialize_familiarization(config):
    """Initialize familiarization state - load videos and rating scales."""
    # Load rating scales (now returns dict with scales, groups, and requirements)
    rating_data = load_rating_scales(config)
    st.session_state.rating_scales = rating_data['scales']
    st.session_state.rating_groups = rating_data['groups']
    st.session_state.group_requirements = rating_data['group_requirements']

    # Track which scales are required individually (not in a group)
    st.session_state.required_scales = [
        scale.get('title') for scale in st.session_state.rating_scales
        if scale.get('required_to_proceed', True) and not scale.get('group')
    ]

    # Get videos from local filesystem
    familiarization_path = config['paths'].get('familiarization_video_path', 'videos_familiarization')
    try:
        all_videos = [f for f in os.listdir(familiarization_path) if f.lower().endswith('.mp4')]
        # Sort to ensure consistent order for all users
        all_videos.sort()
        print(f"[INFO] Found {len(all_videos)} familiarization videos in {familiarization_path}")
        st.session_state.familiarization_path = familiarization_path
    except FileNotFoundError:
        st.error(f"Familiarization video directory not found: {familiarization_path}")
        print(f"[ERROR] Directory not found: {familiarization_path}")
        print(f"[INFO] Current working directory: {os.getcwd()}")
        all_videos = []
    except Exception as e:
        st.error(f"Error loading familiarization videos: {e}")
        print(f"[ERROR] Error loading videos from {familiarization_path}: {e}")
        all_videos = []

    # Store in session state
    st.session_state.familiarization_videos = all_videos
    st.session_state.familiarization_video_index = 0
    st.session_state.familiarization_initialized = True

def display_familiarization_video_screen(video_filename, config):
    """Display only the video for familiarization (no ratings)."""
    familiarization_path = st.session_state.familiarization_path
    rating_scales = st.session_state.rating_scales

    # Add custom CSS to eliminate vertical spacing
    st.markdown("""
        <style>
        .stApp > div:first-child {
            padding-top: 0rem;
        }
        div[data-testid="stVerticalBlock"] > div {
            gap: 0rem;
        }
        .element-container {
            margin: 0rem;
            padding: 0rem;
        }
        .stMarkdown {
            margin: 0rem;
            padding: 0rem;
        }
        [data-testid="stHorizontalBlock"] {
            gap: 0rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Display video info
    current_index = st.session_state.familiarization_video_index
    total_videos = len(st.session_state.familiarization_videos)
    st.info(f"🎯 **Familiarization Trial - Video {current_index + 1} of {total_videos}**. Watch the video carefully.")

    # Define header content as a function
    def show_familiarization_header():
        pass  # Already shown above

    # Use shared display function in video-only mode
    display_video_rating_interface(
        video_filename=video_filename,
        video_path=familiarization_path,
        config=config,
        rating_scales=rating_scales,
        key_prefix="famil_scale_",
        action_id=None,
        metadata=None,
        header_content=show_familiarization_header,
        display_video_func=display_video_with_mode,
        display_mode='video_only'
    )

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        if st.button("Continue to Rating ▶️", use_container_width=True, type="primary", key="famil_advance_to_rating"):
            st.session_state.familiarization_current_screen = 'rating'
            st.rerun()


def display_familiarization_rating_screen(video_filename, config):
    """Display only the rating scales for familiarization (no video)."""
    rating_scales = st.session_state.rating_scales

    # Display rating info
    current_index = st.session_state.familiarization_video_index
    total_videos = len(st.session_state.familiarization_videos)
    st.info(f"📊 **Familiarization Trial - Rating {current_index + 1} of {total_videos}**. Please rate the video you just watched. *These ratings will not be saved.*")

    # Use shared display function in rating-only mode
    scale_values = display_video_rating_interface(
        video_filename=video_filename,
        video_path=st.session_state.familiarization_path,
        config=config,
        rating_scales=rating_scales,
        key_prefix="famil_scale_",
        action_id=None,
        metadata=None,
        header_content=None,
        display_video_func=display_video_with_mode,
        display_mode='rating_only'
    )

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("◀️ Back to Video", use_container_width=True):
            st.session_state.familiarization_current_screen = 'video'
            st.rerun()

    with col3:
        if st.button("Submit Rating ▶️", use_container_width=True, type="primary"):
            # Validate ratings
            validation_errors = _validate_familiarization_ratings(scale_values)

            if validation_errors:
                st.error("⚠️ Please complete the required ratings:")
                for error in validation_errors:
                    st.warning(error)
                st.stop()

            # Don't save rating - just move to next video
            st.session_state.familiarization_video_index += 1
            st.session_state.familiarization_current_screen = 'video'  # Reset to video screen for next video
            st.session_state.confirm_back_famil = False
            st.rerun()


def display_familiarization_interface(video_filename, config):
    """Display the familiarization rating interface (combined mode)."""
    rating_scales = st.session_state.rating_scales

    # Get video path from local filesystem
    familiarization_path = st.session_state.familiarization_path

    # Define header content as a function
    def show_familiarization_header():
        current_index = st.session_state.familiarization_video_index
        total_videos = len(st.session_state.familiarization_videos)
        st.info(f"🎯 **Familiarization Trial** - **Video {current_index + 1} of {total_videos}**. These ratings will not be saved.")

    # Use shared display function
    scale_values = display_video_rating_interface(
        video_filename=video_filename,
        video_path=familiarization_path,
        config=config,
        rating_scales=rating_scales,
        key_prefix="famil_scale_",
        action_id=None,  # Familiarization doesn't use action IDs
        metadata=None,  # Familiarization doesn't use metadata
        header_content=show_familiarization_header,
        display_video_func=display_video_with_mode
    )

    st.markdown("---")

    # Navigation and submission buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("◀️ Back to Questionnaire", use_container_width=True):
            if st.session_state.get('confirm_back_famil', False):
                st.session_state.page = 'questionnaire'
                st.session_state.user_id_confirmed = False
                st.session_state.familiarization_initialized = False
                st.rerun()
            else:
                st.session_state.confirm_back_famil = True
                st.warning("⚠️ Click again to confirm.")

    with col3:
        if st.button("Continue ▶️", use_container_width=True, type="primary"):
            # Validate ratings (same validation as main rating screen)
            validation_errors = _validate_familiarization_ratings(scale_values)

            if validation_errors:
                st.error("⚠️ Please complete the required ratings:")
                for error in validation_errors:
                    st.warning(error)
                st.stop()

            # Don't save rating - just move to next video
            st.session_state.familiarization_video_index += 1
            st.session_state.confirm_back_famil = False
            st.rerun()
