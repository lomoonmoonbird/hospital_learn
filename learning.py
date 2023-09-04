import requests
import json
import random
import time
import math
import struct
from collections import defaultdict
from datetime import datetime, timezone


class HuShiJie():

    def __init__(self):
        self.headers = {
            "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI2NzAwIiwiZXhwIjoxNjY2MDg0MDY1LCJpYXQiOjE2MzQ1NDgwNjV9.qc-mV6s4XbH2ZlZrfCyicsMPE-0slhnM5CY2udCg5AM",
            "Origin": None,
            "appid": "hushijie",
            "isApp": "1",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/44)",
            # "User-Agent": "Mozilla/5.0 (Linux; U; Android 4.4.4; zh-cn; HTC_D820u Build/KTU84P) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30"
            # "User-Agent": "Mozilla/5.0 (Linux; U; Android 8.1.0; zh-cn; BLA-AL00 Build/HUAWEIBLA-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.132 MQQBrowser/8.9 Mobile Safari/537.36"
        }

        self.is_finish = False
        self.BASE_URL = "https://ns.hushijie.com.cn"
        self.VIDEO_BASE_URL = "https://ns-oss.hushijie.com.cn/video_trans_file/"
        self.VIDEO_BASE_URL2 = "https://ns-oss.hushijie.com.cn/customer_926/"
        self.LIST_URL = self.BASE_URL + "/bms/api/trainStudy/app/findList"
        self.DETAIL_URL = self.BASE_URL + "/bms/api/trainStudy/app/getInfo"
        self.RECORD_URL = self.BASE_URL + "/bms/api/trainStudy/app/recordTimes"
        self.LOGIN_URL = self.BASE_URL + "/bms/api/user/login"

    def set_header_authorization(self, token):
        self.headers['Authorization'] = token

    def get_mp4_length_online(self, url, detail = None, lst=None):
        """
        在线获取视频时长 单位秒
        :param url:
        :return:
        """
        if url.startswith("qiniuo"):
            url = self.VIDEO_BASE_URL2 + url
        else:
            url = self.VIDEO_BASE_URL + url
        try_count = 0
        while try_count <= 5:
            try:
                r = requests.get(url, stream=True)
                if r.status_code == 404:
                    return 600
                print("video url : ", url)
                # print('get_mp4_length_online response', r.content)
                for data in r.iter_content(chunk_size=512):
                    if data.find(b'mvhd') > 0:
                        index = data.find(b'mvhd') + 4
                        time_scale = struct.unpack('>I', data[index + 13:index + 13 + 4])
                        durations = struct.unpack('>I', data[index + 13 + 4:index + 13 + 4 + 4])
                        duration = durations[0] / time_scale[0]
                        # print("video length:", duration)
                        # return math.floor(duration%3600//60)
                        return round(duration)
            except:
                try_count += 1
                import traceback
                print(lst)
                print(detail)
                return 600

    def delta(self):
        """
        视频完成时间的偏移量
        :return:
        """
        return random.randint(60,90)

    def request_get(self, url, params=None):
        """
        get请求
        :param url:
        :param params:
        :return:
        """
        try:
            self.headers['Content-Type'] = "application/json"
            response = requests.get(url, headers=self.headers, params=params)
            response_body = json.loads(response.content)
            if response.status_code == 200 and response_body['code'] ==0:
                return response_body
            return {}
        except:
            raise Exception("错误")

    def request_post(self, url, data):
        """
        post请求
        :param url:
        :param data:
        :return:
        """
        self.headers['Content-Type'] = "application/x-www-form-urlencoded"
        try:
            response = requests.post(url, headers=self.headers, data=data)
            response_body = json.loads(response.content)
            print("response_body", response_body)
            if response.status_code == 200 and response_body['code'] == 0:
                return response_body
            return {}
        except:
            pass

    def get_course_list(self, page_num, page_size=10):
        """
        获取课程列表
        :param page_num:
        :param page_size:
        :return:
        """
        params = {"pageNum":page_num,"pageSize":page_size}
        course_list = self.request_get(self.LIST_URL, params=params)
        if course_list['data']['size'] < 10:
            self.is_finish = True
        return course_list['data']['list'] if course_list else []


    def get_course_detail(self, course_id):
        """
        获取课程详情
        :param course_id:
        :return:
        """
        data = {"id": course_id}
        course_detail = self.request_post(self.DETAIL_URL, data)
        return course_detail['data']

    def is_recorded(self, single_video):
        """
        是否已经完成
        :param single_video:
        :return:
        """
        exed_time = single_video['exed_time']
        time_length = single_video['time_length']
        real_time_length = single_video['real_time_length']
        state = single_video['state']
        if exed_time < real_time_length:
            return False
        if exed_time < 0:
            return False
        if real_time_length < exed_time or state == 2:
            return True
        return False

    def extract_record_params(self, course_detail, one_list=None):
        """
        构造完成视频学习的请求参数
        :param course_detail:
        :return:
        """
        coursewares = course_detail['courseWares'] #列表
        train_info = course_detail['trainInfo']
        courses = json.loads(train_info['courses'])
        files = courses['files'] #列表

        coursewares_defaultdict = defaultdict(dict)
        files_defaultdict = defaultdict(dict)
        for cd in coursewares:
            if cd['type'] != 3:
                continue
            coursewares_defaultdict[cd['name']] = cd
        for fd in files:
            if fd['type'] != 3:
                continue
            files_defaultdict[fd['name']] = fd
        video_list = []
        if not coursewares_defaultdict or not files_defaultdict:
            return video_list
        for f in files:
            if f['type'] !=3:
                continue
            # time_length = self.get_mp4_length_online(self.VIDEO_BASE_URL + f['url']) if not\
            #     coursewares_defaultdict[f['name']]['timeLength'] else coursewares_defaultdict[f['name']]['timeLength'] * 60
            time_length = self.get_mp4_length_online(f['url'], detail=course_detail, lst=one_list)
            exed_time = coursewares_defaultdict[f['name']]['exedTime']
            max_progress = coursewares_defaultdict[f['name']]['maxProgress']
            times = time_length  + self.delta()
            if exed_time > 0 and exed_time < time_length:
                times = time_length - exed_time + self.delta()
            if exed_time == 0 and max_progress > 0:
                times -= coursewares_defaultdict[f['name']]['lastPlayTime']
            if exed_time > times:
                times = -(exed_time - times - self.delta())
            if exed_time < 0:
                times = -exed_time + times
            video_list.append({"name": f['name'],
                               "train_id": train_info['id'],
                               "parent_id":coursewares_defaultdict[f['name']]['parentId'],
                               "file_id": f['id'],
                               "type":f['type'],
                               'is_normal':1,
                               "times": times,
                               # "times": 0,
                               "scale": courses['scale'],
                               "time_length": f['timeLength'],
                               'real_time_length': time_length,
                               "state": coursewares_defaultdict[f['name']]['state'],
                               "exed_time": exed_time,
                               "max_progress": 0,
                               "last_playtime": 0
                               # "max_progress": max_progress,
                               # "last_playtime":coursewares_defaultdict[f['id']]['lastPlayTime']
                               })
        return video_list

    def single_course_detail(self, id):
        course_detail = self.get_course_detail(id)
        return course_detail

    def record_video(self, video_list):
        """
        完成视频学习
        :param video_list:
        :return:
        """
        if not video_list:
            return True
        success_flag = 0
        video_list_length = len(video_list)
        for vl in video_list:
            is_finished = self.is_recorded(vl)
            if is_finished:
                success_flag += 1
                continue

            record_time_data = {"name": vl['name'],
                                "trainId": vl['train_id'],
                                "parentId":vl['parent_id'],
                                "fileId":vl['file_id'],
                                "type":vl['type'],
                                "isNormal": vl['is_normal'],
                                "times": vl['times'], #转化成秒
                                "scale":vl['scale'],
                                "timeLength":vl['time_length'], #总时长 分钟
                                "maxProgress":vl['max_progress'], #当前进度
                                "lastPlayTime": vl['last_playtime']} #上次播放时间

            if record_time_data['type'] != 3:
                continue
            res = self.request_post(self.RECORD_URL, data=record_time_data)
            if res['code'] == 0 and res['state'] == 2: #
                success_flag += 1
            time.sleep(1)
        return success_flag == video_list_length


    def count_of_video_course(self):
        page_num = 1
        count = 0
        while not self.is_finish:
            course_list = self.get_course_list(page_num)
            count += len(course_list)
            page_num += 1
        return count

    def count_of_video(self):

        page_num = 1
        count = 0
        while not self.is_finish:
            course_list = hsj.get_course_list(page_num)
            for one in course_list:
                detail = self.get_course_detail(one['id'])
                train_info = detail['trainInfo']
                courses = json.loads(train_info['courses'])
                files = courses['files']  # 列表
                for fd in files:
                    if fd['type'] == 3:
                        count += 1
                        break
            page_num += 1
        return count

    def finish_video_course_2021(self):
        page_num = 1
        timestamp_20210101 = int(datetime(2021, 1, 1).replace(tzinfo=timezone.utc).timestamp() * 1000)
        timestamp_20210924 = int(datetime(2021, 1, 1).replace(tzinfo=timezone.utc).timestamp() * 1000)
        count = 0
        while not self.is_finish:
            course_list = self.get_course_list(page_num)
            time.sleep(1)
            for course in course_list:
                print(course)
                #if course['isLongTime'] == 1: #长期开放的
                #    continue
                print("course", course)
                if course['endTime'] < timestamp_20210924:
                    continue
                print('get course detail ')
                detail = self.get_course_detail(course['id'])
                # time.sleep(1)
                print('extract_record_params')
                video_list = self.extract_record_params(detail, one_list=course)
                # time.sleep(1)
                print("record_video")
                self.record_video(video_list)
            page_num += 1
            count += 1

            print("all finish ", count)
        print('all finish!', count)

    def finish_long_time(self):
        page_num = 1
        count = 0
        while not self.is_finish:
            course_list = self.get_course_list(page_num)
            time.sleep(1)
            for course in course_list:
                print(course)
                if course['isLongTime'] == 1: #长期开放的

                    print('get course detail ')
                    detail = self.get_course_detail(course['id'])
                    # time.sleep(1)
                    print('extract_record_params')
                    video_list = self.extract_record_params(detail, one_list=course)
                    # time.sleep(1)
                    print("record_video")
                    self.record_video(video_list)
            page_num += 1
            count += 1

            print("all finish ", count)
        print('all finish!', count)

    def finish_all_video_course(self):
        page_num = 1
        count = 0
        while not self.is_finish:
            course_list = self.get_course_list(page_num)
            print("course_list length:", len(course_list))
            time.sleep(1)
            for course in course_list:
                print(course)
                if course['isLongTime'] == 1:
                    continue
                detail = self.get_course_detail(course['id'])
                # time.sleep(1)
                video_list = self.extract_record_params(detail, one_list=course)
                # time.sleep(1)
                self.record_video(video_list)
            page_num += 1
            count += 1

            print("finish ", count)
        print('finish!', count)


    def login(self, username, password, hospital):
        data = {"userName": username, "password": password, "hospitalId": hospital}
        # headers = {}
        ret = self.request_post(self.LOGIN_URL, data)
        print(ret)

