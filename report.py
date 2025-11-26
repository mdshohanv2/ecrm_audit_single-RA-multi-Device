import streamlit as st
import pandas as pd
import plotly.express as px

# Page setup
st.set_page_config(page_title="Unauthorized Device Analysis", layout="wide")

# Authorized device models
AUTHORIZED_MODELS = ["SM-T295", "Walpad10HProMax"]

# File uploader
uploaded_file = st.file_uploader("Upload XLSX/CSV/JSON file", type=["xlsx", "csv", "json"])

if uploaded_file:
    # Load file
    if uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)
    else:
        st.error("Unsupported file format")
        st.stop()

    # Clean model names
    df['Used Device Model'] = df['Used Device Model'].astype(str).str.strip().str.replace('"', '')

    # Unauthorized & authorized splits
    unauthorized_df = df[~df['Used Device Model'].isin(AUTHORIZED_MODELS)]
    authorized_df = df[df['Used Device Model'].isin(AUTHORIZED_MODELS)]

    # View toggle
    st.subheader("🔍 Select View Mode")
    view_mode = st.radio("Group Data By:", options=["Area", "Region"], horizontal=True)
    group_col = view_mode

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"👤 Unique Unauthorized Users ({view_mode})", unauthorized_df['Username'].nunique())
    col2.metric("💻 Unique Unauthorized Device IDs", unauthorized_df['Used Device Id'].nunique())
    col3.metric("✅ Unique Authorized Devices", authorized_df['Used Device Id'].nunique())
    

    # Unauthorized summary
    unauth_summary = (
        unauthorized_df.groupby(group_col)
        .agg(
            Unique_Unauthorized_Users=('Username', 'nunique'),
            Unique_Unauthorized_Devices=('Used Device Id', 'nunique'),
            Usernames=('Username', lambda x: ', '.join(sorted(set(x))))
        )
        .reset_index()
    )

    # Authorized summary
    auth_summary = (
        authorized_df.groupby(group_col)['Used Device Id']
        .nunique()
        .reset_index()
        .rename(columns={'Used Device Id': 'Unique_Authorized_Devices'})
    )

    # Merge summaries
    summary_df = pd.merge(unauth_summary, auth_summary, on=group_col, how='left').fillna(0)

    # Calculate unauthorized % against authorized
    summary_df['Unauthorized_Percentage'] = (
        summary_df.apply(lambda row: (row['Unique_Unauthorized_Devices'] / row['Unique_Authorized_Devices'] * 100)
                         if row['Unique_Authorized_Devices'] > 0 else 0, axis=1)
        .round(2)
    )

    # Sort by unauthorized Percentage
    summary_df = summary_df.sort_values(by='Unauthorized_Percentage', ascending=True)

    # Label for bars
    summary_df['Label'] = (
        summary_df['Unique_Unauthorized_Users'].astype(int).astype(str) + " Users / "
        "UD: " + summary_df['Unique_Unauthorized_Devices'].astype(int).astype(str) +
        " / AD: " + summary_df['Unique_Authorized_Devices'].astype(int).astype(str) +
        " / UD %: " + summary_df['Unauthorized_Percentage'].astype(str) + "%"
    )

    # Show Table
    st.subheader(f"📍 {view_mode}-wise Device Usage (Table)")
    st.dataframe(summary_df, use_container_width=True)

    # Bar Chart
    st.subheader(f"📊 {view_mode}-wise Unauthorized Users & Devices Percentage")
    fig = px.bar(
        summary_df,
        x="Unique_Unauthorized_Users",
        y=group_col,
        orientation='h',
        color="Unique_Unauthorized_Users",
        color_continuous_scale=["green", "yellow", "red"],
        text="Label"
    )

    fig.update_traces(
        texttemplate='%{text}',
        textposition='outside',
        hoverinfo="skip",
        hovertemplate=None
    )

    fig.update_layout(
        xaxis=dict(
            range=[0, summary_df['Unique_Unauthorized_Users'].max() * 1.43]  # ~70% bar width
        ),
        xaxis_title=f"Number of Unique Unauthorized Users ({view_mode}-wise)",
        yaxis_title=view_mode,
        coloraxis_colorbar_title="Unauthorized Users Count",
        # Make y-axis respect our DataFrame order
        yaxis={'categoryorder': 'array', 'categoryarray': summary_df[group_col]},
        height=50 * len(summary_df) + 200
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Please upload your dataset (XLSX, CSV, or JSON).")