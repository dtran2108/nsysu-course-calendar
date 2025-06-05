import base64
import hashlib
import json
import re
from typing import Optional, Dict, List, Any, Callable
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dataclasses import dataclass
import chardet
import time

@dataclass
class Location:
    building: str
    room: str

@dataclass
class SectionTime:
    weekday: int
    index: int

@dataclass
class Course:
    code: str
    class_name: str
    title: str
    units: str
    required: str
    location: Location
    instructors: List[str]
    times: List[SectionTime]

@dataclass
class CourseData:
    courses: List[Course]
    time_codes: List[str]

    @staticmethod
    def empty():
        return CourseData(courses=[], time_codes=[])

@dataclass
class TimeCode:
    title: str
    start_time: str
    end_time: str

@dataclass
class TimeCodeConfig:
    time_codes: List[TimeCode]

    @staticmethod
    def from_raw_json(json_str: str) -> 'TimeCodeConfig':
        data = json.loads(json_str)
        time_codes = [
            TimeCode(
                title=code['title'],
                start_time=code['startTime'],
                end_time=code['endTime']
            )
            for code in data['timeCodes']
        ]
        return TimeCodeConfig(time_codes=time_codes)

    def index_of(self, section: str) -> int:
        for i, code in enumerate(self.time_codes):
            if code.title == section:
                return i
        return -1

class GeneralResponse:
    def __init__(self, status_code: int = 200, message: str = "success"):
        self.status_code = status_code
        self.message = message

    @staticmethod
    def success():
        return GeneralResponse()

    @staticmethod
    def unknown_error():
        return GeneralResponse(1000, "Unknown error")

class UserInfo:
    def __init__(self):
        self.name = ""
        self.student_id = ""
        self.department = ""
        self.grade = ""
        self.class_name = ""
        self.email = ""

    @staticmethod
    def empty():
        return UserInfo()

