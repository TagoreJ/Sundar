import streamlit as st
import pandas as pd
import pydeck as pdk
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

st.set_page_config(page_title="Dealer Directory", page_icon="📇", layout="wide")

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

    # Sidebar filters and MAP feature (NO city count here)
    with st.sidebar:
        st.header("🔍 Filter")
        company = st.multiselect("Filter by Company", options=sorted(df['Company'].dropna().unique()))
        sector = st.multiselect("Filter by Sector", options=sorted(df['Sector'].dropna().unique()))
        location = st.multiselect("Filter by Location", options=sorted(df['Location'].dropna().unique()))
        show_map = st.checkbox("Show contacts on map", value=True)

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

    filtered_df = filtered_df.reset_index(drop=True)

    # --- MAP FEATURE ---
    if show_map:
        st.subheader("🗺️ Contacts Map (City Counts)")
        # Group by city and count
        city_group = filtered_df.groupby("Location").size().reset_index(name="Count")
        # Geocode cities if lat/lon not present
        if 'Latitude' in filtered_df.columns and 'Longitude' in filtered_df.columns:
            city_group['Latitude'] = filtered_df.groupby("Location")['Latitude'].first().values
            city_group['Longitude'] = filtered_df.groupby("Location")['Longitude'].first().values
        else:
            geolocator = Nominatim(user_agent="dealer-directory")
            geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

            @st.cache_data(show_spinner=True)
            def get_lat_lon(location):
                try:
                    loc = geocode(location)
                    if loc:
                        return loc.latitude, loc.longitude
                except:
                    return None, None
                return None, None

            city_group['Latitude'], city_group['Longitude'] = zip(*city_group['Location'].astype(str).apply(get_lat_lon))

        city_group = city_group.dropna(subset=['Latitude', 'Longitude'])

        # Prepare layers: one for pins, one for text
        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=city_group,
            get_position='[Longitude, Latitude]',
            get_color='[200, 30, 0, 160]',
            get_radius=12000,
            pickable=True,
        )

        text_layer = pdk.Layer(
            "TextLayer",
            data=city_group,
            get_position='[Longitude, Latitude]',
            get_text="Count",
            get_color=[0, 0, 0, 255],
            get_size=24,
            get_alignment_baseline="'bottom'",
        )

        if not city_group.empty:
            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",  # Normal map style
                initial_view_state=pdk.ViewState(
                    latitude=city_group['Latitude'].mean(),
                    longitude=city_group['Longitude'].mean(),
                    zoom=4,
                ),
                layers=[scatter_layer, text_layer],
                tooltip={"text": "{Location}: {Count} contacts"}
            ))
            st.caption("Red pins = cities. Number = contacts in city.")
        else:
            st.info("No valid locations found to display on map.")

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
