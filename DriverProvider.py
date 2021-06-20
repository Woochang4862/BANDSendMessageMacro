from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import chromedriver_autoinstaller
from webdriver_manager.chrome import ChromeDriverManager
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
logging.basicConfig(format=FORMAT, filename='./log/send_message_macro.log')
logger.setLevel(logging.DEBUG)

def open_chrome_with_debug_mode(path):
    logging.debug(f"path : {path}")
    if path == '':
        if platform.architecture()[0] == '32bit':
            return subprocess.Popen(f'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222 --user-data-dir=C:/ChromeTEMP --daemon')
        else :
            return subprocess.Popen(f'C:\Program Files\Google\Chrome\Application\chrome.exe --remote-debugging-port=9222 --user-data-dir=C:/ChromeTEMP --daemon')

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

def setup_driver(path):
    # logging.info(f"윈도우 비트 : {platform.architecture()[0]}, 크롬 버전 : {getChromeVersion()}")
    # open_chrome_with_debug_mode()
    # if not os.path.exists(getChromeVersion()[0:2]):
    #     chromedriver_autoinstaller.install(cwd=True)
    # co = Options()
    # co.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
    # if getattr(sys, 'frozen', False):   
    #     chromedriver_path = os.path.join(sys._MEIPASS, f"./{getChromeVersion()[0:2]}/chromedriver.exe")   
    #     driver = webdriver.Chrome(chromedriver_path, options=co) 
    # else:    
    #     driver = webdriver.Chrome(options=co)
    # if not os.path.exists(getChromeVersion()[0:2]):
    #     download_chrome_driver(getChromeVersion())
    #     #chromedriver_autoinstaller.install(cwd=True)
    #driver = webdriver.Chrome(options=co, executable_path=os.path.abspath(f"./{getChromeVersion()[0:2]}/chromedriver"))
    try:
        open_chrome_with_debug_mode(path)
        co = Options()
        co.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
        if getattr(sys, 'frozen', False):   
            chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")  
            driver = webdriver.Chrome(chromedriver_path, options=co)
        else:
            chromedriver_autoinstaller.install(cwd=True)
            driver = webdriver.Chrome(f"./{getChromeVersion()[0:2]}/chromedriver.exe", options=co)
        return driver
    except:
        logging.exception("")
        raise Exception("크롬 드라이버를 얻어오는 중 에러 발생")

#setup_driver()