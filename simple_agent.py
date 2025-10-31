"""
Simple LangGraph Agent for CI/CD Testing

This agent has:
- A state with short-term memory
- A single node that calls an LLM to say "Hello!"
- Minimal configuration for easy testing
- Secure configuration from config.json (gitignored)
"""

import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from config_loader import get_config


# Define the state structure with short-term memory
class AgentState(TypedDict):
    """State with short-term memory for the agent"""

    messages: Annotated[list, "The conversation history"]
    output: str


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
    provider = llm_config.get("provider", "openai")

    # Initialize the LLM based on provider
    if provider == "azure":
        llm = AzureChatOpenAI(
            azure_deployment=llm_config.get("deployment_name"),
            azure_endpoint=llm_config.get("azure_endpoint"),
            api_key=llm_config.get("api_key"),
            api_version=llm_config.get("api_version", "2024-08-01-preview"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 1000),
        )
    else:
        # Default to OpenAI
        llm = ChatOpenAI(
            model=llm_config.get("model", "gpt-3.5-turbo"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 1000),
            api_key=llm_config.get("api_key"),
            base_url=llm_config.get("api_base"),
        )

    # Get the current messages from state
    messages = state.get("messages", [])

    # Call the LLM
    response = llm.invoke(messages)

    # Update state with the response
    return {"messages": messages + [response], "output": response.content}


def create_agent():
    """
    Create and compile the LangGraph agent

    Returns:
        Compiled agent graph ready to run
    """
    # Create the graph
    workflow = StateGraph(AgentState)

    # Add the single LLM node
    workflow.add_node("llm", llm_node)

    # Define the flow: START -> llm -> END
    workflow.add_edge(START, "llm")
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
    agent = create_agent()

    # Initial state with a test message
    initial_state = {"messages": [HumanMessage(content="Say Hello!")], "output": ""}

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
    print(f"\nConfiguration loaded:")
    print(f"  Provider: {config.get('llm.provider')}")
    print(f"  Model: {config.get('llm.model')}")
    print(f"  API Base: {config.get('llm.api_base')}")
    print()

    if not config.validate():
        print("\n✗ Configuration validation failed")
        print("\nTo fix this:")
        print("1. Copy env.example to .env:")
        print("   cp env.example .env")
        print("2. Edit .env and add your OPENAI_API_KEY")
        print("\nOr export the environment variable:")
        print("   export OPENAI_API_KEY='your_api_key_here'")
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

        print("\n" + "-" * 50)
        print("✓ CI/CD Test: PASSED")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\n" + "-" * 50)
        print("✗ CI/CD Test: FAILED")
        exit(1)
