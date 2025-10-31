# Simple LangGraph Agent for CI/CD

A minimal LangGraph agent implementation for testing LLM connectivity in CI/CD pipelines.

## Features

- **Short-term memory**: State management with conversation history
- **Mock data support**: Load test and file data from environment variables (JSON strings)
- **Initialization node**: Populates state with mock data before LLM processing
- **LLM node**: Calls Azure OpenAI or vLLM with configurable parameters
- **Multiple LLM providers**: Support for Azure OpenAI and vLLM (OpenAI-compatible) endpoints
- **Secure configuration**: API keys and sensitive data stored in gitignored `.env` file
- **Environment-based config**: Standard `.env` file approach with JSON support
- **CI/CD ready**: Exit codes and clear success/failure indicators
- **Easy to test**: Minimal dependencies and straightforward setup

## Architecture

```
START → Init State Node → LLM Node → END
            ↓                 ↓
    (Mock data loaded)   (LLM called)
```

The agent maintains state with:

- `messages`: Conversation history (short-term memory)
- `output`: Latest LLM response
- `test`: Test information (name, log) - loaded from environment or defaults
- `file`: File information (name, content) - loaded from environment or defaults

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

### 4. (Optional) Configure Mock Data

You can provide mock test and file data via environment variables as JSON strings. This is useful for:

- Testing with sensitive data that shouldn't be committed
- CI/CD pipelines with environment-specific test data
- Dynamic test scenarios

**Add to your `.env` file (or set as environment variables):**

```bash
# Mock test data - JSON string with 'name' and 'log' fields
MOCK_TEST_DATA='{"name":"test_user_authentication","log":"Test passed: User authentication successful with valid credentials"}'

# Mock file data - JSON string with 'name' and 'content' fields
MOCK_FILE_DATA='{"name":"auth_service.py","content":"def authenticate(user, password):\\n    return validate_credentials(user, password)"}'
```

**Important notes:**

- JSON strings must be valid JSON with proper escaping
- Use `\\n` for newlines in the content
- If not provided, the agent will use default mock data
- Never commit `.env` files with sensitive data
- Consider using `.env.local` for local-only sensitive configurations
