# Deployment Guide

## Deploy to Streamlit Cloud (Recommended)

### Prerequisites
1. GitHub account
2. Your API keys ready:
   - OPENAI_API_KEY
   - OPENROUTER_API_KEY
   - LLAMA_CLOUD_API_KEY (for LlamaParse)

### Step 1: Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit for deployment"

# Create GitHub repo and push
# Go to github.com and create a new repository
# Then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set:
   - **Main file path**: `app.py`
   - **Python version**: 3.11 or 3.13

### Step 3: Add Secrets

In Streamlit Cloud app settings, add secrets:

```toml
OPENAI_API_KEY = "sk-..."
OPENROUTER_API_KEY = "sk-or-v1-..."
LLAMA_CLOUD_API_KEY = "llx-..."
DEEPSEEK_API_KEY = "sk-..."
```

### Step 4: Deploy!

Click "Deploy" and wait 2-3 minutes for the app to build and start.

---

## Alternative: Deploy to Hugging Face Spaces (Free)

1. Create account at https://huggingface.co/
2. Create new Space
3. Select "Streamlit" SDK
4. Upload your files or connect GitHub
5. Add secrets in Settings → Repository secrets
6. Your app will be live at: `https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME`

---

## Alternative: Deploy to Railway

1. Go to https://railway.app/
2. Connect GitHub repository
3. Railway auto-detects Streamlit
4. Add environment variables
5. Deploy!

---

## Why NOT Vercel?

❌ Vercel is not suitable because:
- 10-60 second timeout limits (your app needs 2-3 minutes for parsing)
- No persistent storage (cache and generated files lost)
- WebSocket issues with Streamlit
- Expensive ($20/mo Pro plan required)

✅ Use Streamlit Cloud, Hugging Face, or Railway instead!
