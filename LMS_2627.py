# -*- coding: utf-8 -*-
"""
Created on Sat Aug  8 22:00:50 2026

@author: matta
"""

import streamlit as st
import pandas as pd
import datetime as dt
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(layout="wide")

st.title("Premier League - Last Man Standing")

def save_player_to_google(player, pin):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["google"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    
    client = gspread.authorize(creds)
    sh = client.open("LMS_2627")

    # Open or create the "players" sheet
    try:
        worksheet = sh.worksheet("players")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title="players", rows=100, cols=20)
        worksheet.update("A1", [["player", "pin"]])

    # Append new player
    worksheet.append_row([player, pin])

def save_pick_to_google(player, gw, team):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["google"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    
    client = gspread.authorize(creds)
    sh = client.open("LMS_2627")

    # Open or create the "picks" sheet
    try:
        worksheet = sh.worksheet("picks")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title="picks", rows=500, cols=20)
        worksheet.update("A1", [["player", "gw", "team"]])

    # Append pick
    worksheet.append_row([player, gw, team])

import streamlit as st

@st.cache_data(ttl=300)  # cache for 5 minutes
def load_players_from_google():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["google"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    
    client = gspread.authorize(creds)
    sh = client.open("LMS_2627")
    worksheet = sh.worksheet("players")
    data = worksheet.get_all_records()
    players = {row["player"]: str(row["pin"]) for row in data}
    return players

@st.cache_data(ttl=60)
def load_picks_from_google():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["google"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    
    client = gspread.authorize(creds)
    sh = client.open("LMS_2627")
    worksheet = sh.worksheet("picks")
    data = worksheet.get_all_records()
    # Store picks as: picks[player][gw] = pick
    picks = {}
    for row in data:
        p = row["player"]
        gw = row["gw"]
        pick = row["pick"]

        if p not in picks:
            picks[p] = {}

        picks[p][gw] = pick

    return picks


#fixtures = pd.read_excel(r"C:\Users\matta\OneDrive\Documents\Matt's Stuff\Footy\PL2627.xlsx")
url = "https://raw.githubusercontent.com/Mallos17/LMS_2627/main/PL2627.xlsx"
fixtures = pd.read_excel(url, engine="openpyxl")

# Convert
fixtures["Date"] = pd.to_datetime(fixtures["Date"], format="%d/%m/%Y")

# Convert Time (datetime.time → HH:MM string)
fixtures["Time"] = fixtures["Time"].apply(lambda t: t.strftime("%H:%M"))

# Sort using a hidden sortable column
fixtures["TimeSort"] = pd.to_datetime(fixtures["Time"], format="%H:%M")
fixtures = fixtures.sort_values(["Date", "TimeSort", "Home"])
fixtures = fixtures.drop(columns=["TimeSort"])

prem_badges = {"Arsenal": "https://crests.football-data.org/57.png",
"Aston Villa": "https://media.api-sports.io/football/teams/66.png",
"Bournemouth": "https://media.api-sports.io/football/teams/35.png",
"Brentford": "https://media.api-sports.io/football/teams/55.png",
"Brighton": "https://media.api-sports.io/football/teams/51.png",
"Chelsea": "https://media.api-sports.io/football/teams/49.png",
"Coventry City": "https://crests.football-data.org/1076.png",
"Crystal Palace": "https://media.api-sports.io/football/teams/52.png",
"Everton": "https://media.api-sports.io/football/teams/45.png",
"Fulham": "https://media.api-sports.io/football/teams/36.png",
"Hull City": "https://media.api-sports.io/football/teams/64.png",
"Ipswich Town": "https://media.api-sports.io/football/teams/57.png",
"Leeds United": "https://media.api-sports.io/football/teams/63.png",
"Liverpool": "https://crests.football-data.org/64.png",
"Manchester City": "https://media.api-sports.io/football/teams/50.png",
"Manchester United": "https://media.api-sports.io/football/teams/33.png",
"Newcastle United": "https://media.api-sports.io/football/teams/34.png",
"Nottingham Forest": "https://media.api-sports.io/football/teams/65.png",
"Sunderland": "https://crests.football-data.org/71.png",
"Tottenham": "https://crests.football-data.org/73.png"
}

def badge_html_home(team):
    url = prem_badges.get(team, "")
    return f"<img src='{url}' width='25' style='vertical-align:middle;'> {team}"

def badge_html_away(team):
    url = prem_badges.get(team, "")
    return f"{team} <img src='{url}' width='25' style='vertical-align:middle;'>"

#fixtures["HomeBadge"] = fixtures["Home"].apply(badge_html)
#fixtures["AwayBadge"] = fixtures["Away"].apply(badge_html)

def prepare_results_table(df):
    df = df.copy()
    
    df["Date"] = df["Date"].dt.strftime("%d-%b-%Y")
    
    # --- 1. Add flags to Team A and Team B ---
    df["Home"] = df["Home"].apply(badge_html_home)
    df["Away"] = df["Away"].apply(badge_html_away)
    
    df = df.reset_index(drop=True)
    
    # Apply alignment
    df["Home"] = df["Home"].apply(lambda x: f"<div style='text-align:left;'>{x}</div>")
    df["Away"] = df["Away"].apply(lambda x: f"<div style='text-align:right;'>{x}</div>")
    
    # --- 2. Handle HS (Home Score) ---
    if df["HS"].isna().any():
        df = df.drop(columns=["HS"])
    else:
        # Convert to int safely
        df["HS"] = df["HS"].astype(int)
        df["AS"] = df["AS"].astype(int)

        # Convert scores back to strings + center align
        df["HS"] = df["HS"].astype(str).apply(lambda x: f"<div style='text-align:center;'>{x}</div>")
    
    # --- 3. Handle AS (Away Score) ---
    if df["AS"].isna().any():
        df = df.drop(columns=["AS"])
    else:
        df["AS"] = df["AS"].astype(str).apply(lambda x: f"<div style='text-align:center;'>{x}</div>")
    
    return df

def compute_results(fixtures_df):
    df = fixtures_df.copy()

    mask = df["HS"].notna() & df["AS"].notna()

    df.loc[mask & (df["HS"] > df["AS"]), "result"] = df["Home"]
    df.loc[mask & (df["HS"] < df["AS"]), "result"] = df["Away"]
    df.loc[mask & (df["HS"] == df["AS"]), "result"] = "Draw"

    return df

def get_gw_winners(fixtures_df):
    winners = {}

    for gw in fixtures_df["GW"].unique():
        gw_df = fixtures_df[fixtures_df["GW"] == gw]

        # Only matches with results
        gw_df = gw_df[gw_df["result"].notna()]

        winners[gw] = gw_df["result"].tolist()

    return winners


def gw_nav():
    # Always recalc index based on current selected GW
    idx = gw_list.index(st.session_state["selected_gw"])

    # 4 columns: Title, Prev, Next, Current
    col_title, col_prev, col_next, col_current = st.columns([1, 0.5, 0.5, 0.5])

    # TITLE
    with col_title:
        st.markdown(
            f"<h3 style='text-align:center;'>Gameweek {st.session_state['selected_gw']}</h3>",
            unsafe_allow_html=True
        )

    # PREV GW
    with col_prev:
        if idx > 0:
            prev_gw = gw_list[idx - 1]
            if st.button(f"◀ GW {prev_gw}", key="prev_gw"):
                st.session_state["selected_gw"] = prev_gw
                st.rerun()

    # NEXT GW
    with col_next:
        if idx + 1 < len(gw_list):
            next_gw = gw_list[idx + 1]
            if st.button(f"GW {next_gw} ▶", key="next_gw"):
                st.session_state["selected_gw"] = next_gw
                st.rerun()

    # CURRENT GW
    with col_current:
        if st.button("Current GW", key="current_gw"):
            st.session_state["selected_gw"] = current_gw
            st.rerun()
                
results_display = prepare_results_table(fixtures)

# Today or selected date
#selected_date = date.today()
#selected_date = pd.to_datetime(selected_date)

fixtures["Date"] = pd.to_datetime(fixtures["Date"], format="%d/%m/%Y")

gw_start_dates = fixtures.groupby("GW")["Date"].min().sort_values()
today = dt.date.today()

# Find the most recent GW that has already started
past_gws = gw_start_dates[gw_start_dates.dt.date <= today]

if len(past_gws) == 0:
    current_gw = gw_start_dates.index[0]   # season hasn't started yet
else:
    current_gw = past_gws.index[-1]        # latest GW that has started

# Next GW
gw_list = list(gw_start_dates.index)
current_idx = gw_list.index(current_gw)

next_gw = gw_list[current_idx + 1] if current_idx + 1 < len(gw_list) else None
current_df = fixtures[fixtures["GW"] == current_gw]
next_df = fixtures[fixtures["GW"] == next_gw] if next_gw else None
gw_start = current_df["Date"].min()
gw_end   = current_df["Date"].max()
gw_start_date = gw_start.date()
gw_end_date   = gw_end.date()

# --- 2. Compute gameweek start dates ---
gw_start_dates = fixtures.groupby("GW")["Date"].min()
gw_end_dates = fixtures.groupby("GW")["Date"].max()
gw_list = sorted(gw_start_dates.index)

#today = dt.date.today()
today = dt.date(2026,8,27)
past_gws = gw_start_dates[gw_start_dates.dt.date <= today]

current_gw = None
in_play = False

for gw in gw_list:
    start = gw_start_dates[gw].date()
    end   = gw_end_dates[gw].date()
    if today < start:
        # Before this GW starts → this GW is the current one
        current_gw = gw
        break

    if start <= today <= end:
        # Inside this GW → this GW is current
        current_gw = gw
        in_play = True
        break

if current_gw is None:
    current_gw = gw_list[-1]

current_idx = gw_list.index(current_gw)
next_gw = gw_list[current_idx + 1] if current_idx + 1 < len(gw_list) else None

# --- 3. Session state for selected GW ---
if "selected_gw" not in st.session_state:
    st.session_state["selected_gw"] = current_gw
    
def get_fixture_result(fixtures_df, gw):
    row = fixtures_df.loc[fixtures_df["GW"] == gw]

    if row.empty:
        return None

    result = row["result"].iloc[0]

    return result if pd.notna(result) else None

def pick_correct(player, gw, picks_dict, fixtures_df):
    pick = picks_dict.get(player, {}).get(gw)
    result = get_fixture_result(fixtures_df, gw)

    if result is None:
        return None  # GW not completed yet

    return pick == result

def can_make_pick(player, current_gw, picks_dict, gw_winners):
    # GW1 → always allowed
    if current_gw <= 1:
        return True

    prev_gw = current_gw - 1

    # If player didn't pick last GW → allow
    prev_pick = picks_dict.get(player, {}).get(prev_gw)
    if prev_pick is None:
        return True

    # If previous GW has no winners yet → allow
    if prev_gw not in gw_winners:
        return True

    # Block if the pick is NOT in the winners list
    return prev_pick in gw_winners[prev_gw]

def get_used_teams(player, picks_dict):
    return list(picks_dict.get(player, {}).values())

# Determine which GW the deadline should belong to
if next_gw is not None:
    deadline_gw = next_gw
else:
    deadline_gw = current_gw

# Get fixtures for the deadline GW
deadline_df = fixtures[fixtures["GW"] == current_gw]

# First match of the deadline GW
first_match = deadline_df.sort_values(["Date", "Time"]).iloc[0]
first_date = first_match["Date"]
first_time = first_match["Time"]

# Convert time string to datetime.time
first_time_dt = dt.datetime.strptime(first_time, "%H:%M").time()

# Evening = kickoff at or after 17:00
is_evening = first_time_dt >= dt.time(17, 0)

# Deadline rules
if is_evening:
    deadline = dt.datetime.combine(first_date, dt.time(12, 0))
else:
    day_before = first_date - dt.timedelta(days=1)
    deadline = dt.datetime.combine(day_before, dt.time(17, 0))

# Countdown
now = dt.datetime.now()
time_left = deadline - now

if time_left.total_seconds() <= 0:
    countdown_text = "Deadline passed"
else:
    days = time_left.days
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes = remainder // 60
    countdown_text = f"{days}d {hours}h {minutes}m remaining"


#CREATING NEW PLAYER#
#save_player_to_google(new_name, new_pin)

#PLAYER MAKES PICK#
#save_pick_to_google(player, current_gw, pick)

#LOADING PLAYER and PICKS#
#stored_pin = players[player]

#used_teams = [
#    team for gw, team in player_picks.items()
#    if gw < current_gw]

# --- INITIALIZE SESSION STATE ---
if "current_player" not in st.session_state:
    st.session_state["current_player"] = None

# Default page
if "page" not in st.session_state:
    st.session_state.page = "Player Picks"

# Sidebar navigation
pages = {
    "Player Picks": "⭐",
    "Leaderboard": "🏆"
}

choice = st.sidebar.radio(
    "Navigation",
    list(pages.keys()),
    format_func=lambda x: f"{pages[x]}  {x}"
)

st.session_state.page = choice

# CSS that forces colours even in dark mode
st.sidebar.markdown("""
<style>

div[role="radiogroup"] > label {
    display: block;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid var(--secondary-background-color);
    background-color: var(--background-color);
    margin-bottom: 6px;
    cursor: pointer;

    /* Inactive text colour — works in dark mode */
    color: var(--text-color) !important;
}

/* ACTIVE option */
div[role="radiogroup"] > label[data-selected="true"] {
    background-color: #FFD700 !important;   /* gold */
    color: #000000 !important;              /* FORCE black text */
    font-weight: 800 !important;            /* bold */
    text-transform: uppercase !important;   /* uppercase */
}

</style>
""", unsafe_allow_html=True)

#nav_button("Player Picks")
#nav_button("Leaderboard")

#st.write(f"Current page: {st.session_state.page}")

from collections import Counter

if st.session_state.page == "Player Picks":

    choice = st.radio(
        "Please load your user page or create a new log in",
        ["Create New Entry", "Load Player Page"]
        )

    # --- CREATE NEW PLAYER ---
    if choice == "Create New Entry":
        st.text("Create New Player")

        new_name = st.text_input("Enter your full name")
        
        st.caption("Please create a PIN to log in. Recommended PINs are birthdays, years, dates etc - don't use your credit card PINs due to security risks")
        new_pin = st.text_input("Choose a 4‑digit PIN", type="password")

        if st.button("Create"):
            players_dict = load_players_from_google()

            if new_name in players_dict:
                st.error("This player already exists")
            else:
                save_player_to_google(new_name, new_pin)
                st.success(f"Player {new_name} created")

                st.session_state["current_player"] = new_name
                st.rerun()

    # --- LOAD EXISTING PLAYER ---
    if choice == "Load Player Page":
        st.text("Load Player")

        players_dict = load_players_from_google()
        players = list(players_dict.keys())

        if len(players) == 0:
            st.warning("No players created yet")
            st.stop()

        player = st.selectbox("Select your name", players)
        pin_input = st.text_input("Enter your PIN", type="password")

        if st.button("Load"):
            if pin_input != players_dict[player]:
                st.error("Incorrect PIN")
            else:
                st.session_state["current_player"] = player
                st.success(f"Welcome back, {player}")
                st.rerun()

    # --- BLOCK IF NO PLAYER LOGGED IN ---
    #if st.session_state["current_player"] is None:
    #    st.stop()
    
    player = st.session_state["current_player"]
    if player is None:
        st.markdown("Not logged in")
    else:
        st.markdown(f"Logged in as: **{player}**")
    
    picks = load_picks_from_google()
    player_picks = picks.get(player, {})
    existing_pick = player_picks.get(current_gw)
    
    # --- 5. Fixtures for selected GW ---
    gw_df = fixtures[fixtures["GW"] == st.session_state["selected_gw"]]
    gw_df_display = prepare_results_table(gw_df)
    
    st.markdown(
        f"<h4 style='text-align:center; color:green;'>Current Gameweek: GW{current_gw}</h4>",
        unsafe_allow_html=True
    )
    
    fixtures_processed = compute_results(fixtures)
    teams = sorted(set(gw_df["Home"]).union(set(gw_df["Away"])))
    gw_winners = get_gw_winners(fixtures_processed)
    
    allowed = can_make_pick(player, current_gw, picks, gw_winners)
    
    out_week = list(picks[player].keys())[-1]
    used_teams = get_used_teams(player, picks)
    available_teams = sorted(set(teams) - set(used_teams))

    if not allowed:
        st.error(f"You picked incorrectly in Gameweek {out_week} — you are OUT.")
    else:
        # Display
        if st.session_state["current_player"] is not None:
            if in_play and existing_pick:
                st.markdown("<h4 style='color: red;'>Deadline passed - Gameweek in play</h4>",unsafe_allow_html=True)
                st.success(f"You have picked **{existing_pick.upper()}** for GW{current_gw}.")
            elif in_play and not existing_pick:
                st.markdown("<h4 style='color: red;'>Deadline passed - Gameweek in play</h4>",unsafe_allow_html=True)
                st.warning(f"No pick selected for for GW{current_gw}")
            elif not in_play and existing_pick:
                st.markdown(f"### Deadline for GW{current_gw}: {deadline.strftime('%a %d %b, %H:%M')}")
                st.markdown(f"**{countdown_text}**")
                st.success(f"You have picked **{existing_pick.upper()}** for GW{current_gw}.")
            elif not in_play and not existing_pick:
                st.markdown(f"### Deadline for GW{current_gw}: {deadline.strftime('%a %d %b, %H:%M')}")
                st.markdown(f"**{countdown_text}**")
    
                # --- 6. Pick a team ---
                pick = st.selectbox(f"Pick your team for GW{current_gw}:", available_teams)

                # --- 8. Confirm pick ---
                if st.button("Confirm Pick"):
                    st.success(f"You have picked **{pick.upper()}** for Gameweek {current_gw}")
                    save_pick_to_google(player, current_gw, pick)
                    st.cache_data.clear()
        
                # --- 7. Used teams (example) ---
                
                st.warning("Teams not available to you: " + ", ".join(used_teams))

    gw_nav()
    
    with st.container():
        st.markdown('<div class="mobile-table">', unsafe_allow_html=True)
        st.markdown(gw_df_display.to_html(index=False, escape=False), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)



elif st.session_state.page == "Leaderboard":

    st.header("Leaderboard")
    picks = load_picks_from_google()

    def build_leaderboard(picks_dict):
        rows = []

        # Determine latest GW that actually has picks
        all_real_gws = set()
        for gw_dict in picks_dict.values():
            for gw, pick in gw_dict.items():
                if pick not in (None, "", " "):
                    all_real_gws.add(gw)   # <-- keep gw as INT

        latest_gw = max(all_real_gws)

        # Count frequency using RAW team names
        latest_raw_picks = []
        for gw_dict in picks_dict.values():
            pick = gw_dict.get(latest_gw, "")   # <-- use INT key
            latest_raw_picks.append(pick if pick else "")

        freq = Counter(latest_raw_picks)

        # Build rows WITHOUT badges
        for player, gw_dict in picks_dict.items():
            row = {"Player Name": player}

            # Raw picks only
            for gw, pick in gw_dict.items():
                row[f"Gameweek {gw}"] = pick or ""

            # Sorting keys (raw)
            raw_latest_pick = gw_dict.get(latest_gw, "") or ""
            row["_freq"] = freq[raw_latest_pick]
            row["_alpha"] = raw_latest_pick.lower()

            rows.append(row)

        df = pd.DataFrame(rows)

        # Sort by popularity desc, alphabetical asc
        df = df.sort_values(
            ["_freq", "_alpha"],
            ascending=[False, True],
            kind="mergesort"
            )

        # Drop helper columns
        #df = df.drop(columns=["_freq", "_alpha"])

        # Sort GW columns numerically
        gw_cols = [col for col in df.columns if col.startswith("Gameweek ")]
        gw_cols_sorted = sorted(gw_cols, key=lambda x: int(x.split()[1]))

        
        #df = df[["Player Name"] + gw_cols_sorted]
        
        df = df.fillna("❌ OUT ❌")
        
        for col in df.columns:
            if col.startswith("Gameweek "):
                df[col] = df[col].apply(
                    lambda team: (
                        f"{badge_html_home(team)}"
                        ))
                
        return df

    leaderboard_df = build_leaderboard(picks)
    st.markdown(leaderboard_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    