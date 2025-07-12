# pages/2_Driver_Performance.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
# The functions get_drivers, get_driver_results, get_session_info are accessible via st.session_state

st.header("Driver Performance Visualization 📈")

# Accesses get_drivers function via session_state
all_drivers_for_viz = st.session_state.get_drivers() 

if all_drivers_for_viz:
    driver_names_viz = sorted([d['full_name'] for d in all_drivers_for_viz if d.get('full_name')])
else:
    driver_names_viz = []

if driver_names_viz:
    selected_driver_viz_name = st.selectbox(
        "Select a Driver to Visualize Performance:", 
        ["-- Select --"] + driver_names_viz, 
        key='driver_viz_select'
    )
else:
    st.warning("Could not load the list of drivers for visualization.")
    selected_driver_viz_name = None

if st.button("Generate Performance Chart 📊"):
    if selected_driver_viz_name and selected_driver_viz_name != "-- Select --":
        with st.spinner(f"Generating chart for {selected_driver_viz_name}..."):
            selected_driver_viz_number = next((d.get('driver_number') for d in all_drivers_for_viz if d.get('full_name') == selected_driver_viz_name), None)

            if selected_driver_viz_number:
                # Access get_driver_results via session_state, passing the current year
                results_viz = st.session_state.get_driver_results(selected_driver_viz_number, datetime.now().year)
                
                if results_viz:
                    # Filter for 'Race' type sessions with a valid 'position'
                    race_results = [
                        res for res in results_viz 
                        if st.session_state.get_session_info(res['session_key']) and \
                           st.session_state.get_session_info(res['session_key']).get('session_type') == 'Race' and \
                           res.get('position') is not None
                    ]
                    
                    # Sort results by race date
                    race_results_sorted = sorted(
                        race_results, 
                        key=lambda x: st.session_state.get_session_info(x['session_key']).get('date_start', '2000-01-01T00:00:00Z')
                    )
                    
                    if race_results_sorted:
                        data_for_df = []
                        for res in race_results_sorted:
                            session_info = st.session_state.get_session_info(res['session_key'])
                            race_name = session_info.get('session_name', 'Unknown')
                            race_date = pd.to_datetime(session_info.get('date_start')).strftime('%Y-%m-%d')
                            data_for_df.append({
                                "Race": f"{race_name} ({race_date})",
                                "Final Position": int(res['position']),
                                "Date": pd.to_datetime(race_date) 
                            })
                        
                        df_performance = pd.DataFrame(data_for_df)
                        
                        # Create the line chart
                        fig = px.line(
                            df_performance, 
                            x="Race", 
                            y="Final Position", 
                            title=f"Performance of {selected_driver_viz_name} by Race",
                            markers=True,
                            height=500,
                            labels={"Final Position": "Final Position (lower is better)"},
                            hover_data={"Final Position": True}
                        )
                        
                        # Invert y-axis for positions (lower position is better) and adjust x-axis labels
                        fig.update_yaxes(autorange="reversed")
                        fig.update_xaxes(tickangle=45, tickfont=dict(size=10))

                        st.plotly_chart(fig, use_container_width=True)

                    else:
                        st.info(f"No valid race results found for {selected_driver_viz_name} to generate the chart.")
                else:
                    st.warning(f"Could not retrieve results for {selected_driver_viz_name}.")
            else:
                st.warning("Could not find the NUMBER for the selected driver.")
    else:
        st.warning("Please select a driver to generate the chart.")