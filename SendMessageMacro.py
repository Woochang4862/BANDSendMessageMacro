import time
import logging
from selenium.webdriver.support.ui import *
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException, StaleElementReferenceException, InvalidSessionIdException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from DriverProvider import *
from LoginMacro import *

from PyQt5.QtCore import *

logger = logging.getLogger()
FORMAT = "[%(asctime)s][%(filename)s:%(lineno)3s - %(funcName)20s()] %(message)s"
logger.setLevel(logging.INFO)

WAIT_SECONDS = 10

class SendMessageThread(QThread):
    path = ''
    id = ''
    pw = ''
    ip = ''
    keywords = []
    contents = []

    on_finished_send_msg = pyqtSignal(str)
    on_error_send_msg = pyqtSignal(str, str)
    on_logging_send_msg = pyqtSignal(int, str)

    LOGGING_INFO = 0
    LOGGING_WARNING = 1
    LOGGING_ERROR = 2

    def __init__(self, parent=None):
        super().__init__()

    def run(self):
        try:
            self.driver = setup_driver(self.ip)    
            self.on_logging_send_msg.emit(self.LOGGING_INFO, "로그인 시도 중...")
            result = loginWithEmail(self.driver, self.id,self.pw)
            if result == LOGIN_SUCCESS or result == LOGGED_IN:
                self.on_logging_send_msg.emit(self.LOGGING_INFO, "로그인 완료")
                start = time.time()
                self.on_logging_send_msg.emit(self.LOGGING_INFO, '조건에 맞는 채팅방이 있으면 메시지를 보내게 됩니다...')
                self.discoverChatsAndSendMessage(self.driver, self.keywords, self.contents)
                self.on_logging_send_msg.emit(self.LOGGING_INFO, f'실행시간 : {time.time()-start}초')
                self.on_finished_send_msg.emit(self.id)
            elif result == LOGIN_ERROR:
                self.on_error_send_msg.emit(self.id, "로그인 실패")
            self.driver.close()
            self.driver.quit()
            #self.on_logging_send_msg.emit(self.LOGGING_WARNING, "작업이 취소됨 : "+str(e))
        except:
            logging.exception("")

    def stop(self):
        try:
            #self.wait(5000) #5000ms = 5s
            self.isRunning = False
            self.quit()
            self.driver.close()
            self.driver.quit()
            self.on_logging_send_msg.emit(self.LOGGING_INFO, "작업이 취소됨")
        except Exception as e:
            self.on_logging_send_msg.emit(self.LOGGING_WARNING, "제거할 드라이버 없음 : "+str(e))

    def discoverChatsAndSendMessage(self, driver, keywords, texts):
        wait = WebDriverWait(driver, WAIT_SECONDS)

        driver.get("https://band.us/")

        showChannelsBtn = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="btnShowChannels"]'))
        )
        showChannelsBtn.click()

        i=0
        chats = []
        self.on_logging_send_msg.emit(self.LOGGING_INFO, "채팅 목록 불러오는 중...")
        while self.isRunning:
            try:
                chat = driver.find_element_by_xpath(f'//*[@id="header"]/div[2]/ul/li[4]/article/div/ul/li[last()-{i}]')
                
                chat_title = chat.find_elements_by_tag_name('span')[1].text.strip()

                i+=1
                chats.append((chat,chat_title))
                logging.debug(f"채팅요소 및 제목 : {len(chats)}")
            except NoSuchElementException:
                break
            except InvalidSessionIdException as e:
                raise e
            except Exception as e:
                #logging.exception(e)
                continue
        self.on_logging_send_msg.emit(self.LOGGING_INFO, "채팅 목록 모두 불러옴")
        self.on_logging_send_msg.emit(self.LOGGING_INFO,f"검사 예정 채팅 목록 수 : {len(chats)}개")
        
        self.on_logging_send_msg.emit(self.LOGGING_INFO, "채팅방 검사 중...")
        correctChats = []
        for rPos, (chat, chat_title) in enumerate(chats):
            for keyword, text in zip(keywords,texts):
                self.on_logging_send_msg.emit(self.LOGGING_INFO, f"현재 변수 상태 : chat_title : {chat_title}, keyword : {keyword}, text : {text}")
                if keyword in chat_title:
                    while self.isRunning:
                        try:
                            chat.click()
                            driver.switch_to.window(driver.window_handles[1])
                            break
                        except:
                            showChannelsBtn.click()
                            chat = driver.find_element_by_xpath(f'//*[@id="header"]/div[2]/ul/li[4]/article/div/ul/li[{len(chats)-rPos}]')
                            continue
                    start = time.time()
                    self.on_logging_send_msg.emit(self.LOGGING_INFO, "채팅방 로딩 기다리는 중...")
                    while self.isRunning:
                        try:
                            driver.find_element_by_xpath('//*[@id="wrap"]/div[1]/div[2]/div[2]/div')
                            break
                        except InvalidSessionIdException as e:
                            raise e
                        except:
                            if time.time()-start >= 15 if self.ip else 10:
                                driver.refresh()
                                start = time.time()
                            continue
                    
                    time.sleep(0.5)

                    self.on_logging_send_msg.emit(self.LOGGING_INFO, "채팅방 로딩 완료")
                    
                    self.on_logging_send_msg.emit(self.LOGGING_INFO, "채팅방 메시지 목록 불러오는 중...")
                    while self.isRunning:
                        try:    
                            messages = driver.find_elements_by_class_name('txt._messageContent')
                            
                            isOverlaped = False
                            for m in messages:
                                if m.text.strip() == text:
                                    isOverlaped = True
                                    self.on_logging_send_msg.emit(self.LOGGING_WARNING, f"'{chat_title}' 조건에 맞지 않는 채팅방 (메시지가 이미 존재함)")
                                    break
                                    
                            if not isOverlaped:
                                self.on_logging_send_msg.emit(self.LOGGING_INFO, f"'{chat_title}'는 조건에 맞는 채팅방(키워드 : {keyword}, 메시지 : {text})")
                                self.on_logging_send_msg.emit(self.LOGGING_INFO, f"'{chat_title}'에 메시지 보내는 중...")
                                self.sendMessage(driver, None, text, True)
                                self.on_logging_send_msg.emit(self.LOGGING_INFO, f"'{chat_title}'에 메시지 보내기 완료!")
                                correctChats.append(chat_title)
                            break
                        except InvalidSessionIdException as e:
                            raise e
                        except:
                            logging.exception("")
                            continue
                        
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                else:
                    self.on_logging_send_msg.emit(self.LOGGING_WARNING, f"조건에 맞지 않는 채팅방 (키워드 '{chat_title}' 가 존재하지 않음)")
                if len(correctChats)==2:
                    temp = "'"+"', '".join(correctChats)+"'"
                    self.on_logging_send_msg.emit(self.LOGGING_INFO, f"조건에 맞는 채팅방을 2개를 찾아 종료됨({temp})")
                    return
                
        if len(correctChats)==1:
            temp = "'"+"', '".join(correctChats)+"'"
            self.on_logging_send_msg.emit(self.LOGGING_INFO, f"조건에 맞는 채팅방 1개에 대해서 작업을 수행함({temp})")
            return
        self.on_logging_send_msg.emit(self.LOGGING_INFO, "조건에 맞는 채팅방이 없음")

    def sendMessage(self, driver, url, text, onlyAction=False):
        wait = WebDriverWait(driver, WAIT_SECONDS)

        if not onlyAction:
            driver.get(url)
        
        if self.isRunning:
            textarea = wait.until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/section/div[2]/div[1]/textarea'))
            )
            pyperclip.copy(text)
            textarea.send_keys(Keys.CONTROL, 'v')
            textarea.send_keys(Keys.ENTER)

        self.on_logging_send_msg.emit(self.LOGGING_INFO, "전송 확인 중...")
        time.sleep(5)
        while self.isRunning:
            try:
                messages = driver.find_elements_by_class_name('txt._messageContent')
                    
                for m in messages:
                    if m.text.strip() == text:
                        self.on_logging_send_msg.emit(self.LOGGING_INFO, "전송 완료")
                        return
            except InvalidSessionIdException as e:
                raise e
            except:
                logging.exception("")
                continue

