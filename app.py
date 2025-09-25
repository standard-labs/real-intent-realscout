import streamlit as st
import pandas as pd


# Define global variables for column mappings
COLUMN_MAPPINGS = {
    "first_name": "first_name",
    "last_name": "last_name",
    "phone_1": "phone_number",
    "email_1": "email",
    "email_2": "secondary_email",
    "address": "street_address",
    "city": "city",
    "state": "state_abbrev",
    "zip_code": "postal_code",
}


def process_single_file(uploaded_file, tags=None):
    """Process a single CSV file and return the converted DataFrame."""
    df = pd.read_csv(uploaded_file)

    # Check if required columns are in the dataframe
    missing_columns = [col for col in COLUMN_MAPPINGS.keys() if col not in df.columns]

    if missing_columns:
        return None, missing_columns

    # Filter and rename columns
    df_filtered = df[list(COLUMN_MAPPINGS.keys())].rename(columns=COLUMN_MAPPINGS)

    # Add insight as note if available
    if 'insight' in df.columns:
        df_filtered['note'] = df['insight'].apply(lambda x: f"{x}" if pd.notna(x) else "")
    else:
        df_filtered['note'] = ""

    # Add source
    df_filtered['source'] = 'realintent'

    # Add tags
    if tags:
        df_filtered['tags'] = tags
    else:
        df_filtered['tags'] = None

    return df_filtered, None


def main():
    st.title('Real Intent to RealScout Converter')

    st.info("""
    Upload one or multiple CSV files. The app will convert your Real Intent CSV(s) into a single format that can be imported into RealScout.
    If you upload multiple files, they will be concatenated together.
    """)

    # Allow multiple file uploads
    uploaded_files = st.file_uploader(
        "Choose CSV file(s)",
        type="csv",
        accept_multiple_files=True,
        help="You can select multiple files to concatenate them together"
    )

    tags = st.text_input("(Optional) Tags", placeholder="Enter tags to apply to all contacts...")

    if uploaded_files:
        all_dataframes = []
        file_info = []
        errors = []

        # Process each uploaded file
        for i, uploaded_file in enumerate(uploaded_files):
            st.write(f"Processing file {i+1}: {uploaded_file.name}")

            df_converted, missing_columns = process_single_file(uploaded_file, tags)

            if df_converted is not None:
                all_dataframes.append(df_converted)
                file_info.append({
                    'filename': uploaded_file.name,
                    'rows': len(df_converted),
                    'status': 'Success'
                })
                st.success(f"✅ {uploaded_file.name}: {len(df_converted)} contacts processed")
            else:
                error_msg = f"❌ {uploaded_file.name}: Missing required columns: {', '.join(missing_columns)}"
                errors.append(error_msg)
                st.error(error_msg)
                file_info.append({
                    'filename': uploaded_file.name,
                    'rows': 0,
                    'status': f'Error: Missing columns {missing_columns}'
                })

        # If we have successfully processed files, concatenate them
        if all_dataframes:
            # Concatenate all dataframes
            final_df = pd.concat(all_dataframes, ignore_index=True)

            # Remove duplicates based on email (primary identifier)
            initial_count = len(final_df)
            final_df = final_df.drop_duplicates(subset=['email'], keep='first')
            final_count = len(final_df)
            duplicates_removed = initial_count - final_count

            # Display summary
            st.write("## Processing Summary")
            summary_df = pd.DataFrame(file_info)
            st.dataframe(summary_df, use_container_width=True)

            if duplicates_removed > 0:
                st.warning(f"Removed {duplicates_removed} duplicate contacts based on email address")

            st.write(f"## Final Result: {final_count} unique contacts")

            # Display the resulting dataframe
            st.write("### Preview of Converted Data:")
            st.dataframe(final_df.head(10), use_container_width=True)

            if len(final_df) > 10:
                st.info(f"Showing first 10 rows. Total rows: {len(final_df)}")

            # Download the converted dataframe as CSV
            csv = final_df.to_csv(index=False).encode('utf-8')

            # Generate filename based on number of files processed
            if len(uploaded_files) == 1:
                download_filename = f"realscout_import_{uploaded_files[0].name.replace('.csv', '')}.csv"
            else:
                download_filename = f"realscout_import_combined_{len(uploaded_files)}_files.csv"

            st.download_button(
                label=f"📥 Download Combined CSV ({final_count} contacts)",
                data=csv,
                file_name=download_filename,
                mime='text/csv',
            )
        else:
            st.error("No files were successfully processed. Please check that your CSV files contain the required columns.")
            st.write("### Required columns:")
            for real_intent_col, realscout_col in COLUMN_MAPPINGS.items():
                st.write(f"- `{real_intent_col}` → `{realscout_col}`")


if __name__ == "__main__":
    main()
