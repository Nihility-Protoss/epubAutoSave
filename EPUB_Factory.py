import re
import os
import sys
import time
import json
import shutil
import requests
import selenium
import traceback
import func_timeout
import urllib.request
from loguru import logger
from selenium import webdriver
from ebooklib_xierluo import epub
from collections import OrderedDict
import undetected_chromedriver as uc
import xml.etree.ElementTree as ETree
from confuseFont import obfuscate_plus
from func_timeout import func_set_timeout

"""
author: Xierluo
effect: 一键生成EPUB
"""
Your_token = '{%22security_key%22:%22ffffeeeeddddccccbbbbaaaa99998888:000000:0%22}'
EPUB_static = {
    "WebIndex": 1122344,
    "BookName": "我开始做死神的助手了",
    "ImgName": "图片-",
    "OtherName": "",
    "Translator": "",
    "haveHTML": False,
    'haveAPP': False
}


class getAllData:
    def __init__(self, py_static=None):
        # web
        self.Web_Index_num = 0
        self.Web_Source_str = "LK"
        self.Web_URL_dict = {"LK": "https://www.lightnovel.us/cn/detail/", "fromLK": "https://www.lightnovel.us/"}
        self.Web_request_if = True
        self.Web_series_if = False
        self.Web_series_num = 0
        self.Web_series_content = ""
        # app
        self.App_use_TF = False
        self.App_bak_path = "./.appBak/"
        self.App_bak_dict = {"LK": "LK(net.lk.qingguo).bak"}
        self.App_xml_Tree = None
        self.App_img_format = []
        # img
        self.Img_Save_str = "图片-"
        self.Img_have_len = 0
        self.Img_format_list = []
        self.Img_format_easy = False
        self.Img_save_path = None
        # text
        self.Text_name_str = ""
        self.Text_easy_str = ""
        self.Text_easy_list = []
        # static
        self.file_path_dict = {"xhtml": "/xhtml/", "image": "/image/", "config": "/config/", "txt": "/", "epub": "/"}
        self.EPUB_null_file = "./EPUB-NULL.epub"
        self.py_static = py_static
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 '
                                      '(KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36 android 9.9',
                        'Referer': self.Web_URL_dict["from" + self.Web_Source_str]}
        # run
        self.Input()
        print("——————输入区域结束———————")
        self.OsFilePath()
        print("——————文件夹生成完毕——————")
        if self.OsTxtFileAppraise():
            self.ImgSaveList()
            print("——————图片爬取完毕———————")

    def Input(self):
        """

        Returns:
            更新Web_Index_type、Text_name_str的值
        传入待处理的单个网址数据、书本名称

        """
        if not self.py_static:
            print("请输入书籍网址数据：")
            self.Web_Index_num = int(input())
            print("请输入书籍名字：")
            self.Text_name_str = input()
        else:
            self.Web_Index_num = self.py_static["WebIndex"]
            self.Text_name_str = self.py_static["BookName"]
            self.Img_Save_str = self.py_static["ImgName"]
            self.Web_request_if = not self.py_static["haveHTML"]
            self.App_use_TF = self.py_static['haveAPP']
        self.Text_name_str = re.sub('/', '-', self.Text_name_str)
        self.Text_name_str = re.sub('\u3000', ' ', self.Text_name_str)

    def OsFilePath(self):
        """

        Returns:
            生成相应的文件夹组，并更新file_path_dict中的值

        """
        cwd = os.getcwd()
        file_name = os.path.join(cwd, self.Text_name_str)
        file_name_HTML = os.path.join(cwd, self.Text_name_str + "/xhtml")
        file_name_IMGE = os.path.join(cwd, self.Text_name_str + "/image")
        file_name_CONF = os.path.join(cwd, self.Text_name_str + "/config")
        if not os.path.exists(self.Text_name_str):
            os.mkdir(file_name)
            os.mkdir(file_name_HTML)
            os.mkdir(file_name_IMGE)
            os.mkdir(file_name_CONF)

        self.file_path_dict["txt"] = self.Text_name_str + "/"
        self.file_path_dict["xhtml"] = self.Text_name_str + "/xhtml/"
        self.file_path_dict["image"] = self.Text_name_str + "/image/"
        self.file_path_dict["config"] = self.Text_name_str + "/config/"
        self.file_path_dict["epub"] = self.Text_name_str + "/" + self.Text_name_str + ".epub"

        # shutil.copy(self.EPUB_null_file, self.file_path_dict["epub"])

    def OsTxtFileAppraise(self):
        file_list = os.listdir(self.file_path_dict['txt'])
        file_save_txt = self.file_path_dict["txt"] + str(self.Web_Index_num) + " - "
        file_name_txt = str(self.Web_Index_num) + " - "
        # print(file_name_txt + "ImgSave-Index.txt")
        if file_name_txt + "ImgSave-Index.txt" in file_list:
            self.Text_easy_str = open(file_save_txt + "ImgSave-Index.txt", 'r', encoding='utf8').read()
            self.Text_easy_list = open(file_save_txt + "ImgSave-Index.txt", 'r', encoding='utf8').readlines()
            return True
        return False

    def AppGetText(self):
        # logger.remove()
        # logger.add(sys.stdout, level='INFO', format='{message}')
        # logger.add(self.App_bak_path + 'file_{time}.log', level='INFO', format='{message}')

        # bak to xml
        App_bak_byte = open(self.App_bak_path + self.App_bak_dict['LK'], 'rb').read()
        App_bak_byte = App_bak_byte.replace(b"&quot;", b'"').replace(b'\n', b'$').replace(b'\x00' * 100, b'\n')
        App_xml_get = re.findall(b"<\?xml .*</map>\$", App_bak_byte)
        for xml in App_xml_get:
            if xml.find(b'flutter.loginInfo') != -1:
                open(self.App_bak_path + "get_xml.xml", 'wb').write(xml.replace(b'$', b'\n'))
                break

        # get article data
        data_dict = {}
        data_aid_list = []
        self.App_xml_Tree = ETree.parse(self.App_bak_path + "get_xml.xml")
        xml_root = self.App_xml_Tree.getroot()
        for child in xml_root:
            if child.attrib['name'].find('flutter.Article') == -1 or child.tag != 'string':
                continue
            data_json_dict = json.loads(child.text, strict=False)
            data_dict[data_json_dict['aid']] = data_json_dict
            data_aid_list.append(data_json_dict['aid'])

        # data save to app_data
        if self.Web_Index_num not in data_aid_list:
            print("未查询到所需数据")
            return ValueError
        file_name = self.file_path_dict["txt"] + str(self.Web_Index_num) + " - app_data.json"
        data_json = json.dumps(data_dict[self.Web_Index_num])
        open(file_name, 'w', encoding='utf8').write(data_json)

    def AppImgUpdate(self):
        file_name_app = self.file_path_dict["txt"] + str(self.Web_Index_num) + " - app_data.json"
        file_name_txt = self.file_path_dict["txt"] + str(self.Web_Index_num) + " - "
        data_json = json.load(open(file_name_app, 'r', encoding='utf8'))
        file_imgChange = open(file_name_txt + 'ImgSave-Index.txt', 'w', encoding='utf-8')

        # ImgURL data file
        if not self.Web_series_if:
            file_imgURL = open(file_name_txt + 'ImgURL.txt', 'w', encoding='utf-8')
        else:
            file_imgURL = open(file_name_txt + 'ImgURL.txt', 'a', encoding='utf-8')

        # data save to ImgURL and ImgSave-Index
        index_now_img = 1
        list_contents_all = []
        data_res = data_json['res']['res_info']
        data_content = data_json['content'].split('\n')
        for line in data_content:
            # print(line)
            if line.find('[res]') != -1:
                # print(line)
                res_data = line[5:-6]
                line_url = data_res[res_data]['url']
                line_format = data_res[res_data]['ext']
                file_imgURL.write(line_url + "\n")
                self.App_img_format.append(line_format)
                line = self.Img_Save_str + str(index_now_img)
                # print(line)
                index_now_img += 1
            elif line.find('[img]') != -1:
                print('img')
                line = self.Img_Save_str + str(index_now_img)
                index_now_img += 1

            if line.find('[b]') != -1:
                line = line.replace('[b]', '<b>').replace('[/b]', '</b>')
                if line:
                    list_contents_all.append(line + '\n')
            if line.find('[i]') != -1:
                line = line.replace('[i]', '<i>').replace('[/i]', '</i>')

            line += '\n'
            self.Text_easy_list.append(line)
            file_imgChange.write(line)

        print(list_contents_all)
        file_content = open(file_name_txt + "Contents.txt", 'w', encoding='utf-8')
        for i in list_contents_all:
            if i != '\n':
                file_content.write(i)
        file_content.write("\n席尔洛（结束标志）\n")

        file_imgChange.write('\n席尔洛（结束标志）\n')

    def RequestChangeText(self, text_write_arrange):
        num = self.Web_Index_num
        # 基础处理s
        text_write_arrange = re.sub(r'\\"', '"', text_write_arrange)
        text_write_arrange = re.sub('<span style="color.{0,25}>', '', text_write_arrange)
        text_write_arrange = re.sub('<span style="color: #[\da-fA-F]{6}>', '', text_write_arrange)
        text_write_arrange = re.sub('<div class="article-extra-file">', '', text_write_arrange)
        text_write_arrange = re.sub('<div class="inline-align-left">', '', text_write_arrange)
        text_write_arrange = re.sub('<div align="justify">', '', text_write_arrange)
        text_write_arrange = re.sub('<div style="display: none;">', '', text_write_arrange)
        text_write_arrange = re.sub('<span style="font-family:[a-zA-Z-,]*">', '', text_write_arrange)
        text_write_arrange = re.sub('<span style="font-size:.{0,15}">', '', text_write_arrange)
        text_write_arrange = re.sub('.*<article id=\"article-main-contents\">', '', text_write_arrange)
        text_write_arrange = re.sub('</article>', '', text_write_arrange)
        text_write_arrange = re.sub('</span>', '', text_write_arrange)
        text_write_arrange = re.sub('<!---->', '', text_write_arrange)
        # 空格型处理
        text_write_str = re.sub('\u3000', ' ', text_write_arrange)
        text_write_str = re.sub('\\u3000', ' ', text_write_arrange)
        text_write_str = re.sub('\\xa0', ' ', text_write_str)
        text_write_str = re.sub(' {2}', ' ', text_write_str)
        # 重复<b>处理
        for i in range(4, 1, -1):
            text_write_str = re.sub('<b>' * i, '<b>', text_write_str)
            text_write_str = re.sub('</b>' * i, '</b>', text_write_str)
        # 换行符处理
        text_write_str = re.sub('<br>', '\n', text_write_str)
        text_write_str = re.sub('</div>', '\n', text_write_str)
        text_write_str = re.sub('&nbsp;', '\n', text_write_str)
        text_write_str = re.sub('<b></b>', "\n", text_write_str)
        text_write_str = re.sub('\n ', '\n', text_write_str)
        for i in range(4, 2, -1):
            text_write_str = re.sub('\n' * i, '\n\n', text_write_str)
        return text_write_str

    def RequestAllTest(self, base_url):
        useCoin_url = "https://www.lightnovel.us/proxy/api/coin/use"
        useCoin_postData = {"is_encrypted": 0, "platform": "pc", "client": "web", "sign": "", "gz": 0,
                            "d": {"params": self.Web_Index_num, "goods_id": 1, "price": 10, "total_price": 10,
                                  "number": 1, "security_key": "e8795df6e20be1b1edc4c485ec095d2b:933835:0"}}
        token = {'token': Your_token}
        cookie = requests.utils.cookiejar_from_dict(token)
        cookie_token = {
            'name': 'token',
            'domain': 'www.lightnovel.us',
            'path': '/',
            'value': Your_token}

        # # old session
        # session = requests.Session()
        # session.cookies.update(cookie)
        # session.headers.update(self.headers)
        # new selenium
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        driver = uc.Chrome(options=options)
        driver.get(base_url)
        driver.add_cookie(cookie_token)
        driver.get(base_url)

        # data_res0 = session.get(url=base_url)
        data_res0 = driver.execute_script("return document.documentElement.outerHTML")
        file_name_all = self.file_path_dict["txt"] + str(self.Web_Index_num) + " - "
        if not self.Web_series_if:
            file_origin = open(file_name_all + "Base_origin.txt", "w", encoding="utf-8")
            file_origin.write(data_res0)
            file_origin.close()
            print("成功生成Base_origin文件")

        data_res1 = driver.find_element("class name", "article-content")
        print("part1 请求数据结束：" + str(data_res1))

        # data_res0 = re.sub(r"\\u003C", "<", data_res0.text)
        # data_res0 = re.sub(r"\\u003E", ">", data_res0)
        # data_res0 = re.sub(r"\\u002F", "/", data_res0)
        # data_res1 = re.findall('<div class=\"article-content\">.*<div class=\"article-extra-file\">', data_res0)
        try:
            print("part2-1 寻找轻币解锁模块")
            data_lock = data_res1.find_element("class name", "article-content-lock")
            need_coin = re.findall("\d{1,3}.*轻币解锁", data_lock.text)
            need_coin_num = re.findall("\d{1,2}", need_coin[0])
            print("part2-3 即将支付" + need_coin_num[0] + "轻币到当前页面")
            useCoin_postData["d"]["price"] = int(need_coin_num[0])
            useCoin_postData["d"]["total_price"] = int(need_coin_num[0])
            requests.post(url=useCoin_url, json=useCoin_postData)
        except selenium.common.exceptions.NoSuchElementException as e:
            print("part2-2 没有轻币解锁模块")
        finally:
            print("part3 获得真实网页数据")
            driver.get(base_url)
            data_res1 = driver.find_element("class name", "article-content")
            data_res = data_res1.get_attribute('innerHTML')

        # if data_res1:
        #     data_res1 = data_res1.get_attribute('innerHTML')
        #     data_res2 = self.RequestChangeText(data_res1[0])
        #     print("part2-1 寻找轻币解锁模块")
        #     need_coin = re.findall("\d{1,3}.*轻币解锁", data_res2)
        # else:
        #     need_coin = ["10 轻币解锁"]
        # if need_coin:
        #     print("part2-2 找到了轻币解锁模块：\n" + need_coin[0])
        #     need_coin_num = re.findall("\d{1,2}", need_coin[0])
        #     print("part2-3 即将支付" + need_coin_num[0] + "轻币到当前页面")
        #     use_Coin_tf = input("若轻币数不正确，请输入no：")
        #     if use_Coin_tf != 'no':
        #         useCoin_postData["d"]["price"] = int(need_coin_num[0])
        #         useCoin_postData["d"]["total_price"] = int(need_coin_num[0])
        #     else:
        #         true_num = int(input("正确的轻币数字："))
        #         if true_num == 0:
        #             print("part2-2 未曾找到轻币解锁模块")
        #         useCoin_postData["d"]["price"] = true_num
        #         useCoin_postData["d"]["total_price"] = true_num
        #     useCoin_res = session.post(url=useCoin_url, json=useCoin_postData)
        # else:
        #     print("part2-2 未曾找到轻币解锁模块")
        # print("part3 获得真实网页数据")
        # data_res = session.get(url=base_url)
        # data_res = re.sub(r"\\u003C", '<', data_res.text)
        # data_res = re.sub(r"\\u003E", '>', data_res)
        # data_res = re.sub(r"\\u002F", "/", data_res)
        return data_res

    def RequestGetText(self):
        """

        Returns:
            self.Text_easy_str / self.Text_easy_list

        self.Text_easy_str - 经过基础处理的所有文本数据readlines()

        self.Text_easy_list - 经过基础处理的所有文本数据read()

        """
        file_name_all = self.file_path_dict["txt"] + str(self.Web_Index_num) + " - "
        if not self.Web_series_if:
            Web_URL = self.Web_URL_dict[self.Web_Source_str] + str(self.Web_Index_num)
        else:
            Web_URL = self.Web_URL_dict[self.Web_Source_str] + str(self.Web_series_num)

        if not self.Web_request_if:
            all_text = open(self.file_path_dict["txt"] + "people.txt", "r", encoding="utf-8").readlines()
            all_str = ""
            for i in all_text:
                all_str += i
            all_text = all_str
        else:
            while True:
                try:
                    web = self.RequestAllTest(Web_URL)
                    all_text = web
                except ConnectionResetError as e:
                    print(e)
                    time.sleep(2)
                except TimeoutError as e:
                    print(e)
                    time.sleep(2)
                except Exception as e:
                    print(e)
                    time.sleep(1)
                else:
                    break

        # 生成origin的文本文件
        # text_write_all = re.findall('<div class=\"article-content\">.*<div class=\"article-extra-file\">', all_text)
        text_write_all = all_text
        if not self.Web_series_if:
            file_origin = open(file_name_all + "origin.txt", "w", encoding="utf-8")
            file_origin.write(text_write_all)
            file_origin.close()
            print("成功生成origin文件")

        # 进行arrange的文本整理
        text_write_arrange = text_write_all
        text_write_arrange = self.RequestChangeText(text_write_arrange)

        if not self.Web_series_if:
            file_arrange = open(file_name_all + "arrange.txt", "w", encoding="utf-8")
        else:
            file_arrange = open(file_name_all + "arrange.txt", "a", encoding="utf-8")
            file_arrange.write("\n" + self.Web_series_content + "\n")
        file_arrange.write(text_write_arrange)
        file_arrange.close()
        print("成功生成arrange完成文件")

        self.Text_easy_str = text_write_arrange
        self.Text_easy_list = open(file_name_all + "arrange.txt", "r", encoding="utf-8").readlines()

    def TxtGetContents(self):
        """

        Returns:

        """
        text_find_contents = re.sub('<span style="font-family:宋体">', '', self.Text_easy_str)
        text_find_contents = re.findall('<div class="inline-align-center">.{0,50}\n', text_find_contents)
        list_contents_all = []
        print(text_find_contents)
        for i in range(len(text_find_contents)):
            text_find_contents[i] = re.sub('<span style="font-size:x-large">', '', text_find_contents[i])
            text_find_contents[i] = re.sub('<span style="font-family:宋体">', '', text_find_contents[i])
            text_find_contents[i] = re.sub('</span>', '', text_find_contents[i])
            text_find_contents[i] = re.sub('\xa0', '', text_find_contents[i])
            text_find_contents[i] = re.sub('<br>', '', text_find_contents[i])
            text_find_contents[i] = re.sub('</b>', '', text_find_contents[i])
            text_find_contents[i] = re.sub('<b>', '', text_find_contents[i])
            text_find_contents[i] = text_find_contents[i] + '\n'
            if text_find_contents[i] not in list_contents_all:
                list_contents_all.append(text_find_contents[i])
        print(list_contents_all)

        file_txt_path = self.file_path_dict["txt"] + str(self.Web_Index_num)
        file_content = open(file_txt_path + " - Contents.txt", 'w', encoding='utf-8')
        for i in list_contents_all:
            if i != '\n':
                file_content.write(i)
        file_content.write("\n席尔洛（结束标志）\n")
        print("文章目录制作完毕，需要进行检查更新")

    def TxtImgUpdate(self):
        """"""
        text_find_image = re.findall('<img loading=[\"\']lazy[\"\'] src=.*\\n', self.Text_easy_str)
        file_name_txt = self.file_path_dict["txt"] + str(self.Web_Index_num) + " - "
        print("图片总数为：" + str(len(text_find_image)) + "张")

        # 将图片行内容更新为“图片-序号”的模式
        index_now_img = 1
        file_imgChange = open(file_name_txt + 'ImgSave-Index.txt', 'w', encoding='utf-8')
        # file_imgURL = open(file_name_txt + 'ImgURL.txt', 'r', encoding='utf-8').readlines()
        file_imgURL = text_find_image
        for i in range(len(self.Text_easy_list)):
            for k in file_imgURL:
                if self.Text_easy_list[i].count(k):
                    self.Text_easy_list[i] = self.Img_Save_str + str(index_now_img) + "\n"
                    index_now_img += 1
            file_imgChange.write(self.Text_easy_list[i])
        file_imgChange.write("\n席尔洛（结束标志）\n")
        file_imgChange.close()
        print("总共" + str(index_now_img - 1) + "张图片更新完毕")

        # 得到相应的准确ImgURL
        list_imgURL = []
        for i in text_find_image:
            i = re.sub("img-width=.*", "", i)
            i = re.sub("style=.*", "", i)[25:-3]
            list_imgURL.append(i)
        print(list_imgURL)
        print("成功得到图片所在准确url")

        # 生成ImgURL所在行数据对应文件
        if not self.Web_series_if:
            file_imgURL = open(file_name_txt + 'ImgURL.txt', 'w', encoding='utf-8')
        else:
            file_imgURL = open(file_name_txt + 'ImgURL.txt', 'a', encoding='utf-8')
        for i in list_imgURL:
            file_imgURL.write(i + '\n')
        file_imgURL.close()
        print("成功生成图片url所在行数据文件")

    def ImgSaveList(self):
        """"""
        file_name_txt = self.file_path_dict["txt"] + str(self.Web_Index_num) + " - "
        list_imgURL = open(file_name_txt + 'ImgURL.txt', 'r', encoding='utf-8').readlines()

        # 找出相应的图片后缀
        try:
            self.Img_format_list = [re.findall("\..{3,4}[?\"]", i)[0][:-1] for i in list_imgURL]
        except:
            self.Img_format_easy = True
        else:
            if not self.Img_format_list:
                self.Img_format_easy = True
        if self.Img_format_easy:
            for i in list_imgURL:
                if i[-1] == 'i':
                    self.Img_format_list += [".avif"]
                else:
                    self.Img_format_list += ['.jpg']
        # print(self.Img_format_list)

        # 尝试下载图片
        self.Img_save_path = self.file_path_dict["image"] + self.Img_Save_str
        for i in range(len(list_imgURL)):
            if os.path.exists(self.Img_save_path + str(i + 1) + self.Img_format_list[i]):
                print("第" + str(i + 1) + "张图片已经存在")
                self.Img_have_len += 1
                continue
            long_time_index = 0
            while True:
                if long_time_index == 5:
                    print("第" + str(i + 1) + "张图片超时次数过多")
                    break
                try:
                    self.ImgSave(i, str(list_imgURL[i]))
                except func_timeout.exceptions.FunctionTimedOut as e:
                    long_time_index += 1
                    print("第" + str(i + 1) + "张图片下载超时第", long_time_index, "次")
                else:
                    print("第" + str(i + 1) + "张图片下载完毕")
                    self.Img_have_len += 1
                    break
            # if os.path.exists(Img_save_path + str(i + 1) + self.Img_format_list[i]):
            #     print("第" + str(i + 1) + "张图片已经存在")
            #     self.Img_have_len += 1
            #     continue
            # try:
            #     request = urllib.request.Request(str(list_imgURL[i]), headers=self.headers)
            #     response = urllib.request.urlopen(request)
            #     cat_img = response.read()
            #     # 当为.i文件时调整Img_format_list中的值
            #     while len(self.Img_format_list) < i + 1:
            #         self.Img_format_list.append(".jpg")
            #     with open(Img_save_path + str(i + 1) + self.Img_format_list[i], 'wb') as f:
            #         f.write(cat_img)
            #     if i == 0:
            #         with open(self.file_path_dict["image"] + "cover" + self.Img_format_list[i], 'wb') as f:
            #             f.write(cat_img)
            #     response.close()
            # except Exception as e:
            #     print("第" + str(i + 1) + "张图片出现错误:" + str(e))
            # else:
            #     print("第" + str(i + 1) + "张图片下载完毕")
            #     self.Img_have_len += 1

    @func_set_timeout(20)
    def ImgSave(self, index, url):
        while True:
            try:
                request = urllib.request.Request(url, headers=self.headers)
                response = urllib.request.urlopen(request)
                cat_img = response.read()
                # 当为.i文件时调整Img_format_list中的值
                while len(self.Img_format_list) < index + 1:
                    self.Img_format_list.append(".jpg")
                with open(self.Img_save_path + str(index + 1) + self.Img_format_list[index], 'wb') as f:
                    f.write(cat_img)
                if index == 0:
                    with open(self.file_path_dict["image"] + "cover" + self.Img_format_list[index], 'wb') as f:
                        f.write(cat_img)
                response.close()
            except Exception as e:
                print("第" + str(index + 1) + "张图片出现错误:" + str(e))
            else:
                break

    def run(self):
        if not self.OsTxtFileAppraise():
            self.RequestGetText()
            print("——————文本爬取完毕———————")
            self.TxtGetContents()
            print("——————标题获取完毕———————")
            self.TxtImgUpdate()
            print("——————图片行更新完毕——————")
        self.ImgSaveList()
        print("——————图片爬取完毕———————")

    def run_app(self):
        if not self.OsTxtFileAppraise():
            self.AppGetText()
            print("——————APP数据获取完毕———————")
            self.AppImgUpdate()
            print("——————APP图片更新完毕———————")
        self.ImgSaveList()
        print("——————图片爬取完毕———————")

    def run_haveHTML(self):
        open(self.file_path_dict["txt"] + "people.txt", "r", encoding="utf-8")
        stop = input("请输入文本，输入完毕后，请输入：1")
        self.Web_request_if = False
        self.RequestGetText()
        print("——————文本输入完毕———————")
        self.TxtGetContents()
        print("——————标题获取完毕———————")
        self.TxtImgUpdate()
        print("——————图片行更新完毕——————")
        self.ImgSaveList()
        print("——————图片爬取完毕———————")

    def run_series(self, Img_start_len, Web_Index_now, Web_content_now):
        self.Web_series_if = True
        self.Web_series_num = Web_Index_now
        self.Web_series_content = Web_content_now
        self.RequestGetText()
        print("——————文本爬取完毕———————")
        self.TxtImgUpdate()
        print("——————图片行更新完毕——————")
        self.Img_have_len = Img_start_len
        self.ImgSaveList()
        print("——————图片爬取完毕———————")

    # def run_haveTxt(self):
    #     self.Img_format_list.append("")


