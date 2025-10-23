"""
Browser session manager for persistent QA testing.
Keeps a single browser instance alive across multiple tool calls.
"""

import os
import sys
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Add the tools directory to Python path for imports
tools_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from utils.browser_utils import setup_chrome_options # noqa: E402


class BrowserSessionManager:
    """Manages a persistent browser session across multiple tool calls."""
    
    _instance = None
    _driver = None
    _session_dir = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserSessionManager, cls).__new__(cls)
        return cls._instance
    
    def get_driver(self, session_storage_dir: Optional[str] = None, headless: bool = True) -> webdriver.Chrome:
        """Get the persistent browser driver instance."""
        # Normalize session directory
        requested_dir = session_storage_dir or "./browser_session"
                
        if self._driver is None or self._session_dir != requested_dir:
            # If driver doesn't exist or session dir changed, reinitialize
            if self._driver is not None:
                try:
                    self._driver.quit()
                except:
                    pass
            self._session_dir = requested_dir
            self._initialize_driver(headless)
        return self._driver
    
    def _initialize_driver(self, headless: bool = True):
        """Initialize the browser driver with persistent session."""
        try:
            # Clean up any stale Chrome lock files
            self._cleanup_chrome_locks()
            
            # Set up Chrome options
            chrome_options = setup_chrome_options(
                headless=headless,
                enable_cookies=True,
                session_storage_dir=self._session_dir
            )
            
            # Initialize the driver
            # Check if system ChromeDriver is available (Docker/production)
            chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
            if os.path.exists(chromedriver_path):
                print(f"Using system ChromeDriver at: {chromedriver_path}")
                service = Service(chromedriver_path)
                self._driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Fall back to webdriver-manager for local development
                print("Using webdriver-manager to download ChromeDriver")
                service = Service(ChromeDriverManager().install())
                self._driver = webdriver.Chrome(service=service, options=chrome_options)
            
            print(f"Initialized persistent browser session in: {self._session_dir}")
            
        except Exception as e:
            raise Exception(f"Failed to initialize browser session: {str(e)}")
    
    def _cleanup_chrome_locks(self):
        """Clean up Chrome lock files that might prevent startup."""
        import glob
        import os
        
        if not os.path.exists(self._session_dir):
            return
            
        # Common Chrome lock files and directories
        lock_patterns = [
            "SingletonLock",
            "lockfile", 
            "chrome_debug.log",
            "*.lock",
            "Default/LockFile",
            "Default/SingletonLock"
        ]
        
        cleaned_files = []
        for pattern in lock_patterns:
            if "*" in pattern:
                # Handle glob patterns
                for file_path in glob.glob(os.path.join(self._session_dir, pattern)):
                    try:
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                    except (OSError, PermissionError):
                        pass
            else:
                # Handle specific files
                file_path = os.path.join(self._session_dir, pattern)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                    except (OSError, PermissionError):
                        pass
        
        if cleaned_files:
            print(f"Cleaned up Chrome lock files: {cleaned_files}")
    
    def navigate_to(self, url: str):
        """Navigate to a URL in the persistent session."""
        if self._driver is None:
            raise Exception("Browser session not initialized. Call get_driver() first.")
        
        # Only navigate if we're not already on the correct page
        try:
            current_url = self._driver.current_url
            
            # Normalize URLs for comparison (remove trailing slashes)
            current_normalized = current_url.rstrip('/')
            requested_normalized = url.rstrip('/')
            
            print(f"DEBUG: navigate_to - current='{current_normalized}', requested='{requested_normalized}', match={current_normalized == requested_normalized}")
            
            if current_normalized != requested_normalized:
                self._driver.get(url)
                print(f"Navigated to: {url}")
            else:
                print(f"Already on: {url}")
        except Exception as e:
            # If we can't get current URL, navigate anyway
            print(f"DEBUG: navigate_to exception: {e}")
            self._driver.get(url)
            print(f"Navigated to: {url}")
    
    def quit(self):
        """Quit the browser session (call this when done with all tools)."""
        if self._driver is not None:
            try:
                # Try to quit gracefully
                self._driver.quit()
                print("Browser session terminated gracefully")
            except Exception as e:
                print(f"Warning: Browser quit failed: {e}")
                # Force kill any remaining Chrome processes
                self._force_kill_chrome()
            finally:
                # Always clean up lock files after quit attempt
                self._cleanup_chrome_locks()
                self._driver = None
                self._session_dir = None
    
    def _force_kill_chrome(self):
        """Force kill any remaining Chrome processes."""
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                # Kill Chrome processes on Windows
                subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                             capture_output=True, check=False)
                subprocess.run(["taskkill", "/f", "/im", "chromedriver.exe"], 
                             capture_output=True, check=False)
            else:
                # Kill Chrome processes on Unix-like systems
                subprocess.run(["pkill", "-f", "chrome"], 
                             capture_output=True, check=False)
                subprocess.run(["pkill", "-f", "chromedriver"], 
                             capture_output=True, check=False)
            print("Force killed remaining Chrome processes")
        except Exception as e:
            print(f"Warning: Could not force kill Chrome processes: {e}")
    
    def is_alive(self) -> bool:
        """Check if the browser session is still alive."""
        if self._driver is None:
            return False
        try:
            # Try to get the current URL to check if browser is responsive
            self._driver.current_url
            return True
        except Exception:
            return False
    
    def restart_if_needed(self, session_storage_dir: Optional[str] = None, headless: bool = True):
        """Restart the browser session if it's not alive."""
        if not self.is_alive():
            print("Browser session died, restarting...")
            if self._driver is not None:
                try:
                    self._driver.quit()
                except:
                    pass
            self._driver = None
            self._session_dir = session_storage_dir or "./browser_session"
            self._initialize_driver(headless)


# Global session manager instance
session_manager = BrowserSessionManager()


def get_persistent_driver(session_storage_dir: Optional[str] = None, headless: bool = True) -> webdriver.Chrome:
    """Get a persistent browser driver that stays alive across tool calls."""
    return session_manager.get_driver(session_storage_dir, headless)


def navigate_persistent_session(url: str):
    """Navigate the persistent session to a URL."""
    session_manager.navigate_to(url)


def quit_persistent_session():
    """Quit the persistent browser session."""
    session_manager.quit()


def restart_session_if_needed(session_storage_dir: Optional[str] = None, headless: bool = True):
    """Restart the session if it's not alive."""
    session_manager.restart_if_needed(session_storage_dir, headless)
