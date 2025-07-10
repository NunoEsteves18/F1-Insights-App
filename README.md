# F1 Insights App 🏎️✨

This is an interactive Streamlit application that combines data from the [OpenF1 API](https://openf1.org/) with the power of Artificial Intelligence (Google Gemini) to provide dynamic insights into Formula 1 drivers and recent news analysis.

---

## 🚀 Key Features

* **F1 Driver Search and Listing:** Get detailed information about F1 drivers, such as full name, nationality, and car number, directly from the OpenF1 API.
* **F1 News Analysis:** Extract, summarize, and analyze the sentiment and key entities from [Formula1.com](https://www.formula1.com/en/latest) news articles using the advanced Google Gemini model.

---

## 🛠️ Prerequisites

Before you begin, ensure you have **Python installed** (version 3.9 or higher is recommended).

You will also need a **Google Gemini API key**. You can obtain yours for free from [Google AI Studio](https://aistudio.google.com/) or the Google Cloud Console.

---

## 📦 Installation and Setup

Follow these steps to set up and run the application locally:

### 1. Clone the Repository

Start by cloning this repository to your local machine:


```bash
git clone [https://github.com/NunoEsteves18/F1-Insights-App](https://github.com/NunoEsteves18/F1-Insights-App)
cd F1-Insights-App
```

### 2. Create and Activate a Virtual Environment

It's highly recommended to use a virtual environment to manage your project's dependencies.
```bash 
python -m venv venv
```
Activate the virtual environment:
    * ** On Windows (Command Prompt/CMD):
    ```bash 
        .\venv\Scripts\activate
    ```
    * ** On Windows (PowerShell):
    ```bash 
        .\venv\Scripts\Activate.ps1
    ```
    * ** On macOS/Linux:
    ```bash 
        source venv/bin/activate
    ``` 
You'll see (venv) at the beginning of your terminal's command line, indicating the environment is active.

### 3. Install Dependencies

With your virtual environment active, install all the necessary Python libraries:
```bash 
    pip install streamlit requests beautifulsoup4 google-generativeai python-dotenv
```

### 4. Configure Your Google Gemini API Key 🔑
    To keep your API key secure and avoid exposing it directly in your code, we'll use a .env file:
        1. Create a file named .env in the root directory of your project (where app.py is located).
        2. Add your API key to this file in the following format:
            ```bash
                GOOGLE_API_KEY=YOUR_API_KEY_HERE
            ```
            ⚠️ Replace YOUR_API_KEY_HERE with your actual Google Gemini API key. Do not use quotes around it.
        3. Add .env to your .gitignore file to ensure your key is not accidentally committed to GitHub:
            ```bash
                # .gitignore
                .env
            ```

### 5. Run the Streamlit Application ▶️

Finally, execute the application from your terminal:
    ```bash
        streamlit run app.py
    ```
The application will automatically open in your default web browser. If it doesn't, check your terminal for the local URL (usually http://localhost:8501).   