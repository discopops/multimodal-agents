# 👨‍💻 Multimodal-agency

An intelligent multi-agent system built that understands and works with text, images, code, and web pages.

## ✨ What Makes It Multi-Modal?

**Multi-modal** means these agents can work with different types of content simultaneously:

- 📝 **Text**: Write code, documentation, analysis reports.
- 🖼️ **Images**: Generate, edit, and analyze images; capture screenshots.
- 💻 **Files**: Read, write, and modify files.

### How Multi-Modal Tools Work

Each agent has specialized tools that can return different types of content. For example:

Tool can return an image for an agent to analyze:

```python
@function_tool
def load_image():
    # Image loading logic here
    return ToolOutputImage(type="image", image_url=f"data:image/png;base64,{image_b64}", detail="auto")
```

This way, no additional user input is needed for the agent to "see" the provided image.

Similarly agents can receive file output (for now OpenAI supports only PDF files):

```python
@function_tool
def load_report():
    # File loading logic here
    return ToolOutputFileContent(file_data=b64_encoded_file, filename=filename)
```

This is powered by the OpenAI Agents SDK's ability to [return images and files from tools](https://openai.github.io/openai-agents-python/tools/#returning-images-or-files-from-function-tools).

## 🔥 Key Features

- **Developer Agent (AgencyCodeAgent)**: Full code editing, search, git, bash, and notebook tools.
- **QA Agent**: Selenium-powered browser automation for DOM discovery, interaction, screenshots.
- **Data Analyst Agent**: Plotting and dashboard screenshot tools for quick analysis tasks.

The entrypoint `agency.py` loads `.env`, selects the model (default `gpt-5`), creates agents, wires coder → QA communication, and launches the terminal demo.

## 🚀 Quick start

1. Create and activate a virtual environment (Python 3.13), then install deps:

   ```
   python3.13 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

2. Try the agency (terminal demo):

   macOS:

   ```
   sudo python agency.py
   ```

   Windows/Linux:

   ```
   python agency.py
   ```

- Don't forget to run the command with sudo if you're on macOS.
- The agent won't be able to edit files outside of your current directory.

## ⚙️ Models & Configuration

- Select your model in `agency.py` (default: `gpt-5`).
- Put secrets in `.env` (not committed); `dotenv` is loaded in `agency.py`.
- Model behavior is standardized via `shared/agent_utils.py` (instructions selection, reasoning settings, provider extras).

## 🎨 Customization Guide

This guide walks you through customizing the existing agents to fit your specific needs.

**Common Customization Scenarios:**

1. Adding new tools to an existing agent
2. Modifying agent instructions/personality
3. Adjusting tool behavior
4. Extending shared utilities
5. Changing agent communication flows
6. Swapping APIs or integrations

---

#### Example: Adding New Tools to an Existing Agent

Let's say you want to add **accessibility testing** to the QA Agent. Here's the complete workflow:

**Step 1: Understand What You Need**

First, research the new capability:

- What specific feature do you want to add?
- Are there existing tools/APIs for this?
- Does it fit the agent's current role?

**Example: Adding Accessibility Testing to QA Agent**

```bash
# Research accessibility testing options
- axe-core library (popular, comprehensive)
- WCAG 2.1 compliance checking
- Color contrast analysis
- Keyboard navigation testing

# Decision: Use axe-core via Selenium integration
```

**Action checklist:**

- Define the new capability clearly
- Research available libraries/APIs
- Check if it aligns with the agent's existing purpose
- Review the agent's current tools to understand patterns

---

**Step 2: Review Existing Agent Structure**

Navigate to the agent's folder and understand its current organization:

```bash
# Look at the QA agent structure
qa_agent/
├── __init__.py
├── qa_agent.py                    # Agent factory - where we'll wire the new tool
├── instructions.md                # Instructions - we'll update these
└── tools/
    ├── __init__.py               # We'll export our new tool here
    ├── discover_elements.py
    ├── get_page_screenshot.py
    ├── interact_with_page.py
    └── utils/                     # Check if we can reuse utilities
    ├── __init__.py
        ├── browser_utils.py      # ✅ Can reuse browser session!
        ├── image_utils.py
        └── session_manager.py
```

---

**Step 3: Create the New Tool**

Create your new tool file following the agent's existing patterns:

```python
# qa_agent/tools/check_accessibility.py
from agents.tool import function_tool
from axe_selenium_python import Axe
from .utils.browser_utils import get_browser

