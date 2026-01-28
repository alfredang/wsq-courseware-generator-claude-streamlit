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

## 3. Running the App

```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501`.
