# app.py

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import google.generativeai as genai

# --- Main Page Configurations ---
st.set_page_config(page_title="F1 Insights", layout="wide") # Removed 'icon' if it caused an error

st.title("Welcome to F1 Insights! 🏎️")
st.write("Select a feature from the sidebar to explore Formula 1 data.")

# --- Google Gemini API Configuration ---
# IMPORTANT: For production, move your API key to an environment variable or Streamlit secrets!
# Example using environment variable (recommended for local development):
# gemini_api_key = os.getenv('GOOGLE_API_KEY')
# Example using hardcoded key (NOT RECOMMENDED FOR PRODUCTION - FOR TESTING ONLY):
gemini_api_key = os.getenv('GOOGLE_API_KEY') # Replace with os.getenv('GOOGLE_API_KEY') for security

try:
    if not gemini_api_key:
        st.error("GEMINI_API_KEY not found. Please define it in environment variables or Streamlit secrets.")
    else:
        genai.configure(api_key=gemini_api_key)
        try:
            st.info("Listing available Gemini models...")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    st.write(f"- {m.name} (supports generateContent)")
        except Exception as e:
            st.error(f"Error listing models: {e}")
except Exception as e:
    st.error(f"Error configuring the Gemini API: {e}")

# Initialize the Gemini model (can be global or within a cached function)
if 'model' not in st.session_state:
    try:
        st.session_state.model = genai.GenerativeModel('gemini-1.0-pro') # Using gemini-1.0-pro
    except Exception as e:
        st.error(f"Error initializing the Gemini model: {e}")
        st.session_state.model = None

# --- Global API Variables ---
OPENF1_BASE_URL = "https://api.openf1.org/v1"

# --- Functions for Interacting with OpenF1 API (ALL YOUR FUNCTIONS HERE) ---

@st.cache_data(ttl=3600)
def get_drivers(driver_name=None):
    """Fetches driver data from the OpenF1 API, optionally filtering by full name."""
    params = {}
    if driver_name:
        params['full_name'] = driver_name
    
    try:
        response = requests.get(f"{OPENF1_BASE_URL}/drivers", params=params, timeout=15)
        response.raise_for_status() 
        all_drivers = response.json()
        valid_drivers = [d for d in all_drivers if d.get('full_name') and d.get('driver_number')]
        return valid_drivers
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching drivers from OpenF1 API: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected error processing driver data: {e}")
        return None

@st.cache_data(ttl=3600)
def get_driver_results(driver_identifier, year=None):
    """Fetches a driver's results from the OpenF1 API using driver_number, optionally filtering by year."""
    params = {'driver_number': driver_identifier}
    
    if year:
        params['session_year'] = year # API might use 'session_year' or 'date_start_year' for results.
                                     # 'session_year' seems more consistent for results.
    
    st.info(f"Attempting to fetch results for driver_number: {driver_identifier} and year: {year}")
    st.info(f"Request URL: {OPENF1_BASE_URL}/results with parameters: {params}")

    try:
        response = requests.get(f"{OPENF1_BASE_URL}/results", params=params, timeout=15)
        
        st.info(f"API Response Status for results: {response.status_code}")
        response.raise_for_status() 
        
        results = response.json()
        st.info(f"Total results received from API for {driver_identifier} in year {year}: {len(results)}")
        st.info(f"First 200 characters of raw results: {str(results)[:200]}...")

        if not results:
            st.warning(f"The API returned an empty list of results for driver_number {driver_identifier} in year {year}.")
            
        return results
    except requests.exceptions.Timeout:
        st.error(f"Timeout Error: Request for driver {driver_identifier}'s results timed out. Check your connection or try again later.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching results for driver {driver_identifier}: {e}. This might be a network or API issue.")
        return None
    except Exception as e:
        st.error(f"Unexpected error processing results for driver {driver_identifier}: {e}")
        return None
    
@st.cache_data(ttl=3600)
def get_session_info(session_key):
    try:
        response = requests.get(f"{OPENF1_BASE_URL}/sessions", params={'session_key': session_key}, timeout=10)
        response.raise_for_status()
        sessions = response.json()
        return sessions[0] if sessions else None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching session information for {session_key}: {e}")
        return None