class createEPUB:
    def __init__(self, Text_class: getAllData):
        # base_static
        self.py_static = Text_class.py_static
        self.Web_Index_num = str(Text_class.Web_Index_num)
        self.Img_Save_str = Text_class.Img_Save_str
        self.Img_format_list = Text_class.Img_format_list
        self.Img_format_easy = Text_class.Img_format_easy
        self.Text_name_str = Text_class.Text_name_str
        self.file_path_dict = Text_class.file_path_dict
        # text
        self.Text_Content_list = [i[:-1] for i in
                                  open(self.Text_name_str + "/" + self.Web_Index_num + ' - Contents.txt',
                                       'r', encoding='utf-8').readlines()]
        self.Text_easy_list = [i for i in
                               open(self.Text_name_str + "/" + self.Web_Index_num + ' - ImgSave-Index.txt',
                                    'r', encoding='utf-8').readlines()]
        # write
        self.Write_str = ""
        self.Write_title = ""
        self.Write_ncxDict = dict(zip(self.Text_Content_list, [""] * len(self.Text_Content_list)))
        self.Write_opfDict = {"name": self.Text_name_str, "epub": self.py_static["OtherName"],
                              "HTML_ID": str(self.Web_Index_num),
                              "author": "", "summary": "", "content": []}
        # create
        self.create_PageID_num = 1
        self.create_ImageID_num = 1
        self.create_IllusID_num = 0
        self.create_ContentID_num = 0
        self.create_SummaryID_num = 1
        self.create_textIndex_num = 0
        self.create_Catalogue_list = []

        # style
        self.style_path = "./.styles"

    def writeXHTML(self):
        file_name = self.file_path_dict["xhtml"] + self.Write_title + ".xhtml"

        # 给文本添加文件头和尾
        static_str = ''
        # static_str = "<?xml version='1.0' encoding='utf-8'?>\n" \
        #              "<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.1//EN'" \
        #              " 'http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd'>\n"
        # static_str += "<html xmlns='http://www.w3.org/1999/xhtml' xml:lang='zh-CN' " \
        #               "xmlns:epub='http://www.idpf.org/2007/ops' " \
        #               "xmlns:xml='http://www.w3.org/XML/1998/namespace'>\n\n"
        # static_str += "<head>\n  <link href='../Styles/style.css' rel='stylesheet' type='text/css'/>\n"
        # static_str += "  <title>" + self.Write_title + "</title>\n</head>\n"

        static_str += "<body>\n"
        static_str += self.Write_str
        static_str += "\n</body>\n</html>\n"

        # 文本写入与self内容更新
        file_input = open(file_name, "w", encoding="utf-8")
        file_input.write(static_str)
        file_input.close()
        self.create_Catalogue_list.append(self.Write_title)
        self.Write_str = ""
        self.Write_title = ""

    def writeNCX(self):
        file_name = self.file_path_dict["config"] + "toc.txt"

        # 头文件及标题
        static_str = "<?xml version='1.0' encoding='utf-8' ?>\n" \
                     "<!DOCTYPE ncx PUBLIC '-//NISO//DTD ncx 2005-1//EN'\n" \
                     " 'http://www.daisy.org/z3986/2005/ncx-2005-1.dtd'><ncx version='2005-1'" \
                     " xmlns='http://www.daisy.org/z3986/2005/ncx/'>\n" \
                     "  <head>\n" \
                     "    <meta content='1' name='dtb:depth'/>\n" \
                     "    <meta content='0' name='dtb:totalPageCount'/>\n" \
                     "    <meta content='0' name='dtb:maxPageNumber'/>\n" \
                     "  </head>\n"
        static_str += "  <docTitle>\n    <text>" + self.Write_title + "</text>\n  </docTitle>\n  <navMap>\n"
        # 主要目录区
        navPoint = 2
        for i in self.Write_ncxDict.keys():
            static_str += "    <navPoint id='navPoint-" + str(navPoint) + "' playOrder='" + str(navPoint) + "'>\n" \
                          + "      <navLabel>\n" \
                          + "        <text>" + i + "</text>\n" \
                          + "      </navLabel>\n" \
                          + "      <content src='Text/" + self.Write_ncxDict[i] + ".xhtml'/>\n" \
                          + "    </navPoint>"
            navPoint += 1
        # 文件结束
        static_str += "  </navMap>\n</ncx>"

        # 文本写入与self内容更新
        file_input = open(file_name, "w", encoding="utf-8")
        file_input.write(static_str)
        file_input.close()
        self.Write_title = ""

    def writeOPF(self):
        file_name = self.file_path_dict["config"] + "content.txt"

        # 元数据部分
        static_str = "<?xml version='1.0' encoding='utf-8'?>\n" \
                     "<package version='2.0' unique-identifier='BookId' xmlns='http://www.idpf.org/2007/opf'>\n" \
                     "  <metadata xmlns:dc='http://purl.org/dc/elements/1.1/'" \
                     " xmlns:opf='http://www.idpf.org/2007/opf'>\n" \
                     "    <dc:language>zh</dc:language>\n"
        static_str = static_str + "<dc:title>" + self.Write_opfDict["name"] + "</dc:title>\n"
        static_str = static_str + "<dc:creator>" + self.Write_opfDict["author"] + "</dc:creator>\n"
        static_str = static_str + "<meta content='PythonCopyFromLK" +\
                     self.Write_opfDict["epub"] + "' name='epub制作' />\n"
        static_str = static_str + "<dc:description>" + self.Write_opfDict["summary"] + "</dc:description>\n"
        static_str = static_str + "<dc:subject>轻小说</dc:subject>\n"
        static_str = static_str + "<dc:source>轻之国度：https://www.lightnovel.us/</dc:source>\n"
        static_str = static_str + "<meta content='1.6.0' name='Sigil version' />\n"
        static_str = static_str + "<dc:date opf:event='modification' xmlns:opf='http://www.idpf.org/2007/opf'>" \
                     + str(time.strftime("%Y-%m-%d", time.localtime())) + "</dc:date>\n"
        static_str = static_str + "<dc:identifier id='BookId' opf:scheme='轻国网址'>" \
                     + self.Write_opfDict["HTML_ID"] + "</dc:identifier>\n"
        # 文件存储部分
        static_str = static_str + "  </metadata>\n  <manifest>\n"
        static_str += "    <item id='toc.ncx' href='toc.ncx' media-type='application/x-dtbncx+xml'/>\n" \
                      "    <item id='style.css' href='Styles/style.css' media-type='text/css'/>\n" \
                      "    <item id='Cover.xhtml' href='Text/Cover.xhtml' media-type='application/xhtml+xml'/>\n"
        # 文件顺序部分
        static_str = static_str + "  </manifest>\n  <spine toc='toc.ncx'>\n"
        for i in self.Write_opfDict["content"]:
            static_str += "<itemref idref='" + i + ".xhtml'/>\n"

        static_str += "  </spine>\n  <guide>\n" \
                      "    <reference type='cover' title='封面' href='Text/Cover.xhtml'/>\n" \
                      "  </guide>\n</package>\n"

        # 文本写入与self内容更新
        file_input = open(file_name, "w", encoding="utf-8")
        file_input.write(static_str)
        file_input.close()

    def xhtmlCover(self):
        if self.Img_format_easy:
            str_img_link = "Images/cover.avif"
        else:
            str_img_link = "Images/cover.jpg"
        str_cover = "  <div style='text-align: center; padding: 0pt; margin: 0pt;'>\n" \
                    "    <svg xmlns='http://www.w3.org/2000/svg' height='100%' " \
                    "preserveAspectRatio='xMidYMid meet' version='1.1' viewBox='0 0 810 1200' width='100%' " \
                    "xmlns:xlink='http://www.w3.org/1999/xlink'>\n" \
                    "      <image width='810' height='1200' xlink:href='" + str_img_link + "'/>\n" \
                                                                                           "    </svg>\n  </div>\n"
        self.Write_str = str_cover
        self.Write_title = "cover"
        self.writeXHTML()

    def xhtmlMessage(self):
        self.Write_title = "Production information"
        str_message = "<div class='design-box'>\n"
        str_message += "<h1>制作信息</h1>\n"
        str_message += "<p>——————————————</p>\n"
        message_textIndex_num = 0
        for i in self.Text_easy_list:
            if (i.find('——————————————') != -1 or i.find('---------------') != -1) and message_textIndex_num == 1:
                message_textIndex_num = 2
            if (i.find('——————————————') != -1 or i.find('---------------') != -1) and message_textIndex_num == 0:
                message_textIndex_num = 1
            if message_textIndex_num == 1 and i.find('-' * 23 or '—' * 10) == -1 and i != '\n':
                str_message_now = "<p>" + i[:-1] + "</p>\n"
                str_message = str_message + str_message_now
            if i.find('作者') != -1:
                message_author_process = i
                message_author_process = message_author_process[3:-1]
                self.Write_opfDict['author'] = message_author_process

            self.create_textIndex_num += 1
            if message_textIndex_num == 2:
                break

        str_message += "<p>——————————————</p>\n"
        str_message += "<p em08'>epub制作：PythonCopyFromLK</p>\n"
        str_message += "<p>为获得最佳阅读效果，请将多看阅读更新至最新版本。" \
                       "排版设为‘无’，背景建议选择纯白色；" \
                       "字型设定为‘预设’（使用书中指定字型），" \
                       "字型大小设为预设大小（一般手机上为+4，平板上为+3——即减小字型到最小值后，点选增大按钮的次数）。" \
                       "</p>\n"
        str_message += "</div>"
        self.Write_str = str_message
        self.writeXHTML()

    def xhtmlFrontPage(self):
        self.Write_title = "Front Image Page"
        if not self.Img_format_list or not self.Img_format_list[0]:
            self.Img_format_list = ['.jpg']
        str_frontPage = "<div class='duokan-image-single illus'>" \
                        "<img alt='" + self.Img_Save_str + str(self.create_ImageID_num) + "' src='Images/" + \
                        self.Img_Save_str + str(self.create_ImageID_num) + self.Img_format_list[0] + "'/></div>"

        self.create_ImageID_num += 1
        self.Write_str = str_frontPage
        self.writeXHTML()
        self.create_Catalogue_list.append("CONTENTS")

    def xhtmlContents(self):
        self.Write_title = "CONTENTS"
        str_CONTENTS = "<div class='bold illus1' style='margin: 2em 0 0 2em;'>\n"
        str_CONTENTS += "<p class='pius1'>CONTENTS</p>\n"
        for i in self.Write_ncxDict.keys():
            text_process = "<p class='mulu'><a class='no-d' href='" + \
                           self.Write_ncxDict[i] + ".xhtml'>" + i + "</a></p>\n"
            str_CONTENTS += text_process
        str_CONTENTS += "</div>\n"
        self.Write_str = str_CONTENTS
        self.writeXHTML()
        self.create_Catalogue_list = self.create_Catalogue_list[:-1]
        self.Write_opfDict["content"] = self.create_Catalogue_list

    def xhtmlMain(self):
        page_summary_process = ""

        for i in range(self.create_textIndex_num, len(self.Text_easy_list)):
            # 判断是否为标题行
            if self.Text_easy_list[i].find(self.Text_Content_list[self.create_ContentID_num]) != -1:
                # 如果不是第一次遇到标题行，则将现有的文本数据和标题放入一个HTML文件中
                if self.Write_title:
                    # self.Write_str += "</div>\n"
                    self.writeXHTML()

                # 判断该标题行是否为“简介”、“彩插”类型
                if self.Text_Content_list[self.create_ContentID_num].find("简介" or "簡介") != -1:
                    self.Write_title = "Summary" + str(self.create_SummaryID_num).zfill(4)
                    self.create_SummaryID_num += 1
                    self.Write_str += '<div class="intro">'
                elif self.Text_Content_list[self.create_ContentID_num].find("彩插") != -1:
                    self.Write_title = "Illus" + "0001"
                else:
                    self.Write_title = "General" + str(self.create_PageID_num).zfill(4)
                    self.create_PageID_num += 1
                    self.Write_str += '<div class="auth-box">'
                text_process = "<h1>" + self.Text_Content_list[self.create_ContentID_num] + "</h1></div>\n"

                # 将标题与页码对应
                self.Write_ncxDict[self.Text_Content_list[self.create_ContentID_num]] = self.Write_title

                # 修正变量
                print("现在进行到：" + self.Text_Content_list[self.create_ContentID_num] + " 页码：" + self.Write_title)
                # if title_now != title_ColorPainting:
                #     create_Catalogue_list.append(title_now)
                self.create_ContentID_num += 1
                self.Write_str += text_process
                continue

            # 彩插区域
            if self.Text_Content_list[self.create_ContentID_num - 1] == "彩插" \
                    and self.Text_easy_list[i].find(self.Img_Save_str) != -1:
                # 获得当前图片序号
                ColorPainting_process_num = int(self.Text_easy_list[i][-2])
                text_process = self.Img_Save_str + str(ColorPainting_process_num)
                # print("process：" + text_process)
                title_now = "Illus" + str(self.create_IllusID_num).zfill(4)
                # print("now：" + title_now)

                if self.create_IllusID_num != 0:
                    self.writeXHTML()
                    print("现在进行到：" + self.Text_Content_list[self.create_ContentID_num - 1] + " 页码：" + title_now)

                self.create_IllusID_num += 1
                self.create_ImageID_num += 1
                self.Write_title = "Illus" + str(self.create_IllusID_num).zfill(4)
                while ColorPainting_process_num + 1 > len(self.Img_format_list):
                    self.Img_format_list.append('.jpg')
                self.Write_str += "<div class='illus duokan-image-single'><img alt='" + text_process + \
                                  "' src='Images/" + text_process + \
                                  self.Img_format_list[ColorPainting_process_num] + "'/>\n"
                continue

            # 常规图片
            if self.Text_easy_list[i].find(self.Img_Save_str) != -1:
                text_process = self.Text_easy_list[i][:-1]

                # 将图片插入文本中
                img_index_now = int(self.Text_easy_list[i][3:-1])
                if img_index_now > len(self.Img_format_list):
                    self.Img_format_list.append('.jpg')
                self.Write_str += "<div class='illus duokan-image-single'><img alt='" + text_process + \
                                  "' src='Images/" + text_process + \
                                  self.Img_format_list[img_index_now - 1] + "'/></div>\n"
                self.create_ImageID_num += 1
                continue

            # 常规文本
            if self.Text_Content_list[self.create_ContentID_num - 1].find("简介") != -1:
                page_summary_process += self.Text_easy_list[i]
            text_process = self.Text_easy_list[i][:-1]
            if not text_process:
                text_process = " "
            text_process = "<p>" + text_process + "</p>\n"
            text_process = re.sub('<p>' * 2, '<p>', text_process)
            text_process = re.sub('</p>' * 2, '</p>', text_process)
            self.Write_str += text_process

        self.Write_opfDict["summary"] = page_summary_process
        self.Write_ncxDict['制作信息'] = 'Production information'
        del (self.Write_ncxDict['席尔洛（结束标志）'])
        print(self.Write_ncxDict)

    def epubWrite(self):
        book = epub.EpubBook()
        book.EPUB_VERSION = '2.0'
        # add metadata
        # book.set_language('zh')
        book.set_title(self.Text_name_str)

        book.add_author(self.Write_opfDict["author"])
        book.add_author(self.py_static['Translator'], uid='translator')
        book.add_author('Xierluo ' + self.Write_opfDict["epub"], uid='epub制作')

        book.set_unique_metadata('DC', 'description', self.Write_opfDict["summary"])
        book.set_unique_metadata('DC', 'subject', '轻小说')
        book.set_unique_metadata('DC', 'source', '轻之国度：https://www.lightnovel.us/')
        book.set_identifier(str(self.Web_Index_num))

        # add style css
        style_list = os.listdir(self.style_path)
        style_item_list = []
        for style_file in style_list:
            style_uid = style_file[:-4]
            css_item = epub.EpubItem(uid=style_uid, file_name='style/' + style_file, media_type="text/css",
                                     content=open("./.styles/" + style_file, 'rb').read())
            book.add_item(css_item)
            style_item_list.append(css_item)

        # add html
        html_list = []
        print(self.Write_opfDict["content"])
        for i in self.Write_opfDict["content"]:
            file_path = self.file_path_dict["xhtml"] + i + '.xhtml'
            if i == 'CONTENTS':
                html_list.append('nav')
                continue
            html_now = epub.EpubHtml(uid=i, file_name=i + '.xhtml', title=i,
                                     content=open(file_path, 'rb').read())
            for style_item in style_item_list:
                if not style_item.id == 'nav_css':
                    html_now.add_item(style_item)
            book.add_item(html_now)
            html_list.append(html_now)

        # add img
        img_name_list = os.walk(self.file_path_dict["image"])
        for img_name_ in img_name_list:
            img_name_list = img_name_[2]
        for i in img_name_list:
            if "cover" in i:
                # img_now = epub.EpubItem(uid="cover-img", file_name="Images/" + i,
                #                         content=open(self.file_path_dict["image"] + i, 'rb').read())
                book.set_cover(file_name="Images/" + i, create_page=False,
                               content=open(self.file_path_dict["image"] + i, 'rb').read())
                continue
            else:
                img_now = epub.EpubItem(uid=i, file_name="Images/" + i,
                                        content=open(self.file_path_dict["image"] + i, 'rb').read())
            book.add_item(img_now)

        # set toc and nav
        book.toc = [epub.Link(j + '.xhtml', i, j) for i, j in self.Write_ncxDict.items()]
        book.add_item(epub.EpubNcx())
        # book.add_metadata(None, 'meta', '', OrderedDict([('name', 'Cover'), ('content', 'cover-img')]))

        content_Nav = epub.EpubNav(file_name="CONTENTS.xhtml")
        for style_item in style_item_list:
            content_Nav.add_item(style_item)
        book.add_item(content_Nav)

        book.spine = html_list
        epub.write_epub(self.file_path_dict["epub"], book, {})

    def run(self):
        print("——————进入文件制作模块———————")
        self.xhtmlCover()
        print("——————封面页制作完毕———————")
        self.xhtmlMessage()
        print("——————制作信息页制作完毕———————")
        self.xhtmlFrontPage()
        print("——————彩插页制作完毕———————")
        self.xhtmlMain()
        print("——————内容主体页制作完毕———————")
        self.xhtmlContents()
        print("——————目录页制作完毕———————")
        self.writeNCX()
        print("——————NCX文件对应数据生成完毕———————")
        self.writeOPF()
        print("——————OPF文件对应数据生成完毕———————")
        self.epubWrite()
        print("——————EPUB生成完毕———————")


def run():
    book_now = getAllData(py_static=EPUB_static)
    # book_now.run_haveHTML()
    # book_now.run_app()
    book_now.run()

    while True:
        stop = input("请修正目录与文本，修正完毕后，请输入：0")
        if stop == "ok":
            break
        try:
            book_now = createEPUB(Text_class=book_now)
            book_now.run()
        except Exception as e:
            print(repr(e))
            traceback.print_exc()
            print("————有bug，快修————")
    print("——————检查已无误———————")


if __name__ == '__main__':
    run()
