import requests
from datetime import datetime, timedelta, timezone
import argparse
from configparser import ConfigParser
import xml.etree.ElementTree as ET
from pprint import pprint


config_file = "config/config.ini"


class TravelWeather:

    def __init__(self):
        # Configuration checking
        init_config = ConfigParser()
        if not init_config.read(config_file, encoding="utf-8"):
            raise Exception("No config file")
        self.key = init_config['travel_weather'].get('key', raw=True)

        # Argument Checking
        parser = argparse.ArgumentParser(description='Get course ID')
        parser.add_argument('cnum', metavar='CNUM', type=int, nargs='?', default=393,
                            help='A course ID for travel')
        args = parser.parse_args()
        self.cnum = args.cnum

        # Making time information
        now_time_info = datetime.now(timezone(timedelta(hours=-9, minutes=0)))
        self.year = now_time_info.year
        self.month = now_time_info.month
        self.day = now_time_info.day
        self.hour = now_time_info.hour

    def _request_and_check(self):
        req_string = (
            'http://newsky2.kma.go.kr/service/TourSpotInfoService/SpotShrtData?'
            'CURRENT_DATE=%04d%02d%02d%02d&HOUR=24&COURSE_ID=%d&serviceKey=%s' %
            (self.year, self.month, self.day, self.hour, self.cnum, self.key))
        r = requests.get(req_string)
        if r.status_code != 200:
            raise Exception(str(r))
        return r.text

    def _xml_parsing(self, web_request_result_text):
        xml_root = ET.fromstring(web_request_result_text)
        x_header = xml_root.find('header')
        x_result_code = x_header.find('resultCode').text
        if x_result_code != '0000':
            raise Exception("ResultCode from server error: " + x_result_code)
        all_items = xml_root.find('body').find('items').findall('item')
        # one item format
        # <item>
        #   <areaId>5011025300</areaId>
        #   <courseAreaId>5000000000</courseAreaId>
        #   <courseAreaName>제주도</courseAreaName>
        #   <courseId>393</courseId>
        #   <courseName>제주 2박3일 여행코스</courseName>
        #   <pop>0</pop>
        #   <rhm>75</rhm>
        #   <sky>1</sky>
        #   <spotAreaId>39314</spotAreaId>
        #   <spotAreaName>제주</spotAreaName>
        #   <spotName>(제주)프시케월드 나비박물관</spotName>
        #   <th3>19</th3>
        #   <thema>자연/힐링</thema>
        #   <tm>2019-06-04 03:00</tm>
        #   <wd>9</wd>
        #   <ws>2.6</ws>
        # </item>
        return [dict((element.tag, element.text)
                     for element in list(item)) for item in all_items]

    def read(self):
        self.xml_parsed_items = self._xml_parsing(self._request_and_check())
        return self

    def get_data(self):
        return self.xml_parsed_items

    def apply(self, MethodClass):
        self.xml_parsed_items = MethodClass.apply(self.xml_parsed_items)


class SkyChange:
    contents_translation = {
        1: '맑음',
        2: '구름조금',
        3: '구름많음',
        4: '흐림',
        5: '비',
        6: '비눈',
        7: '눈비',
        8: '눈'
    }
    @classmethod
    def apply(cls, input_data):
        return [
            dict((k, cls.contents_translation[int(v)]) if k == 'sky' else (k, v)
                 for k, v in item.items()) for item in input_data]


class Name2Korean:
    name_translation = {
        "tm": "예보시각",
        "courseId": "코스 아이디",
        "courseAreaId": "코스-지역아이디",
        "areaId": "지역 아이디",
        "courseAreaName": "코스-지역이름",
        "spotAreaId": "관광지-지역아이디",
        "spotAreaName": "관광지-지역 이름",
        "courseName": "코스 명",
        "spotName": "관광지명",
        "thema": "테마",
        "th3": "3시간 기온",
        "maxTa": "최고기온",
        "minTa": "최저기온",
        "wd": "풍향",
        "ws": "풍속",
        "sky": "하늘상태",
        "rhm": "습도",
        "pop": "강수확률",
        "rn": "강수량"
    }
    @classmethod
    def apply(cls, input_data):
        return [dict((cls.name_translation[k], v) if k in cls.name_translation else (
                k, v) for k, v in item.items()) for item in input_data]


if __name__ == "__main__":
    weather_info = TravelWeather().read()
    weather_info.apply(SkyChange)
    weather_info.apply(Name2Korean)
    pprint(weather_info.get_data())
