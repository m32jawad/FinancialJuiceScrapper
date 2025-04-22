from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os

def start():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--proxy-server=http://localhost:8080")  # Use mitmproxy's default port
    chrome_options.add_argument("--ignore-certificate-errors")  # Accept insecure certificates

    # Automatically download and set up Chrome driver
    service = Service(ChromeDriverManager().install())

    # Start Selenium browser
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open the target website
    driver.get("https://www.financialjuice.com/")  # Replace with the actual website

    # Now, mitmproxy will capture all WebSocket messages

    # Load environment variables from .env file
    load_dotenv()

    # Retrieve credentials from environment variables
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")

    script = f"""
    form = document.getElementById("loginForm")
    fields = form.querySelectorAll("input")
    fields[0].value = "{email}";
    fields[1].value = "{password}";
    fields[3].click();
    """

    try:
        # Wait until the element with ID 'liSignIn' appears on the page
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "liSignIn")))
        driver.execute_script(script)
    except:
        pass

    while True:
        time.sleep(50000)
        

if __name__ == "__main__":
    start()