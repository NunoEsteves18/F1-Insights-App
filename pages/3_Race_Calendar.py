# pages/3_Race_Calendar.py

import streamlit as st
from datetime import datetime
import pandas as pd # For the final DataFrame, if needed

st.header("Formula 1 Race Calendar 🗓️")

current_year = datetime.now().year
years_to_show = list(range(current_year - 2, current_year + 2)) 

selected_year = st.selectbox(
    "Select Year:", 
    options=years_to_show, 
    index=years_to_show.index(current_year), 
    key='calendar_year_select'
)

if st.button(f"Show {selected_year} Calendar 🏎️"):
    with st.spinner(f"Loading calendar for {selected_year}..."):
        # Access the function via session_state
        races_data = st.session_state.get_races_calendar(selected_year)

        if races_data:
            st.subheader(f"Races for {selected_year}:")
            
            calendar_list = []
            for race in races_data:
                race_name = race.get('session_name', 'Unknown Name')
                
                # The OpenF1 API usually returns the circuit name within the session dictionary
                # Or we can use 'location' for a city/country name
                circuit_name = race.get('circuit_short_name', race.get('location', 'Unknown Location'))
                
                date_start_str = race.get('date_start')
                if date_start_str:
                    # Replace 'Z' with '+00:00' for proper UTC parsing by fromisoformat
                    race_datetime = datetime.fromisoformat(date_start_str.replace('Z', '+00:00'))
                    race_date_formatted = race_datetime.strftime('%d/%m/%Y')
                    race_time_formatted = race_datetime.strftime('%H:%M')
                else:
                    race_date_formatted = 'Unknown Date'
                    race_time_formatted = 'Unknown Time'

                # Check if the race date is in the past relative to now, considering timezone
                is_past_race = race_datetime < datetime.now(race_datetime.tzinfo) if date_start_str else False

                status_emoji = "✅" if is_past_race else "🔜"
                
                calendar_list.append({
                    "Status": status_emoji,
                    "Race": race_name,
                    "Circuit": circuit_name,
                    "Date": race_date_formatted,
                    "Time": race_time_formatted
                })
            
            # Display the calendar in a Streamlit table
            df_calendar = pd.DataFrame(calendar_list)
            st.dataframe(df_calendar, use_container_width=True)

        else:
            st.warning(f"Could not retrieve the calendar for {selected_year}.")