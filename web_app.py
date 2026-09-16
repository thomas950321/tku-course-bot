import os
import json
import time
import datetime
import random
import threading
from dotenv import load_dotenv, set_key

from flask import Flask, render_template, request, jsonify
import requests
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CustomTLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.set_ciphers('DEFAULT:@SECLEVEL=1')
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


app = Flask(__name__)

working_dir = os.path.dirname(os.path.realpath(__file__))
Env_Path = os.path.join(working_dir, ".env")
Courses_Path = os.path.join(working_dir, "data", "courses.json")

load_dotenv(Env_Path)

URL_Chinese = "https://www.ais.tku.edu.tw/EleCos/login.aspx"
URL_English = "https://www.ais.tku.edu.tw/EleCos_English/loginE.aspx"
ActionURL_Chinese = "https://www.ais.tku.edu.tw/EleCos/action.aspx"
ActionURL_English = "https://www.ais.tku.edu.tw/EleCos_English/actionE.aspx"
VerfURL_Chinese = "https://www.ais.tku.edu.tw/EleCos/Handler1.ashx"
VerfURL_English = "https://www.ais.tku.edu.tw/EleCos_English/Handler1.ashx"

NumHash = {
    "86be9a55762d316a3026c2836d044f5fc76e34da10e1b45feee5f18be7edb177": "0",
    "df7e70e5021544f4834bbee64a9e3789febc4be81470df629cad6ddb03320a5c": "1",
    "4ae81572f06e1b88fd5ced7a1a000945432e83e1551e6f721ee9c00b8cc33260": "2",
    "18f5384d58bcb1bba0bcd9e6a6781d1a6ac2cc280c330ecbab6cb7931b721552": "3",
    "a9f51566bd6705f7ea6ad54bb9deb449f795582d6529a0e22207b8981233ec58": "4",
    "a83dd0ccbffe39d071cc317ddf6e97f5c6b1c87af91919271f9fa140b0508c6c": "5",
    "c4694f2e93d5c4e7d51f9c5deb75e6cc8be5e1114178c6a45b6fc2c566a0aa8c": "6",
    "5c62e091b8c0565f1bafad0dad5934276143ae2ccef7a5381e8ada5b1a8d26d2": "7",
    "559aead08264d5795d3909718cdd05abd49572e84fe55590eef31a88a08fdffd": "8",
    "a25513c7e0f6eaa80a3337ee18081b9e2ed09e00af8531c8f7bb2542764027e7": "9"
}

bot_status = {
    "running": False,
    "logs": [],
    "login_ok": False
}


