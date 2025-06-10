import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dealer Directory", page_icon="📇", layout="wide")

# Font Awesome for icons
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    .card:hover {
        transform: translateY(-5px);
        box-shadow:0 8px 24px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
    }
    .card {
        transition: all 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

DEFAULT_AVATAR = "https://www.w3schools.com/howto/img_avatar.png"

st.title("📇 Dealer Directory")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet = st.radio("Select Dealer Type", options=xls.sheet_names, horizontal=True)
    df = pd.read_excel(uploaded_file, sheet_name=sheet)
    df.columns = df.columns.str.strip()

    if 'Photo' not in df.columns:
        df['Photo'] = None

    # Name search with suggestions
    all_names = df['Name'].dropna().astype(str).unique().tolist()
    search_name = st.selectbox("Search by Name (with suggestions)", [""] + all_names)

    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filter")
        company = st.multiselect("Filter by Company", options=sorted(df['Company'].dropna().unique()))
        sector = st.multiselect("Filter by Sector", options=sorted(df['Sector'].dropna().unique()))
        location = st.multiselect("Filter by Location", options=sorted(df['Location'].dropna().unique()))

    # Filtering
    filtered_df = df.copy()
    if search_name:
        filtered_df = filtered_df[filtered_df['Name'].astype(str) == search_name]
    if company:
        filtered_df = filtered_df[filtered_df['Company'].isin(company)]
    if sector:
        filtered_df = filtered_df[filtered_df['Sector'].isin(sector)]
    if location:
        filtered_df = filtered_df[filtered_df['Location'].isin(location)]

    # Reset index to avoid out-of-bounds errors
    filtered_df = filtered_df.reset_index(drop=True)

    st.markdown("### Dealers")
    cols = st.columns(3)

    for idx, row in filtered_df.iterrows():
        with cols[idx % 3]:
            avatar_url = row['Photo'] if pd.notnull(row['Photo']) and str(row['Photo']).strip() else DEFAULT_AVATAR
            name_str = str(row['Name']) if pd.notnull(row['Name']) else "Unknown"
            position_str = str(row['Position']) if pd.notnull(row['Position']) else ""
            company_str = str(row['Company']) if pd.notnull(row['Company']) else ""
            location_str = str(row['Location']) if pd.notnull(row['Location']) else ""
            sector_str = str(row['Sector']) if pd.notnull(row['Sector']) else ""
            email_str = str(row['Email Address']) if pd.notnull(row['Email Address']) else ""
            phone_str = str(row['Phone Number']) if pd.notnull(row['Phone Number']) else ""
            linkedin_str = str(row['Linkedin Link']) if pd.notnull(row['Linkedin Link']) else "#"

            st.markdown(
                f"""
                <div class="card" style="
                    background-color:#fff;
                    border-radius:16px;
                    box-shadow:0 4px 16px rgba(0,0,0,0.10);
                    padding:24px 18px;
                    margin-bottom:24px;
                    text-align:center;
                    border:1px solid #e7e7e7;
                    min-height:420px;
                    display:flex;
                    flex-direction:column;
                    justify-content:space-between;
                ">
                    <div style="display:flex;justify-content:center;">
                        <img src="{avatar_url}" alt="Avatar"
                            style="width:90px;height:90px;border-radius:50%;margin-bottom:12px;border:2px solid #e7e7e7;object-fit:cover;">
                    </div>
                    <div style="margin-bottom:8px;">
                        <span style="font-size:1.3rem;font-weight:700;color:#111;">{name_str}</span>
                    </div>
                    <div style="color:#222;font-size:1.05rem;font-weight:500;margin-bottom:6px;">{position_str}</div>
                    <hr style="margin:10px 0 12px 0; border:0; border-top:1px solid #eee;">
                    <div style="color:#111;font-size:1rem;text-align:left;">
                        <b>Company:</b> {company_str}<br>
                        <b>Location:</b> {location_str}<br>
                        <b>Sector:</b> {sector_str}<br>
                        <div style="margin-top:12px; display:flex; gap:18px; justify-content:center;">
                            <a href="mailto:{email_str}" style="color:#111;font-size:1.5rem;" title="Email">
                                <i class="fas fa-envelope"></i>
                            </a>
                            <a href="{linkedin_str}" target="_blank" style="color:#111;font-size:1.5rem;" title="LinkedIn">
                                <i class="fab fa-linkedin"></i>
                            </a>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
else:
    st.info("Please upload an Excel file with 'final' and 'potential' sheets.")
