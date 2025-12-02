"""
Consent page - Participant information and consent form.
"""
import streamlit as st
import os

def show():
    """Display the consent screen."""
    st.title("📋 Participant Information and Consent")

    st.markdown("---")

    # Get consent PDF path from config
    config = st.session_state.config
    consent_pdf_path = config.get('paths', {}).get('consent_pdf_path', None)

    # Download button for consent PDF
    if consent_pdf_path and os.path.exists(consent_pdf_path):
        st.markdown("""
        **All information about this study is contained in the participant information document.**

        Please download and read the document carefully before providing your consent below.
        """)

        st.markdown("")  # Spacing

        # Read PDF file and create download button
        with open(consent_pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.download_button(
                label="📄 View Consent Form Details",
                data=pdf_bytes,
                file_name="participant_information.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
    else:
        st.warning("⚠️ Participant information document is not available. Please contact the study administration.")
        if consent_pdf_path:
            st.info(f"Expected path: {consent_pdf_path}")

    st.markdown("---")

    # Consent Section
    st.markdown("## Consent Declaration")

    # Consent checkbox
    consent_given = st.checkbox(
        "**I confirm that**",
        key="consent_checkbox"
    )

    st.markdown("""

                1. I have read and understood the participant information above
                2. I consent to participate in this research study voluntarily
                3. I consent to the processing of my data anonymously for research purposes
                4. I consent to being contacted via email for potential follow-up questions
                5. I am at least 18 years old
                """)
    
    st.markdown("")
    st.markdown("")

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("◀️ Back", use_container_width=True):
            st.session_state.page = 'login'
            st.rerun()

    with col3:
        if st.button("Next ▶️", use_container_width=True, type="primary"):
            if not consent_given:
                st.error("⚠️ You must provide your consent to proceed with the study.")
                st.stop()
            else:
                # Store consent in session state with timestamp
                from datetime import datetime
                st.session_state.consent_given = True
                st.session_state.consent_timestamp = datetime.now().isoformat(timespec='seconds')
                st.session_state.page = 'questionnaire'
                st.rerun()
