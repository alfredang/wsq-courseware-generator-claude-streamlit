# WSQ Courseware Generator with OpenAI Multi Agents

A comprehensive AI-powered courseware generation platform built with OpenAI Multi Agents and Streamlit. This system automates the creation of educational documents including Course Proposals, Assessment Plans, Learning Guides, and more for workforce skills qualification (WSQ) training programs.

### 🔴 [Live Demo](https://courseware-generator-openai.streamlit.app/)

## 🚀 Quick Start for New Users

### 1. System Requirements
- **Python 3.11+** (Check with `python3 --version`)
- **macOS/Linux/Windows** supported
- **4GB+ RAM** recommended
- **Git** installed
- **uv** installed (modern Python package manager)

### 2. Download & Setup

**Option A: If you received a folder/ZIP file:**
```bash
# 1. Navigate to the downloaded project folder
cd "/path/to/courseware_openai_agents"

# 2. Initialize project with uv
uv venv
source .venv/bin/activate          # macOS/Linux
# OR
.venv\Scripts\activate             # Windows

# 3. Install dependencies (Fast)
uv pip install -r requirements.txt
```

**Option B: If downloading from Git repository:**
```bash
# 1. Clone the repository
git clone https://github.com/alfredang/courseware_openai_agents.git
cd courseware_openai_agents

# 2. Setup with uv
uv venv
source .venv/bin/activate          # macOS/Linux
uv pip install -r requirements.txt
```

### 3. Configure API Keys

**Using Settings UI (Recommended)**
1. Run the app: `streamlit run app.py`
2. Go to **Settings** → **API Keys** tab
3. Add your **OpenRouter API Key** (recommended for access to all models) or individual provider keys.

**Manual Configuration (Fallback)**
Create `.streamlit/secrets.toml`:
```toml
# System Configuration
GENERATION_MODEL = "deepseek/deepseek-chat"

# API Keys - Use Settings UI instead
# OPENROUTER_API_KEY = "sk-or-your_key_here"
```

### 4. Run the Application
```bash
streamlit run app.py
```

### 5. First Use
1. Open browser to `http://localhost:8501`
2. **Set up API Keys**: Go to **Settings** → **API Keys**
3. **Available Models**: DeepSeek-Chat, GPT-4o-Mini, Claude-3.5-Sonnet, Gemini-Flash, Gemini-Pro
4. Select **"Generate CP"** from sidebar
5. Choose **"DeepSeek-Chat"** (Default & Recommended)
6. Upload a TSC document to test

### 💡 Model Recommendations
- **DeepSeek-Chat**: Best overall (performance/cost ratio)
- **GPT-4o-Mini**: Good for simple tasks
- **Claude-3.5-Sonnet**: Excellent for complex reasoning
- **Gemini-Flash**: Fast and cost-effective

## 🚀 Key Features

### Core Document Generation
- **Course Proposal (CP)** - Automated course proposal generation with multi-agent validation
- **Assessment Documents** - Question & Answer papers (SAQ, CS, PP formats)
- **Courseware Suite** - Assessment Plan, Learning Guide, Lesson Plan, Facilitator Guide
- **Course Brochures** - Marketing materials with web scraping automation
- **Document Integration** - Assessment integration into AP annexes
- **Document Verification** - Supporting document validation and entity extraction

### Advanced AI Architecture
- **Multi-Agent Workflows** - Specialized agent teams for different tasks
- **Model Flexibility** - Support for DeepSeek, OpenAI, Anthropic, and Google models via OpenRouter
- **Content Intelligence** - Context-aware content generation
- **Quality Assurance** - Multi-layer validation and error correction

## 📋 Prerequisites

- Python 3.11+
- Streamlit account (for deployment)
- API Keys (via OpenRouter recommended):
  - DeepSeek
  - OpenAI
  - Anthropic
  - Google Gemini

## 🛠 Installation

### Recommended Method (UV)

1. **Install UV (if not installed):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   *Windows users: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`*

2. **Clone and Setup:**
   ```bash
   git clone https://github.com/alfredang/courseware_openai_agents.git
   cd courseware_openai_agents
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

### Legacy Method (pip)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/alfredang/courseware_openai_agents.git
   cd courseware_openai_agents
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 🚀 Quick Start

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud Deployment
1. Push your code to GitHub
2. Connect to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add your secrets in the Streamlit Cloud dashboard
4. Deploy your app

