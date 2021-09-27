import sqlite3
import logging

logger = logging.getLogger()
FORMAT = "[%(asctime)s][%(filename)s:%(lineno)3s - %(funcName)20s()] %(message)s"
logger.setLevel(logging.DEBUG)

DB_NAME = "send_message_macro.db"

CURRENT_VERSION = "0.1"
"""
"""

TABLE_ACCOUNT = "account"
ACCOUNT_ID = "account_id"
ACCOUNT_PW = "pw"
ACCOUNT_IP = "ip"
ACCOUNT_COLUMNS = [ACCOUNT_ID, ACCOUNT_PW, ACCOUNT_IP]

TABLE_PREFERENCE = "preference"
PREFERENCE_KEY = "preference_key"
PREFERENCE_STRING = "preference_string"
PREFERENCE_INTEGER = "preference_integer"
PREFERENCE_REAL = "preference_real"

"""
PREFERENCE KEY
"""
KEY_KEYWORD = "key_keyword"
KEY_CONTENT = "key_content"

def connect():
    global con
    global cursor
    con = sqlite3.connect(f"./{DB_NAME}")
    cursor = con.cursor()    
    
    SCHEMA_ACCOUNT = f"({ACCOUNT_ID} text primary key, {ACCOUNT_PW} text, {ACCOUNT_IP} text)"
    SCHEMA_PREFERENCE = f"({PREFERENCE_KEY} text primary key, {PREFERENCE_STRING} text, {PREFERENCE_INTEGER} integer, {PREFERENCE_REAL} real)"

    CREATE_ACCOUNT = f"CREATE TABLE IF NOT EXISTS \"{TABLE_ACCOUNT}\""+SCHEMA_ACCOUNT
    CREATE_PREFERENCE = f"CREATE TABLE IF NOT EXISTS \"{TABLE_PREFERENCE}\""+SCHEMA_PREFERENCE

    cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='schema_versions'")
    if cursor.fetchone()[0] == 0: # 버전 기능이 들어가기 전 (완전히 처음이거나 7/13일 전쯤...)
        cursor.execute(f'CREATE TABLE schema_versions(version text)')
        cursor.execute(f'INSERT INTO schema_versions(version) VALUES({CURRENT_VERSION})')
        con.commit()

        cursor.execute("begin")
        try:
            cursor.execute(f"ALTER TABLE {TABLE_ACCOUNT} ADD COLUMN {ACCOUNT_IP} text")
            cursor.execute(f"UPDATE schema_versions SET version = '0.1'")
            con.commit()
        except:
            logging.exception("")
            con.rollback()

        checkSchema(TABLE_ACCOUNT, SCHEMA_ACCOUNT, ACCOUNT_COLUMNS)

    cursor.execute(CREATE_ACCOUNT)
    cursor.execute(CREATE_PREFERENCE)

    cursor.execute("PRAGMA foreign_keys=1")

    # 버전별 변경 사항 적용해줌 컬럼 -> 속성
    if getDatabaseVersion() == "0.1":
        pass

def getDatabaseVersion():
    cursor.execute(f"select max(version) from schema_versions")
    return cursor.fetchone()[0]

def checkSchema(table_name, table_schema, table_columns):
    cursor.execute(f"select * from sqlite_master where type='table' and name='{table_name}';")
    result = cursor.fetchall()[0][4]
    if result[result.index('('):].lower() != table_schema.lower():
        print(table_name)
        cursor.execute("PRAGMA foreign_keys=0")
        cursor.execute("begin")
        try:
            cursor.execute(f"CREATE TABLE IF NOT EXISTS new_{table_name}"+table_schema)
            cursor.execute(f"INSERT INTO new_{table_name}({','.join(table_columns)}) SELECT * FROM {table_name}")
            cursor.execute(f"DROP TABLE {table_name}")
            cursor.execute(f"ALTER TABLE new_{table_name} RENAME TO {table_name}")
            con.commit()
        except:
            logging.exception("")
            con.rollback()
        finally:
            cursor.execute("PRAGMA foreign_keys=1")

def close():
    con.close()

def clearAccounts():
    cursor.execute(f'DELETE FROM {TABLE_ACCOUNT}')
    con.commit()

def addAccount(id, pw, ip):
    cursor.execute(f"INSERT INTO {TABLE_ACCOUNT} ({ACCOUNT_ID}, {ACCOUNT_PW}, {ACCOUNT_IP}) VALUES('{id}','{pw}','{ip}')")
    con.commit()

def deleteAccount(id):
    cursor.execute(f"DELETE FROM {TABLE_ACCOUNT} WHERE {ACCOUNT_ID}='{id}'")
    con.commit()

def putStringExtra(key, extra):
    cursor.execute(f"INSERT OR REPLACE INTO {TABLE_PREFERENCE}({PREFERENCE_KEY}, {PREFERENCE_STRING}) VALUES ('{key}', '{extra}')")
    con.commit()

def getStringExtra(key, empty):
    cursor.execute(f"SELECT {PREFERENCE_STRING} FROM {TABLE_PREFERENCE} WHERE {PREFERENCE_KEY} = '{key}'")
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        return empty

def getAccounts():
    cursor.execute(f"SELECT * FROM {TABLE_ACCOUNT}")
    rows = cursor.fetchall()
    return rows

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