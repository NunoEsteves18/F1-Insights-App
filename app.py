import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import os # For accessing environment variables
from dotenv import load_dotenv # Import to load variables from .env

# Load environment variables from the .env file
load_dotenv()

# --- Google Gemini API Configuration ---
# IMPORTANT: DO NOT HARDCODE YOUR API KEY DIRECTLY IN THE CODE!
# Get the API key from an environment variable for security.
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GEMINI_API_KEY:
    # Display an error if the key is not found and stop the app's execution
    st.error("Error: Google Gemini API key not found. "
             "Please set the 'GOOGLE_API_KEY' environment variable or create a .env file.")
    st.stop() # Stops app execution if the key is not configured

# Configure the Gemini API with the key
genai.configure(api_key=GEMINI_API_KEY)

# --- Gemini Model Initialization ---
try:
    # We try to use 'gemini-1.5-flash', which is fast and generally well-supported.
    # If this model doesn't work for you, check the output of 'genai.list_models()'
    # or the Google AI Studio for alternative model names that support 'generateContent'.
    model = genai.GenerativeModel('gemini-1.5-flash')
    st.success(f"Gemini model configured: {model.model_name}")

    # Optional: For debugging, you can list available models
    # st.info("Available Gemini models supporting 'generateContent':")
    # for m in genai.list_models():
    #     if 'generateContent' in m.supported_generation_methods:
    #         st.write(f"- `{m.name}`")

except Exception as e:
    st.error(f"Error initializing Gemini model: {e}")
    st.warning("Please check if 'gemini-1.5-flash' is available or try another model listed in the Gemini documentation.")
    st.stop()


# --- AI Functions for Text Analysis ---
def summarize_text(text):
    """Summarizes text using the Gemini model."""
    prompt = f"Please summarize the following Formula 1 news text concisely and objectively:\n\n{text}\n\nSummary:"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return "Could not generate summary."

def analyze_entities(text):
    """Lists key entities in a text using the Gemini model."""
    prompt = f"List the main entities (people, teams, events, locations, etc.) mentioned in the following Formula 1 news text. Only list the entities, one per line:\n\n{text}\n\nEntities:"
    try:
        response = model.generate_content(prompt)
        # Process the response to ensure each entity is on its own line
        entities_raw = response.text.split('\n')
        entities = [entity.strip() for entity in entities_raw if entity.strip()]
        return entities
    except Exception as e:
        st.error(f"Error analyzing entities: {e}")
        return []

def analyze_sentiment(text):
    """Analyzes the overall sentiment of a text using the Gemini model."""
    prompt = f"Analyze the overall sentiment of the following Formula 1 news text. State whether it is 'Positive', 'Negative', or 'Neutral' and provide a brief reason. Respond only with the sentiment and reason, example: 'Sentiment: Positive. Reason: The text describes the team's success.'\n\n{text}\n\nSentiment and Reason:"
    try:
        response = model.generate_content(prompt)
        sentiment_output = response.text
        # Attempts to extract sentiment and reason
        if "Sentiment:" in sentiment_output:
            # We return the full string as the prompt asks for a specific format.
            return sentiment_output
        return sentiment_output # Return raw output if format not as expected
    except Exception as e:
        st.error(f"Error analyzing sentiment: {e}")
        return "Could not analyze sentiment."


# --- OpenF1 API Functions ---
OPENF1_BASE_URL = "https://api.openf1.org/v1"

def get_drivers(driver_name=None):
    """Fetches driver data from the OpenF1 API, optionally filtering by full name."""
    params = {}
    if driver_name:
        params['full_name'] = driver_name
    
    try:
        response = requests.get(f"{OPENF1_BASE_URL}/drivers", params=params, timeout=10)
        response.raise_for_status() # Raises an error for 4xx/5xx status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching drivers from OpenF1 API: {e}")
        return None

