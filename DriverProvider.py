from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import subprocess
import platform
import requests
import wget
import zipfile
import os
import sys
import logging

logger = logging.getLogger()
FORMAT = "[%(asctime)s][%(filename)s:%(lineno)3s - %(funcName)20s()] %(message)s"
logger.setLevel(logging.DEBUG)

def open_chrome_with_debug_mode(path):
    logging.info(f"path : {path}")
    if path == '':
        if platform.architecture()[0] == '32bit':
            return subprocess.Popen(rf'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222 --user-data-dir=C:/ChromeTEMP --daemon')
        else :
            return subprocess.Popen(rf'C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222 --user-data-dir=C:/ChromeTEMP --daemon')

    else:
        return subprocess.Popen(f'{path} --remote-debugging-port=9222 --user-data-dir=C:/ChromeTEMP --daemon')

def getChromeVersion(path=None):
    if path is None:
        if platform.architecture()[0] == '32bit':
            output = subprocess.check_output(
                r'wmic datafile where name="C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe" get Version /value',
                shell=True
            )

            return output.decode('utf-8').strip().strip("Version=")
        else:
            output = subprocess.check_output(
                r'wmic datafile where name="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" get Version /value',
                shell=True
            )
            
            return output.decode('utf-8').strip().strip("Version=")

def download_chrome_driver(chrome_version):
    
    # get the latest chrome driver version number
    url = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE_'+chrome_version[0:2]
    response = requests.get(url)
    version_number = response.text

    # build the donwload url
    download_url = "https://chromedriver.storage.googleapis.com/" + version_number +"/chromedriver_win32.zip"

    print(download_url)

    os.makedirs(f'./{chrome_version[0:2]}/')

    # download the zip file using the url built above
    latest_driver_zip = wget.download(download_url,f'./{chrome_version[0:2]}/chromedriver.zip')

    # extract the zip file
    with zipfile.ZipFile(latest_driver_zip, 'r') as zip_ref:
        zip_ref.extractall() # you can specify the destination folder path here
    # delete the zip file downloaded above
    os.remove(latest_driver_zip)

def setup_driver(ip):
    try:
        #open_chrome_with_debug_mode(path)
        co = Options()
        if ip:
            PORT = "3128"
            PROXY = f"{ip}:{PORT}"
            co.add_argument(f'--proxy-server=http://{PROXY}')
        co.add_argument('--user-data-dir=C:/ChromeTEMP')
        co.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36")
        co.add_argument("app-version=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36")
        #co.debugger_address='127.0.0.1:9222'  
        chromedriver_path = "C:/chromedriver.exe"
        driver = webdriver.Chrome(chromedriver_path, options=co)
        return driver
    except:
        logging.exception("")
        raise Exception("크롬 드라이버를 얻어오는 중 에러 발생")