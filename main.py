import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from SendMessageMacro import *
from SMMDBHelper import *

import logging
import time
from collections import deque 

logger = logging.getLogger()
FORMAT = "[%(filename)s:%(lineno)3s - %(funcName)20s()] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)

form_class = uic.loadUiType("./ui/send_message_macro_v2.ui")[0]

class MyWindow(QMainWindow, form_class):

    """
    시그널
    ::START::
    """
    state_validation_finished = pyqtSignal()
    """
    ::END::
    """

    """
    변수
    ::START::
    """
    accounts = []
    oper_accounts = deque([])
    """
    ::END::
    """

    """
    상수
    ::START::
    """
    OPER_DELETE = 0
    OPER_ADD = 1
    """
    ::END::
    """

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        """
        스레드
        ::START::
        """
        self.validateAccountThread = ValidateAccountThread(parent=self)
        self.validateAccountThread.state_logged_in.connect(self.state_logged_in)
        self.validateAccountThread.state_login_success.connect(self.state_login_success)
        self.validateAccountThread.state_login_fail.connect(self.state_login_fail)
        self.validateAccountThread.state_login_error.connect(self.state_login_error)
        self.validateAccountThread.state_login_validation.connect(self.state_login_validation)

        self.sendMessageThread = SendMessageThread(parent=self)
        self.sendMessageThread.on_finished_send_msg.connect(self.on_finished_send_msg)
        self.sendMessageThread.on_error_send_msg.connect(self.on_error_send_msg)
        self.sendMessageThread.on_logging_send_msg.connect(self.on_logging_send_msg)
        """
        ::END::
        """

        connect()
        self.accounts = getAccounts()
        close()
        self.bindToAccountTable()

    """
    계정 화면 설정
    ::START::
    """
    def on_id_changed(self, text):
        logging.debug(text)
        self.toggleAddButton(False)

    def on_pw_changed(self, text):
        logging.debug(text)
        self.toggleAddButton(False)

    def toggleAddButton(self, enabled=None):
        if enabled is None:
            self.add_btn.setEnabled(not self.add_btn.isEnabled())
        else:
            self.add_btn.setEnabled(enabled)

    def on_validation_account_clicked(self):
        logging.debug("계정 확인")
        id = self.id_edit.text().strip()
        pw = self.pw_edit.text().strip()

        if id != '' and pw != '':
            self.validateAccountThread.id = id
            self.validateAccountThread.pw = pw
            self.validateAccountThread.start()
        else:
            self.loggingWarning("계정 확인", "아이디 혹은 비밀번호가 비어 있음")

    def on_add_account_clicked(self):
        logging.debug("계정 추가")
        id = self.id_edit.text().strip()
        pw = self.pw_edit.text().strip()
        
        for _id, _ in self.accounts:
            if _id == id:
                self.loggingError("계정 추가", "동일한 아이디가 이미 존재함")
                return
        self.accounts.append((id,pw))
        self.oper_accounts.append((self.OPER_ADD,(id,pw)))

        self.loggingInfo("계정 추가", f"{id} 을/를 추가함")

        self.bindToAccountTable()

        self.id_edit.clear()
        self.pw_edit.clear()

        self.toggleAddButton(False)

        self.validateRunButton()

    
    def on_save_account_clicked(self):
        logging.debug("계정 저장")
        connect()
        logging.debug(f"프로그램에 저장된 계정 목록(저장되지 않음): {self.accounts}")
        add_cnt = 0
        delete_cnt = 0
        for oper in self.oper_accounts:
            if oper[0] == self.OPER_ADD:
                addAccount(oper[1][0], oper[1][1])
                add_cnt+=1
            if oper[0] == self.OPER_DELETE:
                deleteAccount(oper[1][0])
                delete_cnt+=1
        self.accounts = getAccounts()
        close()

        self.loggingInfo("계정 저장", f"{add_cnt} 개가 DB에 추가됨")
        self.loggingInfo("계정 저장", f"{delete_cnt} 개가 DB에서 삭제됨")

        self.oper_accounts.clear()

    def on_delete_account_clicked(self):
        logging.debug("계정 삭제")
        
        deletedAccounts = 0
        for _range in self.account_table.selectedRanges():
            topRow = _range.topRow()
            bottomRow = _range.bottomRow()

            for row in range(topRow, bottomRow+1):
                id = self.account_table.item(row, 0).text()
                pw = self.account_table.item(row, 1).text()
                self.accounts.remove((id,pw))
                self.oper_accounts.append((self.OPER_DELETE, (id,pw)))
                deletedAccounts+=1

        self.loggingInfo("계정 삭제", f"{deletedAccounts} 개를 삭제 시킴")

        self.bindToAccountTable()

        self.validateRunButton()


    def bindToAccountTable(self):
        self.account_table.clear()
        self.account_table.setColumnCount(2)
        self.account_table.setRowCount(len(self.accounts))
        self.account_table.setHorizontalHeaderLabels(["아이디", "비밀번호"])

        for idx, (id, pw) in enumerate(self.accounts): # 사용자정의 item 과 checkbox widget 을, 동일한 cell 에 넣어서 , 추후 정렬 가능하게 한다. 

            self.account_table.setItem(idx, 0, QTableWidgetItem(id)) 
            self.account_table.setItem(idx, 1, QTableWidgetItem(pw)) 

        self.account_table.setSortingEnabled(False)  # 정렬기능
        self.account_table.resizeRowsToContents()
        self.account_table.resizeColumnsToContents()  # 이것만으로는 checkbox 컬럼은 잘 조절안됨.

        self.loggingInfo("계정 로딩", f"{len(self.accounts)} 개가 로딩됨")

    @pyqtSlot()
    def state_logged_in(self):
        self.toggleAddButton(False)
        QMessageBox.warning(self.centralwidget, '로그인 상태', '로그아웃 후 다시 시도해 주세요', QMessageBox.Ok, QMessageBox.Ok)

    @pyqtSlot()
    def state_login_success(self):
        self.toggleAddButton(True)
        QMessageBox.information(self.centralwidget, '로그인 성공', '아래 추가 버튼을 눌러 주세요', QMessageBox.Ok, QMessageBox.Ok)

    @pyqtSlot()
    def state_login_fail(self):
        self.toggleAddButton(False)
        QMessageBox.critical(self, '로그인 실패', '아이디 또는 비밀번호를 확인해 주세요', QMessageBox.Ok, QMessageBox.Ok)

    @pyqtSlot()
    def state_login_error(self):
        self.toggleAddButton(False)
        QMessageBox.critical(self, '로그인 오류', '로그인 시도 중 문제가 발생하였습니다', QMessageBox.Ok, QMessageBox.Ok)

    @pyqtSlot()
    def state_login_validation(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("휴대폰 인증 후 아래 확인 버튼을 눌러 주세요")
        msgBox.setWindowTitle("휴대폰 인증 요청")
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.buttonClicked.connect(lambda _ : self.state_validation_finished.emit())
        msgBox.exec()
    """
    ::END::
    """

    def on_keyword_changed(self, text):
        logging.debug(text)
        self.validateRunButton()
    
    def on_content_changed(self):
        text = self.content_edit.toPlainText().strip()
        logging.debug(text)
        self.validateRunButton()

    """
    실행/중단 설정
    ::START::
    """
    def on_run_clicked(self):
        logging.debug("실행")

        self.progressBar.reset()

        self.toggleRunButton(False)
        self.toggleStopButton(True)

        self.remain_accounts = deque(self.accounts)
        keywords = list(map(lambda x: x.strip(), self.keyword_edit.text().strip().split(',')))
        contents = list(map(lambda x: x.strip(' \n'), self.content_edit.toPlainText().strip(' \n').split(',')))

        _keywords = "'"+"', '".join(keywords)+"'"
        _contents = "'"+"', '".join(contents)+"'"
        self.loggingInfo("채팅 보내기", f"키워드 : {_keywords}, 내용 : {_contents}")

        while self.remain_accounts:
            id,pw = self.remain_accounts.popleft()
            self.sendMessageThread.id = id
            self.sendMessageThread.pw = pw
            self.sendMessageThread.keywords = keywords
            self.sendMessageThread.contents = contents
            self.sendMessageThread.start()
        


    def on_stop_clicked(self):
        logging.debug("중단")
        if self.sendMessageThread.isRunning():
            self.sendMessageThread.stop()
        self.toggleStopButton(False)
        self.toggleRunButton(True)

    def validateRunButton(self):
        if len(self.accounts) == 0 or self.content_edit.toPlainText().strip()=='' or self.keyword_edit.text().strip()=='':
            self.toggleRunButton(False)
        else:
            self.toggleRunButton(True)

    def toggleRunButton(self, enabled=None):
        if enabled is None:
            self.run_btn.setEnabled(not self.run_btn.isEnabled())
        else:
            self.run_btn.setEnabled(enabled)

    def toggleStopButton(self, enabled=None):
        if enabled is None:
            self.stop_btn.setEnabled(not self.stop_btn.isEnabled())
        else:
            self.stop_btn.setEnabled(enabled)

    def on_finished_send_msg(self, id):
        self.loggingInfo("채팅 보내기", f"{id}가 완료됨")
        self.progressBar.setValue((1-len(self.remain_accounts)/len(self.accounts))*100)
        self.toggleStopButton(False)
        self.validateRunButton()
        
    def on_error_send_msg(self, id, msg):
        self.loggingError("채팅 보내기", f"{id}에서 {msg}")

    def on_logging_send_msg(self, _type, msg):
        {
            0:self.loggingInfo,
            1:self.loggingWarning,
            2:self.loggingError
        }.get(_type)("채팅 보내기", msg)
    """
    :::END::
    """

    """
    LOG!!!
    ::START::
    """
    def loggingInfo(self, action, msg):
        currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_view.append(f"[{currentTime}] {action} - <b>{msg}</b>")

    def loggingError(self, action, msg):
        currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_view.append(f'<p style="color: red"><b>[{currentTime}] {action} - <i>{msg}</i></b></p>') 
    def loggingWarning(self, action, msg):
        currentTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_view.append(f'<p style="color: grey">[{currentTime}] {action} - <b>{msg}</b></p>') 
    """
    ::END::
    """


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()