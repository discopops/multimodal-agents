# import base64
# import tempfile
from typing import List, Dict, Optional, Union
from urllib.parse import urlparse
from enum import Enum

from agency_swarm.tools import BaseTool
from pydantic import Field, BaseModel

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException
)
from typing import Literal
import sys
import os
# Add the tools directory to Python path for imports
tools_dir = os.path.dirname(os.path.abspath(__file__))
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from utils.session_manager import get_persistent_driver, navigate_persistent_session, restart_session_if_needed  # noqa: E402


class ActionType(str, Enum):
    """Available action types for page interaction"""
    CLICK = "click"
    FILL = "fill"
    SCROLL = "scroll"
    HOVER = "hover"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    PRESS_KEY = "press_key"
    SELECT_OPTION = "select_option"
    CHECK_CHECKBOX = "check_checkbox"
    UNCHECK_CHECKBOX = "uncheck_checkbox"
    WAIT = "wait"
    NAVIGATE = "navigate"
    MOVE_CURSOR = "move_cursor"
    MOUSE_CLICK = "mouse_click"


class ElementReference(BaseModel):
    """Reference to an element on the page"""
    selector: Optional[str] = Field(None, description="CSS selector, XPath, or other selector")
    by_type: str = Field("css", description="Type of selector: css, xpath, id, name, class, tag, text, partial_text")
    attributes: Optional[Dict[str, str]] = Field(None, description="Element attributes to match (e.g., {'data-testid': 'login-btn'})")
    text: Optional[str] = Field(None, description="Element text content to match")
    tag_name: Optional[str] = Field(None, description="HTML tag name (e.g., 'button', 'input')")
    
    def get_selector(self) -> tuple[str, str]:
        """Get the selector and by_type for Selenium"""
        if self.attributes:
            # Build attribute selector
            attr_selectors = []
            for key, value in self.attributes.items():
                attr_selectors.append(f"[{key}='{value}']")
            return "".join(attr_selectors), "css"
        elif self.selector:
            return self.selector, self.by_type
        elif self.text and self.tag_name:
            return f"//{self.tag_name}[text()='{self.text}']", "xpath"
        elif self.text:
            return f"//*[text()='{self.text}']", "xpath"
        else:
            raise ValueError("Must provide either selector, attributes, or text")


class BaseAction(BaseModel):
    """Base class for all actions"""
    type: ActionType
    element: Optional[ElementReference] = Field(None, description="Element to interact with")
    wait_after: Optional[float] = Field(None, description="Seconds to wait after this action")


class ClickAction(BaseAction):
    """Click an element"""
    type: ActionType = ActionType.CLICK


class FillAction(BaseAction):
    """Fill an input field"""
    type: ActionType = ActionType.FILL
    text: str = Field(..., description="Text to fill")
    clear_first: bool = Field(True, description="Whether to clear the field first")


class ScrollAction(BaseAction):
    """Scroll the page"""
    type: ActionType = ActionType.SCROLL
    direction: str = Field("down", description="Direction: down, up, top, bottom, to_element")
    amount: int = Field(500, description="Pixels to scroll (for up/down)")


class HoverAction(BaseAction):
    """Hover over an element"""
    type: ActionType = ActionType.HOVER


class DoubleClickAction(BaseAction):
    """Double click an element"""
    type: ActionType = ActionType.DOUBLE_CLICK


class RightClickAction(BaseAction):
    """Right click an element"""
    type: ActionType = ActionType.RIGHT_CLICK


class PressKeyAction(BaseAction):
    """Press a key or key combination"""
    type: ActionType = ActionType.PRESS_KEY
    key: str = Field(..., description="Key to press (enter, tab, ctrl+c, etc.)")


class SelectOptionAction(BaseAction):
    """Select an option from a dropdown"""
    type: ActionType = ActionType.SELECT_OPTION
    option_value: Optional[str] = Field(None, description="Value of option to select")
    option_text: Optional[str] = Field(None, description="Text of option to select")


