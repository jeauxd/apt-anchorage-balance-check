import streamlit as st
import pandas as pd
import io
from datetime import datetime

# Streamlit app title
st.title("CSV File Comparison Tool")

# Date input for analysis
analysis_date = st.date_input("Select Analysis Date", value=datetime(2025, 4, 30))

# File uploaders for two CSV files
bitwave_file = st.file_uploader("Upload Bitwave Balance File", type="csv")
anchorage_file = st.file_uploader("Upload Anchorage Balance Statement", type="csv")

# Process files if both are uploaded
if bitwave_file and anchorage_file:
    # Read the uploaded CSV files
    df_bitwave = pd.read_csv(bitwave_file)
    df_anchorage = pd.read_csv(anchorage_file)
    
    # Validate required columns in Bitwave file
    if 'Qty' not in df_bitwave.columns or 'Inventory' not in df_bitwave.columns:
        st.error("Bitwave Balance File must contain 'Qty' and 'Inventory' columns.")
    # Validate required columns in Anchorage file
    elif 'Date' not in df_anchorage.columns or 'Wallet Name' not in df_anchorage.columns or 'Quantity' not in df_anchorage.columns:
        st.error("Anchorage Balance Statement must contain 'Date', 'Wallet Name', and 'Quantity' columns.")
    else:
        # Clean and prepare Bitwave data
        bitwave_data = df_bitwave[['Qty', 'Inventory']].copy()
        bitwave_data['Qty'] = pd.to_numeric(bitwave_data['Qty'], errors='coerce')
        bitwave_data = bitwave_data.dropna(subset=['Qty', 'Inventory'])
        bitwave_data = bitwave_data[bitwave_data['Qty'] != 0]  # Remove zero quantities
        
        # Extract wallet number from Inventory and create standardized wallet name
        bitwave_data['Wallet_Number'] = bitwave_data['Inventory'].str.extract(r'(\d+)$')
        bitwave_data = bitwave_data.dropna(subset=['Wallet_Number'])
        bitwave_data['Wallet_Name'] = 'Wallet ' + bitwave_data['Wallet_Number']
        
        # Group by wallet number and sum quantities for Bitwave
        bitwave_grouped = bitwave_data.groupby('Wallet_Name', as_index=False)['Qty'].sum()
        bitwave_grouped = bitwave_grouped.rename(columns={'Qty': 'Bitwave_Balance'})
        
        # Clean and prepare Anchorage data
        anchorage_data = df_anchorage[['Date', 'Wallet Name', 'Quantity']].copy()
        anchorage_data['Date'] = pd.to_datetime(anchorage_data['Date'], errors='coerce')
        anchorage_data['Quantity'] = pd.to_numeric(anchorage_data['Quantity'], errors='coerce')
        anchorage_data = anchorage_data.dropna(subset=['Date', 'Wallet Name', 'Quantity'])
        
        # Filter Anchorage data for the selected analysis date
        anchorage_data = anchorage_data[anchorage_data['Date'] == pd.to_datetime(analysis_date)]
        
        # Extract wallet number from Wallet Name for partial matching
        anchorage_data['Wallet_Number'] = anchorage_data['Wallet Name'].str.extract(r'(\d+)$')
        anchorage_data = anchorage_data.dropna(subset=['Wallet_Number'])
        anchorage_data['Wallet_Name'] = 'Wallet ' + anchorage_data['Wallet_Number']
        
        # Group by wallet name and sum quantities for Anchorage
        anchorage_grouped = anchorage_data.groupby('Wallet_Name', as_index=False)['Quantity'].sum()
        anchorage_grouped = anchorage_grouped.rename(columns={'Quantity': 'Anchorage_Balance'})
        
        # Merge Bitwave and Anchorage data on standardized wallet name
        output_df = bitwave_grouped.merge(
            anchorage_grouped,
            how='left',  # Use left join to keep all Bitwave wallets
            on='Wallet_Name'
        )
        
        # For wallets with no match in Anchorage, set Anchorage_Balance and Difference to "N/A"
        output_df['Anchorage_Balance'] = output_df['Anchorage_Balance'].fillna('N/A')
        output_df['Difference'] = output_df.apply(
            lambda row: row['Anchorage_Balance'] - row['Bitwave_Balance'] 
            if row['Anchorage_Balance'] != 'N/A' else 'N/A',
            axis=1
        )
        
        # Sort by wallet name for consistency
        output_df = output_df.sort_values(by='Wallet_Name')
        
        # Select and order columns for output
        output_df = output_df[['Wallet_Name', 'Bitwave_Balance', 'Anchorage_Balance', 'Difference']]
        
        # Display the result
        st.write(f"Comparison Results as of {analysis_date}:")
        st.dataframe(output_df)
        
        # Convert the output to CSV and provide download button
        if not output_df.empty:
            csv = output_df.to_csv(index=False)
            st.download_button(
                label="Download Comparison Results",
                data=csv,
                file_name=f"comparison_results_{analysis_date.strftime('%Y-%m-%d')}.csv",
                mime="text/csv"
            )
else:
    st.write("Please upload both CSV files to proceed.")
