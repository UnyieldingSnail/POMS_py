# -*- encoding:utf-8 -*-
import os

import time
from pymongo import MongoClient
import configparser
import pandas as pd
from urllib import parse
from urllib import request
import json
import re
import time
from dateutil import parser


def getUid(userName):
    url = 'https://m.weibo.cn/api/container/getIndex?'
    param = {'type': 'user',
             'queryVal': userName,
             'featurecode': '20000320',
             'luicode': '10000011',
             'lfid': '106003type=1',
             'title': userName,
             'containerid': '100103type=3&q=%s' % (userName)}
    url_data = parse.urlencode(param)  # unlencode()将字典{k1:v1,k2:v2}转化为k1=v1&k2=v2
    url = url + url_data
    print(url)  # url_data：wd=%E7%99%BE%E5%BA%A6%E7%BF%BB%E8%AF%91

    req = request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'})
    html = request.urlopen(req).read()
    html = html.decode('utf-8')  # 将响应结果用utf8编码
    html = json.loads(html)
    print(html)
    if html['ok'] == 0:
        return '0'
    uid = html['data']['cards'][1]['card_group'][0]['user']['id']
    return uid


def save_dict(dict_name, file):
    f = open(file, 'w')
    f.write(str(dict_name))
    f.close()


def read_dict(file):
    f = open(file, 'r')
    a = f.read()
    f.close()
    return eval(a)


# 获取用户的uid
def save_uid(items):
    users = dict()
    print(items)
    print("------------")
    for i in items:

            print(i)
            keys = i.keys()
            if 'reposters' in keys:
                reposters = i['reposters']
                for r in reposters:
                    text = r['text']

                    userNames = re.findall("(?<=//@).+?(?=:)", text)
                    for name in userNames:
                        print(name)
                        try:
                            users[name] = getUid(name)
                        except Exception:
                            print(Exception)
                            users[name] = getUid(name)
    save_dict(users, "user_name_mapping.txt")
    items.close()


def get_graph(items, users):
    graph_str = ''
    for i in items:
        weibo_str = ""
        n = n + 1
        print("正在输出 %s 条" % n)
        keys = i.keys()
        print(keys)

        if '_id' in keys:
            weiboId = i['_id']
            weibo_str += weiboId
        else:
            continue
        if 'userId' in keys:
            userId = i['userId']
            weibo_str += ("\t" + userId)

        if 'userName' in keys:
            userName = i['userName']

        if 'createdAt' in keys:
            createdAt = i['createdAt']
            weibo_str += ("\t" + createdAt.split("\s+")[0])
        last_repostsCount = 0
        repostsCount = 0
        if 'repostsCount' in keys:
            repostsCount = i['repostsCount']
        if 'last_repostsCount' in keys:
            last_repostsCount = i['last_repostsCount']

        edges = []
        if 'reposters' in keys:
            reposters = i['reposters']
            rid = reposters['_id']
            text = reposters['text']
            num_nodes = len(reposters) + 1
            if num_nodes < 2:
                continue
            graph_str += ("\t" + str(num_nodes))
            for r in reposters:
                userNames = re.findall("(?<=//@).+?(?=:)", text)
                if len(userNames) == 0:
                    edges.append("%s:%s:1" % (userId, rid))
                else:
                    f_id = userId
                    for r_name in range(len(userNames) - 1, -1, -1):
                        r_id = users[r_name]
                        edges.append("%s:%s:1" % (f_id, r_id))
                        f_id = r_id
            weibo_str += ("\t" + " ".join(edges))
            weibo_str += ("\t%s" % (last_repostsCount - repostsCount))
        graph_str += (weibo_str + "\t\r")
    graph_str.strip("\t\r")
    return graph_str


cf = configparser.ConfigParser()
conf_path = os.path.join(os.path.dirname(__file__), 'mongo.conf')
cf.read(conf_path)

mongo_url = cf.get("mongo", "url")
client = MongoClient(mongo_url)
print(client.list_database_names())
db = client.poms01
weibo = db.weibo

items = weibo.find({'reposters': {'$exists': 'true'}}, no_cursor_timeout=True)
weibo.remove({'reposters': {'$exists': 'false'}})

for i in items:
    id = i['_id']
    time = i['createdAt']

    repost_num = i['repostsCount']
    truth = [repost_num]

weibo.update({"name":"test"},{"$set":{"age":33}})

save_uid(items)
users = read_dict("user_name_mapping.txt")
graph_str = get_graph(items, users)

print(graph_str)
#
#
#
#
# df = pd.DataFrame({'dateId': dateId,
#                    'ai_type': ai_type,
#                    'ai_name': ai_name,
#                    'quorum': quorum,
#                    'priceUSD': priceUSD,
#                    'ai_disageform': ai_disageform,
#                    'country': country,
#                    'continent': continent,
#                    'ai_cap_tr': ai_cap_tr,
#                    'company': company})
