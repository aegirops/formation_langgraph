# Simple LangGraph Agent for CI/CD

A minimal LangGraph agent implementation for testing LLM connectivity in CI/CD pipelines.

## Features

- **Short-term memory**: State management with conversation history
- **Single LLM node**: Simple node that calls an LLM to say "Hello!"
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

#### Option A: OpenAI Configuration

Edit `.env` with your OpenAI credentials:

```bash
# Required
OPENAI_API_KEY=your_actual_api_key_here

# Optional - customize as needed
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
OPENAI_API_BASE=https://api.openai.com/v1
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000
```

#### Option B: Azure OpenAI Configuration

Edit `.env` with your Azure OpenAI credentials:

```bash
# Required for Azure
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name

# Optional - customize as needed
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000
```

**Note for Azure:** The `AZURE_OPENAI_DEPLOYMENT_NAME` is the name you gave your deployment in the Azure portal, not the underlying model name (e.g., `my-gpt-4-deployment` not `gpt-4`).

### For CI/CD Pipelines

You can export environment variables directly (no `.env` file needed):

**For OpenAI:**

```bash
export OPENAI_API_KEY="your_api_key_here"
export LLM_MODEL="gpt-3.5-turbo"
```

**For Azure OpenAI:**

```bash
export LLM_PROVIDER="azure"
export AZURE_OPENAI_API_KEY="your_azure_api_key_here"
export AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com"
export AZURE_OPENAI_API_VERSION="2024-08-01-preview"
export AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name"
```

## Usage

### Activate Virtual Environment

Always activate the virtual environment first:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Run the agent directly:

```bash
python simple_agent.py
```

### Deactivate when done:

```bash
deactivate
```

### Use in CI/CD:

```bash
# The script will exit with code 1 on failure, 0 on success
python simple_agent.py
echo $?  # Check exit code
```

### Import and use in your code:

```python
from simple_agent import create_agent, run_agent

# Run the pre-configured test
result = run_agent()
print(result['output'])

# Or create your own agent instance
agent = create_agent()
custom_state = {
    "messages": [HumanMessage(content="Your message here")],
    "output": ""
}
result = agent.invoke(custom_state)
```

## Expected Output

```
Running simple LangGraph agent...
--------------------------------------------------
✓ Agent executed successfully!

Output: Hello! How can I assist you today?

Conversation history (2 messages):
  1. [Human] Say Hello!
  2. [AI] Hello! How can I assist you today?

--------------------------------------------------
✓ CI/CD Test: PASSED
```

## CI/CD Integration Examples

### GitHub Actions

**With OpenAI:**

```yaml
- name: Test LangGraph Agent
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: python simple_agent.py
```

**With Azure OpenAI:**

```yaml
- name: Test LangGraph Agent with Azure
  env:
    LLM_PROVIDER: azure
    AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_API_VERSION: "2024-08-01-preview"
    AZURE_OPENAI_DEPLOYMENT_NAME: ${{ secrets.AZURE_OPENAI_DEPLOYMENT_NAME }}
  run: python simple_agent.py
```

### GitLab CI

**With OpenAI:**

```yaml
test_agent:
  script:
    - pip install -r requirements.txt
    - python simple_agent.py
  variables:
    OPENAI_API_KEY: $OPENAI_API_KEY
```

**With Azure OpenAI:**

```yaml
test_agent_azure:
  script:
    - pip install -r requirements.txt
    - python simple_agent.py
  variables:
    LLM_PROVIDER: azure
    AZURE_OPENAI_API_KEY: $AZURE_OPENAI_API_KEY
    AZURE_OPENAI_ENDPOINT: $AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_API_VERSION: "2024-08-01-preview"
    AZURE_OPENAI_DEPLOYMENT_NAME: $AZURE_OPENAI_DEPLOYMENT_NAME
```

### Jenkins

**With OpenAI:**

```groovy
stage('Test Agent') {
    steps {
        withEnv(["OPENAI_API_KEY=${env.OPENAI_API_KEY}"]) {
            sh 'python simple_agent.py'
        }
    }
}
```

**With Azure OpenAI:**

```groovy
stage('Test Agent with Azure') {
    steps {
        withEnv([
            "LLM_PROVIDER=azure",
            "AZURE_OPENAI_API_KEY=${env.AZURE_OPENAI_API_KEY}",
            "AZURE_OPENAI_ENDPOINT=${env.AZURE_OPENAI_ENDPOINT}",
            "AZURE_OPENAI_API_VERSION=2024-08-01-preview",
            "AZURE_OPENAI_DEPLOYMENT_NAME=${env.AZURE_OPENAI_DEPLOYMENT_NAME}"
        ]) {
            sh 'python simple_agent.py'
        }
    }
}
```

