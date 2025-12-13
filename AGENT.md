# Multimodal-agency

## Summary
Multimodal-agency is an intelligent multi-agent system designed to work with various content types including text, images, code, and web pages, enabling agents to perform complex tasks through specialized tools and collaborative workflows.

## Key Technologies & Frameworks
- **Agent Orchestration**: `agency-swarm`, `openai-agents` SDK
- **Programming Language**: Python 3.13
- **Web Automation**: Selenium, Playwright (implied by context), `beautifulsoup4`
- **Code & Version Control**: `dulwich` (Git), Jupyter for notebooks
- **Image Processing**: `pillow`
- **Data Visualization**: `matplotlib`
- **AI/ML**: Google Gemini API (`google-genai`)
- **Testing**: `pytest`, `pytest-asyncio`
- **Utilities**: `pydantic`, `dotenv`

## Main Features
- **Developer Agent (AgencyCodeAgent)**: Full code editing, search, Git, Bash, and Jupyter notebook tools.
- **QA Agent**: Selenium-powered browser automation for DOM discovery, interaction, screenshots, and accessibility checks.
- **Data Analyst Agent**: Plotting, dashboard screenshot tools, and data analysis capabilities.
- **Ad Creator Agent**: Generates, edits, and combines visual content like logos and ad creatives.
- **Multi-modal Capabilities**: Agents can process and generate text, images, and files directly.
- **Collaborative Workflows**: Agents can communicate and hand off tasks to each other (e.g., Coder to QA).

## Architectural Patterns
- **Multi-Agent System**: Composed of several specialized agents working cooperatively.
- **Tool-Based Architecture**: Each agent is equipped with a distinct set of tools tailored to its role.
- **Modularity & Extensibility**: Designed for easy addition of new tools, agents, and customization of existing behaviors.
- **Configurable**: Utilizes `.env` for secrets and `agency.py` for model selection and agent configuration.
- **Standardized Behavior**: Agent instructions and model interactions are managed via shared utilities.