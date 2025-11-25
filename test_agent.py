"""
Test script for the Agent system.

This script tests the agent's ability to understand queries and use tools
to answer questions about the ArticleApproveds database.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

from src.llm import OllamaProvider
from src.agent import Agent, create_agent


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)


async def test_agent_initialization():
    """Test agent initialization."""
    print_section("Testing Agent Initialization")

    try:
        llm = OllamaProvider()
        agent = create_agent(llm)

        print(f"✓ Agent created successfully")
        print(f"  Available tools: {len(agent.get_available_tools())}")
        for tool_name in agent.get_available_tools():
            print(f"    - {tool_name}")

        return True, agent

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False, None


async def test_simple_question(agent: Agent):
    """Test agent with a simple non-database question."""
    print_section("Testing Simple Question (No Tools)")

    try:
        question = "What is Python?"
        print(f"Question: {question}\n")

        response = await agent.process_message(question)

        print(f"✓ Response received!")
        print(f"\nAgent response:")
        print(f"{response}\n")

        # Clear history for next test
        agent.clear_history()

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_count_articles(agent: Agent):
    """Test agent with counting approved articles."""
    print_section("Testing: Count Approved Articles")

    try:
        question = "How many articles have been approved?"
        print(f"Question: {question}\n")

        response = await agent.process_message(question)

        print(f"✓ Response received!")
        print(f"\nAgent response:")
        print(f"{response}\n")

        # Clear history for next test
        agent.clear_history()

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_search_articles(agent: Agent):
    """Test agent with searching for articles."""
    print_section("Testing: Search for Articles")

    try:
        question = "Find articles about safety recalls"
        print(f"Question: {question}\n")

        response = await agent.process_message(question)

        print(f"✓ Response received!")
        print(f"\nAgent response:")
        print(f"{response}\n")

        # Clear history for next test
        agent.clear_history()

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_date_range_query(agent: Agent):
    """Test agent with date range query."""
    print_section("Testing: Date Range Query")

    try:
        question = "Show me articles from November 2025"
        print(f"Question: {question}\n")

        response = await agent.process_message(question)

        print(f"✓ Response received!")
        print(f"\nAgent response:")
        print(f"{response}\n")

        # Clear history for next test
        agent.clear_history()

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_conversation_history(agent: Agent):
    """Test agent with multi-turn conversation."""
    print_section("Testing: Conversation History")

    try:
        questions = [
            "How many approved articles are there?",
            "Can you search for articles about injury?",
        ]

        for i, question in enumerate(questions):
            print(f"Turn {i+1}: {question}\n")

            response = await agent.process_message(question)

            print(f"Agent: {response}\n")
            print("-" * 60)

        print(f"\n✓ Conversation completed!")
        print(f"  History length: {len(agent.get_history())} messages")

        # Clear history for next test
        agent.clear_history()

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_list_recent_articles(agent: Agent):
    """Test agent with listing recent articles."""
    print_section("Testing: List Recent Articles")

    try:
        question = "List 3 recent approved articles"
        print(f"Question: {question}\n")

        response = await agent.process_message(question)

        print(f"✓ Response received!")
        print(f"\nAgent response:")
        print(f"{response}\n")

        # Clear history for next test
        agent.clear_history()

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_streaming_response(agent: Agent):
    """Test agent with streaming response."""
    print_section("Testing: Streaming Response")

    try:
        question = "What can you help me with?"
        print(f"Question: {question}\n")
        print("Streaming response:")
        print("-" * 40)

        async for chunk in agent.stream_response(question):
            print(chunk, end="", flush=True)

        print("\n" + "-" * 40)
        print(f"\n✓ Streaming completed!")

        # Clear history for next test
        agent.clear_history()

        return True

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FLUXION00API - AGENT SYSTEM TESTS")
    print("="*60)

    # Check environment variables
    print(f"\nEnvironment variables:")
    print(f"  URL_BASE_OLLAMA: {os.getenv('URL_BASE_OLLAMA')}")
    print(f"  PATH_TO_DATABASE: {os.getenv('PATH_TO_DATABASE')}")
    print(f"  NAME_DB: {os.getenv('NAME_DB')}")

    # Initialize agent
    success, agent = await test_agent_initialization()
    if not success or not agent:
        print("\n✗ Failed to initialize agent. Stopping tests.")
        return

    tests = [
        ("Simple Question", lambda: test_simple_question(agent)),
        ("Count Approved Articles", lambda: test_count_articles(agent)),
        ("Search Articles", lambda: test_search_articles(agent)),
        ("Date Range Query", lambda: test_date_range_query(agent)),
        ("Conversation History", lambda: test_conversation_history(agent)),
        ("List Recent Articles", lambda: test_list_recent_articles(agent)),
        ("Streaming Response", lambda: test_streaming_response(agent)),
    ]

    results = [("Agent Initialization", success)]

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
