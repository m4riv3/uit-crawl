import json
import sqlite3
import requests
from bs4 import BeautifulSoup

# global variable

scores = {
    'term': '',
    'subject': {
        'id': '',
        'name': '',
        'credits': '',
        'qt': '',
        'gk': '',
        'th': '',
        'ck': '',
        'dtb': ''
    }
}
URL_LOGIN = 'https://daa.uit.edu.vn/user/login'
URL = 'https://daa.uit.edu.vn/sinhvien/kqhoctap'
_session = requests.session()
ACCOUNT = {
    'user': '',  # ghi mssv vô đây
    'password': ''  # password
}
conn = sqlite3.connect('your database') # database chứa data sau khi crawl thành công
cur = conn.cursor()


def login(acc):
    r = _session.get(URL_LOGIN)  # session
    """đăng nhập dùng token csrf, dùng 2 token , 1 build ngẫu nhiên và luôn luôn thay đổi, 1 cho biết phiên này đang đăng nhập, vì vậy ta phải truy cập trong cùng 1 phiên"""
    soup = BeautifulSoup(r.content, "html.parser")
    tokens = soup.find_all('input', attrs={'type': 'hidden', 'name': 'form_build_id'})
    """có 2 token với type hidden , token[0] là user_login, còn 1 là build in ngẫu nhiên, mình sẽ lấy token này """
    token = tokens[1]['value']  # lấy được token

    """tạo payload chứa các thông tin như user,pass,các token cần thiết để đăng nhập"""
    payload = {
        'name': acc['user'],
        'pass': acc['password'],
        'form_build_id': token,  # token build từ mssv, mặc nhiên và sẽ thay đổi khi hết phiên
        'form_id': 'user_login'  # token user login
    }
    # đăng nhập
    res = _session.post(URL_LOGIN, data=payload)
    if res.status_code == 200:
        print("Log in with", acc['user'], "successfully!")


def parser_html(url):
    """crawl với bs4"""
    res = _session.get(url)
    return BeautifulSoup(res.content, "html.parser")


def list_to_dict(data, l):
    subjects = {
        'stt': '',
        'mahp': '',
        'tenhp': '',
        'sotc': '',
        'qt': '',
        'gk': '',
        'th': '',
        'ck': '',
        'dtbhp': '',
        'note': ''
    }
    if len(l) != 0:
        subjects['stt'] = str(l[0])
        subjects['mahp'] = l[1]
        subjects['tenhp'] = l[2]
        subjects['sotc'] = str(l[3])
        subjects['qt'] = str(l[4])
        subjects['gk'] = str(l[5])
        subjects['th'] = str(l[6])
        subjects['ck'] = str(l[7])
        subjects['dtbhp'] = str(l[8])
        subjects['note'] = l[9]
        data.append(subjects)
    return data


def get_scores():
    URL_SCORE = "https://daa.uit.edu.vn/sinhvien/kqhoctap"
    soup = parser_html(URL_SCORE)

    rows = soup.find_all('tr')  # tìm tất cả các thẻ <tr>, cái này F12 lên mới thấy nha :')

    data = []  # list data contains subjects
    l = []  # contains infor of subject to processing
    """loop đầu tiên để lấy các dòng (là các thẻ <tr>), mình sẽ bỏ từ 0-3 vì các dòng này không cần thiết"""
    for i in range(4, len(rows)):
        if len(rows[i]) != 16 and len(
                rows[i]) != 15:  # các môn học sẽ có len là 16 , riêng môn hđh có 15, chắc dev lỗi :3
            pass  # bỏ qua
        else:
            cells = rows[i].findChildren()  # tương ứng với mỗi dòng mình đi tìm cột, là tìm con của nó
            for it in cells:  # rồi với mỗi thằng con ta được 1 ô
                if '\xa0' in it.text:  # bỏ các ký tự &nbsp (= \xa0) 
                    s = it.text.replace('\xa0', '')
                    l.append(s)  # đưa vô list chứa, như vậy mỗi phần tử trong list là các ô trên web
                else:
                    l.append(it.text)

    """với mỗi môn học, mình có 10 ô, nên chia các sublist này theo len 10 là ok"""
    for i in range(0, len(l) + 1, 10):
        # subls này chứa 10 ô của 1 môn, mình sẽ push thằng này vô dict subject bên dưới
        subls = l[i:i + 10]
        data = list_to_dict(data, subls)
    return data

"""lưu vào db sau khi đã có data"""
"""def insert_to_databse():
    data = get_scores()
    with conn:
        cur.execute(
            'CREATE TABLE uit_score(stt INT,mahp TEXT,tenhp TEXT,sotc INT,qt REAL,gk REAL,th REAL,ck REAL,dtbhp REAL,note TEXT )')
        for item in data:
            cur.execute('INSERT INTO uit_score VALUES(?,?,?,?,?,?,?,?,?,?)', [
                item['stt'], item['mahp'], item['tenhp'], item['sotc'], item['qt'], item['gk'], item['th'], item['ck'],
                item['dtbhp'], item['note']
            ])


def from_db_to_cmp():
    cur.execute('SELECT * FROM uit_score')
    e = cur.fetchall()
    l = []

    for item in e:
        item = list(item)
        for i in range(len(item)):
            # if type(item[i]) == int or type(item[i]) == float:
            item[i] = str(item[i]).replace('.0', '')
        l.append(item)
    data = []
    for item in l:
        data = list_to_dict(data, item)
    return data


def update_data():
    old_score = from_db_to_cmp()
    new_score = get_scores()
    for old, new in zip(old_score, new_score):
        if old != new:
            update = new.items() - old.items()
            for key, val in update:
                print(key,val)
                cur.execute(
                    'UPDATE uit_score SET ' + key + '= \'' + val + '\' WHERE stt = \'' + old['stt'] + '\' and mahp = \'' + old['mahp'] + '\''
                )
"""

if __name__ == '__main__':
    login(ACCOUNT)
    data = get_scores()
    for i in data:
        print(i)
    # update_data()
