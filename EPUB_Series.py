import json
import time
import requests
import traceback
from EPUB_Factory import EPUB_static, getAllData, createEPUB

profile_ID = 358191
series_ID = 2023
Your_token = 'ffffeeeeddddccccbbbbaaaa99998888:000000:0'
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36 android 9.9',
           'Referer': "https://www.lightnovel.us/",
           'origin': "https://www.lightnovel.us"}


def get_aidDict():
    pageID = 1
    pageData_all = []
    profile_url = "https://www.lightnovel.us/proxy/api/user/get-articles"
    while True:
        profile_postData = {"is_encrypted": 0, "platform": "pc", "client": "web", "sign": "", "gz": 0,
                            "d": {"uid": str(profile_ID), "page": pageID, "type": 1,
                                  "security_key": Your_token}}
        while True:
            try:
                pageData = requests.post(url=profile_url, json=profile_postData, headers=headers).text
                pageData = json.loads(pageData)
            except ConnectionResetError as ex:
                print(ex)
                time.sleep(2)
            except TimeoutError as ex:
                print(ex)
                time.sleep(2)
            except Exception as ex:
                print(ex)
                time.sleep(1)
            else:
                break

        if not pageData["data"]["list"]:
            break

        for data_now in pageData["data"]["list"]:
            if data_now['sid'] == series_ID:
                new_data = {'uid': data_now['uid'], 'sid': series_ID, 'aid': data_now['aid'],
                            'title': data_now['title']}
                pageData_all.append(new_data)
        pageID += 1
        time.sleep(1)
    pageData_all = pageData_all[::-1]
    return pageData_all


def seriesData_toEPUB(seriesDict, base_title):
    base_aid = seriesDict[0]['aid']
    # base_title = seriesDict[0]['title']
    EPUB_static["WebIndex"] = base_aid
    EPUB_static["BookName"] = base_title
    base_book = getAllData(py_static=EPUB_static)
    base_book.run()

    seriesDict = seriesDict[1:]
    img_format_list = base_book.Img_format_list
    img_start_len = len(img_format_list)
    file_txt_path = base_book.file_path_dict["txt"] + str(base_book.Web_Index_num)
    file_content = open(file_txt_path + " - Contents.txt", 'a', encoding='utf-8')
    for data_now in seriesDict:
        print("======正在处理的标题为：" + data_now['title'] + "======")
        now_nook = getAllData(py_static=EPUB_static)
        now_nook.run_series(Img_start_len=img_start_len,
                            Web_Index_now=data_now['aid'],
                            Web_content_now=data_now['title'])
        file_content.write(data_now['title'] + '\n')
        img_format_list = now_nook.Img_format_list
        img_start_len = len(img_format_list)
    file_content.write("席尔洛（结束标志）\n")
    file_content.close()
    base_book.Img_format_list = img_format_list

    return base_book


if __name__ == '__main__':
    series_data = get_aidDict()
    for i in series_data:
        print(i)
    book_name = input("看看是否符合要求，输入书名：")
    book_now = seriesData_toEPUB(series_data, book_name)
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
