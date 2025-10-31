# Simple LangGraph Agent for CI/CD

A minimal LangGraph agent implementation for testing LLM connectivity in CI/CD pipelines.

## Features

- **Short-term memory**: State management with conversation history
- **Single LLM node**: Simple node that calls an LLM to say "Hello!"
- **Multiple LLM providers**: Support for Azure OpenAI and vLLM (OpenAI-compatible) endpoints
- **Secure configuration**: API keys stored in gitignored `.env` file
- **Environment-based config**: Standard `.env` file approach
- **CI/CD ready**: Exit codes and clear success/failure indicators
- **Easy to test**: Minimal dependencies and straightforward setup

## Architecture

```
START → LLM Node → END
         ↓
    (State: messages, output)
```

The agent maintains state with:

- `messages`: Conversation history (short-term memory)
- `output`: Latest LLM response

## Installation

### 1. Create Virtual Environment

**Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**

```cmd
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Your API Key

Create a `.env` file from the example:

**Linux/macOS:**

```bash
cp env.example .env
nano .env  # Add your API credentials
```

**Windows:**

```cmd
copy env.example .env
notepad .env
```
