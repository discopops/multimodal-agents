# 👨‍💻 Multimodal-agency

An intelligent multi-agent system built that understands and works with text, images, code, and web pages.

## ✨ What Makes It Multi-Modal?

**Multi-modal** means these agents can work with different types of content simultaneously:

- 📝 **Text**: Write code, documentation, analysis reports.
- 🖼️ **Images**: Generate, edit, and analyze images; capture screenshots.
- 💻 **Files**: Read, write, and modify files.

### How Multi-Modal Tools Work

Each agent has specialized tools that can return different types of content. For example:

**QA Agent** can take a screenshot and return it as an image:
```python
# The agent sees the webpage and returns both text analysis AND the actual screenshot
result = await qa_agent.get_screenshot("https://example.com")
# Returns: ToolOutputImage containing the visual screenshot
```

**Data Analyst** can create a chart and return it as both text insight and image:
```python
# Agent analyzes your data and returns both interpretation AND a visual chart
result = await analyst.plot_chart(data)
# Returns: Text analysis + ToolOutputImage (the chart)
```

**Ad Creator** generates visual content:
```python
# Agent creates visual assets based on your description
result = await ad_creator.generate_image("Modern tech logo with blue accent")
# Returns: ToolOutputImage (the generated logo)
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

### Creating Your Own Multi-Modal Tools

You can create custom tools that return images, files, or text. Here's how:

#### Example 1: Screenshot Tool (Returns Image)

```python
from agents.tool import function_tool, ToolOutputImage
import base64
from pathlib import Path

@function_tool
async def capture_diagram(diagram_name: str) -> list[ToolOutputImage]:
    """Capture a system diagram and return it as an image.
    
    Args:
        diagram_name: Name of the diagram to capture
    """
    # Your logic to generate or capture the diagram
    image_path = Path(f"diagrams/{diagram_name}.png")
    
    # Read the image and encode it
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    # Return as ToolOutputImage so the agent can "see" it
    # Uses data URI format: data:image/{format};base64,{base64_string}
    return [ToolOutputImage(
        type="image",
        image_url=f"data:image/png;base64,{image_b64}",
        detail="auto"
    )]
```

#### Example 2: Report Tool (Returns File)

```python
from agents.tool import function_tool, ToolOutputFileContent
from typing import Any
import base64

@function_tool
async def generate_report(data: dict[str, Any]) -> list[ToolOutputFileContent]:
    """Generate a PDF report from data.
    
    Args:
        data: The data to include in the report
    """
    # Your logic to generate the PDF
    pdf_bytes = create_pdf_report(data)
    
    # Encode the file as base64 string
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    
    # Return as file content that the agent can download/use
    # Options: file_data (base64), file_url (URL), or file_id (ID reference)
    return [ToolOutputFileContent(
        type="file",
        file_data=pdf_b64,
        filename="report.pdf"
    )]
```

#### Example 3: Hybrid Tool (Returns Text + Image)

```python
from agents.tool import function_tool, ToolOutputImage, ToolOutputText
import base64

@function_tool
async def analyze_with_visualization(data_url: str) -> list[ToolOutputText | ToolOutputImage]:
    """Fetch data, analyze it, and create a visualization.
    
    Args:
        data_url: URL to fetch the data from
    """
    # Fetch and analyze data
    analysis = perform_analysis(data_url)
    
    # Create visualization chart
    chart_image = create_chart(analysis)
    chart_b64 = base64.b64encode(chart_image).decode("utf-8")
    
    # Return both text analysis and the chart image in a list
    return [
        ToolOutputText(
            type="text",
            text=f"Analysis: {analysis['summary']}\n\nKey findings: {analysis['insights']}"
        ),
        ToolOutputImage(
            type="image",
            image_url=f"data:image/png;base64,{chart_b64}",
            detail="auto"
        )
    ]
```

#### Example 4: Multiple Images with Labels (Like Ad Creator)

```python
from agents.tool import function_tool, ToolOutputImage, ToolOutputText
import base64

@function_tool
async def generate_variants(prompt: str, num_variants: int = 3) -> list[ToolOutputText | ToolOutputImage]:
    """Generate multiple image variants with labels.
    
    Args:
        prompt: The image generation prompt
        num_variants: Number of variants to generate (1-4)
    """
    results = []
    
    # Generate multiple variants
    for i in range(num_variants):
        variant_image = generate_image_variant(prompt, variation=i)
        variant_b64 = base64.b64encode(variant_image).decode("utf-8")
        
        # Add optional text label before each image
        results.append(ToolOutputText(
            type="text",
            text=f"Variant {i+1}:\n"
        ))
        
        # Add the image
        results.append(ToolOutputImage(
            type="image",
            image_url=f"data:image/png;base64,{variant_b64}",
            detail="auto"
        ))
    
    return results
```

> **💡Tip:** Use JPEG format (`data:image/jpeg;base64,...`) for photos and PNG (`data:image/png;base64,...`) for graphics with transparency. Set `detail="auto"` for normal quality or `detail="high"` for detailed analysis.

### Adding a New Agent

Create a new specialized agent in 3 steps:

**Step 1:** Create agent folder structure
```
my_new_agent/
├── __init__.py
├── my_new_agent.py       # Agent factory
├── instructions.md       # Agent's system prompt
└── tools/
    ├── __init__.py
    └── my_tool.py        # Your custom tools
```

**Step 2:** Define your agent with tools (my_new_agent.py)
```python
from agents import Agent
from .tools.my_tool import my_custom_tool

def create_my_agent(model: str = "gpt-4", reasoning_effort: str = "medium"):
    """Create a specialized agent with custom tools."""
    
    with open("my_new_agent/instructions.md") as f:
        instructions = f.read()
    
    return Agent(
        name="MyAgent",
        instructions=instructions,
        model=model,
        tools=[my_custom_tool],
        # Enable if your tools return images/files
        supports_parallel_tool_calls=True,
    )
```

**Step 3:** Wire it into the main agency (agency.py)
```python
from my_new_agent import create_my_agent

# Create your agent
my_agent = create_my_agent(model=selected_model)

# Add it to the agency
agency = Agency(
    [
        coder,
        [coder, qa_agent],
        [coder, my_agent],  # Coder can handoff to your agent
        [coder, data_analyst],
        [coder, ad_creator],
    ],
    shared_instructions=SHARED_INSTRUCTIONS,
)
```

### Customizing Existing Agents

**Modify Agent Instructions:**
Edit the `instructions.md` file in any agent folder:
```bash
# Make the QA agent more thorough
vim qa_agent/instructions.md

# Add specific testing guidelines
# Change the tone or focus areas
# Add domain-specific knowledge
```

**Add Tools to Existing Agents:**
```python
# In agency.py or the agent file
from agents import WebSearchTool
from agents.tool import function_tool

# Add a custom tool to the QA agent
@function_tool
async def validate_accessibility(url: str) -> str:
    """Check accessibility compliance of a webpage."""
    # Your accessibility checking logic
    return "WCAG 2.1 AA compliant"

qa_agent = create_qa_agent(model=selected_model)
qa_agent.tools.append(validate_accessibility)
```

**Change Agent Communication Flow:**
```python
# In agency.py, modify the Agency structure
agency = Agency(
    [
        coder,
        [coder, qa_agent],
        [coder, data_analyst],
        [qa_agent, data_analyst],  # NEW: QA can handoff to Data Analyst
        [coder, ad_creator],
    ],
    shared_instructions=SHARED_INSTRUCTIONS,
)
```

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
