"""
Simple LangGraph Agent for CI/CD Testing

This agent has:
- A state with short-term memory
- An initialization node that populates mock data (test and file info)
- An LLM node that calls Azure OpenAI or vLLM
- Minimal configuration for easy testing
- Secure configuration from .env file
"""

import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from config_loader import get_config


# Define nested state structures
class TestInfo(TypedDict):
    """Test information"""

    name: str
    log: str


class FileInfo(TypedDict):
    """File information"""

    name: str
    content: str


# Define the state structure with short-term memory
class AgentState(TypedDict):
    """State with short-term memory for the agent"""

    messages: Annotated[list, "The conversation history"]

    output: str

    test: TestInfo

    file: FileInfo


def init_state_node(state: AgentState) -> AgentState:
    """
    Initialize the state with mock data for testing

    Args:
        state: Current agent state

    Returns:
        Updated state with mock test and file information
    """
    # Load configuration
    config = get_config()
    mock_config = config.mock_config

    # Get mock data from configuration or use defaults
    mock_test = mock_config.get("test", {})
    if not mock_test:
        # Default mock test data if not configured
        mock_test = {
            "name": "test_user_authentication",
            "log": "Test passed: User authentication successful with valid credentials",
        }

    mock_file = mock_config.get("file", {})
    if not mock_file:
        # Default mock file data if not configured
        mock_file = {
            "name": "auth_service.py",
            "content": "def authenticate(user, password):\n    return validate_credentials(user, password)",
        }

    return {"test": mock_test, "file": mock_file}


def llm_node(state: AgentState) -> AgentState:
    """
    Single node that calls an LLM to say Hello!

    Args:
        state: Current agent state with messages

    Returns:
        Updated state with LLM response
    """
    # Load configuration
    config = get_config()
    llm_config = config.llm_config
    provider = llm_config.get("provider", "azure")

    # Initialize LLM based on provider
    if provider == "vllm":
        llm = ChatOpenAI(
            model=llm_config.get("model"),
            base_url=llm_config.get("base_url"),
            api_key=llm_config.get("api_key"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 1000),
        )
    else:  # azure (default)
        llm = AzureChatOpenAI(
            azure_deployment=llm_config.get("deployment_name"),
            azure_endpoint=llm_config.get("azure_endpoint"),
            api_key=llm_config.get("api_key"),
            api_version=llm_config.get("api_version", "2024-08-01-preview"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 1000),
        )

    # # Get the current messages from state
    messages = state.get("messages", [])

    # Call the LLM
    response = llm.invoke(messages)

    # Update state with the response
    return {"messages": messages + [response], "output": response.content}


def create_agent_workflow():
    """
    Create and compile the LangGraph agent

    Returns:
        Compiled agent graph ready to run
    """
    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("init_state", init_state_node)
    workflow.add_node("llm", llm_node)

    # Define the flow: START -> init_state -> llm -> END
    workflow.add_edge(START, "init_state")
    workflow.add_edge("init_state", "llm")
    workflow.add_edge("llm", END)

    # Compile the graph
    agent = workflow.compile()

    return agent


def run_agent():
    """
    Run the agent with a simple "Hello!" test message

    Returns:
        The agent's response
    """
    # Create the agent
    agent = create_agent_workflow()

    # Initial state with a test message
    initial_state = {
        "messages": [HumanMessage(content="What model are you using ?")],
        "output": "",
        "test": {},
        "file": {},
    }

    # Run the agent
    result = agent.invoke(initial_state)

    return result


if __name__ == "__main__":
    # Load environment variables (fallback)
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    print("Running simple LangGraph agent...")
    print("-" * 50)

    # Load and validate configuration
    config = get_config()
    provider = config.get("llm.provider", "azure")

    print(f"\nConfiguration loaded:")
    print(f"  Provider: {provider.upper()}")

    if provider == "vllm":
        print(f"  Model: {config.get('llm.model')}")
        print(f"  Base URL: {config.get('llm.base_url')}")
    else:
        print(f"  Deployment: {config.get('llm.deployment_name')}")
        print(f"  Endpoint: {config.get('llm.azure_endpoint')}")
    print()

    if not config.validate():
        print("\n✗ Configuration validation failed")
        print("\nTo fix this:")
        print("1. Copy env.example to .env:")
        print("   cp env.example .env")
        print("2. Edit .env and add your LLM credentials")

        if provider == "vllm":
            print("\nFor vLLM, export these environment variables:")
            print("   export LLM_PROVIDER='vllm'")
            print("   export VLLM_MODEL='MY_MODEL_NAME'")
            print("   export VLLM_BASE_URL='https://your-endpoint.com/v1'")
            print("   export VLLM_API_KEY='your_api_key_here'")
        else:
            print("\nFor Azure OpenAI, export these environment variables:")
            print("   export AZURE_OPENAI_API_KEY='your_api_key_here'")
            print("   export AZURE_OPENAI_ENDPOINT='your_endpoint_here'")
            print("   export AZURE_OPENAI_DEPLOYMENT='your_deployment_here'")

        print("\n" + "-" * 50)
        print("✗ CI/CD Test: FAILED")
        exit(1)

    try:
        # Run the agent
        result = run_agent()

        # Display results
        print(f"\n✓ Agent executed successfully!")
        print(f"\nOutput: {result['output']}")
        print(f"\nConversation history ({len(result['messages'])} messages):")
        for i, msg in enumerate(result["messages"], 1):
            msg_type = "Human" if isinstance(msg, HumanMessage) else "AI"
            print(f"  {i}. [{msg_type}] {msg.content}")

        # Display mock data
        print(f"\nMock Test Info:")
        print(f"  Name: {result['test']['name']}")
        print(f"  Log: {result['test']['log']}")

        print(f"\nMock File Info:")
        print(f"  Name: {result['file']['name']}")
        print(f"  Content: {result['file']['content'][:50]}...")

        print("\n" + "-" * 50)
        print("✓ CI/CD Test: PASSED")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\n" + "-" * 50)
        print("✗ CI/CD Test: FAILED")
        exit(1)
