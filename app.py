import os
import re
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials
import gspread
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credentials = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
gc = gspread.authorize(credentials)


# Load environment variables
load_dotenv()

# Set the API keys
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Groq API Key
GOOGLE_SHEET_CREDENTIALS_PATH = os.getenv("GOOGLE_SHEET_CREDENTIALS_PATH")

def upload_csv_file():
    """Handle CSV file upload and return the data as a pandas DataFrame."""
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
    if uploaded_file is not None:
        try:
            # Read CSV file
            data = pd.read_csv(uploaded_file)
            return data
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")
            return None
    return None

# Streamlit app setup
st.set_page_config(
    page_title="AI Web Scraping and Extraction",
    page_icon="🤖",
    layout="wide"
)

def clean_html_response(html_content):
    """Clean HTML content and extract relevant text."""
    soup = BeautifulSoup(html_content, 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s@.()-]', '', text)
    return text.strip()

def search_for_entity(search_query):
    """Perform web search using ScraperAPI with improved response handling."""
    url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url=https://www.google.com/search?q={search_query}"
    response = requests.get(url)

    if response.status_code == 200:
        try:
            cleaned_text = clean_html_response(response.text)
            sentences = [s.strip() for s in cleaned_text.split('.') if s.strip()]
            return {
                "organic_results": [
                    {"snippet": sentence} for sentence in sentences
                    if len(sentence) > 20
                ]
            }
        except Exception as e:
            return {"error": f"Error processing response: {str(e)}"}
    else:
        return {"error": f"API error: {response.status_code} - {response.text}"}

def extract_info_from_results(search_query, search_results):
    """Extract information using Groq API with improved prompting."""
    if not search_results or 'error' in search_results:
        return None  # Return None if no valid results found

    search_texts = "\n".join([
        result.get('snippet', '')
        for result in search_results.get('organic_results', [])
        if result.get('snippet')
    ])
    
    query_parts = search_query.lower().split(' of ')
    entity_type = query_parts[0] if len(query_parts) > 0 else "information"
    company = query_parts[1] if len(query_parts) > 1 else ""
    
    prompt = f"""Please extract only the {entity_type} for {company} from the following text. 
If no clear {entity_type} is found, respond with 'No specific {entity_type} found'.

Context:
{search_texts}

Extracted Information:"""

    try:
        headers = {
            'Authorization': f'Bearer {GROQ_API_KEY}',
            'Content-Type': 'application/json',
        }

        payload = {
            "model": "mixtral-8x7b-32768",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise information extraction assistant. Extract only the requested information, such as a URL, phone number, or email, without extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 50
        }

        groq_api_url = 'https://api.groq.com/openai/v1/chat/completions'
        response = requests.post(groq_api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            extracted_info = result['choices'][0]['message']['content'].strip()

            # Clean extracted information to isolate core answer
            match = re.search(r'(https?://[^\s>]+|www\.[^\s>]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', extracted_info)
            if match:
                return match.group(0)
            return extracted_info  # Return as is if no further cleaning is needed
        else:
            return None  # Return None for unsuccessful API calls
    except Exception as e:
        return None  # Return None if an error occurs


def read_google_sheet(sheet_id, range_name):
    """Read data from Google Sheets."""
    try:
        creds = Credentials.from_service_account_file(GOOGLE_SHEET_CREDENTIALS_PATH)
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(sheet_id).worksheet(range_name)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error reading Google Sheet: {e}")
        return None

# Streamlit UI
st.title("🤖 AI Scraper Agent")
st.write("Enter a company name and query, and retrieve relevant information.")

# Choose between Google Sheets or CSV upload
st.markdown("<h1 class='main-header'>📂 Upload Data</h1>", unsafe_allow_html=True)
st.write("Upload your data source, either a CSV file or Google Sheet, to begin.")

option = st.radio("Choose data source:", ("Upload CSV", "Google Sheets"), index=0)

data = None
if option == "Upload CSV":
        data = upload_csv_file()
        if data is not None:
            st.subheader("🔍 Uploaded CSV Preview")
            st.dataframe(data)
elif option == "Google Sheets":
        sheet_id = st.text_input("📋 Enter Google Sheet ID:")
        range_name = st.text_input("📌 Enter range (e.g., Sheet1!A1:B10):")
        if st.button("Load Google Sheet"):
            try:
                creds = Credentials.from_service_account_file(GOOGLE_SHEET_CREDENTIALS_PATH)
                gc = gspread.authorize(creds)
                sheet = gc.open_by_key(sheet_id).worksheet(range_name)
                data = pd.DataFrame(sheet.get_all_records())
                st.success("✅ Google Sheet loaded successfully!")
                st.write(data)
            except HttpError as e:
                st.error(f"❌ Error loading Google Sheet: {e}")

# User input for company name and queries
st.markdown("<h1 class='main-header'>🧠 Extract Information</h1>", unsafe_allow_html=True)
st.write("Use AI to extract valuable information from your data.")

company_name = st.text_input("🏢 Enter company name:")
queries = st.text_area("🔍 Enter queries to search (e.g., email address, phone number):")

# Initialize a DataFrame to store extracted information
extracted_data = pd.DataFrame(columns=["Company Name", "Query", "Extracted Information"])

# Get information button
if st.button("Get Information"):
    if company_name and queries:
        query_list = [query.strip() for query in queries.split(',')]  # Split and strip queries
        with st.spinner("Searching..."):
            for query in query_list:
                search_query = f"{query} of {company_name}"
                search_results = search_for_entity(search_query)
                if 'error' not in search_results:
                    extracted_info = extract_info_from_results(search_query, search_results)
                    
                    # Append results to the DataFrame
                    new_data = pd.DataFrame({
                        "Company Name": [company_name],
                        "Query": [query],
                        "Extracted Information": [extracted_info]
                    })
                    extracted_data = pd.concat([extracted_data, new_data], ignore_index=True)
                else:
                    st.error(f"No valid search results found for query: {query}")

            # Display extracted data
            if not extracted_data.empty:
                st.markdown("<h1 class='main-header'>📊 Results</h1>", unsafe_allow_html=True)
                st.write(extracted_data)

                # Option to download the extracted data as CSV
                csv = extracted_data.to_csv(index=False)
                st.download_button(
                     label="💾 Download Results",
                    data=csv,
                    file_name='extracted_info.csv',
                    mime='text/csv'
                )
            else:
                st.error("No valid data extracted.")
    else:
        st.error("Please enter both company name and queries.")


# Save to Google Sheets
if option == "Google Sheets" and st.button("Save to Google Sheets"):
    if company_name and query and data is not None and search_results is not None:
        search_query = f"{query} of {company_name}"
        extracted_info = extract_info_from_results(search_query, search_results)
        if extracted_info:
            creds = Credentials.from_service_account_file(GOOGLE_SHEET_CREDENTIALS_PATH)
            gc = gspread.authorize(creds)
            sheet = gc.open_by_key(sheet_id).worksheet(range_name)
            sheet.append_row([company_name, query, extracted_info])
            st.success("Data saved successfully!")
        else:
            st.error("No data to save.")
    else:
        st.error("Please ensure all required information is available before saving.")
