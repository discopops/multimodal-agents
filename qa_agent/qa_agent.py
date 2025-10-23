import os

# # Add the parent directory to the Python path for imports
# parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# if parent_dir not in sys.path:
#     sys.path.insert(0, parent_dir)

from agency_swarm import Agent, ModelSettings
from openai.types.shared.reasoning import Reasoning

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))


def create_qa_agent(model:str = "gpt-5-mini", reasoning_effort: str = "medium") -> Agent:
    """Factory that returns a fresh QAAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.
    """
    return Agent(
        name="QAAgent",
        description="An agent that performs QA testing of web pages.",
        instructions="instructions.md",
        tools_folder="./tools",
        model=model,
        model_settings=ModelSettings(
            reasoning=Reasoning(summary="auto", effort=reasoning_effort), truncation="auto", parallel_tool_calls=False,
        ),
    )

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    from agency_swarm import Agency
    agent = create_qa_agent()
    agency = Agency(agent)
    agency.terminal_demo()

    from tools.utils.session_manager import session_manager

    session_manager.quit()
