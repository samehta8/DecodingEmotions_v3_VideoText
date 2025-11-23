"""
Login page - Check if user has participated before.
"""
import streamlit as st
from utils.data_persistence import user_exists

def show():
    """Display the login screen."""
    st.title("🔐 Login")

    st.markdown("### Have you participated in this study before?")

    # Radio button for Yes/No
    participated = st.radio(
        "Select one:",
        options=["No, this is my first time", "Yes, I have participated before"],
        key="participated_radio",
        label_visibility="collapsed"
    )

    st.markdown("")  # Spacing

    # If user selected "Yes", show user ID input
    if participated == "Yes, I have participated before":
        st.markdown("### Please enter your User ID")

        user_id_input = st.text_input(
            "User ID:",
            key="user_id_input",
            placeholder="Enter your user ID (e.g., ABCD12 or giha3042)",
            help="Your user ID was shown to you after completing the questionnaire"
        ).strip()

        # Check if user ID exists
        if user_id_input:
            if user_exists(user_id_input):
                st.success(f"✓ User ID '{user_id_input}' found!")
                st.session_state.user_id_valid = True
                # Store the user ID as entered (preserve original case)
                st.session_state.validated_user_id = user_id_input
            else:
                st.error("⚠️ User ID not found. Please check your ID or select 'No' if this is your first time.")
                st.info("💡 If you cannot remember your user ID, please reach out to the study administration.")
                st.session_state.user_id_valid = False
        else:
            st.session_state.user_id_valid = False

    # Navigation buttons
    st.markdown("")
    st.markdown("")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("◀️ Back", use_container_width=True):
            st.session_state.page = 'welcome'
            st.rerun()

    with col3:
        if st.button("Next ▶️", use_container_width=True, type="primary"):
            # Validation
            if participated == "Yes, I have participated before":
                if not user_id_input:
                    st.error("Please enter your user ID")
                    st.info("💡 If you cannot remember your user ID, please reach out to the study administration.")
                    st.stop()
                elif not st.session_state.get('user_id_valid', False):
                    st.error("User ID not found. Please check your ID.")
                    st.info("💡 If you cannot remember your user ID, please reach out to the study administration.")
                    st.stop()
                else:
                    # Valid returning user - use the validated ID with original case
                    st.session_state.user.user_id = st.session_state.get('validated_user_id', user_id_input)

                    # Check if familiarization is enabled
                    config = st.session_state.config
                    enable_familiarization = config.get('settings', {}).get('enable_familiarization', True)

                    if enable_familiarization:
                        st.session_state.page = 'pre_familiarization'
                    else:
                        st.session_state.page = 'videoplayer'

                    st.rerun()
            else:
                # New user - go to questionnaire
                st.session_state.page = 'questionnaire'
                st.rerun()
