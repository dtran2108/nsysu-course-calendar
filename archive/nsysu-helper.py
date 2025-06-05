import asyncio
import base64
import hashlib
from http.cookiejar import CookieJar
from typing import Optional
from bs4 import BeautifulSoup
import httpx

class SelcrsHelper:
    base_url = 'https://selcrs.nsysu.edu.tw'
    course_timeout_text = '請重新登錄'
    score_timeout_text = '請重新登錄'
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SelcrsHelper, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.client = httpx.AsyncClient(cookies=httpx.Cookies(), timeout=10.0)
        self.username = ''
        self.password = ''
        self.is_login = False
        self.relogin_count = 0
        self.index = 1
        self.error = 0

    @property
    def selcrs_url(self):
        return self.base_url  # In Dart, it's formatted — not needed here

    @property
    def can_relogin(self):
        return self.relogin_count < 5

    @staticmethod
    def base64_md5(text: str) -> str:
        md5 = hashlib.md5(text.encode()).digest()
        return base64.b64encode(md5).decode()

    async def login(self, username: str, password: str):
        self.username = username
        self.password = password
        encoded_pw = self.base64_md5(password)
        try:
            score_response = await self.client.post(
                f'{self.selcrs_url}/scoreqry/sco_query_prs_sso2.asp',
                data={
                    'SID': username,
                    'PASSWD': encoded_pw,
                    'ACTION': '0',
                    'INTYPE': '1'
                }
            )
            text = score_response.text
            if '資料錯誤請重新輸入' in text:
                return {'status': 400, 'message': 'score error'}

            course_response = await self.client.post(
                f'{self.selcrs_url}/menu4/Studcheck_sso2.asp',
                data={
                    'stuid': username,
                    'SPassword': encoded_pw,
                }
            )
            course_text = course_response.text
            if '學號碼密碼不符' in course_text:
                return {'status': 400, 'message': 'course error'}
            elif '請先填寫' in course_text:
                return {'status': 401, 'message': 'need to fill out form'}

            self.is_login = True
            return {'status': 200, 'message': 'success'}
        except httpx.HTTPError as e:
            self.error += 1
            if self.error > 5:
                raise e
            else:
                self.index = (self.index % 4) + 1
                return await self.login(username, password)

    async def get_user_info(self):
        try:
            response = await self.client.get(f'{self.selcrs_url}/menu4/tools/changedat.asp')
            text = response.text
            if self.course_timeout_text in text and self.can_relogin:
                await self.relogin()
                return await self.get_user_info()

            soup = BeautifulSoup(text, 'html.parser')
            tds = soup.find_all('td')
            if not tds or len(tds) < 10
