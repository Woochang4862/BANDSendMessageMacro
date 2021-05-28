import sqlite3
import os

DB_NAME = "send_message_macro.db"

TABLE_ACCOUNT = "account"
ACCOUNT_ID = "account_id"
ACCOUNT_PW = "pw"

"""
TABLE_CHAT = "chat"
CHAT_ID = "_id"
CHAT_BAND_NAME = "chat_band_name"
CHAT_NAME = "chat_name"
CHAT_URL = "chat_url"
"""

def connect():
    global con
    global cursor
    if os.path.isfile(DB_NAME):
        con = sqlite3.connect(f"./{DB_NAME}")
        cursor = con.cursor()
    else:
        con = sqlite3.connect(f"./{DB_NAME}")
        cursor = con.cursor()
        cursor.execute(f"CREATE TABLE {TABLE_ACCOUNT}({ACCOUNT_ID} text primary key, {ACCOUNT_PW} text)")
        ## foreign [이 테이블의 컬럼] references [참조할 테이블]([그 테이블의 칼럼명])
        #cursor.execute(f"CREATE TABLE {TABLE_CHAT}({CHAT_ID} integer primary key autoincrement, {CHAT_BAND_NAME} text, {CHAT_NAME} text, {CHAT_URL} text, {ACCOUNT_ID} text, foreign key({ACCOUNT_ID}) references {TABLE_ACCOUNT}({ACCOUNT_ID}) )")
    
    #cursor.execute("PRAGMA foreign_keys=1")

def close():
    con.close()

def clearAccounts():
    cursor.execute(f'DELETE FROM {TABLE_ACCOUNT}')
    con.commit()

def addAccount(id, pw):
    cursor.execute(f"INSERT INTO {TABLE_ACCOUNT} ({ACCOUNT_ID}, {ACCOUNT_PW}) SELECT '{id}','{pw}' WHERE NOT EXISTS ( SELECT *  FROM {TABLE_ACCOUNT} WHERE  {ACCOUNT_ID} =  '{id}')")
    con.commit()

def deleteAccount(id):
    #cursor.execute(f"DELETE FROM {TABLE_CHAT} WHERE {ACCOUNT_ID}='{id}'")
    cursor.execute(f"DELETE FROM {TABLE_ACCOUNT} WHERE {ACCOUNT_ID}='{id}'")
    con.commit()

def clearChats():
    cursor.execute(f'DELETE FROM {TABLE_CHAT}')
    con.commit

def addChat(bandName, chatName, url, accountId):
    cursor.execute(f"INSERT INTO {TABLE_CHAT} ({CHAT_BAND_NAME}, {CHAT_NAME}, {CHAT_URL}, {ACCOUNT_ID}) VALUES('{bandName}', '{chatName}', '{url}', '{accountId}')")
    con.commit()

def getAccounts():
    cursor.execute(f"SELECT * FROM {TABLE_ACCOUNT}")
    rows = cursor.fetchall()
    return rows

def getChats(accountId=None):
    if accountId:
        cursor.execute(f"SELECT * FROM {TABLE_CHAT} WHERE {ACCOUNT_ID}='{accountId}'")
    else:
        cursor.execute(f"SELECT * FROM {TABLE_CHAT}")
    rows = cursor.fetchall()
    return rows

def getChatsWithoutId(accountId=None):
    if accountId:
        cursor.execute(f"SELECT {CHAT_BAND_NAME}, {CHAT_NAME}, {CHAT_URL}, {ACCOUNT_ID} FROM {TABLE_CHAT} WHERE {ACCOUNT_ID}='{accountId}'")
    else:        
        cursor.execute(f"SELECT {CHAT_BAND_NAME}, {CHAT_NAME}, {CHAT_URL}, {ACCOUNT_ID} FROM {TABLE_CHAT}")
    rows = cursor.fetchall()
    return rows

def addChats(chats):
    for chat in chats:
        addChat(chat[0], chat[1], chat[2], chat[3])

def addAccounts(accounts):
    for account in accounts:
        addAccount(account[0], account[1])

def deleteAccounts(accounts):
    for account in accounts:
        deleteAccount(account[0])

def getAccountById(_id):
    cursor.execute(f"SELECT * FROM {TABLE_ACCOUNT} WHERE {ACCOUNT_ID}='{_id}'")
    row = cursor.fetchall()[0] # id로 찾았으므로 1개만 존재할 것임
    return row

connect()
#clearAccounts()
#clearChats()
#addAccount('01038554671', 'asdf0706')
#addChat('a', 'a', 'xyz.com', '01038554671')
# addBand('테스트', '테스트', 'https://band.us/band/123456/chat/xyz')
#print(getAccountById('01038554671'))
#print(getChats())
close()