hsj = HuShiJie()
hsj.set_header_authorization("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxMjYxMTMiLCJleHAiOjE2NzIyMTA0MjYsImlhdCI6MTY0MDY3NDQyNn0.OZDKeLhsp_FlEgDGs4o-h3P_xhG_luLJMhq0mTSz9Sg")
# hsj.login("13598877895", "a840528", 926)

#单个课程
# single_course = hsj.single_course_detail(47030)
# print(single_course)
# video_list = hsj.extract_record_params(single_course)
# print(video_list)
# flag = hsj.record_video(video_list)
# print(flag)

#完成2021 9 25之前的
hsj.finish_long_time()
#完成所有的
# hsj.finish_all_video_course()
#所有
# for one in hsj.get_course_list(2):
#     course_detail = hsj.get_course_detail(one['id'])
#     video_list = hsj.extract_record_params(course_detail, one_list=one)
#     print(video_list)
    # flag = hsj.record_video(video_list)
    # print(flag)
# print(len(hsj.get_course_list(2)))
# headers = {
#                 "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIxMjYxMTMiLCJleHAiOjE2NjQzNDQwNTMsImlhdCI6MTYzMjgwODA1M30.8FlSgiDjEs_LfEV-hwI5z9MgIusziEo-Ipx1GEISLrg",
#                 "Origin": None,
#                 "appid": "hushijie",
#                 "isApp": "1",
#                 "Content-Type": "application/x-www-form-urlencoded",
#                 # "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/44)",
#                 "User-Agent": "Mozilla/5.0 (Linux; U; Android 4.4.4; zh-cn; HTC_D820u Build/KTU84P) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30"
#             }
# data = {"name":"不同人群预防新型冠状病毒感染口罩选择与使用技术指引-孙明洁",
#         "scale": 50,
#         "fileId":1,
#         "trainId":47517,
#         "type":3,
#         "times":1779,
#         "parentId":157178,
#         "maxProgress": 0,
#         "lastPlayTime": 0,
#         "isNormal": 1,
#         "timeLength":0}
#
# res = requests.post("https://ns.hushijie.com.cn/bms/api/trainStudy/app/recordTimes", data=data, headers=headers)
# print(res.status_code)
# print(res.content)