class CheckboxAction(BaseAction):
    """Check or uncheck a checkbox"""
    type: ActionType = Field(..., description="check_checkbox or uncheck_checkbox")


class WaitAction(BaseAction):
    """Wait for a specified amount of time or condition"""
    type: ActionType = ActionType.WAIT
    seconds: float = Field(1, description="Seconds to wait")
    condition: Optional[str] = Field(None, description="Condition to wait for: element_visible, element_clickable")


class NavigateAction(BaseAction):
    """Navigate to a different URL"""
    type: ActionType = ActionType.NAVIGATE
    url: str = Field(..., description="URL to navigate to")


class MoveCursorAction(BaseAction):
    """Move cursor to specific coordinates or element"""
    type: ActionType = ActionType.MOVE_CURSOR
    x: Optional[int] = Field(None, description="X coordinate (absolute position)")
    y: Optional[int] = Field(None, description="Y coordinate (absolute position)")
    relative_x: Optional[int] = Field(None, description="X offset from current position")
    relative_y: Optional[int] = Field(None, description="Y offset from current position")
    center_on_element: bool = Field(False, description="Whether to center cursor on the element")


class MouseClickAction(BaseAction):
    """Perform mouse click at specific coordinates or on element"""
    type: ActionType = ActionType.MOUSE_CLICK
    x: Optional[int] = Field(None, description="X coordinate (absolute position)")
    y: Optional[int] = Field(None, description="Y coordinate (absolute position)")
    button: Literal["left", "right", "middle"] = Field("left", description="Mouse button: left, right, middle")
    click_count: int = Field(1, description="Number of clicks to perform")


# Union type for all actions
Action = Union[
    ClickAction, FillAction, ScrollAction, HoverAction, DoubleClickAction,
    RightClickAction, PressKeyAction, SelectOptionAction, CheckboxAction,
    WaitAction, NavigateAction, MoveCursorAction, MouseClickAction
]