def getChatUrls(driver, url, keyword, onlyAction=False):
    wait = WebDriverWait(driver, WAIT_SECONDS)

    if not onlyAction:
        driver.get(url)

    time.sleep(3)

    chats = driver.find_elements_by_xpath('//ul[@class="chat"]/li[*]')

    len_of_chats = len(chats)

    #print(len_of_chats, chats[0].get_attribute('innerHTML'))

    result = []

    if len_of_chats > 1:
        i = 1
        while True:
            done = False
            err_cnt = 0
            timeout = False
            while not done:
                try:
                    chat = wait.until(
                        EC.element_to_be_clickable((By.XPATH, f'//ul[@class="chat"]/li[{i}]/a'))
                    )
                
                    chat_title = wait.until(
                            EC.element_to_be_clickable((By.XPATH, f'//ul[@class="chat"]/li[{i}]/a/span[2]/strong'))
                    ).text
                    chat.click()
                    done = True
                except TimeoutException:
                    timeout = True
                    break
                except Exception:
                    err_cnt+=1
                    logger.exception(f"채팅방 찾는데 문제발생 {err_cnt}")

            if timeout:
                break
            driver.switch_to.window(driver.window_handles[1])
            if keyword in chat_title:
                url = driver.current_url
                result.append((chat_title,url))
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            i+=1

    elif len_of_chats == 1:
        try:
            chat = wait.until(
                EC.element_to_be_clickable((By.XPATH, f'//ul[@class="chat"]/li/a'))
            )
            chat_title = wait.until(
                    EC.element_to_be_clickable((By.XPATH, f'//ul[@class="chat"]/li/a/span[2]/strong'))
            ).text
            chat.click()
            driver.switch_to.window(driver.window_handles[1])
            if keyword in chat_title:
                url = driver.current_url
                result.append((chat_title,url))
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception:
            logger.exception("채팅방 찾는데 문제발생")

    return result