def FindLoginData(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')
    viewstate = soup.find(id="__VIEWSTATE")
    viewstategenerator = soup.find(id="__VIEWSTATEGENERATOR")
    eventval = soup.find(id="__EVENTVALIDATION")
    if viewstate and viewstategenerator and eventval:
        return viewstate["value"], viewstategenerator["value"], eventval["value"]
    return None, None, None


def GetVerfcode(session, LoginURL, VerfURL):
    r = session.get(LoginURL)
    r.encoding = "utf8"
    vc_data = session.get(VerfURL)
    if vc_data.status_code == 200:
        vc_array = json.loads(vc_data.text)
        vc_ans = []
        for raw_num in vc_array:
            vc_ans.append(NumHash.get(str(raw_num), ""))
        verfcode_raw = "".join(vc_ans)
        return verfcode_raw, r
    return "", r


def Login(session, account, password, LoginURL, VerfURL):
    vfcode, r = GetVerfcode(session, LoginURL, VerfURL)
    viewstate, vstgen, eventval = FindLoginData(r.text)
    if not viewstate:
        return r, 1
    payload_login = {
        "txtStuNo": str(account),
        "txtPSWD": str(password),
        "txtCONFM": str(vfcode),
        "__EVENTTARGET": "btnLogin",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": str(viewstate),
        "__VIEWSTATEGENERATOR": str(vstgen),
        "__EVENTVALIDATION": str(eventval)
    }
    r = session.post(LoginURL, data=payload_login)
    if "btnLogout" in r.text:
        return r, 0
    return r, 1


def AddCourse(session, open_code, ActionURL):
    viewstate, vstgen, eventval = FindLoginData(session.get(ActionURL).text)
    if not viewstate:
        return None, "系統錯誤"
    payload = {
        "__EVENTTARGET": "btnAdd",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": str(viewstate),
        "__VIEWSTATEGENERATOR": str(vstgen),
        "__EVENTVALIDATION": str(eventval),
        "txtCosEleSeq": str(open_code)
    }
    r = session.post(ActionURL, data=payload)
    import re
    respdata = re.findall("[E,I][0-9]{3}", r.text)
    for code in respdata:
        if code == "I000":
            return r, "加選成功"
        elif code == "E054":
            return r, "名額已滿"
        elif code == "E045":
            return r, "重複加選"
        elif code == "E999":
            return r, "加選失敗"
    return r, "未知結果"


def RemoveCourse(session, open_code, ActionURL):
    viewstate, vstgen, eventval = FindLoginData(session.get(ActionURL).text)
    if not viewstate:
        return None, "系統錯誤"
    payload = {
        "__EVENTTARGET": "btnDel",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": str(viewstate),
        "__VIEWSTATEGENERATOR": str(vstgen),
        "__EVENTVALIDATION": str(eventval),
        "txtCosEleSeq": str(open_code)
    }
    r = session.post(ActionURL, data=payload)
    import re
    respdata = re.findall("[E,I][0-9]{3}", r.text)
    for code in respdata:
        if code == "I000":
            return r, "退選成功"
        elif code == "E999":
            return r, "退選失敗"
    return r, "未知結果"


def add_log(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    bot_status["logs"].append(f"[{timestamp}] {msg}")
    if len(bot_status["logs"]) > 100:
        bot_status["logs"] = bot_status["logs"][-100:]


def run_bot(account, password, language, mode, schedule_time, course_list):
    bot_status["running"] = True
    bot_status["logs"] = []
    bot_status["login_ok"] = False

    if language == "chinese":
        LoginURL, ActionURL, VerfURL = URL_Chinese, ActionURL_Chinese, VerfURL_Chinese
    else:
        LoginURL, ActionURL, VerfURL = URL_English, ActionURL_English, VerfURL_English

    session = requests.Session()
    session.verify = False
    session.mount('https://', CustomTLSAdapter())
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    add_log("機器人啟動")

    if mode == "schedule" and schedule_time:
        add_log(f"預約搶課，等待至 {schedule_time}")
        while True:
            now = datetime.datetime.now()
            target = datetime.datetime.strptime(schedule_time, "%Y-%m-%d %H:%M:%S")
            if now >= target:
                break
            time.sleep(0.5)
        add_log("時間到達，開始執行")

    for attempt in range(3):
        add_log(f"嘗試登入 (第{attempt+1}次)...")
        r, state = Login(session, account, password, LoginURL, VerfURL)
        if state == 0:
            add_log("登入成功")
            bot_status["login_ok"] = True
            break
        else:
            add_log("登入失敗，重試中...")
            time.sleep(1)

    if not bot_status["login_ok"]:
        add_log("登入失敗，機器人停止")
        bot_status["running"] = False
        return

    for course in course_list:
        action = course["action"]
        code = course["code"]
        if action == "add":
            add_log(f"加選 {code} ...")
            r, msg = AddCourse(session, code, ActionURL)
        else:
            add_log(f"退選 {code} ...")
            r, msg = RemoveCourse(session, code, ActionURL)
        add_log(f"{code}: {msg}")
        time.sleep(1)

    add_log("搶課完成")
    bot_status["running"] = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/save_account", methods=["POST"])
def save_account():
    data = request.json
    account = data.get("account", "")
    password = data.get("password", "")
    if not account or not password:
        return jsonify({"ok": False, "msg": "帳號密碼不能為空"})
    try:
        set_key(Env_Path, "TKU_ACCOUNT", account)
        set_key(Env_Path, "TKU_PASSWORD", password)
        os.environ["TKU_ACCOUNT"] = account
        os.environ["TKU_PASSWORD"] = password
        return jsonify({"ok": True, "msg": "帳號密碼儲存成功 (.env)"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@app.route("/api/load_account")
def load_account():
    try:
        load_dotenv(Env_Path, override=True)
        account = os.environ.get("TKU_ACCOUNT", "")
        password = os.environ.get("TKU_PASSWORD", "")
        return jsonify({"ok": True, "account": account, "password": password})
    except Exception as e:
        return jsonify({"ok": True, "account": "", "password": ""})


@app.route("/api/save_courses", methods=["POST"])
def save_courses():
    data = request.json
    courses = data.get("courses", [])
    try:
        os.makedirs(os.path.dirname(Courses_Path), exist_ok=True)
        with open(Courses_Path, 'w', encoding='utf-8') as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True, "msg": "課程清單儲存成功"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})


@app.route("/api/load_courses")
def load_courses():
    try:
        if os.path.exists(Courses_Path):
            with open(Courses_Path, 'r', encoding='utf-8') as f:
                courses = json.load(f)
                return jsonify({"ok": True, "courses": courses})
        return jsonify({"ok": True, "courses": []})
    except Exception as e:
        return jsonify({"ok": True, "courses": []})


@app.route("/api/start", methods=["POST"])
def start_bot():
    if bot_status["running"]:
        return jsonify({"ok": False, "msg": "機器人正在運行中"})
    data = request.json
    account = data.get("account", "")
    password = data.get("password", "")
    language = data.get("language", "chinese")
    mode = data.get("mode", "immediate")
    schedule_time = data.get("schedule_time", "")
    courses = data.get("courses", [])
    if not account or not password:
        return jsonify({"ok": False, "msg": "帳號密碼不能為空"})
    if not courses:
        return jsonify({"ok": False, "msg": "加退選清單為空"})
    thread = threading.Thread(target=run_bot, args=(account, password, language, mode, schedule_time, courses))
    thread.daemon = True
    thread.start()
    return jsonify({"ok": True, "msg": "機器人已啟動"})


@app.route("/api/stop", methods=["POST"])
def stop_bot():
    bot_status["running"] = False
    add_log("手動停止機器人")
    return jsonify({"ok": True, "msg": "已停止"})


@app.route("/api/status")
def get_status():
    return jsonify({
        "running": bot_status["running"],
        "logs": bot_status["logs"],
        "login_ok": bot_status["login_ok"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