@function_tool
def check_accessibility(url: str) -> str:
    """Run accessibility audit on a webpage using axe-core.

    Checks for WCAG 2.1 Level A and AA violations including:
    - Color contrast issues
    - Missing alt text
    - Keyboard navigation problems
    - ARIA attribute errors

    Args:
        url: The webpage URL to audit

    Returns:
        String with accessibility report
    """
    try:
        # Reuse existing browser session manager (same pattern as other tools)
        driver = get_browser()
        driver.get(url)

        # Run axe accessibility checks
        axe = Axe(driver)
        axe.inject()
        results = axe.run()

        # Format results
        violations = results.get("violations", [])
        if not violations:
            report = f"✅ No accessibility violations found on {url}"
        else:
            report = f"⚠️ Found {len(violations)} accessibility issues on {url}:\n\n"
            for i, violation in enumerate(violations[:10], 1):  # Limit to top 10
                report += f"{i}. {violation['help']}\n"
                report += f"   Impact: {violation['impact']}\n"
                report += f"   Affected elements: {len(violation['nodes'])}\n\n"

        # Return plain string for text output
        return report
    except Exception as e:
        return f"Error checking accessibility: {str(e)}"
```

**Key patterns to follow:**

- Use `@function_tool` decorator
- Reuse existing utilities (`get_browser()` in this case)
- **For text output:** Return plain strings
- **For image output:** Return `ToolOutputImage` objects (or list of them)
- **For mixed output:** Return list combining strings and `ToolOutputImage` objects
- Include comprehensive docstring
- Add proper error handling

**Return type examples:**

```python
# Text only - return string
return "Analysis complete"

# Single image - return ToolOutputImage
return ToolOutputImage(
    type="image",
    image_url=f"data:image/png;base64,{image_b64}",
    detail="auto"
)

# Multiple images - return list
return [
    ToolOutputImage(image_url=f"data:image/png;base64,{img1_b64}"),
    ToolOutputImage(image_url=f"data:image/png;base64,{img2_b64}")
]
```

---

**Step 4: Update Dependencies**

Add any new libraries to `requirements.txt`:

```bash
# Add to requirements.txt
axe-selenium-python==2.1.6
```

Install and test:

```bash
python -m pip install axe-selenium-python==2.1.6
```

---

**Step 5: Export the Tool**

Add your new tool to the agent's exports:

```python
# qa_agent/tools/__init__.py
from .check_accessibility import check_accessibility  # NEW
from .discover_elements import discover_elements
from .get_page_screenshot import get_page_screenshot
from .interact_with_page import interact_with_page

__all__ = [
    "check_accessibility",  # NEW
    "discover_elements",
    "get_page_screenshot",
    "interact_with_page",
]
```

---

**Step 6: Test the Tool in Isolation**

Test your tool directly before integrating. Here's the correct way to test function tools:

```python
# qa_agent/tools/check_accessibility.py
# Add this at the bottom of your tool file for quick testing

if __name__ == "__main__":
    import asyncio
    import json
    from agency_swarm import MasterContext, RunContextWrapper

    # Create context for tool execution
    ctx = MasterContext(user_context={}, thread_manager=None, agents={})
    run_ctx = RunContextWrapper(context=ctx)

    # Test the tool
    result = asyncio.run(
        check_accessibility.on_invoke_tool(
            run_ctx,
            json.dumps({"url": "https://www.example.com"})
        )
    )
    print(result)
```

Run the test:

```bash
python qa_agent/tools/check_accessibility.py
```

**For pytest integration tests:**

```python
# tests/test_qa_accessibility.py
import pytest
import asyncio
import json
from agency_swarm import MasterContext, RunContextWrapper
from qa_agent.tools import check_accessibility

@pytest.fixture
def tool_context():
    """Create tool execution context"""
    ctx = MasterContext(user_context={}, thread_manager=None, agents={})
    return RunContextWrapper(context=ctx)

def test_check_accessibility_valid_url(tool_context):
    """Test accessibility checker on a real webpage"""
    result = asyncio.run(
        check_accessibility.on_invoke_tool(
            tool_context,
            json.dumps({"url": "https://www.example.com"})
        )
    )

    assert isinstance(result, str)
    assert "accessibility" in result.lower()

def test_check_accessibility_error_handling(tool_context):
    """Test error handling for invalid URL"""
    result = asyncio.run(
        check_accessibility.on_invoke_tool(
            tool_context,
            json.dumps({"url": "invalid-url"})
        )
    )
    assert "Error" in result
```

Run tests:

```bash
pytest tests/test_qa_accessibility.py -v
```

---

**Step 7: Update Agent Instructions**

Open the agent's `instructions.md` and add documentation for your new tool:

```markdown
# qa_agent/instructions.md

# QA Analyst Agent