@st.cache_data(ttl=3600)
def get_races_calendar(year=None):
    """
    Fetches the race calendar (sessions of type 'Race') and filters by year in Python.
    """
    base_url = f"{OPENF1_BASE_URL}/sessions"
    params = {"session_type": "Race"}
    
    # Removed the year parameter from the API request
    # if year:
    #     params["date_start_year"] = year 

    #st.info(f"Attempting to fetch ALL 'Race' type sessions with URL: {base_url} and parameters: {params}") # Debugging info

    try:
        response = requests.get(base_url, params=params, timeout=30) # Increased timeout to 30s
        
        #st.info(f"API Response Status for calendar (general): {response.status_code}") # Debugging info
        response.raise_for_status() 
        
        all_races = response.json()
        #st.info(f"Total ALL 'Race' sessions received from API: {len(all_races)}") # Debugging info
        
        # Now, filter by year in Python
        races_filtered_by_year = [
            r for r in all_races 
            if 'date_start' in r and isinstance(r['date_start'], str) and datetime.fromisoformat(r['date_start'].replace('Z', '+00:00')).year == year
        ]
        
        #st.info(f"Total 'Race' sessions for year {year} after Python filter: {len(races_filtered_by_year)}") # Debugging info
        if not races_filtered_by_year:
            st.warning(f"No valid 'Race' sessions found for year {year} after filtering. The API might not have data for this year or the date format is incorrect.")
            # If data was received but none were valid, show the first for debugging
            if all_races:
                st.write("Example API session item (first one):", all_races[0])


        # Sort races by start date (now already filtered by year)
        races_sorted = sorted(
            races_filtered_by_year, 
            key=lambda x: datetime.fromisoformat(x['date_start'].replace('Z', '+00:00'))
        )
        #st.info(f"Total sorted races for {year}: {len(races_sorted)}") # Debugging info
        return races_sorted
    except requests.exceptions.Timeout:
        st.error("Timeout Error: The OpenF1 API request for the calendar timed out. Check your connection or try again later.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching the race calendar: {e}. This might be a network, API, or incorrect URL issue.")
        return None
    except ValueError as e:
        st.error(f"Error processing calendar date data: {e}. Check the date format in the API.")
        return None
    except Exception as e:
        st.error(f"Unexpected error processing the calendar: {e}")
        return None


# Formatting functions (should also be here)
def format_driver_data_for_gemini(driver_name, results):
    if not results:
        return f"No recent result data available for {driver_name}."

    data_string = []
    data_string.append(f"Latest Results for {driver_name} (limited to 10):")
    
    for res in results[:10]:
        session_key = res.get('session_key')
        race_name = "Unknown Race"
        race_date = "Unknown Date"

        if session_key:
            session_info = get_session_info(session_key)
            if session_info:
                race_name = session_info.get('session_name', 'Unknown Race')
                try:
                    race_datetime = datetime.fromisoformat(session_info.get('date_start').replace('Z', '+00:00'))
                    race_date = race_datetime.strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    pass

        position = res.get('position', 'N/A')
        points = res.get('points', 'N/A')
        laps = res.get('laps', 'N/A')
        status = res.get('status', 'N/A')

        data_string.append(
            f"- {race_name} ({race_date}): Position {position}, "
            f"Points {points}, Laps Completed {laps}, Status: {status}"
        )
    
    return "\n".join(data_string)

# --- Initialize functions in session_state for access across pages ---
# Ensure these functions are always available in session_state
st.session_state.get_drivers = get_drivers
st.session_state.get_driver_results = get_driver_results
st.session_state.get_session_info = get_session_info
st.session_state.get_races_calendar = get_races_calendar
st.session_state.format_driver_data_for_gemini = format_driver_data_for_gemini

# Ensure the Gemini model is also initialized once
# This part of the code should also be at the end, after function definitions
if 'model' not in st.session_state:
    try:
        # Assuming genai.configure(api_key=...) is set up correctly earlier in app.py
        st.session_state.model = genai.GenerativeModel('gemini-1.0-pro') # Using gemini-1.0-pro
    except Exception as e:
        st.error(f"Error initializing the Gemini model: {e}")
        st.session_state.model = None

# --- DEBUGGING: Check what's actually in session_state ---
import logging
logging.basicConfig(level=logging.INFO)
logging.info(f"Session State Keys at app.py end: {list(st.session_state.keys())}")