## 📁 Project Structure

```
courseware_autogen/
├── app.py                      # Main Streamlit application
├── settings/                   # Configuration and API management
│   ├── settings.py            # Settings UI and configuration
│   ├── api_manager.py         # API key management
│   └── model_configs.py       # AI model configurations
├── common/                     # Shared utilities
│   ├── common.py              # Common helper functions
│   ├── company_manager.py     # Company/organization management
│   ├── logo/                  # Company logos storage
│   └── prompts/               # AI prompt templates
├── generate_cp/               # Course Proposal generation
│   ├── app.py                 # Streamlit interface
│   ├── agents/                # Multi-agent implementations
│   └── utils/                 # CP-specific utilities
├── generate_assessment/       # Assessment generation (SAQ, CS, PP)
│   ├── assessment_generation.py
│   └── utils/                 # Assessment utilities & templates
├── generate_ap_fg_lg_lp/      # Courseware document generation
│   ├── courseware_generation.py  # AP, FG, LG, LP generation
│   └── utils/                 # Document generators & templates
├── generate_brochure_v2/      # Marketing brochure generation
│   ├── brochure_generation_v2.py
│   └── brochure_template/     # HTML brochure templates
├── add_assessment_to_ap/      # Assessment integration into AP
│   └── annex_assessment.py    # Annex assessment tools
├── check_documents/           # Supporting document tools
│   └── sup_doc.py            # Document verification & extraction
└── requirements.txt           # Python dependencies
```

## 💡 Usage Guide

### 1. Generate Course Proposal
1. Upload TSC (Training Specification Content) document
2. Select AI model (GPT-4o-Mini recommended)
3. Choose CP type (Excel CP or Legacy DOCX)
4. Process and download generated documents

### 2. Generate Assessment Documents
1. Upload Facilitator Guide and Slide Deck
2. Select assessment types (SAQ/CS/PP)
3. Generate and download question-answer sets

### 3. Generate Courseware Suite
1. Upload Course Proposal document
2. Select required documents (AP/FG/LG/LP)
3. Configure organization details
4. Generate complete courseware package

### 4. Additional Features
- **Brochure Generation**: Automated marketing material creation
- **Document Verification**: Entity extraction and validation
- **Assessment Integration**: Merge assessments into AP documents

## 🔧 Configuration

### Model Selection
- **GPT-4o-Mini**: Default for structured tasks (cost-effective)
- **Gemini-2.5-Pro**: Best for content generation
- **GPT5/GPT-4o**: Premium options for complex tasks

### Document Templates
All document templates are located in respective module directories:
- Course Proposal: `generate_cp/templates/`
- Courseware: `generate_ap_fg_lg_lp/input/Template/`
- Assessment: `generate_assessment/utils/Templates/`
- Brochure: `generate_brochure_v2/brochure_template/`

## 🔍 TSC Document Requirements

For optimal results, ensure your TSC documents follow these conventions:

**Learning Unit Format:**
```
LU1: Introduction to Data Analytics (K1, K2, A1)
```

**Topic Format:**
```
Topic 1: Data Collection Methods (K1, A1)
```

**Key Requirements:**
- Include colon (:) after LU/Topic labels
- Use proper Knowledge (K) and Ability (A) factor notation
- Ensure LUs appear before their associated topics

## 🚨 Troubleshooting

### Common Issues

**Import Errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- For UV users: `uv pip install -r requirements.txt` (much faster)
- Check Python version compatibility (3.11+)
- Verify virtual environment is activated

**API Key Issues:**
- Use **Settings → API Keys** tab to manage API keys (recommended)
- For fallback: verify API keys are set in `secrets.toml`
- Check API key validity and quotas
- Ensure correct provider is selected for each model

**Document Processing Errors:**
- Ensure uploaded documents follow TSC formatting requirements
- Check file formats (DOCX for most uploads)

**Memory Issues:**
- Large document processing may require additional memory
- Consider using lighter models for development

## 🔐 Security Notes

- Never commit API keys to version control
- Use Streamlit secrets management for production
- Regularly rotate API keys
- Monitor API usage and costs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following the existing code style
4. Test thoroughly with sample documents
5. Submit a pull request

## 📝 License

This project is proprietary software developed for Tertiary Infotech. All rights reserved.

## 📞 Support

For technical support or questions:
- Check the troubleshooting section above
- Review the comprehensive analysis in `details.md`
- Contact the development team

