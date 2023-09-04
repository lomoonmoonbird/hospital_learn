import requests
from bs4 import BeautifulSoup

site = "http://116.255.143.138/"

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/60.0.3112.78 Safari/537.36'}


# 第一次遍历首页所有url
def get_url_lists(site_url):
    urla = []
    global headers
    rs = requests.get(site_url, headers=headers)
    soup = BeautifulSoup(rs.text, 'html.parser')
    print(soup)
    url_list = soup.select('a')
    for i in url_list:
        if i.has_attr("href"):
            # 只输出带有href属性的a标签url
            if "javascript:" in i["href"]:
                continue
            urla.append(site + i["href"])

    urlb = set(urla)
    # 将列表转换成set集合来实现去重

    # return len(urlb), urlb
    return urlb


def get_sub_url(urlb):
    sub_url = []
    for i in urlb:
        sub_url += list(get_url_lists(i))
    # 把刚抓到的url列表并入新的列表
    sub_url = set(sub_url)
    return len(sub_url), sub_url

print(get_sub_url(get_url_lists(site)))