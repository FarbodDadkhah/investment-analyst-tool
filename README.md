# Investment Analyst Research Tool

A minimalistic yet powerful tool that generates high-quality research sources for investment analysis presentations. Built with Streamlit and OpenAI's GPT-4o-mini.

## Features

- **Structured Research Generation**: Generate 20 curated research links for each sub-objective
- **Investment-Focused**: Designed for VC analysts conducting due diligence on companies
- **Clean Web Interface**: Simple Streamlit UI for easy input and visualization
- **JSON Schema Output**: Structured, validated outputs using OpenAI's JSON schema feature
- **Robust Error Handling**: Automatic retries with exponential backoff
- **Persistent Results**: Auto-saves results to JSON files with timestamps

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure OpenAI API Key

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

Get your API key from: https://platform.openai.com/api-keys

## Usage

### Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Using the Interface

1. **Company Name**: Enter the company you're analyzing (e.g., "Harvey AI")

2. **General Objective**: Select from:
   - Market & Competition
   - Technology & Product
   - Business Model & Go-to-Market
   - Founding Team & Talent
   - Funding & Capital Structure

3. **Sub-Objectives**: Enter 4 specific sub-objectives that break down your general objective

   Example for "Market & Competition":
   - TAM/SAM/SOM for each company specifically
   - Growth drivers and inflection points
   - Market maturity and timing
   - Direct competitor mapping with market shares

4. **Generate**: Click the button and wait 1-2 minutes for results

### Output

- **Web Display**: View results directly in the browser with expandable sections
- **JSON Files**: Results auto-saved to `outputs/CompanyName_TIMESTAMP.json`
- **Structure**: Each sub-objective returns 20 curated research links

## Project Structure

```
companion_investment_analyst/
├── app.py                 # Streamlit web interface
├── src/
│   ├── llm_service.py     # OpenAI API integration
│   └── schemas.py         # Pydantic models for validation
├── outputs/               # Generated JSON results
├── requirements.txt       # Python dependencies
└── .env                   # API key configuration
```

## Example Output

```json
{
  "company_name": "Harvey AI",
  "general_objective": "Market & Competition",
  "research_results": [
    {
      "general_objective": "Market & Competition",
      "sub_objective": "TAM/SAM/SOM for legal tech AI specifically",
      "links": [
        "https://www.gartner.com/...",
        "https://www.mckinsey.com/...",
        ...
      ]
    }
  ]
}
```

## Technical Details

- **Model**: GPT-4o-mini (cost-effective and fast)
- **Framework**: Streamlit for web UI
- **Validation**: Pydantic for data schemas
- **Error Handling**: Automatic retries with exponential backoff
- **Output Format**: Structured JSON using OpenAI's JSON schema feature

## Notes

- Each API call generates exactly 20 research links
- The tool makes 4 API calls (one per sub-objective)
- Results include both display in browser and JSON file output
- Failed requests are logged and reported in the UI
