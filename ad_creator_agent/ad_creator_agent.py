import os

from agency_swarm import Agent, ModelSettings
from openai.types.shared.reasoning import Reasoning

# import sys
# parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# if parent_dir not in sys.path:
#     sys.path.insert(0, parent_dir)

# Get the absolute path to the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))


def create_ad_creator(model:str = "gpt-5-mini", reasoning_effort: str = "medium") -> Agent:
    """Factory that returns a fresh QAAgent instance.
    Use this in tests to avoid reusing a singleton across multiple agencies.
    """
    return Agent(
        name="AdCreatorAgent",
        description="An agent that generates advertisement images and logos.",
        instructions="instructions.md",
        tools_folder="./tools",
        model=model,
        model_settings=ModelSettings(
            reasoning=Reasoning(summary="auto", effort=reasoning_effort), truncation="auto"
        ),   
    )

if __name__ == "__main__":
    from dotenv import load_dotenv
    from agency_swarm import Agency

    load_dotenv()
    
    agent = create_ad_creator()
    agency = Agency(agent)
    agency.terminal_demo()
