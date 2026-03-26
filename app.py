import streamlit as st
from datetime import datetime, timedelta
from modules import (
    display_map,
    display_session_summary,
    display_recent_games,
    display_personalized_recommendations
)
import community_page
import activity_page
import data_fetcher
 
# --- CONFIG ---
st.set_page_config(page_title="Sports Connect", layout="wide")
 
# --- SESSION STATE ---
if "user_id" not in st.session_state:
    st.session_state["user_id"] = "user1"
 
# --- SIDEBAR ---
with st.sidebar:
    st.title("🏆 Sports Connect")
    st.markdown("---")
 
    # User selector
    user_id = st.text_input("User ID", value=st.session_state["user_id"])
    st.session_state["user_id"] = user_id
 
    st.markdown("---")
    menu = st.radio("Menu", ["Home", "Activity", "Community", "Profile", "Find a Game", "Friends"], index=0)
    st.write(f"Currently viewing: **{menu}**")
 
# --- MAIN CONTENT ---
if menu == "Home":
    st.header("Sports Connect")
    st.divider()
 
    user_id = st.session_state["user_id"]
 
    # Fetch real data from database
    try:
        raw_activity = data_fetcher.get_user_activity(user_id, limit=10)
        friends      = data_fetcher.get_friends(user_id)
        user         = data_fetcher.get_user(user_id)
        home_lat     = user["home_lat"] if user and user.get("home_lat") else 25.7617
        home_lng     = user["home_lng"] if user and user.get("home_lng") else -80.1918
    except Exception as e:
        st.error(f"Could not load data: {e}")
        raw_activity = []
        friends      = []
        home_lat, home_lng = 25.7617, -80.1918
 
    # Convert activity rows to session format that modules.py expects
    sessions = []
    for a in raw_activity:
        if a.get("timestamp") and a.get("sport"):
            loc_name = "Unknown"
            if a.get("location") and isinstance(a["location"], dict):
                loc_name = a["location"].get("name", "Unknown")
 
            # Use duration_minutes to calculate end time
            duration = a.get("duration_minutes") or 0
            start = a["timestamp"]
            if isinstance(start, str):
                start = datetime.fromisoformat(start)
            end = start + timedelta(minutes=duration)
 
            sessions.append({
                "sport":      a["sport"],
                "start_time": start,
                "end_time":   end,
                "location":   loc_name,
            })
 
    user_location = {"lat": home_lat, "lng": home_lng}
 
    left_col, right_col = st.columns([1, 1.2], gap="large")
    with left_col:
        display_session_summary(sessions)
        st.write("")
        display_recent_games(sessions)
        st.write("")
        display_personalized_recommendations(sessions, friends)
    with right_col:
        display_map(user_location)
 
elif menu == "Activity":
    activity_page.show_activity_page(st.session_state["user_id"])
 
elif menu == "Community":
    community_page.show_community_page(st.session_state["user_id"])
 
elif menu == "Profile":
    st.header("Profile")
    st.write("Profile page coming soon.")
 
elif menu == "Find a Game":
    st.header("Find a Game")
    st.write("Find a game page coming soon.")
 
elif menu == "Friends":
    st.header("Friends")
    st.write("Friends page coming soon.")