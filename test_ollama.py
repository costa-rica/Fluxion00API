"""
Test script for Ollama LLM integration.

This script tests the Ollama provider implementation.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

from src.llm import OllamaProvider, LLMMessage


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)


async def test_connection():
    """Test basic connection to Ollama API."""
    print_section("Testing Ollama Connection")

    try:
        provider = OllamaProvider()
        print(f"✓ Provider initialized")
        print(f"  Base URL: {provider.base_url}")
        print(f"  API Endpoint: {provider.api_endpoint}")
        print(f"  Default Model: {provider.default_model}")
        print(f"  API Key: {'Set' if provider.api_key else 'Not set'}")

        # Test connection
        print("\n  Testing connection with simple prompt...")
        success = await provider.test_connection()

        if success:
            print("✓ Connection test successful!")
            return True
        else:
            print("✗ Connection test failed!")
            return False

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


async def test_simple_generation():
    """Test simple text generation."""
    print_section("Testing Simple Text Generation")

    try:
        provider = OllamaProvider()

        prompt = "What is Python programming language? Answer in one sentence."
        print(f"Prompt: {prompt}\n")

        response = await provider.generate(prompt, max_tokens=100)

        print(f"✓ Response received!")
        print(f"  Model: {response.model}")
        print(f"  Finish Reason: {response.finish_reason}")
        print(f"  Usage: {response.usage}")
        print(f"\nResponse content:")
        print(f"  {response.content}")

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_system_prompt():
    """Test generation with system prompt."""
    print_section("Testing Generation with System Prompt")

    try:
        provider = OllamaProvider()

        system_prompt = "You are a helpful assistant that answers in a very concise manner."
        prompt = "What is FastAPI?"

        print(f"System: {system_prompt}")
        print(f"Prompt: {prompt}\n")

        response = await provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=100
        )

        print(f"✓ Response received!")
        print(f"\nResponse content:")
        print(f"  {response.content}")

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


async def test_chat_format():
    """Test chat format with conversation history."""
    print_section("Testing Chat Format")

    try:
        provider = OllamaProvider()

        messages = [
            LLMMessage(role="system", content="You are a helpful assistant."),
            LLMMessage(role="user", content="What is 2+2?"),
            LLMMessage(role="assistant", content="2+2 equals 4."),
            LLMMessage(role="user", content="What about 3+3?"),
        ]

        print("Conversation:")
        for msg in messages:
            print(f"  {msg.role}: {msg.content}")
        print()

        response = await provider.chat(messages, max_tokens=50)

        print(f"✓ Response received!")
        print(f"\nAssistant response:")
        print(f"  {response.content}")

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


async def test_streaming():
    """Test streaming generation."""
    print_section("Testing Streaming Generation")

    try:
        provider = OllamaProvider()

        prompt = "Count from 1 to 5, one number per line."
        print(f"Prompt: {prompt}\n")
        print("Streaming response:")
        print("-" * 40)

        full_response = ""
        async for chunk in provider.stream_generate(prompt, max_tokens=50):
            print(chunk, end="", flush=True)
            full_response += chunk

        print("\n" + "-" * 40)
        print(f"\n✓ Streaming completed!")
        print(f"  Total length: {len(full_response)} characters")

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_temperature_variation():
    """Test different temperature settings."""
    print_section("Testing Temperature Variation")

    try:
        provider = OllamaProvider()

        prompt = "Say hello"
        temperatures = [0.0, 0.5, 1.0]

        for temp in temperatures:
            print(f"\nTemperature: {temp}")
            response = await provider.generate(
                prompt=prompt,
                temperature=temp,
                max_tokens=30
            )
            print(f"  Response: {response.content[:100]}")

        print(f"\n✓ Temperature variation test completed!")
        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


async def test_available_models():
    """Test getting available models."""
    print_section("Testing Available Models")

    try:
        provider = OllamaProvider()

        models = provider.get_available_models()
        print(f"✓ Available models: {len(models)}")
        for model in models:
            print(f"  - {model}")

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FLUXION00API - OLLAMA INTEGRATION TESTS")
    print("="*60)

    # Check environment variables
    print(f"\nEnvironment variables:")
    print(f"  URL_BASE_OLLAMA: {os.getenv('URL_BASE_OLLAMA')}")
    print(f"  KEY_OLLAMA: {'Set' if os.getenv('KEY_OLLAMA') else 'Not set'}")

    tests = [
        ("Connection Test", test_connection),
        ("Simple Generation", test_simple_generation),
        ("System Prompt", test_system_prompt),
        ("Chat Format", test_chat_format),
        ("Streaming", test_streaming),
        ("Temperature Variation", test_temperature_variation),
        ("Available Models", test_available_models),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ FATAL ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    asyncio.run(main())
