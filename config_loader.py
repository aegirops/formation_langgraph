"""
Configuration loader for LangGraph Agent

Supports multiple LLM providers:
- Azure OpenAI
- vLLM (OpenAI-compatible endpoints)

Supports loading configuration from:
1. .env file (primary method)
2. Environment variables
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for the LangGraph agent"""

    def __init__(self, env_path: Optional[str] = None):
        """
        Initialize configuration

        Args:
            env_path: Path to .env file (default: ./.env)
        """
        self.env_path = env_path or os.path.join(os.path.dirname(__file__), ".env")
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_json_env(self, env_var: str, default: Any = None) -> Any:
        """
        Load and parse JSON from environment variable

        Args:
            env_var: Environment variable name
            default: Default value if variable not found or parsing fails

        Returns:
            Parsed JSON value or default
        """
        value = os.getenv(env_var)
        if not value:
            return default

        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse JSON from {env_var}: {e}")
            return default

    def _load_config(self):
        """Load configuration from .env file or environment variables"""
        # Try to load .env file first
        if os.path.exists(self.env_path):
            try:
                from dotenv import load_dotenv

                load_dotenv(self.env_path)
                print(f"✓ Loaded configuration from {self.env_path}")
            except ImportError:
                print(
                    "Warning: python-dotenv not installed, using existing environment variables"
                )
            except Exception as e:
                print(f"Warning: Failed to load {self.env_path}: {e}")
        else:
            print("✓ Using environment variables for configuration")

        # Build configuration from environment variables
        # Get provider from environment (default: azure)
        provider = os.getenv("LLM_PROVIDER", "azure").lower()

        # Common configuration
        base_config = {
            "provider": provider,
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1000")),
        }

        # Provider-specific configuration
        if provider == "vllm":
            llm_config = {
                **base_config,
                "model": os.getenv("VLLM_MODEL", ""),
                "base_url": os.getenv("VLLM_BASE_URL", ""),
                "api_key": os.getenv("VLLM_API_KEY", ""),
            }
        else:  # azure (default)
            llm_config = {
                **base_config,
                "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
                "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                "api_version": os.getenv(
                    "AZURE_OPENAI_API_VERSION", "2024-08-01-preview"
                ),
                "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", ""),
                "model": os.getenv(
                    "AZURE_OPENAI_DEPLOYMENT_NAME", ""
                ),  # For Azure, model is the deployment name
            }

        # Load mock data from environment variables (as JSON strings)
        mock_test = self._load_json_env("MOCK_TEST_DATA", {})
        mock_file = self._load_json_env("MOCK_FILE_DATA", {})

        self._config = {
            "llm": llm_config,
            "agent": {
                "name": os.getenv("AGENT_NAME", "simple_langgraph_agent"),
                "version": os.getenv("AGENT_VERSION", "1.0.0"),
            },
            "mock": {
                "test": mock_test,
                "file": mock_file,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key: Configuration key (e.g., "llm.api_key")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self._config.get("llm", {})

    @property
    def agent_config(self) -> Dict[str, Any]:
        """Get agent configuration"""
        return self._config.get("agent", {})

    @property
    def mock_config(self) -> Dict[str, Any]:
        """Get mock data configuration"""
        return self._config.get("mock", {})

    def validate(self) -> bool:
        """
        Validate that required configuration is present

        Returns:
            True if valid, False otherwise
        """
        provider = self.get("llm.provider", "azure")

        if provider == "vllm":
            # Validate vLLM configuration
            required_keys = ["llm.model", "llm.base_url", "llm.api_key"]
            placeholder_values = [
                "your_vllm_api_key_here",
                "https://your-vllm-endpoint.com/v1",
            ]

            missing_keys = []
            for key in required_keys:
                value = self.get(key)
                if (
                    not value
                    or value == ""
                    or any(
                        str(value) == placeholder for placeholder in placeholder_values
                    )
                ):
                    missing_keys.append(key)

            if missing_keys:
                print(
                    f"✗ Missing required configuration keys for vLLM: {', '.join(missing_keys)}"
                )
                print(
                    f"   Please set these in your .env file or as environment variables"
                )
                print(f"   Required for vLLM:")
                print(f"   - VLLM_MODEL (e.g., 'MY_MODEL_NAME')")
                print(f"   - VLLM_BASE_URL (e.g., 'https://your-endpoint.com/v1')")
                print(f"   - VLLM_API_KEY")
                return False

        else:  # azure (default)
            # Validate Azure OpenAI configuration
            required_keys = [
                "llm.api_key",
                "llm.azure_endpoint",
                "llm.api_version",
                "llm.deployment_name",
            ]
            placeholder_values = [
                "your_azure_api_key_here",
                "https://your-resource-name.openai.azure.com",
                "your-deployment-name",
            ]

            missing_keys = []
            for key in required_keys:
                value = self.get(key)
                if (
                    not value
                    or value == ""
                    or any(
                        str(value) == placeholder for placeholder in placeholder_values
                    )
                ):
                    missing_keys.append(key)

            if missing_keys:
                print(
                    f"✗ Missing required configuration keys for Azure OpenAI: {', '.join(missing_keys)}"
                )
                print(
                    f"   Please set these in your .env file or as environment variables"
                )
                print(f"   Required for Azure OpenAI:")
                print(f"   - AZURE_OPENAI_API_KEY")
                print(f"   - AZURE_OPENAI_ENDPOINT")
                print(f"   - AZURE_OPENAI_API_VERSION")
                print(f"   - AZURE_OPENAI_DEPLOYMENT_NAME")
                return False

        print("✓ Configuration validated successfully")
        return True

    def __repr__(self) -> str:
        """String representation (with masked secrets)"""
        safe_config = self._mask_secrets(self._config.copy())
        return json.dumps(safe_config, indent=2)

    def _mask_secrets(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive values for display"""
        if isinstance(config, dict):
            masked = {}
            for key, value in config.items():
                if any(
                    secret in key.lower()
                    for secret in ["key", "token", "password", "secret"]
                ):
                    if value and len(str(value)) > 8:
                        masked[key] = str(value)[:4] + "..." + str(value)[-4:]
                    else:
                        masked[key] = "***"
                elif isinstance(value, dict):
                    masked[key] = self._mask_secrets(value)
                else:
                    masked[key] = value
            return masked
        return config


# Singleton instance
_config_instance: Optional[Config] = None


def get_config(env_path: Optional[str] = None) -> Config:
    """
    Get or create configuration singleton

    Args:
        env_path: Optional path to .env file

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(env_path)
    return _config_instance


if __name__ == "__main__":
    # Test the configuration loader
    print("Testing configuration loader...")
    print("=" * 50)

    config = get_config()
    print("\nConfiguration:")
    print(config)

    print("\n" + "=" * 50)
    print("Validation:")
    is_valid = config.validate()

    if is_valid:
        print("\n✓ Configuration is ready to use")
    else:
        print("\n✗ Please configure Azure OpenAI in .env file or environment variables")
        print("\nCreate a .env file with:")
        print("AZURE_OPENAI_API_KEY=your_api_key_here")
        print("AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com")
        print("AZURE_OPENAI_API_VERSION=2024-08-01-preview")
        print("AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name")
