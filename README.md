# pa11y-libguides

A couple of streamlit apps to process SpringShare LibGuides for accessibility, vibecoded with help from Claude.AI
NB: you must have pa11y installed to use this https://github.com/pa11y/pa11y go here and install pa11y for your OS


## What This Does

**audit.py** - Checks a list of URLs for accessibility problems using pa11y
- Upload a CSV with URLs
- Get back error counts and descriptions for each page
- Download results to prioritize fixes

**render.py** - Analyzes pa11y results to find patterns
- Shows which problems appear most often
- Identifies which URLs need the most attention
- Provides recommendations for common fixes

## Setup

Install requirements (only needed once):
```bash
pip install -r requirements.txt
```

You'll also need pa11y installed:
```bash
npm install -g pa11y
```

## Usage

Run either app:
```bash
streamlit run audit.py
streamlit run render.py
```

Your browser will open automatically. Upload a CSV and follow the prompts.

## Workflow

1. Run **audit.py** with a CSV containing a column of URLs
2. Download the results CSV
3. Upload that CSV to **render.py** to see aggregated patterns
4. Use the priority list to focus your accessibility improvements

Questions? Reach out: anson@virginia.edu
