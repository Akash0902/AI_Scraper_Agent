# AI_Scraper_Agent
This project demonstrates an AI-powered agent that performs web searches to retrieve specific information for entities in a dataset. It leverages LLMs for parsing search results, providing structured outputs via a user-friendly dashboard.

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AI-Agent-Information-Retrieval.git
   cd AI-Agent-Information-Retrieval

#pip install -r requirements.txt

### Usage
- **Dashboard**:
  1. Upload a CSV file or connect a Google Sheet.
  2. Select the primary column for entities (e.g., company names).
  3. Define a query template (e.g., "Get the email of {company}").
  4. Click "Search" to retrieve and display results.
  5. Download results as CSV or save to Google Sheets.

- **Google Sheets Integration**:
  - Authenticate using your Google account.
  - Select a sheet and primary column for queries.

### API Keys
- **SERPAPI_KEY**: For web searches.
- **GROQ_API_KEY**: For leveraging LLM.
- Add these to a `.env` file in the root directory.

### Optional Features
- Multi-field query extraction.
- Robust error handling for failed API queries.

## Demo Video Link 
**Link - https://drive.google.com/file/d/1TjFYV1tmcCZFvuN20KewdMLJrhowuUMJ/view?usp=sharing **

