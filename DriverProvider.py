from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import subprocess

def open_chrome_with_debug_mode(path='C:\Program Files\Google\Chrome\Application\chrome.exe'):
    return subprocess.Popen(f'{path} --remote-debugging-port=9222 --user-data-dir=C:/ChromeTEMP --daemon')

def setup_driver():
    open_chrome_with_debug_mode()
    chromedriver_autoinstaller.install(cwd=True)
    co = Options()
    co.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
    driver = webdriver.Chrome(options=co)
    return driver