## Configuration Options

All configuration is done via environment variables (loaded from `.env` file):

### Common Settings

- `LLM_PROVIDER`: Provider name - `openai` or `azure` (default: `openai`)
- `LLM_TEMPERATURE`: Response randomness 0.0-1.0 (default: `0.7`)
- `LLM_MAX_TOKENS`: Maximum response tokens (default: `1000`)
- `AGENT_NAME`: Agent identifier (default: `simple_langgraph_agent`)
- `AGENT_VERSION`: Agent version (default: `1.0.0`)

### OpenAI Settings (when `LLM_PROVIDER=openai`)

**Required:**

- `OPENAI_API_KEY`: Your OpenAI API key

**Optional:**

- `LLM_MODEL`: Model name (default: `gpt-3.5-turbo`)
- `OPENAI_API_BASE`: API endpoint URL (default: `https://api.openai.com/v1`)

### Azure OpenAI Settings (when `LLM_PROVIDER=azure`)

**Required:**

- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Your Azure endpoint (e.g., `https://your-resource-name.openai.azure.com`)
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Your deployment name from Azure portal
- `AZURE_OPENAI_API_VERSION`: API version (default: `2024-08-01-preview`)

### Configuration Priority

1. `.env` file in project root
2. System environment variables
3. Default values

## Customization

You can easily customize the agent:

- **Change the LLM model**:
  - For OpenAI: Set `LLM_MODEL` in `.env` (e.g., `gpt-4`, `gpt-4-turbo`)
  - For Azure: Use `AZURE_OPENAI_DEPLOYMENT_NAME` with your deployment name
- **Switch providers**: Set `LLM_PROVIDER` to `openai` or `azure`
- **Use custom endpoints**: Set `OPENAI_API_BASE` for custom OpenAI-compatible services
- **Adjust creativity**: Modify `LLM_TEMPERATURE` (0.0 = deterministic, 1.0 = creative)
- **Add more nodes**: Extend the workflow in `simple_agent.py`
- **Extend the state**: Add more fields to `AgentState`
- **Use different LLM providers**: The code already supports OpenAI and Azure OpenAI

## Security Best Practices

✅ **DO:**

- Store secrets in `.env` file (automatically gitignored)
- Keep `env.example` updated with structure (without real secrets)
- Use environment variables in CI/CD pipelines
- Rotate API keys regularly
- Use different API keys for dev/staging/production

❌ **DON'T:**

- Commit `.env` file with real API keys
- Hardcode secrets in source code
- Share your `.env` file
- Push secrets to version control
- Use production keys in development

## Troubleshooting

**Error: Configuration validation failed**

- Make sure you've created `.env` from `env.example`: `cp env.example .env`
- For OpenAI: Verify `OPENAI_API_KEY` is set in `.env`
- For Azure: Verify all Azure settings are configured (see Azure section below)
- Check that your keys are valid (not placeholder text)

**Error: OPENAI_API_KEY not found**

- Ensure `.env` file exists in project root
- Check that `OPENAI_API_KEY` is set in `.env` or system environment
- Verify `.env` file format (no spaces around `=`)
- If using Azure, make sure `LLM_PROVIDER=azure` is set

**Azure OpenAI specific issues**

- **Missing configuration**: Ensure all required Azure variables are set:
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_DEPLOYMENT_NAME`
  - `AZURE_OPENAI_API_VERSION`
- **Endpoint format**: Azure endpoint should be `https://your-resource-name.openai.azure.com` (no `/v1` suffix)
- **Deployment name**: Use the deployment name from Azure portal, not the model name
- **API version**: Use a valid Azure API version (e.g., `2024-08-01-preview`, `2024-02-15-preview`)
- **Authentication error**: Verify your Azure API key is correct and the resource is active

**Configuration not loading**

- Test the config loader: `python config_loader.py`
- Ensure `python-dotenv` is installed: `pip install python-dotenv`
- Check `.env` file location (must be in project root)

**Import errors**

- Install all dependencies: `pip install -r requirements.txt`
- Verify Python 3.8 or later: `python --version`

**API errors**

- For OpenAI:
  - Verify your API key is valid and active
  - Check your OpenAI account has available credits
  - Ensure `OPENAI_API_BASE` is correct if using custom endpoint
- For Azure:
  - Verify your Azure subscription is active
  - Check that the deployment exists and is running
  - Ensure you have appropriate permissions
  - Verify the API version is supported

## License

MIT