class SelcrsHelper:
    BASE_URL = 'https://selcrs.nsysu.edu.tw'
    COURSE_TIMEOUT_TEXT = '請重新登錄'
    SCORE_TIMEOUT_TEXT = '請重新登錄'

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.session = requests.Session()
        self.username = ''
        self.password = ''
        self.is_login = False
        self.re_login_count = 0
        self.index = 1
        self.error = 0
        self.selcrs_url = self.BASE_URL

    @property
    def can_re_login(self) -> bool:
        return self.re_login_count < 5

    def change_selcrs_url(self):
        self.index += 1
        if self.index == 5:
            self.index = 1
        self.selcrs_url = self.BASE_URL
        print(f"Changed URL to: {self.selcrs_url}")

    def logout(self):
        self.username = ''
        self.password = ''
        self.index = 1
        self.error = 0
        self.is_login = False
        self.session = requests.Session()

    @staticmethod
    def base64md5(password: str) -> str:
        md5_hash = hashlib.md5(password.encode()).digest()
        return base64.b64encode(md5_hash).decode()

    def login(self, username: str, password: str, callback: Optional[Callable] = None) -> Optional[GeneralResponse]:
        base64md5_password = self.base64md5(password)
        
        try:
            # Score system login
            score_data = {
                'SID': username,
                'PASSWD': base64md5_password,
                'ACTION': '0',
                'INTYPE': '1'
            }
            score_response = self.session.post(
                f'{self.selcrs_url}/scoreqry/sco_query_prs_sso2.asp',
                data=score_data
            )
            
            if '資料錯誤請重新輸入' in score_response.text:
                if callback:
                    return callback.on_error(GeneralResponse(400, 'score error'))
                return GeneralResponse(400, 'score error')

            # Course system login
            course_data = {
                'stuid': username,
                'SPassword': base64md5_password
            }
            course_response = self.session.post(
                f'{self.selcrs_url}/menu4/Studcheck_sso2.asp',
                data=course_data
            )

            if '學號碼密碼不符' in course_response.text:
                if callback:
                    return callback.on_error(GeneralResponse(400, 'course error'))
                return GeneralResponse(400, 'course error')
            elif '請先填寫' in course_response.text:
                if callback:
                    return callback.on_error(GeneralResponse(401, 'need to fill out form'))
                return GeneralResponse(401, 'need to fill out form')

            self.username = username
            self.password = password
            self.is_login = True
            
            if callback:
                return callback.on_success(GeneralResponse.success())
            return GeneralResponse.success()

        except requests.RequestException as e:
            self.error += 1
            if self.error > 5:
                if callback:
                    callback.on_failure(e)
                raise
            else:
                self.change_selcrs_url()
                return self.login(username, password, callback)

    def re_login(self) -> Optional[GeneralResponse]:
        self.re_login_count += 1
        return self.login(self.username, self.password)

    def get_user_info(self, callback: Optional[Callable] = None) -> Optional[UserInfo]:
        try:
            response = self.session.get(f'{self.selcrs_url}/menu4/tools/changedat.asp')
            
            if self.COURSE_TIMEOUT_TEXT in response.text and self.can_re_login:
                self.re_login()
                return self.get_user_info(callback)

            if not self.can_re_login:
                if callback:
                    callback.on_error(GeneralResponse.unknown_error())
                return None

            self.re_login_count = 0
            
            user_info = self._parse_user_info(response.text)
            if callback:
                callback.on_success(user_info)
                return None
            return user_info

        except requests.RequestException as e:
            if callback:
                callback.on_failure(e)
        except Exception:
            if callback:
                callback.on_error(GeneralResponse.unknown_error())
            raise
        return None

    def _parse_user_info(self, text: str) -> UserInfo:
        def decode_field(raw_value):
            try:
                raw_bytes = raw_value.encode('latin1')
                for enc in ['big5', 'cp950', 'utf-8']:
                    try:
                        decoded = raw_bytes.decode(enc)
                        if any('\u4e00' <= c <= '\u9fff' for c in decoded):
                            return decoded
                    except Exception:
                        continue
                return raw_value
            except Exception:
                return raw_value

        soup = BeautifulSoup(text, 'html.parser')
        td_elements = soup.find_all('td')
        user_info = UserInfo()
        if len(td_elements) >= 10:
            # department
            raw_department = td_elements[1].get_text(strip=True)
            user_info.department = decode_field(raw_department)
            # class_name
            raw_class_name = td_elements[3].get_text(strip=True).replace(' ', '')
            user_info.class_name = decode_field(raw_class_name)
            # student_id
            raw_student_id = td_elements[5].get_text(strip=True)
            user_info.student_id = decode_field(raw_student_id)
            # name
            raw_name = td_elements[7].get_text(strip=True)
            user_info.name = decode_field(raw_name)
            # email
            raw_email = td_elements[9].get_text(strip=True)
            user_info.email = decode_field(raw_email)
        return user_info

    def get_course_data(self, username: str, semester: str, time_code_config: Optional[TimeCodeConfig] = None) -> Optional[CourseData]:
        try:
            # The course data is available at /menu4/query/stu_slt_data.asp
            data = {
                'stuact': 'B',
                'YRSM': semester,
                'Stuid': username,
                'B1': '%BDT%A9w%B0e%A5X'
            }
            resp = self.session.post(
                f"{self.selcrs_url}/menu4/query/stu_slt_data.asp",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            # Try to detect the encoding
            detected = chardet.detect(resp.content)
            print("DEBUG: Detected encoding:", detected)
            
            # Try different encodings
            encodings = ['big5', 'cp950', 'utf-8', 'gbk']
            decoded_text = None
            for encoding in encodings:
                try:
                    decoded_text = resp.content.decode(encoding)
                    if any('\u4e00' <= c <= '\u9fff' for c in decoded_text):  # Check if contains Chinese characters
                        print(f"DEBUG: Successfully decoded with {encoding}")
                        break
                except UnicodeDecodeError:
                    continue
            
            if decoded_text is None:
                decoded_text = resp.content.decode('big5', errors='replace')
            
            if self.COURSE_TIMEOUT_TEXT in decoded_text and self.can_re_login:
                print("DEBUG: Session timeout detected, attempting re-login")
                self.re_login()
                return self.get_course_data(username, semester, time_code_config)
                
            if not self.can_re_login:
                print("Failed to get course data: login timeout")
                return None

            self.re_login_count = 0
            start_time = time.time()
            
            soup = BeautifulSoup(decoded_text, "html.parser")
            tr_elements = soup.find_all("tr")
            
            if len(tr_elements) <= 1:
                return CourseData.empty()

            course_data = CourseData(
                courses=[],
                time_codes=[code.title for code in time_code_config.time_codes] if time_code_config else []
            )
            
            # Skip header row
            for tr in tr_elements[1:]:
                td_elements = tr.find_all("td")
                if len(td_elements) < 10:
                    continue

                # Get course title
                title_element = td_elements[4].find("a")
                if not title_element:
                    continue
                    
                titles = title_element.get_text(strip=True).split('\n')
                title = titles[0]  # Default to Chinese title
                
                # Get course details
                course = Course(
                    code=td_elements[2].get_text(strip=True),
                    class_name=f"{td_elements[1].get_text(strip=True)} {td_elements[3].get_text(strip=True)}",
                    title=title,
                    units=td_elements[5].get_text(strip=True),
                    required=td_elements[7].get_text(strip=True) + "修" if len(td_elements[7].get_text(strip=True)) == 1 else td_elements[7].get_text(strip=True),
                    location=Location(
                        building="",
                        room=td_elements[9].get_text(strip=True)
                    ),
                    instructors=[td_elements[8].get_text(strip=True)],
                    times=[]
                )
                
                # Get course times
                for j in range(10, len(td_elements)):
                    time_text = td_elements[j].get_text(strip=True)
                    if time_text:
                        sections = list(time_text)
                        for section in sections:
                            if section != ' ':
                                index = time_code_config.index_of(section) if time_code_config else -1
                                if index != -1:
                                    course.times.append(SectionTime(weekday=j-9, index=index))
                
                course_data.courses.append(course)
            
            end_time = time.time()
            print(f"Course parsing took {end_time - start_time:.2f} seconds")
            
            return course_data
            
        except Exception as e:
            print(f"Error getting course data: {e}")
            return None