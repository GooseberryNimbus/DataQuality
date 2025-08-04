import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, inspect
import os

st.set_page_config(page_title="Data Quality Dashboard", layout="wide")
st.title("📊 Data Quality Dashboard")

# --- Step 1: Data Source Selection ---
st.sidebar.header("🔌 Select Data Source")
source = st.sidebar.radio("Choose data input method:", ["📂 Excel File", "🗃️ Database"])

df = None  # will hold the loaded data

# --- Step 2: Load Data ---
if source == "📂 Excel File":
    uploaded_file = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)

elif source == "🗃️ Database":
    db_url = st.sidebar.text_input("Enter DB Connection String", value="sqlite:///cleaned_data.db", help="e.g. sqlite:///mydb.db or postgresql://user:pass@host:port/dbname")

    if db_url:
        try:
            engine = create_engine(db_url)
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            if tables:
                selected_table = st.sidebar.selectbox("Select a table", tables)
                if selected_table:
                    df = pd.read_sql_table(selected_table, con=engine)
        except Exception as e:
            st.sidebar.error(f"Failed to connect: {e}")

# --- Step 3: Data Quality Dashboard ---
if df is not None:
    df_original = df.copy()

    # Store original null metrics
    original_total_nulls = int(df.isnull().sum().sum())
    original_null_rows = df[df.isnull().any(axis=1)]
    original_null_row_count = len(original_null_rows)

    st.subheader("1. Data Summary")

    # Show reactive nulls
    null_rows = df[df.isnull().any(axis=1)]
    edited_df = st.data_editor(
        null_rows,
        use_container_width=True,
        key="editable_table"
    )

    current_total_nulls = int(edited_df.isnull().sum().sum())
    current_null_row_count = len(edited_df[edited_df.isnull().any(axis=1)])

    col1, col2 = st.columns(2)
    with col1:
        st.metric("🔍 Total Null Values", f"{current_total_nulls} / {original_total_nulls}")
    with col2:
        st.metric("🧾 Rows Containing Nulls", f"{current_null_row_count} / {original_null_row_count}")

    # Update full dataset with changes
    updated_df = df.copy()
    for idx in edited_df.index:
        updated_df.loc[idx] = edited_df.loc[idx]
        updated_df.loc[idx, "timestamp_updated"] = datetime.now()

    st.subheader("2. Save Cleaned Data")

    col3, col4 = st.columns(2)

    with col3:
        if st.button("💾 Save to Excel"):
            output_filename = "cleaned_data.xlsx"
            updated_df.to_excel(output_filename, index=False)
            with open(output_filename, "rb") as f:
                st.download_button("📥 Download Updated Excel", f, file_name=output_filename)
            st.success("Excel saved.")
            os.remove(output_filename)

    with col4:
        if st.button("🗃️ Upload to Database"):
            if source == "🗃️ Database":
                try:
                    updated_df.to_sql(selected_table, con=engine, if_exists='replace', index=False)
                    st.success(f"✅ Data updated in DB table `{selected_table}`")
                except Exception as e:
                    st.error(f"❌ Failed to upload to DB: {e}")
            else:
                try:
                    engine = create_engine("sqlite:///cleaned_data.db")
                    updated_df.to_sql("cleaned_data", con=engine, if_exists='replace', index=False)
                    st.success("✅ Data uploaded to local SQLite database.")
                except Exception as e:
                    st.error(f"❌ Failed to upload to SQLite: {e}")

else:
    st.info("Please select a data source and load data to begin.")
