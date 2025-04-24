import streamlit as st
import pandas as pd


# Define global variables for column mappings
COLUMN_MAPPINGS = {
    "first_name": "first_name",
    "last_name": "last_name",
    "email_1": "email",
    "email_2": "secondary_email",
    "address": "address",
    "city": "city",
    "state": "state_abbrev",
    "zip_code": "postal_code",
}


def main():
    st.title('Real Intent to RealScout Converter')

    st.info("""
    Upload a CSV file. The app will convert your Real Intent CSV into a format that can be imported into RealScout.
    """)

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        
        # Check if required columns are in the dataframe
        missing_columns = [col for col in COLUMN_MAPPINGS.keys() if col not in df.columns]
        
        if not missing_columns:
            df = df[list(COLUMN_MAPPINGS.keys())].rename(columns=COLUMN_MAPPINGS)

            # Display the resulting dataframe
            st.write("Converted DataFrame:")
            st.write(df)
            
            # Download the converted dataframe as CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download converted CSV",
                data=csv,
                file_name='converted_file.csv',
                mime='text/csv',
            )
        else:
            st.write(f"The uploaded file does not contain the required columns: {', '.join(missing_columns)}.")


if __name__ == "__main__":
    main()