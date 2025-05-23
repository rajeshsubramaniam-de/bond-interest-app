import streamlit as st
import pandas as pd
import altair as alt


st.title("📊 Bond Interest Monthly Tracker")

# Upload multiple Excel files
uploaded_files = st.file_uploader(
    "Upload one or more Excel files", type=["xlsx"], accept_multiple_files=True
)

if uploaded_files:
    all_data = []

    for file in uploaded_files:
        file_name = file.name.lower()

        # Skip first row (bond title), use second row as headers
        df = pd.read_excel(file, header=1)
        df.columns = [col.strip() for col in df.columns]

        if {'IP Date', 'Gross INT', 'TDS', 'NET INT'}.issubset(df.columns):
            df['IP Date'] = pd.to_datetime(df['IP Date'], errors='coerce')
            df = df.dropna(subset=['IP Date'])
            df['Month'] = df['IP Date'].dt.to_period('M').astype(str)

            # Special rule for "navi"
            if 'navi' in file_name:
                df['Gross INT'] *= 10
                df['NET INT'] *= 10
                st.info(f"Applied 10x multiplier for {file.name}")

            df['File Name'] = file.name  # Optional: to track which file
            all_data.append(df)
        else:
            st.warning(f"Missing required columns in {file.name}, skipping.")

    if all_data:
        combined_df = pd.concat(all_data).sort_values(by='IP Date')
        combined_df['Year'] = combined_df['IP Date'].dt.year
        combined_df['Month Number'] = combined_df['IP Date'].dt.month

        # Month selection
        years = sorted(combined_df['Year'].dropna().unique())
        months = list(range(1, 13))
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']

        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox("Select Year", years, index=len(years)-1)
        with col2:
            selected_month = st.selectbox("Select Month", month_names, index=pd.Timestamp.now().month - 1)

        # Filter data
        filtered = combined_df[
            (combined_df['Year'] == selected_year) &
            (combined_df['Month Number'] == month_names.index(selected_month) + 1)
        ]

        st.subheader(f"📅 Transactions for {selected_month} {selected_year}")
        st.dataframe(filtered[['IP Date', 'Gross INT', 'TDS', 'NET INT', 'File Name']])

        # Monthly total
        total = filtered[['Gross INT', 'TDS', 'NET INT']].sum().to_frame(name='Total').T
        st.subheader("🧾 Totals for Selected Month")
        st.dataframe(total)

        # Also show full monthly chart
        monthly_summary = (
            combined_df
            .groupby('Month')[['Gross INT']]
            .sum()
            .reset_index()
            .sort_values(by='Month')
        )

        st.subheader("📈 Overall Monthly Summary")
        # Reshape for grouped bar chart
        monthly_long = monthly_summary.melt(id_vars='Month', var_name='Category', value_name='Amount')

        bar_chart = alt.Chart(monthly_long).mark_bar().encode(
            x=alt.X('Month:N', title='Month', sort=monthly_summary['Month'].tolist()),
            y=alt.Y(
                'Amount:Q',
                title='Amount',
                scale=alt.Scale(domain=[0, 50000]),  # 👈 Set your own Y-axis range
                axis=alt.Axis(values=list(range(0, 50001, 5000)))
            ),
        color='Category:N',
            tooltip=['Month', 'Category', 'Amount']
        ).properties(
            width=700,
            height=400,
            title='Monthly Interest Breakdown (Bar Chart)'
        )

        st.altair_chart(bar_chart, use_container_width=True)
    else:
        st.error("No valid data found in uploaded files.")
