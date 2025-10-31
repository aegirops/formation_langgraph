"""
Simple LangGraph Agent for CI/CD Testing

This agent has:
- A state with short-term memory
- An initialization node that populates mock data (test and file info)
- An LLM analysis node that analyzes test log information
- A notification node that posts analysis to Microsoft Teams via webhook
- Minimal configuration for easy testing
- Secure configuration from .env file
"""

import os
import requests
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
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

    log_analysis: str

    file: FileInfo

    notification_status: str


# Define the Teams notification tool
@tool
def teams_notification_tool(message: str) -> str:
    """
    Post a notification message to Microsoft Teams via webhook.

    Args:
        message: The message content to send to Teams

    Returns:
        Status message indicating success or failure
    """
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL", "")

    if not webhook_url:
        return "Error: TEAMS_WEBHOOK_URL not configured in environment variables"

    # TMP: Remove this when we have a proper message format
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "body": [{"type": "TextBlock", "text": message, "wrap": True}],
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.4",
                },
            }
        ],
    }

    try:
        response = requests.post(webhook_url, json=payload)

        if response.status_code == 200:
            return "✓ Successfully posted notification to Teams"
        else:
            return f"✗ Failed to post to Teams. Status code: {response.status_code}"

    except Exception as e:
        return f"✗ Error posting to Teams: {str(e)}"


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

    # Get mock data from configuration or use defaults
    mock_test = {
        "name": "test_log",
        "log": os.getenv("MOCK_TEST_DATA", ""),
    }

    mock_file = {
        "name": "auth_service.py",
        "content": os.getenv("MOCK_TEST_FILE", ""),
    }

    return {"test": mock_test, "file": mock_file}


def llm_analysis_node(state: AgentState) -> AgentState:
    """
    Node that calls an LLM to analyze the test log information from the state

    Args:
        state: Current agent state with test log data

    Returns:
        Updated state with LLM analysis response
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

    # Get test log from state
    test_info = state.get("test", {})
    test_log = test_info.get("log", "No test log available")

    # Create analysis prompt
    analysis_prompt = f"""Fait moi une synthèse des différents cas de test qui FAIL:

Test Log:
{test_log}

Donne moi la synthèse en Markdown."""

    # Get the current messages from state
    messages = state.get("messages", [])

    # Add the analysis prompt as a new message
    messages_with_prompt = messages + [HumanMessage(content=analysis_prompt)]

    # Call the LLM
    response = llm.invoke(messages_with_prompt)

    # Update state with the response
    return {
        "messages": messages_with_prompt + [response],
        "output": response.content,
        "log_analysis": response.content,
    }


def notify_node(state: AgentState) -> AgentState:
    """
    LLM node that uses the teams_notification_tool to send log analysis to Teams.
    The LLM will decide whether and how to use the tool based on the context.

    Args:
        state: Current agent state with log analysis data

    Returns:
        Updated state with notification status
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

    # Bind the tool to the LLM
    # For vLLM, explicitly set tool_choice to a named tool or "none"
    # vLLM accepts: named tool, "auto", or "none" (not "required")
    if provider == "vllm":
        # Use the tool name directly to force its usage
        llm_with_tools = llm.bind_tools(
            [teams_notification_tool], tool_choice="teams_notification_tool"
        )
    else:
        # Azure OpenAI supports "auto" mode by default
        llm_with_tools = llm.bind_tools([teams_notification_tool])

    # Get log analysis from state
    log_analysis = state.get("log_analysis", "No analysis available")

    # Create notification prompt
    notification_prompt = f"""Tu as généré une analyse de logs de tests. Utilise l'outil teams_notification_tool pour envoyer cette analyse à Microsoft Teams.

Analyse des logs:
{log_analysis}

Poste cette analyse sur Teams en utilisant l'outil disponible."""

    # Get the current messages from state
    messages = state.get("messages", [])

    # Add the notification prompt
    messages_with_prompt = messages + [HumanMessage(content=notification_prompt)]

    # Call the LLM with tools
    response = llm_with_tools.invoke(messages_with_prompt)

    # Check if the LLM wants to use the tool
    notification_status = "No notification sent"
    updated_messages = messages_with_prompt + [response]

    if response.tool_calls:
        # Execute the tool calls
        for tool_call in response.tool_calls:
            if tool_call["name"] == "teams_notification_tool":
                # Execute the tool
                tool_result = teams_notification_tool.invoke(tool_call["args"])
                notification_status = tool_result

                # Add tool result to messages
                tool_message = ToolMessage(
                    content=tool_result, tool_call_id=tool_call["id"]
                )
                updated_messages.append(tool_message)

    # Update state with notification status
    return {
        "messages": updated_messages,
        "notification_status": notification_status,
    }


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
    workflow.add_node("llm_analysis", llm_analysis_node)
    workflow.add_node("notify", notify_node)

    # Define the flow: START -> init_state -> llm_analysis -> notify -> END
    workflow.add_edge(START, "init_state")
    workflow.add_edge("init_state", "llm_analysis")
    workflow.add_edge("llm_analysis", "notify")
    workflow.add_edge("notify", END)

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
        "messages": [],
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

        print(f"\nNotification Status:")
        print(f"  {result.get('notification_status', 'No status available')}")

        print("\n" + "-" * 50)
        print("✓ CI/CD Test: PASSED")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\n" + "-" * 50)
        print("✗ CI/CD Test: FAILED")
        exit(1)
