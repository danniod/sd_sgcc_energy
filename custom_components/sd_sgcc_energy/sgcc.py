import requests
import logging
import uuid
import time
import rsa
import hashlib
import base64
import datetime
import re
from pyquery import PyQuery as pq
from .const import PGC_PRICE

_LOGGER = logging.getLogger(__name__)

BASE_SITE = "https://www.sd.sgcc.com.cn/ppm"
CAPTCHA_URL = f"{BASE_SITE}/common/captcha.jhtml"
PUBLIC_KEY_URL = f"{BASE_SITE}/common/public_key.jhtml"
LOGIN_URL = f"{BASE_SITE}/login.jhtml"
SUBMIT_URL = f"{BASE_SITE}/login/submit.jhtml"
MENU_URL = f"{BASE_SITE}/powerCommon/allMenu.jhtml"
CHANGE_CONS_NO_URL = f"{BASE_SITE}/member/powerUse/changeUser.jhtml"
POWER_TREND_DAY_URL = f"{BASE_SITE}/member/powerUse/powerTrendDay.jhtml"
METER_READ_URL = f"{BASE_SITE}/member/powerUse/dayRead.jhtml"
VIRTUAL_METER_URL = f"{BASE_SITE}/member/powerUse/virtualMeters.jhtml"
BALANCE_DETAIL_URL = f"{BASE_SITE}/member/powerUse/balanceDetail.jhtml"
LADDER_URL = f"{BASE_SITE}/member/powerUse/ladderPower.jhtml"
DETAIL_URL = "http://weixin.sd.sgcc.com.cn/ott/app/electric/bill/overview"
BILLINFO_URL = "http://weixin.sd.sgcc.com.cn/ott/app/electric/bill/queryElecBillInfoEveryYear"

LEVEL_CONSUME = ["levelOneSum", "levelTwoSum", "levelThreeSum"]
LEVEL_REMAIN = ["levelOneRemain", "levelTwoRemain"]


def get_pgv_type(bill_range):
    dt = datetime.datetime.now()
    for pgc_price in PGC_PRICE:
        # month is none or month matched
        if pgc_price.get("moon") is None or pgc_price.get("moon")[0] <= dt.month <= pgc_price.get("moon")[1]:
            slot_len = len(pgc_price.get("time_slot"))
            for n in range(0, slot_len):
                if (((pgc_price.get("time_slot")[n][0] <= pgc_price.get("time_slot")[n][1] and
                      pgc_price.get("time_slot")[n][0] <= dt.hour < pgc_price.get("time_slot")[n][1]) or
                     (pgc_price.get("time_slot")[n][0] > pgc_price.get("time_slot")[n][1] and
                      (pgc_price.get("time_slot")[n][0] <= dt.hour or pgc_price.get("time_slot")[n][1] > dt.hour))) and
                        pgc_price.get("key") in bill_range):
                    return pgc_price.get("key")
    return "Unknown"


