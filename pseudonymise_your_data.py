import streamlit as st
import os
import pandas as pd
import uuid  # For generating unique IDs
import time

# Initialize session state variables
def initialize():

    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame()

    if "load_csv" not in st.session_state: #'Load CSV' button state
        st.session_state.load_csv = False

    if "columns" not in st.session_state: # Columns from our dataset
       st.session_state.columns = {}
    
    if "select_all" not in st.session_state: # 'Select all' checkbox
        st.session_state.select_all = False
    
    if "validate_PII_to_delete" not in st.session_state: #'Validate' button state (when selecting PII)
       st.session_state.validate_PII_to_delete = False
    
    if "selected_columns" not in st.session_state: #  Selected columns with checkboxes
       st.session_state.selected_columns = []
    
    if "name_column" not in st.session_state: # Selected column with radio buttons
       st.session_state.name_column = ''

    if "tokenize" not in st.session_state: #'Tokenize' button state (when selecting name column)
       st.session_state.tokenize = False

# Read the CSV file selected and load data
@st.cache_data
def load_data(file_path):
    try:
        st.session_state.df = pd.read_csv(file_path)
    except Exception as e:
        st.write(f"An error occurred while reading the CSV file: {e}")

# Function to list CSV files in the source directory
def list_csv_files(source_directory):
    if os.path.isdir(source_directory):
        return [f for f in os.listdir(source_directory) if f.endswith('.csv')]
    else:
        st.write("The specified source directory does not exist.")
        return []
    
# Function to toggle 'Select All'
def toggle_select_all():
    select_all_state = st.session_state.select_all
    for key in st.session_state.columns:
        st.session_state.columns[key] = select_all_state
    
# Function to lock answers after selecting PII to delete
def validate():
    # Check if at least one checkbox is selected
    if not any(st.session_state.columns.values()):
        st.error("⚠️ You must select at least one choice")
    else:
        st.session_state.validate_PII_to_delete = True        
        #We keep the unticked columns names
        st.session_state.selected_columns = [key for key, value in st.session_state.columns.items() if not value]
        st.success("✅ Your columns have been saved successfully")
        time.sleep(2)
        st.rerun()  # Force UI update

# Function to remove selected columns and return modified DataFrame
def remove_columns(df, selected_columns):
    return df.drop(columns=selected_columns)

# Function to tokenize and pseudonymize selected columns (reversible via mapping)
def tokenize(df, column_to_tokenize, destination_directory):
    #Create a dataframe with the selected columns
    df_wihout_PII = df[st.session_state.selected_columns]

    # Generate a mapping for unique names in the column
    name_map = {name: str(uuid.uuid4())[:8] for name in df_wihout_PII[column_to_tokenize].unique()}
        
    # Map the names in the column to their generated pseudonyms
    df_wihout_PII[column_to_tokenize] = df_wihout_PII[column_to_tokenize].map(name_map)    

    # Rename the columns to "ID" 
    df_wihout_PII = df_wihout_PII.rename(columns={column_to_tokenize: "ID"})
    
    st.write("Overview of your pseudonymised dataset")
    st.dataframe(df_wihout_PII.head(4))

    # Save the pseudonymized dataset to the destination directory
    output_file_path = os.path.join(destination_directory, "pseudonymized_data.csv")
    df_wihout_PII.to_csv(output_file_path, index=False)
    st.write(f"✅ Pseudonymized data saved to {output_file_path}")
    
    # Save the mapping securely for reversibility
    column_mapping = pd.DataFrame(list(name_map.items()), columns=["Original Name", "Pseudonym"])

    mapping_file_path = os.path.join(destination_directory, "name_mapping.csv")
    column_mapping.to_csv(mapping_file_path, index=False)
    st.write(f"✅ Name mapping saved to {mapping_file_path}")
    
# Main function
def main():

    header = st.container()
    body_load_csv = st.container()
    body_checkboxes = st.container()
    body_radio_buttons = st.container()
    body_result = st.container()

    with header:
        st.title("Pseudonymize your data")
        st.text("This project aims to pseudonymize data from a CSV file using a user interface built with the Streamlit library")

    # Initialize session state variables
    initialize()

    with body_load_csv:
        # User inputs for directories
        destination_directory = st.text_input("Enter the directory path where you would like to save your data:", 
                                              disabled=st.session_state.load_csv)
        source_directory = st.text_input("Enter the source directory path:", 
                                         disabled=st.session_state.load_csv)
        
        if source_directory:
            csv_files = list_csv_files(source_directory)
            if csv_files:
                selected_file = st.selectbox("Select a CSV file:", csv_files)
                file_path = os.path.join(source_directory, selected_file)
                load_data(file_path)
                # NOT OK BECAUSE I CREATED A COPY FROM THE GLOBAL VARIABLE
                #df = read_csv_file(file_path)

                # Button action
                if st.button("Load CSV", disabled=st.session_state.load_csv):
                    if not destination_directory or not source_directory:
                        st.error("⚠️ Please enter both source and destination paths. ")
                    else:
                        #if df is not None:
                        if st.session_state.df is not None:
                            st.session_state.columns = {col: False for col in st.session_state.df.columns.tolist()}  # Store column names as keys and set the values to False
                            st.session_state.load_csv = True # Disable inputs 
                            st.success("✅ Submission successful! Inputs are now locked.")
                            time.sleep(2)
                            st.rerun()  # Force UI update
                        else:
                            st.error("⚠️ dataframe is non-existent (null)")
                        
    with body_checkboxes:                  
        # Display checkboxes if columns are loaded
        if st.session_state.columns:                
            st.write("Select the PII you would like to remove (do not select Name yet):")

            # 'Select All' checkbox
            st.checkbox("Select All", key="select_all", disabled=st.session_state.validate_PII_to_delete, on_change=toggle_select_all)

            # Select checkboxes
            for key in st.session_state.columns.keys():
                st.session_state.columns[key] = st.checkbox(key, value=st.session_state.columns[key], 
                                                key=key, disabled=st.session_state.validate_PII_to_delete)
                            
            if st.button("Validate", disabled=st.session_state.validate_PII_to_delete) and not st.session_state.validate_PII_to_delete:
                validate()
    
    with body_radio_buttons:
        # Display the selected columns for TESTING
        st.write(f"Selected columns: {st.session_state.selected_columns}")

        # Display radio buttons if columns are loaded
        if st.session_state.selected_columns:
            st.write("Select the names column you would like to tokenize:")

            #Select with a radio button
            st.session_state.name_column = st.radio(label = '',options=st.session_state.selected_columns, disabled=st.session_state.tokenize)

            # Display the selected column for TESTING
            st.write(f"Selected column: {st.session_state.name_column}")
            
            # Button action
            if st.button("Tokenize", disabled=st.session_state.tokenize) and not st.session_state.tokenize:
                st.session_state.tokenize = True
                st.success("✅ Your name column has been saved successfully")
                time.sleep(2)
                st.rerun()  # Force UI update
    
    with body_result:
        if st.session_state.name_column and st.session_state.tokenize == True:
            tokenize(st.session_state.df, st.session_state.name_column, destination_directory)


# Run the main function
if __name__ == "__main__":
    main()