class InteractWithPage(BaseTool):
    """
    Interact with elements on a webpage for QA testing purposes.
    Supports clicking, filling forms, scrolling, and other common testing actions.
    """

    page_url: str = Field(
        ...,
        description="The URL of the page to interact with (e.g., http://localhost:3000)",
    )
    
    actions: List[Action] = Field(
        ...,
        description="List of actions to perform. Each action is a structured model with specific parameters.",
    )
    
    wait_seconds: int = Field(
        default=3,
        description="Default wait time for page loads and element visibility",
    )
    
    headless: bool = Field(
        default=False,
        description="Whether to run the browser in headless mode. Do not set to True unless specifically requested.",
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
                headless=self.headless
            )
            
            # Restart session if it died
            restart_session_if_needed(
                session_storage_dir=self.session_storage_dir,
                headless=self.headless
            )
            
            # Navigate to the page
            navigate_persistent_session(self.page_url)
            
            # Wait for the page to load
            WebDriverWait(driver, self.wait_seconds).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            results = []
            actions = ActionChains(driver)
            
            # Execute each action
            for i, action in enumerate(self.actions):
                try:
                    result = self._execute_action(driver, actions, action, i + 1)
                    results.append(result)
                    
                    # Wait after action if specified
                    if action.wait_after:
                        import time
                        time.sleep(action.wait_after)
                        
                except Exception as e:
                    # Provide detailed error context
                    action_type = action.type if hasattr(action, 'type') else 'unknown'
                    element_info = ""
                    if hasattr(action, 'element') and action.element:
                        try:
                            selector, by_type = action.element.get_selector()
                            element_info = f" (element: {by_type}='{selector}')"
                        except Exception:
                            element_info = f" (element: {action.element})"
                    
                    error_msg = f"Action {i + 1} ({action_type}) failed{element_info}: {str(e)}"
                    results.append(error_msg)
            
            # # Take a final screenshot
            # screenshot = driver.get_screenshot_as_png()
            # screenshot_b64 = base64.b64encode(screenshot).decode('utf-8')
            
            # # Save screenshot to temporary file
            # with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            #     tmp_file.write(screenshot)
            #     temp_path = tmp_file.name
            
            # Format results
            result_text = f"Page Interaction Results for {self.page_url}:\n"
            result_text += "=" * 50 + "\n\n"
            
            for i, result in enumerate(results, 1):
                result_text += f"Action {i}: {result}\n"
            
            # result_text += f"\nFinal screenshot saved to: {temp_path}\n"
            # result_text += f"Base64 data length: {len(screenshot_b64)} characters"
            
            return result_text
                
        except Exception as e:
            return f"Error during page interaction: {str(e)}"

    def _execute_action(self, driver, actions, action, action_num):
        """Execute a single action on the page"""
        action_type = action.type
        
        if action_type == ActionType.CLICK:
            return self._click_element(driver, action, action_num)
        elif action_type == ActionType.FILL:
            return self._fill_element(driver, action, action_num)
        elif action_type == ActionType.SCROLL:
            return self._scroll_page(driver, action, action_num)
        elif action_type == ActionType.HOVER:
            return self._hover_element(driver, actions, action, action_num)
        elif action_type == ActionType.DOUBLE_CLICK:
            return self._double_click_element(driver, actions, action, action_num)
        elif action_type == ActionType.RIGHT_CLICK:
            return self._right_click_element(driver, actions, action, action_num)
        elif action_type == ActionType.PRESS_KEY:
            return self._press_key(driver, action, action_num)
        elif action_type == ActionType.SELECT_OPTION:
            return self._select_option(driver, action, action_num)
        elif action_type == ActionType.CHECK_CHECKBOX:
            return self._check_checkbox(driver, action, action_num)
        elif action_type == ActionType.UNCHECK_CHECKBOX:
            return self._uncheck_checkbox(driver, action, action_num)
        elif action_type == ActionType.WAIT:
            return self._wait_action(driver, action, action_num)
        elif action_type == ActionType.NAVIGATE:
            return self._navigate_to(driver, action, action_num)
        elif action_type == ActionType.MOVE_CURSOR:
            return self._move_cursor(driver, actions, action, action_num)
        elif action_type == ActionType.MOUSE_CLICK:
            return self._mouse_click(driver, actions, action, action_num)
        else:
            return f"Unknown action type: {action_type}"

    def _find_element(self, driver, element_ref: ElementReference):
        """Find an element using ElementReference"""
        try:
            selector, by_type = element_ref.get_selector()
        except ValueError as e:
            raise ValueError(f"Invalid element reference: {e}")
        
        by_map = {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "name": By.NAME,
            "class": By.CLASS_NAME,
            "tag": By.TAG_NAME,
            "text": By.LINK_TEXT,
            "partial_text": By.PARTIAL_LINK_TEXT
        }
        
        by = by_map.get(by_type.lower(), By.CSS_SELECTOR)
        
        try:
            return WebDriverWait(driver, self.wait_seconds).until(
                EC.element_to_be_clickable((by, selector))
            )
        except TimeoutException:
            # Try to find if element exists but is not clickable
            try:
                element = driver.find_element(by, selector)
                if not element.is_displayed():
                    raise TimeoutException(f"Element found but not visible: {by_type}='{selector}'. Element may be hidden or outside viewport.")
                elif not element.is_enabled():
                    raise TimeoutException(f"Element found but not enabled: {by_type}='{selector}'. Element may be disabled.")
                else:
                    raise TimeoutException(f"Element found but not clickable: {by_type}='{selector}'. Element may be covered by another element or not ready for interaction.")
            except NoSuchElementException:
                raise TimeoutException(f"Element not found: {by_type}='{selector}'. Please verify the reference is correct and the element exists on the page.")
        except NoSuchElementException:
            raise NoSuchElementException(f"Element not found: {by_type}='{selector}'. Please verify the reference is correct and the element exists on the page.")
        except StaleElementReferenceException:
            raise StaleElementReferenceException(f"Element reference became stale: {by_type}='{selector}'. The element may have been removed from the DOM.")
        except WebDriverException as e:
            raise WebDriverException(f"WebDriver error while finding element {by_type}='{selector}': {str(e)}")

    def _click_element(self, driver, action, action_num):
        """Click an element"""
        if not action.element:
            return "Missing element reference for click action"
        
        try:
            element = self._find_element(driver, action.element)
            element.click()
            selector, by_type = action.element.get_selector()
            return f"Clicked element: {by_type}='{selector}'"
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
            # Re-raise with more context
            selector, by_type = action.element.get_selector()
            raise type(e)(f"Failed to click element {by_type}='{selector}': {str(e)}")
        except Exception as e:
            # Catch any other unexpected errors
            selector, by_type = action.element.get_selector()
            raise Exception(f"Unexpected error while clicking element {by_type}='{selector}': {str(e)}")

    def _fill_element(self, driver, action, action_num):
        """Fill an input field"""
        if not action.element:
            return "Missing element reference for fill action"
        
        try:
            element = self._find_element(driver, action.element)
            
            if action.clear_first:
                element.clear()
            
            element.send_keys(action.text)
            selector, by_type = action.element.get_selector()
            return f"Filled element {by_type}='{selector}' with: '{action.text}'"
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
            # Re-raise with more context
            selector, by_type = action.element.get_selector()
            raise type(e)(f"Failed to fill element {by_type}='{selector}' with text '{action.text}': {str(e)}")
        except Exception as e:
            # Catch any other unexpected errors
            selector, by_type = action.element.get_selector()
            raise Exception(f"Unexpected error while filling element {by_type}='{selector}' with text '{action.text}': {str(e)}")

    def _scroll_page(self, driver, action, action_num):
        """Scroll the page"""
        direction = action.direction
        amount = action.amount
        
        if direction == 'down':
            driver.execute_script(f"window.scrollBy(0, {amount});")
        elif direction == 'up':
            driver.execute_script(f"window.scrollBy(0, -{amount});")
        elif direction == 'top':
            driver.execute_script("window.scrollTo(0, 0);")
        elif direction == 'bottom':
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        elif direction == 'to_element':
            if action.element:
                element = self._find_element(driver, action.element)
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                return f"Scrolled to element: {action.element.get_selector()[0]}"
            else:
                return "Missing element reference for scroll to element"
        
        return f"Scrolled {direction} by {amount} pixels"

    def _hover_element(self, driver, actions, action, action_num):
        """Hover over an element"""
        if not action.element:
            return "Missing element reference for hover action"
        
        element = self._find_element(driver, action.element)
        actions.move_to_element(element).perform()
        return f"Hovered over element: {action.element.get_selector()[0]}"

    def _double_click_element(self, driver, actions, action, action_num):
        """Double click an element"""
        if not action.element:
            return "Missing element reference for double click action"
        
        element = self._find_element(driver, action.element)
        actions.double_click(element).perform()
        return f"Double clicked element: {action.element.get_selector()[0]}"

    def _right_click_element(self, driver, actions, action, action_num):
        """Right click an element"""
        selector = action.get('selector')
        by_type = action.get('by', 'css')
        
        if not selector:
            return "Missing 'selector' parameter for right click action"
        
        element = self._find_element(driver, selector, by_type)
        actions.context_click(element).perform()
        return f"Right clicked element: {selector}"

    def _press_key(self, driver, action, action_num):
        """Press a key or key combination"""
        # Map string keys to Keys constants
        key_map = {
            'enter': Keys.ENTER,
            'tab': Keys.TAB,
            'escape': Keys.ESCAPE,
            'space': Keys.SPACE,
            'backspace': Keys.BACKSPACE,
            'delete': Keys.DELETE,
            'arrow_up': Keys.ARROW_UP,
            'arrow_down': Keys.ARROW_DOWN,
            'arrow_left': Keys.ARROW_LEFT,
            'arrow_right': Keys.ARROW_RIGHT,
            'ctrl+a': Keys.CONTROL + 'a',
            'ctrl+c': Keys.CONTROL + 'c',
            'ctrl+v': Keys.CONTROL + 'v',
            'ctrl+z': Keys.CONTROL + 'z',
        }
        
        key_value = key_map.get(action.key.lower(), action.key)
        
        if action.element:
            element = self._find_element(driver, action.element)
            element.send_keys(key_value)
            return f"Pressed key '{action.key}' on element: {action.element.get_selector()[0]}"
        else:
            # Send to active element
            driver.switch_to.active_element.send_keys(key_value)
            return f"Pressed key '{action.key}' on active element"

    def _select_option(self, driver, action, action_num):
        """Select an option from a dropdown"""
        selector = action.get('selector')
        option_value = action.get('option_value')
        option_text = action.get('option_text')
        by_type = action.get('by', 'css')
        
        if not selector:
            return "Missing 'selector' parameter for select option action"
        
        from selenium.webdriver.support.ui import Select
        element = self._find_element(driver, selector, by_type)
        select = Select(element)
        
        if option_value:
            select.select_by_value(option_value)
            return f"Selected option by value '{option_value}' in {selector}"
        elif option_text:
            select.select_by_visible_text(option_text)
            return f"Selected option by text '{option_text}' in {selector}"
        else:
            return "Missing 'option_value' or 'option_text' parameter for select option action"

    def _check_checkbox(self, driver, action, action_num):
        """Check a checkbox"""
        selector = action.get('selector')
        by_type = action.get('by', 'css')
        
        if not selector:
            return "Missing 'selector' parameter for check checkbox action"
        
        element = self._find_element(driver, selector, by_type)
        if not element.is_selected():
            element.click()
        return f"Checked checkbox: {selector}"

    def _uncheck_checkbox(self, driver, action, action_num):
        """Uncheck a checkbox"""
        selector = action.get('selector')
        by_type = action.get('by', 'css')
        
        if not selector:
            return "Missing 'selector' parameter for uncheck checkbox action"
        
        element = self._find_element(driver, selector, by_type)
        if element.is_selected():
            element.click()
        return f"Unchecked checkbox: {selector}"

    def _wait_action(self, driver, action, action_num):
        """Wait for a specified amount of time or condition"""
        if action.condition:
            # Wait for specific condition
            if action.condition == 'element_visible':
                if action.element:
                    selector, by_type = action.element.get_selector()
                    by_map = {
                        "css": By.CSS_SELECTOR,
                        "xpath": By.XPATH,
                        "id": By.ID,
                        "name": By.NAME,
                        "class": By.CLASS_NAME,
                        "tag": By.TAG_NAME,
                        "text": By.LINK_TEXT,
                        "partial_text": By.PARTIAL_LINK_TEXT
                    }
                    by = by_map.get(by_type.lower(), By.CSS_SELECTOR)
                    WebDriverWait(driver, action.seconds).until(
                        EC.visibility_of_element_located((by, selector))
                    )
                    return f"Waited for element {selector} to be visible"
            elif action.condition == 'element_clickable':
                if action.element:
                    selector, by_type = action.element.get_selector()
                    by_map = {
                        "css": By.CSS_SELECTOR,
                        "xpath": By.XPATH,
                        "id": By.ID,
                        "name": By.NAME,
                        "class": By.CLASS_NAME,
                        "tag": By.TAG_NAME,
                        "text": By.LINK_TEXT,
                        "partial_text": By.PARTIAL_LINK_TEXT
                    }
                    by = by_map.get(by_type.lower(), By.CSS_SELECTOR)
                    WebDriverWait(driver, action.seconds).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    return f"Waited for element {selector} to be clickable"
        else:
            # Simple wait
            import time
            time.sleep(action.seconds)
            return f"Waited for {action.seconds} seconds"

    def _move_cursor(self, driver, actions, action, action_num):
        """Move cursor to specific coordinates or element"""
        try:
            if action.element and action.center_on_element:
                # Move cursor to center of element
                element = self._find_element(driver, action.element)
                actions.move_to_element(element).perform()
                selector, by_type = action.element.get_selector()
                return f"Moved cursor to center of element: {by_type}='{selector}'"
            elif action.x is not None and action.y is not None:
                # Move to absolute coordinates
                actions.move_by_offset(action.x, action.y).perform()
                return f"Moved cursor to absolute position: ({action.x}, {action.y})"
            elif action.relative_x is not None and action.relative_y is not None:
                # Move relative to current position
                actions.move_by_offset(action.relative_x, action.relative_y).perform()
                return f"Moved cursor relative by: ({action.relative_x}, {action.relative_y})"
            elif action.element:
                # Move to element without centering
                element = self._find_element(driver, action.element)
                actions.move_to_element(element).perform()
                selector, by_type = action.element.get_selector()
                return f"Moved cursor to element: {by_type}='{selector}'"
            else:
                return "Missing coordinates or element reference for cursor movement"
        except Exception as e:
            return f"Failed to move cursor: {str(e)}"

    def _mouse_click(self, driver, actions, action, action_num):
        """Perform mouse click at specific coordinates or on element"""
        try:
            # Map button strings to Selenium button constants
            button_map = {
                'left': 0,  # Left mouse button
                'right': 2,  # Right mouse button  
                'middle': 1   # Middle mouse button
            }
            
            button_code = button_map.get(action.button.lower(), 0)
            
            if action.element:
                # Click on element
                element = self._find_element(driver, action.element)
                actions.move_to_element(element)
                
                # Perform the specified number of clicks
                for _ in range(action.click_count):
                    if action.button.lower() == 'right':
                        actions.context_click(element)
                    elif action.button.lower() == 'middle':
                        actions.click(element, button=button_code)
                    else:  # left click
                        actions.click(element)
                
                actions.perform()
                selector, by_type = action.element.get_selector()
                return f"Mouse {action.button} clicked {action.click_count} time(s) on element: {by_type}='{selector}'"
            elif action.x is not None and action.y is not None:
                # Click at absolute coordinates
                actions.move_by_offset(action.x, action.y)
                
                # Perform the specified number of clicks
                for _ in range(action.click_count):
                    if action.button.lower() == 'right':
                        actions.context_click()
                    elif action.button.lower() == 'middle':
                        actions.click(button=button_code)
                    else:  # left click
                        actions.click()
                
                actions.perform()
                return f"Mouse {action.button} clicked {action.click_count} time(s) at position: ({action.x}, {action.y})"
            else:
                return "Missing coordinates or element reference for mouse click"
        except Exception as e:
            return f"Failed to perform mouse click: {str(e)}"

    def _navigate_to(self, driver, action, action_num):
        """Navigate to a different URL"""
        driver.get(action.url)
        return f"Navigated to: {action.url}"



# Create alias for Agency Swarm tool loading
interact_with_page = InteractWithPage

if __name__ == "__main__":
    # Example usage with persistent sessions and cookies
    tool = InteractWithPage(
        page_url="http://localhost:3000",
        actions=[
            # Move cursor to an element
            MoveCursorAction(
                element=ElementReference(attributes={"data-testid": "name-prompt-input"}, tag_name="input"),
                center_on_element=True
            ),
            # Fill input field
            FillAction(
                element=ElementReference(attributes={"data-testid": "name-prompt-input"}, tag_name="input"), 
                text="testuser"
            ),
            # Mouse click on button
            MouseClickAction(
                element=ElementReference(attributes={"data-testid": "name-prompt-join"}, tag_name="button"),
                button="left",
                click_count=1
            ),
            # Move cursor to specific coordinates
            MoveCursorAction(x=10, y=20),
            # Left click at coordinates
            MouseClickAction(x=10, y=20, button="left", click_count=1),
        ],
        enable_cookies=True,  # Enable cookies for session persistence
        session_storage_dir="./browser_session"  # Will use temp directory, or specify absolute path like "/tmp/browser_session"
    )
    result = tool.run()
    print(result)
