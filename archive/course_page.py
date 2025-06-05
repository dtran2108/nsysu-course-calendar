from dataclasses import dataclass
from typing import Optional, List, Callable
from enum import Enum
import json

class CourseState(Enum):
    LOADING = "loading"
    FINISH = "finish"
    ERROR = "error"
    EMPTY = "empty"

@dataclass
class Semester:
    year: str
    value: str
    text: str

@dataclass
class SemesterData:
    data: List[Semester]
    current_index: int
    default_index: int
    current_semester: Semester
    default_semester: Semester

@dataclass
class CourseNotifyData:
    @staticmethod
    def load(key: str) -> Optional['CourseNotifyData']:
        # Implementation would depend on your storage system
        pass

    def save(self, key: str):
        # Implementation would depend on your storage system
        pass

class CoursePage:
    def __init__(self):
        self.state = CourseState.LOADING
        self.semester_data: Optional[SemesterData] = None
        self.course_data = None  # Would be your CourseData type
        self.notify_data: Optional[CourseNotifyData] = None
        self.custom_state_hint: Optional[str] = None
        self.custom_hint: Optional[str] = None
        self.is_offline = False
        self.default_semester_code = ""

    def get_semester(self):
        try:
            # This would be your remote config implementation
            remote_config = self._get_remote_config()
            self.default_semester_code = remote_config.get_string("default_course_semester_code")
            raw_time_code_config = remote_config.get_string("time_code_config")
            time_code_config = TimeCodeConfig.from_raw_json(raw_time_code_config)
            
            # Save to preferences
            self._save_preference("default_course_semester_code", self.default_semester_code)
            self._save_preference("time_code_config", raw_time_code_config)
            
        except Exception:
            # Fallback to stored preferences
            self.default_semester_code = self._get_preference(
                "default_course_semester_code",
                f"{Constants.default_year}{Constants.default_semester}"
            )
            time_code_config = TimeCodeConfig.from_raw_json(
                self._get_preference(
                    "time_code_config",
                    # Your default time code config JSON string
                    '{"timeCodes":[...]}'
                )
            )

        default_semester = Semester(
            year=self.default_semester_code[:3],
            value=self.default_semester_code[3:],
            text=self._parse_semester_text(self.default_semester_code)
        )

        # Get course semester data
        self._get_course_semester_data(
            default_semester=default_semester,
            callback=GeneralCallback(
                on_failure=self._on_failure,
                on_error=self._on_error,
                on_success=self._on_semester_success
            )
        )

    def _parse_semester_text(self, text: str) -> str:
        if len(text) == 4:
            last_code = text[3]
            last = ""
            if last_code == "0":
                last = "continuing_summer_education_program"
            elif last_code == "1":
                last = "fall_semester"
            elif last_code == "2":
                last = "spring_semester"
            elif last_code == "3":
                last = "summer_semester"

            first = ""
            if self._is_english_locale():
                year = int(text[:3]) + 1911
                first = f"{year}~{year + 1}"
            else:
                first = f"{text[:3]}course_year"

            return f"{first} {last}"
        return text

    def _on_semester_success(self, data: SemesterData):
        self.semester_data = data
        semester = self._get_preference(
            "current_semester_code",
            "semester_latest"
        )
        
        if semester != self.default_semester_code:
            self._save_preference("current_semester_code", self.default_semester_code)
        
        for option in self.semester_data.data:
            option.text = self._parse_semester_text(option.text)
        
        self.semester_data.current_index = self.semester_data.default_index
        self._get_course_tables()

    def _get_course_tables(self):
        if self.semester_data is None:
            self.get_semester()
            return

        self.notify_data = CourseNotifyData.load(self._get_course_notify_cache_key())
        
        # Get course data
        self._get_course_data(
            username=self._get_username(),
            time_code_config=self._get_time_code_config(),
            semester=self.semester_data.current_semester.code,
            callback=GeneralCallback(
                on_failure=self._on_failure,
                on_error=self._on_error,
                on_success=self._on_course_success
            )
        )

    def _on_course_success(self, data):
        self.course_data = data
        self.course_data.save(self._get_course_notify_cache_key())
        
        if not self.course_data.courses:
            self.state = CourseState.EMPTY
        else:
            self.state = CourseState.FINISH

    def _on_failure(self, error):
        self.custom_hint = "offline_course"
        self.state = CourseState.FINISH

    def _on_error(self, _):
        self.state = CourseState.ERROR

    def _get_course_notify_cache_key(self) -> str:
        return self.semester_data.default_semester.code if self.semester_data else "1091"

    # Helper methods that would need to be implemented based on your system
    def _get_remote_config(self):
        # Implementation would depend on your remote config system
        pass

    def _save_preference(self, key: str, value: str):
        # Implementation would depend on your preferences system
        pass

    def _get_preference(self, key: str, default: str) -> str:
        # Implementation would depend on your preferences system
        pass

    def _is_english_locale(self) -> bool:
        # Implementation would depend on your locale system
        pass

    def _get_username(self) -> str:
        # Implementation would depend on your user system
        pass

    def _get_time_code_config(self):
        # Implementation would depend on your time code config system
        pass

    def _get_course_semester_data(self, default_semester: Semester, callback: GeneralCallback):
        # Implementation would depend on your course semester data system
        pass

    def _get_course_data(self, username: str, time_code_config, semester: str, callback: GeneralCallback):
        # Implementation would depend on your course data system
        pass 