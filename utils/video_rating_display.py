"""
Shared display logic for video rating interface.
Used by both main videoplayer and familiarization screens.
"""
import streamlit as st
import os


def display_video_rating_interface(
    video_filename,
    video_path,
    config,
    rating_scales,
    key_prefix,
    action_id=None,
    metadata=None,
    header_content=None,
    display_video_func=None
):
    """
    Display the video rating interface with configurable options.

    Parameters:
    - video_filename: Name of the video file to display
    - video_path: Path to the directory containing the video
    - config: Configuration dictionary
    - rating_scales: List of rating scale configurations
    - key_prefix: Prefix for Streamlit widget keys (e.g., 'scale_' or 'famil_scale_')
    - action_id: Optional action ID for metadata lookup (used in main videoplayer)
    - metadata: Optional metadata DataFrame
    - header_content: Optional content to display at the top (e.g., familiarization header)
    - display_video_func: Function to display video (should accept file_path and playback_mode)

    Returns:
    - scale_values: Dictionary of {scale_title: selected_value}
    """
    # Display options from config
    display_metadata = config['settings'].get('display_metadata', True)
    display_pitch = config['settings'].get('display_pitch', True)
    video_playback_mode = config['settings'].get('video_playback_mode', 'loop')

    # Display optional header content (e.g., familiarization info)
    if header_content:
        header_content()

    # Top metadata bar (if enabled and metadata available)
    if display_metadata and metadata is not None and not metadata.empty and action_id:
        row = metadata[metadata['id'] == action_id]
        if not row.empty:
            # Get metadata fields to display from config
            metadata_to_show = config['settings'].get('metadata_to_show', [])

            if metadata_to_show:
                # Create columns dynamically based on number of metadata fields
                cols = st.columns(len(metadata_to_show))

                # Display each metadata field
                for idx, field_config in enumerate(metadata_to_show):
                    label = field_config.get('label', '')
                    column = field_config.get('column', '')

                    # Check if column exists in metadata
                    if column and column in row.columns:
                        with cols[idx]:
                            st.metric(label, row[column].values[0])

        st.markdown("---")

    # Video and pitch visualization area
    if display_pitch and metadata is not None and not metadata.empty and action_id:
        # Show video and pitch side by side
        col_video, col_pitch = st.columns([55, 45])

        with col_video:
            video_file = os.path.join(video_path, video_filename)
            if display_video_func:
                display_video_func(video_file, video_playback_mode)
            else:
                st.video(video_file, autoplay=True, loop=(video_playback_mode == 'loop'))

        with col_pitch:
            # Generate pitch visualization
            row = metadata[metadata['id'] == action_id]
            if not row.empty:
                try:
                    # Lazy imports to avoid binary conflicts on Streamlit Cloud
                    import matplotlib
                    matplotlib.use('Agg')
                    import matplotlib.pyplot as plt
                    import mplsoccer

                    pitch = mplsoccer.Pitch(pitch_type="statsbomb", pitch_color="grass")
                    fig, ax = pitch.draw(figsize=(6, 4))

                    fig.patch.set_facecolor('black')
                    fig.patch.set_alpha(1)

                    # Draw arrow
                    start_x = row.start_x.values[0]
                    start_y = row.start_y.values[0]
                    end_x = row.end_x.values[0]
                    end_y = row.end_y.values[0]

                    pitch.arrows(start_x, start_y, end_x, end_y,
                                ax=ax, color="blue", width=2, headwidth=10, headlength=5)
                    ax.plot(start_x, start_y, 'o', color='blue', markersize=10)

                    fig.tight_layout(pad=0)
                    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

                    st.pyplot(fig)
                    plt.close(fig)
                except ImportError:
                    st.warning("⚠️ Pitch visualization requires mplsoccer package. Please install it to enable this feature.")
                except Exception as e:
                    st.error(f"Failed to generate pitch visualization: {e}")
            else:
                st.info("No metadata available for this video")

    else:
        # Show video and rating scales side by side
        col_video, col_rating_scales = st.columns([50, 50])

        with col_video:
            video_file = os.path.join(video_path, video_filename)
            if display_video_func:
                display_video_func(video_file, video_playback_mode)
            else:
                st.video(video_file, autoplay=True, loop=(video_playback_mode == 'loop'))

        with col_rating_scales:
            # Display rating scales
            scale_values = {}

            for scale_config in rating_scales:
                scale_type = scale_config.get('type', 'discrete')
                title = scale_config.get('title', 'Scale')
                label_low = scale_config.get('label_low', '')
                label_high = scale_config.get('label_high', '')
                required = scale_config.get('required_to_proceed', True)

                # Check if both labels are empty (saves vertical space)
                labels_empty = not label_low and not label_high

                if labels_empty:
                    # Side-by-side layout: title on left, scale on right
                    col_title, col_scale = st.columns([1, 3])

                    with col_title:
                        st.markdown(f"**{title}** {'*(required)*' if required else ''}")

                    with col_scale:
                        # Generate unique key for this scale
                        unique_key = f"{key_prefix}{video_filename}_{title}" if not action_id else f"{key_prefix}{action_id}_{title}"

                        if scale_type == 'discrete':
                            values = scale_config.get('values', [1, 2, 3, 4, 5, 6, 7])
                            selected = st.pills(
                                label=title,
                                options=values,
                                key=unique_key,
                                label_visibility="collapsed",
                                selection_mode="single"
                            )
                            scale_values[title] = selected

                        elif scale_type == 'slider':
                            slider_min = scale_config.get('slider_min', 0)
                            slider_max = scale_config.get('slider_max', 100)
                            initial_state = scale_config.get('initial_state', 'low')

                            # Calculate initial value based on initial_state
                            if initial_state == 'low':
                                initial_value = float(slider_min)
                            elif initial_state == 'high':
                                initial_value = float(slider_max)
                            else:  # 'center' or any other value defaults to center
                                initial_value = float(slider_min + slider_max) / 2

                            selected = st.slider(
                                label=title,
                                min_value=float(slider_min),
                                max_value=float(slider_max),
                                value=initial_value,
                                key=unique_key,
                                label_visibility="collapsed"
                            )
                            scale_values[title] = selected

                        elif scale_type == 'text':
                            selected = st.text_input(
                                label=title,
                                key=unique_key,
                                placeholder="Enter your response...",
                                label_visibility="collapsed"
                            )
                            scale_values[title] = selected if selected else None

                else:
                    # Stacked layout with labels: title on top, labels on sides of scale
                    st.markdown(f"**{title}** {'*(required)*' if required else ''}")

                    col_low, col_scale, col_high = st.columns([1, 3, 1])

                    with col_low:
                        st.markdown(f"*{label_low}*")

                    with col_scale:
                        # Generate unique key for this scale
                        unique_key = f"{key_prefix}{video_filename}_{title}" if not action_id else f"{key_prefix}{action_id}_{title}"

                        if scale_type == 'discrete':
                            values = scale_config.get('values', [1, 2, 3, 4, 5, 6, 7])
                            selected = st.pills(
                                label=title,
                                options=values,
                                key=unique_key,
                                label_visibility="collapsed",
                                selection_mode="single"
                            )
                            scale_values[title] = selected

                        elif scale_type == 'slider':
                            slider_min = scale_config.get('slider_min', 0)
                            slider_max = scale_config.get('slider_max', 100)
                            initial_state = scale_config.get('initial_state', 'low')

                            # Calculate initial value based on initial_state
                            if initial_state == 'low':
                                initial_value = float(slider_min)
                            elif initial_state == 'high':
                                initial_value = float(slider_max)
                            else:  # 'center' or any other value defaults to center
                                initial_value = float(slider_min + slider_max) / 2

                            selected = st.slider(
                                label=title,
                                min_value=float(slider_min),
                                max_value=float(slider_max),
                                value=initial_value,
                                key=unique_key,
                                label_visibility="collapsed"
                            )
                            scale_values[title] = selected

                        elif scale_type == 'text':
                            selected = st.text_input(
                                label=title,
                                key=unique_key,
                                placeholder="Enter your response...",
                                label_visibility="collapsed"
                            )
                            scale_values[title] = selected if selected else None

                    with col_high:
                        st.markdown(f"*{label_high}*")

                st.markdown("")  # Spacing

            return scale_values

    # This shouldn't be reached but return empty dict as fallback
    return {}
