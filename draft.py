import streamlit as st

# Initialize session state
if "validated" not in st.session_state:
    st.session_state.validated = False
if "select_all" not in st.session_state:
    st.session_state.select_all = False
if "options" not in st.session_state:
    st.session_state.options = {"3": False, "4": False, "5": False}
if "error" not in st.session_state:
    st.session_state.error = False  # Tracks if an error should be displayed

# Function to validate (lock answers)
def validate():
    # Check if at least one checkbox is selected
    if not any(st.session_state.options.values()):
        st.session_state.error = True  # Trigger error message
    else:
        st.session_state.validated = True
        st.session_state.error = False  # Reset error
        st.rerun()  # Force UI update

# Function to toggle 'Select All'
def toggle_select_all():
    select_all_state = st.session_state.select_all
    for key in st.session_state.options:
        st.session_state.options[key] = select_all_state

# Display question
st.write("What is 2 + 2?")

# 'Select All' checkbox
st.checkbox("Select All", key="select_all", disabled=st.session_state.validated, on_change=toggle_select_all)

# Answer checkboxes
for key in st.session_state.options.keys():
    st.session_state.options[key] = st.checkbox(key, value=st.session_state.options[key], 
                                                key=key, disabled=st.session_state.validated)

# Validate button
if st.button("Validate") and not st.session_state.validated:
    validate()

# Show error message if no checkbox is selected
if st.session_state.error:
    st.error("⚠️ You must select at least one choice")
