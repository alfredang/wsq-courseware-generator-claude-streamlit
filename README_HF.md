# Hugging Face Spaces Deployment

This app is configured for deployment on Hugging Face Spaces using Docker.

## Setup

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Select "Docker" as the SDK
4. Connect your GitHub repo or upload files
5. Set secrets in Settings:
   - `ANTHROPIC_API_KEY`
   - `DATABASE_URL`
   - `CHAINLIT_AUTH_SECRET`

## Files

- `Dockerfile` - Docker configuration
- `app.py` - Main Chainlit application
