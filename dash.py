import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import networkx as nx
from traceback import format_exc

st.set_page_config(page_title="Dealer Directory", page_icon="📇", layout="wide")

DEFAULT_AVATAR = "https://www.w3schools.com/howto/img_avatar.png"

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def safe_display(val):
    return "-" if val is None or str(val).strip() == "" else str(val)

def contact_card(row):
    avatar_url = safe_display(row['Photo']) if safe_display(row['Photo']) != "-" else DEFAULT_AVATAR
    name = safe_display(row['Name'])
    position = safe_display(row['Position'])
    company = safe_display(row['Company'])
    location = safe_display(row['Location'])
    place = safe_display(row['Place'])
    sector = safe_display(row['Sector'])
    email = safe_display(row['Email Address'])
    phone = safe_display(row['Phone Number'])
    linkedin = safe_display(row['Linkedin Link'])

    st.markdown(
        f"""
        <div style="background:#fff; border-radius:16px; box-shadow:0 4px 16px rgba(0,0,0,0.1);
        padding:20px; min-height:430px; max-height:430px; display:flex; flex-direction:column; justify-content:space-between; text-align:center;">
            <img src="{avatar_url}" alt="Avatar" style="width:90px; height:90px; border-radius:50%; margin-bottom:12px; border:2px solid #e7e7e7; object-fit:cover; display:block; margin-left:auto; margin-right:auto;">
            <div style="margin-bottom:0;">
                <h4 style="color:#111; margin:0;">{name}</h4>
                <p style="color:#666; margin:0;">{position}</p>
            </div>
            <hr style="border:none; border-top:1px solid #eee; margin:10px 0;">
            <div style="color:#111; font-size:14px; text-align:left;">
                <b>Company:</b> {company}<br>
                <b>Location:</b> {location}<br>
                <b>Place:</b> {place}<br>
                <b>Sector:</b> {sector}<br>
                <b>Email:</b> {email}<br>
                <b>Phone:</b> {phone}<br>
                <b>LinkedIn:</b> {linkedin}<br>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

def show_cards(df):
    n = len(df)
    rows = n // 3 + int(n % 3 > 0)
    for i in range(rows):
        cols = st.columns(3)
        for j in range(3):
            idx = i * 3 + j
            if idx < n:
                with cols[j]:
                    contact_card(df.iloc[idx])

def main():
    st.title("📇 Dealer Directory")

    try:
        uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
        if not uploaded_file:
            st.info("Please upload an Excel file to continue.")
            return

        with st.spinner("Reading file..."):
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            selected_sheet = st.radio("Select Dealer Type", options=["All"] + sheet_names, horizontal=True)

            # Load data
            if selected_sheet == "All":
                df_list = []
                for sheet in sheet_names:
                    sheet_df = pd.read_excel(xls, sheet_name=sheet)
                    sheet_df.columns = sheet_df.columns.str.strip()
                    df_list.append(sheet_df)
                df = pd.concat(df_list, ignore_index=True)
            else:
                df = pd.read_excel(xls, sheet_name=selected_sheet)
                df.columns = df.columns.str.strip()

            # Ensure expected columns exist or add defaults
            expected_cols = ['Name', 'Company', 'Location', 'Place', 'Latitude', 'Longitude',
                             'Email Address', 'Linkedin Link', 'Phone Number', 'Position', 'Sector', 'Photo']
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = None

        # Sidebar filters
        st.sidebar.header("Filters & Route Planner")

        # Search by name
        all_names = [""] + sorted(df['Name'].dropna().astype(str).unique().tolist())
        search_name = st.sidebar.selectbox("Search by Name", options=all_names)

        # Filters
        company_filter = st.sidebar.multiselect("Filter by Company", options=sorted(df['Company'].dropna().unique()))
        sector_filter = st.sidebar.multiselect("Filter by Sector", options=sorted(df['Sector'].dropna().unique()))
        position_filter = st.sidebar.multiselect("Filter by Position", options=sorted(df['Position'].dropna().unique()))
        location_filter = st.sidebar.multiselect("Filter by Location (City/State)", options=sorted(df['Location'].dropna().unique()))

        # Route Planner controls
        st.sidebar.markdown("---")
        st.sidebar.subheader("Optimal Route Planner")
        route_location = st.sidebar.selectbox("Select Location for Route", options=[""] + sorted(df['Location'].dropna().unique()))
        route_places = []
        if route_location:
            route_places = st.sidebar.multiselect("Select Places to Visit",
                options=sorted(df[df['Location'] == route_location]['Place'].dropna().unique()))
        calc_route = False
        if route_location and route_places:
            calc_route = st.sidebar.checkbox("Calculate Route")

        # Always define filtered_df before any early return or stop!
        with st.spinner("Filtering contacts..."):
            filtered_df = df.copy()
            if search_name and search_name != "":
                filtered_df = filtered_df[filtered_df['Name'].astype(str).str.contains(search_name, case=False, na=False)]
            if company_filter:
                filtered_df = filtered_df[filtered_df['Company'].isin(company_filter)]
            if sector_filter:
                filtered_df = filtered_df[filtered_df['Sector'].isin(sector_filter)]
            if position_filter:
                filtered_df = filtered_df[filtered_df['Position'].isin(position_filter)]
            if location_filter:
                filtered_df = filtered_df[filtered_df['Location'].isin(location_filter)]
            filtered_df = filtered_df.reset_index(drop=True)

        # --------- Optimal Route Planner Output ---------
        if route_location and not route_places and not calc_route:
            with st.spinner("Loading contacts for selected location..."):
                location_contacts = df[df['Location'] == route_location]
                st.markdown(f"## Contacts in {safe_display(route_location)}")
                if len(location_contacts) == 0:
                    st.info("No contacts found for this location.")
                else:
                    show_cards(location_contacts)
                st.stop()

        if route_location and route_places and not calc_route:
            with st.spinner("Loading contacts for selected places..."):
                selected_contacts = df[(df['Location'] == route_location) & (df['Place'].isin(route_places))]
                st.markdown(f"## Contacts in Selected Places: {', '.join([safe_display(p) for p in route_places])}")
                if len(selected_contacts) > 0:
                    show_cards(selected_contacts)
                st.stop()

        if calc_route:
            with st.spinner("Calculating optimal route and preparing results..."):
                try:
                    route_df = df[(df['Location'] == route_location) &
                                  (df['Place'].isin(route_places)) &
                                  (pd.notnull(df['Latitude'])) &
                                  (pd.notnull(df['Longitude']))].reset_index(drop=True)

                    if len(route_df) < 2:
                        st.warning("Need at least 2 valid places with coordinates for routing.")
                    else:
                        coords = route_df[['Latitude', 'Longitude']].values
                        n = len(route_df)
                        dist_matrix = np.zeros((n, n))
                        for i in range(n):
                            for j in range(n):
                                if i != j:
                                    dist_matrix[i, j] = haversine(coords[i][0], coords[i][1], coords[j][0], coords[j][1])

                        G = nx.complete_graph(n)
                        for i in range(n):
                            for j in range(n):
                                if i != j:
                                    G[i][j]['weight'] = dist_matrix[i, j]

                        tsp_path = nx.approximation.traveling_salesman_problem(G, cycle=False)

                        total_distance = sum(dist_matrix[tsp_path[i], tsp_path[i+1]] for i in range(n-1))
                        avg_speed_kmh = 40  # avg urban speed
                        total_time_hours = total_distance / avg_speed_kmh
                        hours = int(total_time_hours)
                        minutes = int((total_time_hours - hours) * 60)

                        st.markdown("## Optimal Route & Travel Time")
                        st.write(f"**Total Distance:** {total_distance:.1f} km")
                        st.write(f"**Estimated Total Time:** {hours} hours {minutes} minutes (assuming avg speed {avg_speed_kmh} km/h)")

                        # Prepare lines for map (no points, just line)
                        lines = []
                        for i in range(len(tsp_path)-1):
                            start_idx = tsp_path[i]
                            end_idx = tsp_path[i+1]
                            start = route_df.iloc[start_idx]
                            end = route_df.iloc[end_idx]
                            dist = dist_matrix[start_idx, end_idx]
                            time_min = dist / avg_speed_kmh * 60
                            lines.append({
                                "path": [[start['Longitude'], start['Latitude']], [end['Longitude'], end['Latitude']]],
                                "distance": dist,
                                "time_min": time_min,
                            })

                        path_layer = pdk.Layer(
                            "PathLayer",
                            data=lines,
                            get_path="path",
                            get_color=[0, 0, 255],
                            width_scale=10,
                            width_min_pixels=4,
                        )

                        st.pydeck_chart(pdk.Deck(
                            map_style="mapbox://styles/mapbox/light-v9",
                            initial_view_state=pdk.ViewState(
                                latitude=np.mean(route_df['Latitude']),
                                longitude=np.mean(route_df['Longitude']),
                                zoom=12,
                            ),
                            layers=[path_layer],
                        ))

                        # Show travel times between places
                        st.markdown("### Travel Times Between Places")
                        for i, line in enumerate(lines):
                            st.write(f"{route_df.iloc[tsp_path[i]]['Place']} → {route_df.iloc[tsp_path[i+1]]['Place']}: "
                                     f"{line['distance']:.1f} km, approx {line['time_min']:.0f} minutes")

                        # Show cards for only the route contacts, in order
                        st.markdown("### Contacts for Route (in Visit Order)")
                        show_cards(route_df.iloc[tsp_path])
                except Exception as e:
                    st.error("Error calculating or displaying route.")
                    st.error(str(e))
                st.stop()

        # --------- Main Dashboard (only if not in route mode or location selection) ---------
        with st.spinner("Rendering dashboard..."):
            st.markdown(f"## {len(filtered_df)} Contacts Found")
            if len(filtered_df) == 0:
                st.info("No contacts found with the current filters.")
            else:
                show_cards(filtered_df)

    except Exception as e:
        st.error("An unexpected error occurred while processing your file or inputs.")
        st.error(str(e))

if __name__ == "__main__":
    main()