# --- Functions to Extract News from Formula1.com (Web Scraping) ---
def fetch_f1_latest_articles(url="https://www.formula1.com/en/latest"):
    """
    Fetches the latest news articles from Formula1.com.
    Updated to the latest URL.
    """
    articles = []
    # Use headers to mimic a real browser, which can help prevent blocking
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        st.info(f"Attempting to fetch URL: {url}")
        response = requests.get(url, headers=headers, timeout=15) # Added timeout
        response.raise_for_status() # Check if the request was successful (status 200 OK)
        st.success(f"HTTP request successful. Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Selectors based on inspection of the Formula1.com website
        # Container for each article in the news list
        article_cards = soup.find_all('li', class_='ArticleListCard-module_articlecard__T-Ylh')
        st.info(f"Number of article cards found: {len(article_cards)}")

        if not article_cards:
            st.warning("No article cards found with the specified class. HTML selectors might have changed.")
            # Optional: Save HTML for debugging if nothing is found
            # with open("debug_f1_news_failed_scrape.html", "w", encoding="utf-8") as f:
            #     f.write(soup.prettify())
            # st.info("Page HTML saved to 'debug_f1_news_failed_scrape.html' for inspection.")

        for i, card in enumerate(article_cards):
            # Find the <a> tag that contains the article title and link
            link_tag = card.find('a', class_='ArticleListCard-module_title__-4ovb')
            if link_tag:
                title = link_tag.get_text(strip=True)
                relative_url = link_tag.get('href')
                if relative_url:
                    # Construct the full article URL
                    full_url = f"https://www.formula1.com{relative_url}"
                    articles.append({"title": title, "url": full_url})
                    if i < 3: # Show the first 3 for quick feedback in Streamlit
                        st.write(f"  Article found: **{title}**")
            else:
                st.info(f"  Title link not found in card {i}.") # Helps debug incomplete cards

    except requests.exceptions.RequestException as e:
        st.error(f"Network or HTTP error fetching articles: {e}. Check your connection or the URL.")
        return []
    except Exception as e:
        st.error(f"Unexpected error processing article HTML: {e}")
        return []
    return articles

def extract_article_content(url):
    """
    Extracts the main text content from an individual article on Formula1.com.
    Selectors might need adjustment if the article structure changes.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Try to find the main container of the article body.
        # These classes are common, but can vary.
        article_body = soup.find('div', class_='ArticleContent-module_content__w0P_T')
        if not article_body:
            # Fallback to try finding the article body in other common classes
            article_body = soup.find('div', class_='f1-article--body') # Another possible selector
        if not article_body:
            article_body = soup.find('article') # Or the <article> tag
        
        if article_body:
            # Extract all text from paragraphs within the article body
            paragraphs = article_body.find_all('p')
            text_content = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            return text_content
        else:
            st.warning("Could not find the main article body with known selectors. Attempting broader extraction.")
            # Fallback: Extract all visible text from the page, may include navigation and other elements
            return soup.get_text(separator='\n', strip=True)

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching article content: {e}")
        return None
    except Exception as e:
        st.error(f"Error parsing article content: {e}")
        return None

# --- Streamlit Layout ---
st.set_page_config(page_title="F1 Insights", layout="wide") # Browser tab icon

st.title("F1 Insights with AI and Real-time Data 🏎️📊")

st.markdown("""
This interactive application allows you to explore Formula 1 driver data using the
**OpenF1 API** and analyze recent news from Formula1.com with the power of **artificial intelligence (Google Gemini)**.
""")

# --- F1 Drivers Section ---
st.markdown("---")
st.header("Formula 1 Drivers 🚦")

driver_search_query = st.text_input("🔍 **Search driver by full name** (e.g., 'Max Verstappen', 'Lewis Hamilton'):")

col1, col2 = st.columns(2)

with col1:
    if st.button("Search Driver 🏎️"):
        if driver_search_query:
            with st.spinner("Searching for driver(s)..."):
                drivers_data = get_drivers(driver_search_query)
                if drivers_data:
                    st.subheader(f"Search Results for '{driver_search_query}':")
                    for driver in drivers_data:
                        st.write(f"**Name:** {driver.get('full_name', 'N/A')}")
                        st.write(f"**Country:** {driver.get('country_code', 'N/A')}")
                        st.write(f"**Car Number:** {driver.get('driver_number', 'N/A')}")
                        st.write(f"**OpenF1 ID:** {driver.get('driver_id', 'N/A')}")
                        if driver.get('headshot_url'):
                            st.image(driver['headshot_url'], width=100)
                        st.markdown("---")
                else:
                    st.warning("No driver found with that name or API error.")
        else:
            st.warning("Please enter a driver name to search.")

with col2:
    if st.button("List All Active Drivers (Recent) 🏁"):
        # Note: The OpenF1 API returns many drivers, this might be slow.
        # Consider adding a season filter here if the API easily supports it.
        with st.spinner("Listing all drivers (this might take a moment)..."):
            all_drivers = get_drivers() # Fetches all without name filter
            if all_drivers:
                st.subheader("All Active Drivers (Limited to 20 for demonstration):")
                # To avoid loading hundreds of drivers and keep the interface responsive, we limit the display
                for driver in all_drivers[:20]: 
                    st.write(f"**Name:** {driver.get('full_name', 'N/A')}, **Country:** {driver.get('country_code', 'N/A')}, **Number:** {driver.get('driver_number', 'N/A')}")
                if len(all_drivers) > 20:
                    st.info(f"Showing the first 20 out of {len(all_drivers)} drivers. For more, use the specific search.")
            else:
                st.warning("Could not list drivers from the OpenF1 API.")


# --- Formula 1 News Section ---
st.markdown("---")
st.header("Formula 1 News Analysis 📰🤖")

st.subheader("Latest Articles from Formula1.com")
if st.button("Load Latest F1.com News 🔄"):
    with st.spinner("Loading news..."):
        latest_articles = fetch_f1_latest_articles()
        if latest_articles:
            # Store articles in session state so they are not lost on page reload
            st.session_state['latest_articles'] = latest_articles
            st.success("News loaded! Select one from the list below for analysis.")
        else:
            st.error("Could not load the latest articles. Check the error messages above.")

# Display the selectbox only if articles are loaded in session state
if 'latest_articles' in st.session_state and st.session_state['latest_articles']:
    st.write("---")
    st.markdown("### 📝 Select an Article for Analysis")
    
    # Create a dictionary to map titles to URLs for the selectbox
    # This ensures we have the correct URL associated with the selected title
    article_options_map = {article['title']: article['url'] for article in st.session_state['latest_articles']}
    
    # Add an empty option at the beginning to force the user to make an active selection
    selected_title = st.selectbox(
        "Choose an article from the list:", 
        ["-- Select an article --"] + list(article_options_map.keys()),
        index=0 # Starts with the empty option selected
    )

    # Check if a valid article was selected (not the empty option)
    if selected_title and selected_title != "-- Select an article --":
        selected_url = article_options_map[selected_title]
        st.info(f"Article selected for analysis: **[{selected_title}]({selected_url})**")
        
        # Store the selected URL in session state for later use in analysis
        st.session_state['current_article_url'] = selected_url

        if st.button("Analyze Selected Article with AI ✨"):
            if 'current_article_url' in st.session_state and st.session_state['current_article_url']:
                with st.spinner(f"Extracting and analyzing the article '{selected_title}' with AI..."):
                    article_content = extract_article_content(st.session_state['current_article_url'])
                    
                    if article_content:
                        st.subheader("Full Extracted Content (First 500 words):")
                        # Limit content display to avoid overwhelming the interface
                        st.text_area("Article Text", article_content[:500] + "..." if len(article_content) > 500 else article_content, height=200, disabled=True)

                        st.subheader("AI Analysis Results:")
                        
                        st.markdown("#### 📖 Article Summary")
                        summary = summarize_text(article_content)
                        st.write(summary)

                        st.markdown("#### 👤 Key Entities")
                        entities = analyze_entities(article_content)
                        if entities:
                            for entity in entities:
                                st.write(f"- {entity}")
                        else:
                            st.info("No key entities found.")

                        st.markdown("#### 😊 Sentiment Analysis")
                        sentiment_output = analyze_sentiment(article_content) 
                        st.write(sentiment_output)
                    else:
                        st.error("Could not extract article content from the provided URL. Try another article.")
            else:
                st.warning("Please select an article before attempting to analyze.")
    else:
        st.info("Awaiting your article selection...")
else:
    st.info("Click 'Load Latest F1.com News' to see available articles.")

st.markdown("---")
st.markdown("Developed with ❤️ and F1 & Google Gemini APIs.")