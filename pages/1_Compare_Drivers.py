# pages/1_Compare_Drivers.py

import streamlit as st
from datetime import datetime
# Imports functions and global variables from the main app file.
# Streamlit handles global import when pages are loaded,
# so you don't need 'from ..app import get_drivers' etc.
# but you need to ensure the 'model' for Gemini is in st.session_state.

st.header("Driver Comparison ⚔️")

# Accesses functions and the model directly, as they are in the main app's scope,
# and Streamlit handles this automatically with the multipage model.
# Assumes get_drivers is in app.py and accessible via session_state.
all_drivers_for_comparison = st.session_state.get_drivers()

if all_drivers_for_comparison:
    driver_names_sorted = sorted([d['full_name'] for d in all_drivers_for_comparison if d.get('full_name')])
else:
    driver_names_sorted = []

if driver_names_sorted:
    col_comp1, col_comp2 = st.columns(2)
    with col_comp1:
        driver1_name_comp = st.selectbox("Select Driver 1:", ["-- Select --"] + driver_names_sorted, key='driver1_compare_select')
    with col_comp2:
        driver2_name_comp = st.selectbox("Select Driver 2:", ["-- Select --"] + driver_names_sorted, key='driver2_compare_select')
else:
    st.warning("Could not load the list of drivers for comparison.")
    driver1_name_comp = None
    driver2_name_comp = None

if st.button("Compare Drivers with AI 🤖"):
    if driver1_name_comp and driver2_name_comp and driver1_name_comp != "-- Select --" and driver2_name_comp != "-- Select --":
        if driver1_name_comp == driver2_name_comp:
            st.warning("Please select two different drivers to compare.")
        else:
            with st.spinner(f"Comparing {driver1_name_comp} vs {driver2_name_comp}..."):
                driver1_number_comp = next((d.get('driver_number') for d in all_drivers_for_comparison if d.get('full_name') == driver1_name_comp), None)
                driver2_number_comp = next((d.get('driver_number') for d in all_drivers_for_comparison if d.get('full_name') == driver2_name_comp), None)

                if driver1_number_comp and driver2_number_comp:
                    # Access get_driver_results via session_state
                    results1_comp = st.session_state.get_driver_results(driver1_number_comp, datetime.now().year) # Pass current year
                    results2_comp = st.session_state.get_driver_results(driver2_number_comp, datetime.now().year) # Pass current year

                    if results1_comp is not None and results2_comp is not None:
                        # Access format_driver_data_for_gemini via session_state
                        compiled_data1_comp = st.session_state.format_driver_data_for_gemini(driver1_name_comp, results1_comp)
                        compiled_data2_comp = st.session_state.format_driver_data_for_gemini(driver2_name_comp, results2_comp)

                        comparison_prompt = (
                            f"Analyze and compare the recent performance of the following two Formula 1 drivers based on the provided data. "
                            f"Focus on identifying strengths and weaknesses, consistency, and significant results for both. "
                            f"Provide a conclusion on who demonstrated superior or more consistent performance.\n\n"
                            f"Driver 1 Data:\n{compiled_data1_comp}\n\n"
                            f"Driver 2 Data:\n{compiled_data2_comp}\n\n"
                            f"Present your analysis concisely, impartially, and in clear bullet points or paragraphs. "
                            f"Avoid generic introductions and conclusions."
                        )

                        try:
                            if st.session_state.model:
                                # Access the Gemini model
                                comparison_response = st.session_state.model.generate_content(comparison_prompt)
                                st.subheader(f"Comparative Analysis between {driver1_name_comp} and {driver2_name_comp}:")
                                st.write(comparison_response.text)
                            else:
                                st.error("Gemini model not initialized. Check the API key.")
                        except Exception as e:
                            st.error(f"Error generating driver comparison: {e}. Check the API key or prompt content.")
                    else:
                        st.warning("Could not get race results for one or both drivers. Please try again later.")
                else:
                    st.warning("Could not find the NUMBERS for the selected drivers. Please check if the names are correct.")
    else:
        st.warning("Please select two drivers to compare.")