# Hiring Agent

<p align="center"><strong>A Secure, Zero-Retention Web Application for AI-Powered Resume Analysis and ATS Optimization.</strong></p>

<p align="center">
  <a href="https://github.com/err0rgod/hiring-agent/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/framework-FastAPI-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/llm-Groq-f55036.svg" alt="Groq">
</p>

## Overview

Hiring Agent has evolved from a CLI tool into a full-featured, secure web application built with **FastAPI**. It allows users to upload their resume (PDF), provide a temporary Groq API key, and optionally input a Job Description. The system uses high-speed LLMs via Groq to extract structured data, enrich it with live GitHub signals, and provide a comprehensive, 100-point evaluation dashboard.

### Key Features
- **Modern Web Interface:** Clean, responsive UI built with Tailwind CSS.
- **ATS Optimization Guide:** Get actionable feedback on keyword gaps, formatting, and impact statements.
- **Job Description Alignment:** Optionally paste a JD to get a tailored gap analysis and role alignment strategy.
- **Zero-Retention Security:** Your data is safe. PDFs are processed in a temporary directory and permanently deleted immediately after analysis. API keys are processed entirely in-memory and are never logged or stored.
- **Thread-Safe Concurrency:** The backend is refactored to support multiple users simultaneously without API key leakage.
- **GitHub Enrichment:** Automatically fetches live GitHub stats (stars, commits, languages) if a profile link is found.

---

## Architecture

1. **Frontend:** Server-rendered HTML using Jinja2 and Tailwind CSS.
2. **Backend:** FastAPI handles secure file uploads and concurrent request routing.
3. **Extraction (`pdf.py`):** Uses PyMuPDF4LLM to convert PDF to markdown, then prompts Groq to extract structured JSON (Work, Education, Skills, Projects).
4. **Evaluation (`evaluator.py`):** Scores the structured data across multiple categories (Open Source, Self Projects, Production, Technical Skills) out of a maximum of 100 points.
5. **ATS Optimization:** A dedicated LLM prompt analyzes the raw resume against standard ATS rules (or a provided JD) to generate improvement suggestions.

---

## Quick Start

### 1. Environment Setup

Clone the repository and set up a Python virtual environment:

```bash
git clone https://github.com/err0rgod/hiring-agent.git
cd hiring-agent
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

Install the required packages, including FastAPI, Uvicorn, and the Groq client:

```bash
pip install -r requirements.txt
```

### 3. Run the Web Server

Start the FastAPI application using Uvicorn:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Use the Application

1. Open your browser and navigate to `http://127.0.0.1:8000`.
2. Upload your resume (PDF).
3. Paste your [Groq API Key](https://console.groq.com/keys) (starts with `gsk_...`).
4. *(Optional)* Paste a Job Description for tailored ATS feedback.
5. Click **Analyze Resume** to view your dashboard!

---

## Project Structure

```text
├── app.py                  # FastAPI web server and routes
├── config.py               # Global configuration (e.g., DEVELOPMENT_MODE)
├── evaluator.py            # AI scoring logic and ATS generation
├── github.py               # GitHub API integration
├── llm_utils.py            # LLM provider initialization and JSON extraction
├── models.py               # Pydantic schemas and GroqProvider implementation
├── pdf.py                  # PDF to Markdown and Markdown to JSON extraction
├── score.py                # Main orchestration pipeline
├── templates/              # Jinja2 HTML templates
│   ├── index.html          # Upload form
│   ├── result.html         # Evaluation dashboard
│   └── privacy.html        # Zero-retention privacy policy
└── prompts/
    └── templates/          # Jinja2 prompts for the LLM
```

## Security & Privacy
This application operates on a strict **Zero-Retention** policy:
- Files are saved to a transient system temp folder and destroyed via `shutil` immediately after the response is generated.
- `groq_api_key` variables are scoped locally to the active request thread and cleared when the HTTP request terminates.

## License

[MIT](LICENSE) © Nirbhay Katiyar
