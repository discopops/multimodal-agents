from typing import List, Optional
from urllib.parse import urlparse

from agency_swarm.tools import BaseTool
from pydantic import Field

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import os
# Add the tools directory to Python path for imports
tools_dir = os.path.dirname(os.path.abspath(__file__))
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from utils.session_manager import get_persistent_driver, navigate_persistent_session, restart_session_if_needed  # noqa: E402


class DiscoverElements(BaseTool):
    """
    Discover interactive elements on a webpage and suggest selectors for testing.
    """

    page_url: str = Field(
        ...,
        description="The URL of the page to discover elements on (e.g., http://localhost:3000)",
    )
    
    element_types: List[str] = Field(
        default=["button", "input", "select", "a", "form"],
        description="Types of elements to discover (button, input, select, a, form, etc.)",
    )
    
    include_text: bool = Field(
        default=True,
        description="Whether to include element text in the discovery results",
    )
    
    include_attributes: bool = Field(
        default=True,
        description="Whether to include element attributes (id, class, etc.)",
    )
    
    enable_cookies: bool = Field(
        default=True,
        description="Whether to enable cookies for session persistence",
    )
    
    session_storage_dir: Optional[str] = Field(
        default="./browser_session",
        description="Directory to store session data (cookies, local storage). If not provided, uses temporary directory.",
    )

    def run(self):
        
        try:
            # Validate URL format
            parsed_url = urlparse(self.page_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return f"Error: Invalid URL format: {self.page_url}. Please provide a complete URL like http://localhost:3000"
            
            # Get persistent driver (stays alive across tool calls)
            driver = get_persistent_driver(
                session_storage_dir=self.session_storage_dir,
                headless=True  # Always headless for element discovery
            )
            
            # Restart session if it died
            restart_session_if_needed(
                session_storage_dir=self.session_storage_dir,
                headless=True
            )
            
            # Navigate to the page
            navigate_persistent_session(self.page_url)
            
            # Wait for the page to load
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            discovered_elements = []
            
            # Discover elements by type
            for element_type in self.element_types:
                elements = driver.find_elements(By.TAG_NAME, element_type)
                
                for i, element in enumerate(elements):
                    try:
                        element_info = self._analyze_element(element, element_type, i)
                        if element_info:
                            discovered_elements.append(element_info)
                    except Exception as e:
                        print(f"Error analyzing element: {e}")
                        # Skip elements that can't be analyzed
                        continue
            
            # Format results
            result = f"Element Discovery Results for {self.page_url}:\n"
            result += "=" * 60 + "\n\n"
            
            if not discovered_elements:
                result += "No interactive elements found on the page.\n"
                return result
            
            # Group by element type
            by_type = {}
            for element in discovered_elements:
                element_type = element['type']
                if element_type not in by_type:
                    by_type[element_type] = []
                by_type[element_type].append(element)
            
            for element_type, elements in by_type.items():
                result += f"\n{element_type.upper()} ELEMENTS ({len(elements)} found):\n"
                result += "-" * 40 + "\n"
                
                for element in elements:
                    result += f"Element {element['index']}:\n"
                    result += f"  Text: {element['text']}\n"
                    result += "  Selectors:\n"
                    for selector_type, selector_value in element['selectors'].items():
                        result += f"    {selector_type}: {selector_value}\n"
                    if self.include_attributes and element['attributes']:
                        result += f"  Attributes: {element['attributes']}\n"
                    result += "\n"
            
            result += f"\nTotal elements discovered: {len(discovered_elements)}\n"
            
            return result
                
        except Exception as e:
            return f"Error discovering elements: {str(e)}"

    def _analyze_element(self, element, element_type, index):
        """Analyze a single element and extract useful information"""
        try:
            # Get element text
            text = element.text.strip() if self.include_text else ""
            
            # Get element attributes
            attributes = {}
            if self.include_attributes:
                # Use JavaScript to get all attributes
                all_attrs = element.get_property('attributes')
                for attr in all_attrs:
                    attr_name = attr['name']
                    attr_value = attr['value']
                    if attr_value:  # Only include non-empty attributes
                        attributes[attr_name] = attr_value
            
            # Generate selectors
            selectors = {}
            
            # ID selector (most reliable)
            element_id = element.get_attribute('id')
            if element_id:
                selectors['id'] = f"#{element_id}"
            
            # Class selector
            element_class = element.get_attribute('class')
            if element_class:
                classes = element_class.strip().split()
                if classes:
                    selectors['css'] = f".{classes[0]}"
                    if len(classes) > 1:
                        selectors['css_multiple'] = f".{'.'.join(classes)}"
            
            # Name selector
            element_name = element.get_attribute('name')
            if element_name:
                selectors['name'] = element_name
            
            # Text-based selectors
            if text:
                # XPath by text
                selectors['xpath_text'] = f"//{element_type}[text()='{text}']"
                selectors['xpath_contains'] = f"//{element_type}[contains(text(), '{text[:20]}')]"
            
            # CSS selector by attributes
            if element_id:
                selectors['css_id'] = f"#{element_id}"
            elif element_class:
                selectors['css_class'] = f".{element_class.split()[0]}"
            else:
                selectors['css_tag'] = element_type
            
            # Generic CSS selector
            selectors['css'] = element_type
                
            return {
                'type': element_type,
                'index': index + 1,
                'text': text,
                'selectors': selectors,
                'attributes': attributes
            }
            
        except Exception as e:
            print(f"Error analyzing element: {e}")
            return None



# Create alias for Agency Swarm tool loading
discover_elements = DiscoverElements

if __name__ == "__main__":
    # Example usage with cookie persistence
    tool = DiscoverElements(
        page_url="http://localhost:3000",
        element_types=["canvas","svg"],
        include_text=True,
        include_attributes=True,
        enable_cookies=True,  # Enable cookies for session persistence
        session_storage_dir="./browser_session"  # Same directory as interact tool
    )
    result = tool.run()
    print(result)
