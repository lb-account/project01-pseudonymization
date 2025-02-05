import streamlit as st
import os
import shutil
import pandas as pd
import uuid  # For generating unique IDs

# Function to list CSV files in the source directory
def list_csv_files(source_directory):
    if os.path.isdir(source_directory):
        return [f for f in os.listdir(source_directory) if f.endswith('.csv')]
    else:
        st.write("The specified source directory does not exist.")
        return []

# Function to read a CSV file
def read_csv_file(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.write(f"An error occurred while reading the CSV file: {e}")
        return None

# Function to remove selected columns and return modified DataFrame
def remove_columns(df, selected_columns):
    return df.drop(columns=selected_columns)

# Function to tokenize and pseudonymize selected columns (reversible via mapping)
def tokenize_columns(df, columns_to_tokenize, destination_directory):
    # Create an empty dictionary to store mappings for reversibility
    name_map = {}
    
    # Iterate through each column to tokenize
    for column in columns_to_tokenize:
        # Generate a mapping for unique names in the column
        name_map[column] = {name: str(uuid.uuid4())[:8] for name in df[column].unique()}
        
        # Map the names in the column to their generated pseudonyms
        df[column] = df[column].map(name_map[column])
    
    # Rename the columns to "ID" (or other preferred name)
    for column in columns_to_tokenize:
        df = df.rename(columns={column: "ID"})
    
    # Save the pseudonymized dataset to the destination directory
    output_file_path = os.path.join(destination_directory, "pseudonymized_data.csv")
    df.to_csv(output_file_path, index=False)
    
    # Save the mapping securely for reversibility
    mapping_data = []
    for column in columns_to_tokenize:
        column_mapping = pd.DataFrame(list(name_map[column].items()), columns=["Original Name", "Pseudonym"])
        mapping_data.append(column_mapping)
    
    # Combine mappings into one DataFrame
    full_mapping = pd.concat(mapping_data, ignore_index=True)
    mapping_file_path = os.path.join(destination_directory, "name_mapping.csv")
    full_mapping.to_csv(mapping_file_path, index=False)
    
    st.write(f"✅ Pseudonymized data saved to {output_file_path}")
    st.write(f"✅ Name mapping saved to {mapping_file_path}")
    
    return df

# Main function
def main():
    st.title("CSV Column Modifier & Tokenizer")

    # User inputs for directories
    destination_directory = st.text_input("Enter the destination directory path:")
    source_directory = st.text_input("Enter the source directory path:")

    # Initialize session state variables
    if "selected_columns" not in st.session_state:
        st.session_state.selected_columns = []
    
    if "columns" not in st.session_state:
        st.session_state.columns = []

    if "remaining_columns" not in st.session_state:
        st.session_state.remaining_columns = []

    if "df_modified" not in st.session_state:
        st.session_state.df_modified = None

    if "selected_tokenization" not in st.session_state:
        st.session_state.selected_tokenization = []

    selected_file = None

    # Step 3: Select a CSV file
    if source_directory:
        csv_files = list_csv_files(source_directory)
        if csv_files:
            selected_file = st.selectbox("Select a CSV file:", csv_files)

            # Load CSV button
            if st.button("Load CSV"):
                file_path = os.path.join(source_directory, selected_file)
                df = read_csv_file(file_path)
                
                if df is not None:
                    st.session_state.columns = df.columns.tolist()  # Store column names
                    st.session_state.selected_columns = []  # Reset selected columns
                    st.session_state.df_modified = None  # Reset modified DataFrame

            # Display checkboxes if columns are loaded
            if st.session_state.columns:
                st.write("✅ Select the columns to remove:")
                
                for column in st.session_state.columns:
                    checked = column in st.session_state.selected_columns
                    if st.checkbox(column, value=checked, key=f"remove_{column}"):
                        if column not in st.session_state.selected_columns:
                            st.session_state.selected_columns.append(column)
                    else:
                        if column in st.session_state.selected_columns:
                            st.session_state.selected_columns.remove(column)

                # Validate button to process the file
                if st.button("Validate"):
                    if st.session_state.selected_columns:
                        file_path = os.path.join(source_directory, selected_file)
                        df = read_csv_file(file_path)  # Read the CSV again
                        st.session_state.df_modified = remove_columns(df, st.session_state.selected_columns)

                        # Update remaining columns (columns not removed)
                        st.session_state.remaining_columns = [
                            col for col in df.columns if col not in st.session_state.selected_columns
                        ]
                    else:
                        st.write("⚠️ No columns selected to remove.")

            # If we have a modified DataFrame, show tokenization options
            if st.session_state.df_modified is not None:
                st.write("### Select the names you would like to tokenize:")
                
                for column in st.session_state.remaining_columns:
                    checked = column in st.session_state.selected_tokenization
                    if st.checkbox(column, value=checked, key=f"tokenize_{column}"):
                        if column not in st.session_state.selected_tokenization:
                            st.session_state.selected_tokenization.append(column)
                    else:
                        if column in st.session_state.selected_tokenization:
                            st.session_state.selected_tokenization.remove(column)

                # Button to tokenize selected columns
                if st.button("Tokenize Selected Columns"):
                    if st.session_state.selected_tokenization:
                        st.session_state.df_modified = tokenize_columns(
                            st.session_state.df_modified, st.session_state.selected_tokenization, destination_directory
                        )
                    else:
                        st.write("⚠️ No columns selected for tokenization.")

# Run the main function
if __name__ == "__main__":
    main()