class SGCCData:
    def __init__(self, username, password, ocr_url=None):
        self._ocr_url = ocr_url
        self._username = username
        self._password = password
        self._exponent = None
        self._modulus = None
        self._captcha_id = None
        self._captcha = None
        self._cons = []
        self._info = {}
        self._cookies = {}

    def get_captcha(self):
        ret = False
        self._captcha_id = uuid.uuid4()
        r = requests.get(CAPTCHA_URL, params={"captchaId": self._captcha_id},
                         headers=self.get_headers(referer=LOGIN_URL),
                         allow_redirects=False,
                         timeout=10)
        if r.status_code == 200 or r.status_code == 302:
            res = requests.post(self._ocr_url, data=r.content, verify=False)
            self._captcha = res.text
            ret = True
            _LOGGER.debug(f"get captcha[{self._captcha}] with id[{self._captcha_id}]")
        return ret

    def get_public_key(self):
        r = requests.get(PUBLIC_KEY_URL + f"?_={int(time.time() * 1000)}", headers=self.get_headers(referer=LOGIN_URL),
                         timeout=10)
        if r.status_code == 200:
            result = r.json()
            self._modulus = base64.b64decode(result["modulus"]).hex()
            self._exponent = base64.b64decode(result["exponent"]).hex()

    def enc_pass(self, s):
        pub_key = rsa.PublicKey(int(self._modulus, 16), int(self._exponent, 16))
        h = hashlib.md5(s.encode("utf-8")).hexdigest() + s
        encrypted = rsa.encrypt(h.encode("utf-8"), pub_key)
        return base64.b64encode(encrypted)

    def login(self):

        r = requests.get(LOGIN_URL, headers=self.get_headers(LOGIN_URL), allow_redirects=False, timeout=10)
        if r.status_code == 200 or r.status_code == 302:
            if "Set-Cookie" in r.headers:
                set_cookies = r.headers["Set-Cookie"].split("Path=/, ")
                for set_cookie in set_cookies:
                    cookie = set_cookie.split(";")[0].split("=")
                    self._cookies[cookie[0]] = cookie[1]
                _LOGGER.debug(f"Got new cookie {self._cookies}")

        self.get_captcha()

        headers = {
            "Host": "www.sd.sgcc.com.cn",
            "Connection": "keep-alive",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
            "DNT": "1",
            "X-Ca-Nonce": f"{uuid.uuid4()}",
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/102.0.5005.61 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "X-Ca-Timestamp": f"{int(time.time() * 1000)}",
            "token": self._cookies["token"],
            "sec-ch-ua-platform": '"macOS"',
            "Origin": "https://www.sd.sgcc.com.cn",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://www.sd.sgcc.com.cn/ppm/login.jhtml",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": "; ".join([str(x) + "=" + str(y) for x, y in self._cookies.items()]),
        }

        self.get_public_key()
        data = {
            "checkType": "1",
            "city": "济南市",
            "district": "历下区",
            "username": self.enc_pass(self._username),
            "enPassword": self.enc_pass(self._password),
            "isRemberme": "true",
            "captchaId": self._captcha_id,
            "captcha": self._captcha,
        }
        ret = False
        try:
            r = requests.post(SUBMIT_URL, data=data, headers=headers, allow_redirects=False, timeout=10)
            _LOGGER.debug(f"login submit response status[{r.status_code}], result[{r.json()}]"
                          f"with cookies[{self._cookies}]")

            if r.status_code == 200:
                response_headers = r.headers
                if "Set-Cookie" in response_headers:
                    set_cookies = response_headers["Set-Cookie"].split("Path=/, ")
                    for set_cookie in set_cookies:
                        cookie = set_cookie.split(";")[0].split("=")
                        self._cookies[cookie[0]] = cookie[1]
                    _LOGGER.debug(f"login submit response set-cookie[{set_cookies}]")
                if r.json()["type"] == "success":
                    ret = True
                else:
                    if r.json()["content"] == "验证码输入错误":
                        ret = self.login()

            else:
                _LOGGER.error(f"login response status_code = {r.status_code}")
        except Exception as e:
            _LOGGER.error(f"login response got error: {e}")
        return ret

    def get_headers(self, referer=None):

        headers = {
            "Host": "www.sd.sgcc.com.cn",
            "Referer": referer if referer is not None else f"{BASE_SITE}/powerCommon/allMenu.jhtml",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                      "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "zh-cn",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": f"{BASE_SITE}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/102.0.5005.61 Safari/537.36",
            "Cookie": "; ".join([str(x) + "=" + str(y) for x, y in self._cookies.items()]),
        }
        return headers

    def get_cons_no(self):
        headers = self.get_headers()
        ret = True
        try:
            r = requests.get(MENU_URL, headers=headers, timeout=10)
            if r.status_code == 200:
                doc = pq(r.text)
                cons = doc.find("ul#consUl>li>a[name]")
                if len(cons) > 0:
                    for c in cons:
                        another_cons = pq(c)
                        cons_no = another_cons.attr("name")
                        if cons_no not in self._cons:
                            self._cons.append(cons_no)
                            _LOGGER.debug(f"Got ConsNo {cons_no}")
                            self._info[cons_no] = {"cons_name": another_cons.text()[0:another_cons.text().index("(")]}
                else:
                    ret = False
                    _LOGGER.info(f"no cons, need login")
            else:
                ret = False
                _LOGGER.error(f"getConsNo response status_code = {r.status_code}")

        except Exception as e:
            _LOGGER.error(f"getConsNo response got error: {e}")
            ret = False
        return ret

    def change_cons_no(self, cons_no):
        params = {
            "curConsNo": cons_no,
            "_": int(time.time() * 1000)
        }
        r = requests.get(CHANGE_CONS_NO_URL, params=params, headers=self.get_headers(), timeout=10)
        ret = False
        if r.status_code == 200 and r.json()["type"] == "success":
            ret = True
            _LOGGER.debug(f"change consNo{cons_no} success")
        else:
            _LOGGER.error(f"getBalance response status_code = {r.status_code}")
        return ret

    def power_trend_days(self, cons_no):
        r = requests.get(POWER_TREND_DAY_URL, headers=self.get_headers(), timeout=10)
        if r.status_code == 200:
            doc = pq(r.text)
            self._info[f"{cons_no}_consumption_daily"] = dict(zip(doc.find('input#ymList').val().split(","),
                                                                  doc.find('input#dlList').val().split(",")))

    def meter(self, cons_no):
        p = pq(url=VIRTUAL_METER_URL, headers=self.get_headers())
        script = p('script:contains("var assetList =")')
        assets = re.search(r"var assetList = \[(.*?)\]", script.text()).group(1).split(",")

        for asset in assets:
            data = {
                "assetNo": asset.strip().strip("\""),
                "fromToday": 0,
                "_": int(time.time() * 1000)
            }
            r = requests.get(METER_READ_URL, params=data,
                             headers=self.get_headers(referer=VIRTUAL_METER_URL), timeout=10)
            if r.status_code == 200:
                self._info[cons_no]["meter_display"] = r.json()["dayRead0"]

    def get_balance(self, cons_no):
        d = pq(url=BALANCE_DETAIL_URL, headers=self.get_headers())

        self._info[cons_no]["bill"] = d.find(".num.goNewBill").text()
        self._info[cons_no]["balance"] = d.find(".num.goBalanceDetail").text()

    def get_detail(self, cons_no):
        d = pq(LADDER_URL, headers=self.get_headers())
        ladder = pq(d.find(".new-text-title_tmp>span>span")[1]).text()
        ladder = 1 if ladder == "一" else 2 if ladder == "二" else 3
        self._info[cons_no]["current_level"] = ladder
        tr = d.find(".jtydtable>tr")[ladder]
        if tr is not None:
            result = pq(pq(tr)("td"))
            self._info[cons_no]["current_level_consume"] = result[1].text
            self._info[cons_no]["current_level_remain"] = result[2].text
            self._info[cons_no]["current_level_remain_percent"] = result[3].text.rstrip("%")

    def get_bill_by_year(self, cons_no):
        headers = self.get_headers()
        cur_year = self._info[cons_no]["year"]
        period = 12
        try:
            for i in range(2):
                year = cur_year - i
                params = f"consNo={cons_no}&currentYear={year}&isFlag=1"
                r = requests.post(BILLINFO_URL, headers=headers, data=params, timeout=10)
                if r.status_code == 200:
                    _LOGGER.debug(f"getBillByYear {params} response: {r.text}")
                    result = r.json()
                    if result["status"] == 0:
                        monthBills = result["data"]["monthBills"]
                        if period == 12:
                            for month in range(12):
                                if monthBills[month]["SUM_ELEC"] == "--":
                                    period = month
                                    break
                        if i == 0:
                            self._info[cons_no]["history"] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                            for i in range(period):
                                self._info[cons_no]["history"][i] = {}
                                self._info[cons_no]["history"][i]["name"] = monthBills[period - i - 1]["AMT_YM"]
                                self._info[cons_no]["history"][i]["consume"] = monthBills[period - i - 1]["SUM_ELEC"]
                                self._info[cons_no]["history"][i]["consume_bill"] = monthBills[period - i - 1][
                                    "SUM_ELECBILL"]
                        else:
                            for i in range(12 - period):
                                self._info[cons_no]["history"][11 - i] = {}
                                self._info[cons_no]["history"][11 - i]["name"] = monthBills[period + i]["AMT_YM"]
                                self._info[cons_no]["history"][11 - i]["consume"] = monthBills[period + i]["SUM_ELEC"]
                                self._info[cons_no]["history"][11 - i]["consume_bill"] = monthBills[period + i][
                                    "SUM_ELECBILL"]
                    else:
                        _LOGGER.error(f"getBillByYear error: {result['msg']}")
                else:
                    _LOGGER.error(f"getBillByYear response status_code = {r.status_code}, params = {params}")
        except:
            pass

    def get_data(self):

        retry = 0
        while not self.get_cons_no():
            if ++retry >= 3:
                _LOGGER.warning("login failure 3 times, cancel the task")
                return
            self.login()
        for cons_no in self._cons:
            self.change_cons_no(cons_no)
            self.meter(cons_no)
            self.power_trend_days(cons_no)
            self.get_balance(cons_no)
            # self.get_detail(cons_no)
            # self.get_bill_by_year(cons_no)
        _LOGGER.debug(f"Data {self._info}")
        return self._info