def getBandUrls(driver, onlyAction=False):
    wait = WebDriverWait(driver, WAIT_SECONDS)
    
    if not onlyAction:
        driver.get('https://band.us/')

    result = []

    i = 1
    while True:
        try:
            item = wait.until(
                EC.element_to_be_clickable((By.XPATH, f'//*[@id="content"]/div/section/div[2]/div/div/ul/li[{i}]'))
            )
        except:
            break
        
        if item.get_attribute('data-item-type') == 'band':
            title = driver.find_element_by_xpath(f'//*[@id="content"]/div/section/div[2]/div/div/ul/li[{i}]/div/div/a/div[2]/p').text
            item.click()
            url = driver.current_url
            result.append((title, url))
            driver.get('https://band.us/')
        i+=1
    
    return result

# driver = setup_driver()
# result = loginWithPhone(driver, '01038554671','asdf0706')
# if result == LOGIN_SUCCESS or result == LOGGED_IN:
#     # chat_urls = getChatUrls(driver, 'https://band.us/band/60518206', '공부')
#     # print(chat_urls)
#     start = time.time()
#     logging.info('밴드 주소 가져오는 중...')
#     bands = getBandUrls(driver)
#     logging.info(f'가져온 밴드 주소 개수 : "{len(bands)}"')
#     keyword = '마카롱'
#     logging.info(f'"{keyword}"이/가 들어간 채팅 주소 가져오는 중...')
#     chats = []
#     for title, url in bands:
#         _chats = getChatUrls(driver, url, keyword)
#         for chat in _chats:
#             chats.append((title, chat[0], chat[1]))
#     logging.info(f'가져온 채팅 주소 개수 : "{len(chats)}"')
#     for band_title, chat_title, chat_url in chats:
#         sendMessage(driver, chat_url, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
#     logging.info(f'실행시간 : {time.time()-start}초')
# driver.close()

class GetChatThread(QThread):
    
    on_finished_get_chat = pyqtSignal(list)
    on_error_get_chat = pyqtSignal()

    id = ''
    pw = ''
    ip = ''
    keyword = ''

    def __init__(self, parent=None):
        super().__init__()

    def run(self):
        self.driver = setup_driver(self.ip)
        result = loginWithEmail(self.driver, self.id,self.pw)
        if result == LOGIN_SUCCESS or result == LOGGED_IN:
            start = time.time()
            logging.info('밴드 주소 가져오는 중...')
            bands = getBandUrls(self.driver)
            logging.info(f'가져온 밴드 주소 개수 : "{len(bands)}"')
            logging.info(f'"{self.keyword}"이/가 들어간 채팅 주소 가져오는 중...')
            chats = []
            for title, url in bands:
                _chats = getChatUrls(self.driver, url, self.keyword)
                for chat in _chats:
                    chats.append((title, chat[0], chat[1], self.id))
            logging.info(f'가져온 채팅 주소 개수 : "{len(chats)}"')
            logging.info(f'실행시간 : {time.time()-start}초')
            self.on_finished_get_chat.emit(chats)
        elif result == LOGIN_ERROR:
            self.on_error_get_chat.emit()
        try:
            self.driver.close()
            self.driver.quit()
        except:
            logging.info("작업이 취소됨")

    def stop(self):
        try:
            #self.wait(5000) #5000ms = 5s
            self.quit()
            self.driver.close()
            self.driver.quit()
        except:
            logging.error("드라이버 없음")

# class SendMessageThread(QThread):

#     id = ''
#     pw = ''
#     chat_urls = []
#     content = ''
#     on_finished_send_msg = pyqtSignal()
#     on_error_send_msg = pyqtSignal()

#     def __init__(self, parent=None):
#         super().__init__()

#     def run(self):
#         self.driver = setup_driver()
#         result = loginWithPhone(self.driver, self.id,self.pw)
#         if result == LOGIN_SUCCESS or result == LOGGED_IN:
#             start = time.time()
#             logging.info('채팅 보내는 중...')
#             for chat_url in self.chat_urls:
#                 sendMessage(self.driver, chat_url, self.content)
#             logging.info(f'실행시간 : {time.time()-start}초')
#             self.on_finished_send_msg.emit()
#         elif result == LOGIN_ERROR:
#             self.on_error_send_msg.emit()
#         try:
#             self.driver.close()
#         except:
#             logging.info("작업이 취소됨")

#     def stop(self):
#         try:
#             #self.wait(5000) #5000ms = 5s
#             self.quit()
#             self.driver.close()
#         except:
#             logging.error("드라이버 없음")
