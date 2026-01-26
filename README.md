# WSQ Courseware Generator with OpenAI Multi Agents

A comprehensive AI-powered courseware generation platform built with OpenAI Multi Agents and Streamlit. This system automates the creation of educational documents including Course Proposals, Assessment Plans, Learning Guides, and more for workforce skills qualification (WSQ) training programs.

### 🔴 [Live Demo](https://courseware-generator-openai.streamlit.app/)

## 🚀 Quick Start for New Users

### 1. System Requirements
- **Python 3.11+** (Check with `python3 --version`)
- **macOS/Linux/Windows** supported
- **4GB+ RAM** recommended
- **Git** installed

### 2. Download & Setup

**Option A: If you received a folder/ZIP file:**
```bash
# 1. Navigate to the downloaded project folder
cd "/path/to/courseware_openai_agents"

# 2. Create virtual environment (IMPORTANT - isolates dependencies)
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate          # macOS/Linux
# OR
.venv\Scripts\activate             # Windows

# 4. Install all dependencies (this may take 5-10 minutes)
pip install -r requirements.txt
```

**Option B: If downloading from Git repository:**
```bash
# 1. Clone the repository
git clone https://github.com/alfredang/courseware_openai_agents.git
cd courseware_openai_agents

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate          # macOS/Linux

# 4. Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Keys (2 Options)

**Option A: Using Settings UI (Recommended)**
1. Skip manual configuration - just run the app
2. Go to **Settings** → **API Keys** tab in the web interface
3. Add your API keys through the user-friendly interface
4. Keys are automatically saved and managed

**Option B: Manual Configuration (Fallback)**
```bash
# 1. Create the secrets directory
mkdir -p .streamlit

# 2. Create secrets file
touch .streamlit/secrets.toml

# 3. Add system configuration (API keys now managed via UI):
```

**Edit `.streamlit/secrets.toml`:**
```toml
# System Configuration (required)
GENERATION_MODEL = "gpt-4o"
REPLACEMENT_MODEL = "gpt-4o-mini"
LLAMA_CLOUD_API_KEY = "llx-your_llama_key_here"

# API Keys - Now managed through Settings UI
# These are fallback only - use Settings UI instead
# OPENAI_API_KEY = "sk-proj-your_openai_key_here"
# GEMINI_API_KEY = "AIza-your_gemini_key_here"
# DEEPSEEK_API_KEY = "sk-your_deepseek_key_here"
# OPENROUTER_API_KEY = "sk-or-your_openrouter_key"
# GROQ_API_KEY = "gsk_your_groq_key"
# GROK_API_KEY = "your_grok_key_here"
```

### 4. Run the Application
```bash
# Make sure virtual environment is activated
source .venv/bin/activate          # macOS/Linux

# Start the application
streamlit run app.py
```

### 5. First Use
1. Open browser to `http://localhost:8501`
2. **Set up API Keys**: Go to **Settings** → **API Keys** tab and add your API keys
3. **Available Models**: GPT-5, GPT-4o, GPT-4o-Mini, Gemini-2.5-Pro/Flash, DeepSeek-V3.1, OpenRouter, Groq, Grok-2
4. Select **"Generate CP"** from sidebar
5. Choose **"DeepSeek-V3.1"** model (best value)
6. Upload a TSC document to test
7. Generate your first course proposal!

### 💡 Model Recommendations
- **DeepSeek-3.1**: Best overall (cheap + high quality)
- **Gemini-2.5-Pro**: Best for content generation
- **GPT-4o-Mini**: Cheapest for simple tasks

### 🆘 Common First-Time Issues
**"API key not provided"**: Check your `.streamlit/secrets.toml` file
**"Import errors"**: Restart terminal and reactivate virtual environment
**"pandas security warning"**: Click "Allow" in macOS System Preferences > Privacy & Security

## 🚀 Key Features

### Core Document Generation
- **Course Proposal (CP)** - Automated course proposal generation with multi-agent validation
- **Assessment Documents** - Question & Answer papers (SAQ, CS, PP formats)
- **Courseware Suite** - Assessment Plan, Learning Guide, Lesson Plan, Facilitator Guide
- **Course Brochures** - Marketing materials with web scraping automation
- **Presentation Slides** - AI-powered slide generation (in development)
- **Document Integration** - Assessment integration into AP annexes
- **Document Verification** - Supporting document validation and entity extraction

### Advanced AI Architecture
- **Multi-Agent Workflows** - Specialized agent teams for different tasks
- **Model Flexibility** - Support for OpenAI GPT, Google Gemini, and DeepSeek models
- **Content Intelligence** - RAG-based content retrieval and generation
- **Quality Assurance** - Multi-layer validation and error correction

## 📋 Prerequisites

- Python 3.11+
- Streamlit account (for deployment)
- API Keys for:
  - OpenAI (GPT models)
  - Google Gemini API
  - DeepSeek API (optional)
  - LlamaCloud API (document parsing)

## 🛠 Installation

### Option 1: Standard Installation (pip)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/alfredang/courseware_autogen.git
   cd courseware_autogen
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # OR
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Option 2: UV Installation (Faster & Modern)

1. **Install UV:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.local/bin/env  # Add to PATH
   ```

2. **Clone and set up project:**
   ```bash
   git clone https://github.com/alfredang/courseware_autogen.git
   cd courseware_autogen
   uv venv                    # Create virtual environment
   source .venv/bin/activate  # Activate environment
   uv pip install -r requirements.txt  # Install dependencies (10-100x faster)
   ```

### Benefits of UV:
- ⚡ **10-100x faster** package installation
- 🔒 **Isolated environment** by default (no system conflicts)
- 📋 **Lock file support** for reproducible builds
- 🛡️ **Better dependency resolution**

### Configure API Keys (Both Methods):

**Primary Method**: Use **Settings UI** in the web application (recommended)

**Fallback Method**: Create a `.streamlit/secrets.toml` file:
```toml
# System Configuration
LLAMA_CLOUD_API_KEY = "your_llama_cloud_api_key"
GENERATION_MODEL = "gpt-4o"
REPLACEMENT_MODEL = "gpt-4o-mini"

# API Keys - Use Settings UI instead
# OPENAI_API_KEY = "your_openai_api_key"
# GEMINI_API_KEY = "your_gemini_api_key" 
# DEEPSEEK_API_KEY = "your_deepseek_api_key"
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

