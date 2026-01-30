# Getting Started

Follow these steps to set up the WSQ Courseware Generator on your local machine.

## Prerequisites

- **Python 3.11+**
- **Git**
- **uv** (Recommended package manager)
- **Node.js** (Required for MCP servers)

## 1. Installation

### Recommended Method (uv)

```bash
# Clone the repository
git clone https://github.com/alfredang/courseware_openai_agents.git
cd courseware_openai_agents

# Initialize environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### Manual Method (pip)

```bash
git clone https://github.com/alfredang/courseware_openai_agents.git
cd courseware_openai_agents
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Configuration

### API Keys
The application supports multiple providers. You can configure them via the UI:

1. Run the app: `streamlit run app.py`
2. Navigate to **Settings** → **API Keys**
3. Input your keys for **OpenRouter**, **OpenAI**, or **Gemini**.

### Database Configuration
To store company settings and model configurations, ensure your `DATABASE_URL` (PostgreSQL) is set in `.streamlit/secrets.toml` or as an environment variable.

## 3. NotebookLM Setup (Required for Slides Generation)

The **Generate Slides** module uses Google NotebookLM to create slide decks. This requires a one-time login with a Google account.

### Step 1: Install NotebookLM library

```bash
pip install notebooklm-py[browser]
```

### Step 2: Run the login script

```bash
python notebooklm-mcp/login_windows.py
```

This will:
1. Open a Chromium browser window
2. Navigate to Google NotebookLM

### Step 3: Sign in with your Google account

1. Complete the Google login in the browser window
2. Wait until you see the NotebookLM homepage
3. Press **Enter** in the terminal to save your session

Your session is saved locally at `~/.notebooklm/storage_state.json`. This file is **not** pushed to GitHub — each user must log in on their own machine.

### Notes

- **Any Google account works** (personal or workspace Gmail)
- The login only needs to be done **once** per machine
- If your session expires, simply run the login script again
- The slides module also works in **non-agentic mode** (no LLM API tokens needed)
- **Agentic mode** (AI-enhanced) requires an OpenRouter API key configured in Settings (Gemini 2.0 Flash is free)

## 4. Running the App

```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501`.