## Role

You are an expert QA engineer specializing in web testing, bug detection, and quality assurance.

## Core Capabilities

1. Navigate and interact with web applications
2. Discover and analyze UI elements
3. Capture screenshots for visual verification
4. **Check accessibility compliance (NEW)** ← Add this
   ...

## Tools at Your Disposal

### check_accessibility (NEW) ← Add this section

Runs comprehensive accessibility audits using axe-core. Use this to:

- Check WCAG 2.1 Level A/AA compliance
- Identify color contrast issues
- Find missing alt text
- Detect keyboard navigation problems

**When to use:** After testing core functionality, or when specifically asked to check accessibility.

### discover_elements

Finds interactive elements on the page (buttons, links, forms, etc.)...

(rest of existing tools)
...

## Workflow Guidelines

1. **Basic Functional Testing**

   - Navigate to the URL
   - Discover elements
   - Interact and verify behavior
   - Capture screenshots

2. **Accessibility Testing (NEW)** ← Add this workflow
   - Run check_accessibility on key pages
   - Review violations by severity
   - Report issues with clear descriptions
   - Suggest remediation steps
     ...
```

**What to update:**

- Add the tool to the "Core Capabilities" list
- Document the tool in "Tools at Your Disposal"
- Add workflow guidance for when/how to use it
- Update any relevant examples

---

**Step 8: Wire the Tool into the Agent (Optional)**

If you're not using tools_folder - update the agent factory to include your new tool:

```python
# qa_agent/qa_agent.py
from agents import Agent
from pathlib import Path
from .tools import (
    check_accessibility,    # NEW - Add import
    discover_elements,
    get_page_screenshot,
    interact_with_page,
)

def create_qa_agent(
    model: str = "gpt-4o",
    reasoning_effort: str = "medium"
) -> Agent:
    """Create a QA Analyst agent with browser automation tools."""

    instructions_path = Path(__file__).parent / "instructions.md"
    with open(instructions_path) as f:
        instructions = f.read()

    return Agent(
        name="QA Analyst",
        instructions=instructions,
        model=model,
        tools=[
            check_accessibility,    # NEW - Add to tools list
            discover_elements,
            get_page_screenshot,
            interact_with_page,
        ],
        supports_parallel_tool_calls=True,
    )
```

---

**Step 9: Test End-to-End**

Test your customization with the full agent:

**Manual testing:**

```bash
python agency.py
```

Try queries that use the new tool:

```
User: "@QAAgent test the login page at https://example.com"
(Agent tests functionality)

User: "Now check if it's accessible"
(Agent should use check_accessibility tool)
```

**Integration test:**

```python
# tests/test_qa_integration.py
import pytest
from qa_agent import create_qa_agent

@pytest.mark.asyncio
async def test_qa_with_accessibility():
    """Test that QA agent can perform accessibility checks"""
    agent = create_qa_agent(model="gpt-4o")

    # Test that the tool is available
    tool_names = [tool.name for tool in agent.tools]
    assert "check_accessibility" in tool_names
```

---

**Step 10: Lint, Format, and Finalize**

Run quality checks:

```bash
# Format code
ruff format qa_agent/

# Check for issues
ruff check qa_agent/ --fix

# Run all QA tests
pytest tests/test_qa* -v

# Test in production
python agency.py
```

---

### Tips for Successful Customization

**Start Small:** Add one tool or change one thing at a time

**Test Incrementally:** Don't wait until everything is done to test

**Reuse Existing Code:** Check other agents for utilities you can reuse (we reused browser utils across QA and Data Analyst)

**Follow Existing Patterns:** Match the code style, tool structure, and naming conventions

**Document as You Go:** Add comments and update agent capability descriptions

---

### Common Customization Pitfalls

❌ **Skipping instructions updates** → Agent won't know when/how to use new features

❌ **Breaking existing functionality** → Always test existing tools after changes

❌ **Not testing with real data** → Synthetic tests don't catch real issues

❌ **Overcomplicating tools** → Keep tools focused on one task

❌ **Forgetting dependencies** → Update requirements.txt immediately

❌ **Inconsistent patterns** → Follow the agent's existing code style

## 🛠️ Built-in Agents & Tools

### AgencyCodeAgent (Developer)

**What it does:** Your coding partner that can read, write, and modify code files, run commands, and manage git operations.

**Tools:** `Read`, `Write`, `Edit`, `MultiEdit`, `Grep`, `Glob`, `Bash`, `Git`, `TodoWrite`, notebook editors
**Use when:** You need to build features, fix bugs, refactor code, or run tests

### QA Agent

**What it does:** Automates web testing by navigating sites, clicking buttons, filling forms, and capturing screenshots.

**Tools:** DOM discovery, page interaction, screenshot capture (Selenium-powered)
**Use when:** You need to test web applications, verify UI behavior, or capture visual bugs

### Data Analyst Agent

**What it does:** Analyzes data and creates visual representations like charts and graphs.

**Tools:** `plot_chart.py`, `get_page_screenshot.py`
**Use when:** You need to visualize data, create reports, or extract insights from dashboards

### Ad Creator Agent

**What it does:** Generates and edits visual content for marketing and creative projects.

**Tools:** `generate_image.py`, `edit_image.py`, `combine_images.py`
**Use when:** You need logos, ad creatives, image compositions, or visual assets

## 💡 Real-World Use Cases

### Building & Testing a Feature End-to-End

```
You: "Build a user login page with email/password fields, then test it"

