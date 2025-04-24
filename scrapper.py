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
    load_dotenv()
    # Set up Chrome options
    chrome_options = Options()
    print('starting')
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')             # use the new headless mode
    chrome_options.add_argument('--no-sandbox')               # required on many Linux hosts
    chrome_options.add_argument('--disable-dev-shm-usage')    # avoid /dev/shm issues
    chrome_options.add_argument('--disable-gpu')              # (just in case)
    chrome_options.add_argument('--ignore-certificate-errors')# trust the mitmproxy cert
    chrome_options.add_argument('--proxy-server=http://127.0.0.1:8080')

    print("installing driver")
    # Automatically download and set up Chrome driver
    service = Service(ChromeDriverManager().install())

    # Start Selenium browser
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("starting browser")
    # Open the target website
    driver.get("https://www.financialjuice.com/")  # Replace with the actual website
    print("juice scrapper loading")
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
        print("logging in")
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "liSignIn")))
        driver.execute_script(script)
    except:
        pass

    while True:
        time.sleep(50000)
        

if __name__ == "__main__":
    start()