1. AgencyCodeAgent creates the login component
2. Automatically hands off to QA Agent
3. QA Agent opens the page, tests form inputs, captures screenshots
4. Returns test results + screenshots to you
```

### Data Analysis with Visualization

```
You: "@DataAnalystAgent analyze my sales dashboard at https://dashboard.example.com"

1. Data Analyst navigates to the dashboard
2. Captures screenshot to "see" the data
3. Extracts metrics and creates trend charts
4. Returns analysis + visual charts
```

### Creating Marketing Materials

```
You: "@AdCreatorAgent create a logo and social media banner for my coffee shop"

1. Ad Creator generates logo based on your description
2. Creates variations with different styles
3. Combines logo with background for banner
4. Returns all visual assets as images
```

### Multi-Agent Collaboration

```
You: "@AgencyCodeAgent build a landing page, test it, and create ad creatives for it"

1. AgencyCodeAgent builds the landing page
2. Hands off to QA Agent for testing
3. QA captures screenshots and validates functionality
4. Ad Creator uses the screenshots to create promotional materials
5. Data Analyst tracks metrics after launch
```

## 🔧 Need More? See the Customization Guide Above

The [Customization Guide](#-customization-guide) section shows you how to:

- Create your own multi-modal tools
- Add new specialized agents
- Modify existing agent behavior
- Change communication flows between agents

## 🧹 Linting & Formatting

- Pre-commit hooks are configured. Run:

  ```
  pre-commit run --all-files
  ```

- If using Ruff locally, format with:

  ```
  ruff check . --fix
  ruff format .
  ```

## 📝 Demo Tasks

### 🎨 Website development

```
Create a shared pixel art canvas like r/place using Next.js and Socket.io:

- 50x50 grid where each player can color one pixel at a time
- 16 color palette at the bottom
- See other players' cursors moving in real-time with their names
- 5-second cooldown between placing pixels (show countdown on cursor)
- Minimap in corner showing full canvas
- Chat box for players to coordinate
- Download canvas as image button
- Show "Player X placed a pixel" notifications
- Persist canvas state in JSON file
- Mobile friendly with pinch to zoom

Simple and fun - just a shared canvas everyone can draw on together. Add rainbow gradient background.

Ask QA agent to perform a qa once finished developing.
```

### 🖼️ Ad creative generation

```
Create an ad creative package for a new product, then generate its logo.

Product: "Lumos LED Desk Lamp" — dimmable, eye-care desk lamp with adjustable color temperature.

- Ad requirements:
  - Produce an ad post highlighting eye-care LEDs, stepless dimming, and 4 color temps (warm to cool).
  - Add a short tagline "Bright Ideas, Gentle on Eyes".

- Logo requirements:
  - Generate a 1024x1024 logo for Lumos with a clean, modern aesthetic.
  - Use a palette of cool white (#F5F8FF), slate gray (#2A2F3A), and electric blue accent (#2D7DFF); prefer a minimal vector lamp/beam motif.
```

### 📈 Dashboard analysis

```
Analyze my dashboard: [DASHBOARD_VIEW_URL] and provide insides on the current performance. Extract hidden trends and build a graph for future estimates.
```

### 📈 Dataset analysis

Pre-requisites:
Publicly available dataset, that agent would be able to download by following provided url.

You can setup a server with a demo dataset by following steps below:

1. Navigate to test files folder

   ```bash
   cd data_analyst_agent\test_files
   ```

2. Start http server

   ```bash
   python -m http.server 8080 --bind 0.0.0.0
   ```

3. Use the following url when querying the agent
   ```txt
   http://localhost:8080/test_file.csv
   ```

Ask agent the following:

```
Analyze the store data at [FILE_URL] and provide me with some estimates on the further dynamics.
```
