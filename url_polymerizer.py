# -*- coding: utf-8 -*-

import sys, re, urlparse

########## URL聚合 提取关键词数量限制8个 #########
# degree聚合程度: 
# 1: 低 pathinfo + querystring
# 2: 中 pathinfo + querystring, 仅保留符合PHP变量命名规则的关键词
# 3: 高 pathinfo, 仅保留符合PHP变量命名规则的关键词
def polymerize(url, degree = 2):
    url = url.strip(' "\'\r\n\t')
    if not url: return 

    info = urlparse.urlparse(url)
    if not info.hostname: return
    if re.search(r'\.(?:js|css|ico|png|jpe?g|g?zip|xml|apk)', info.path, re.I): return

    keysPath, keysQuery = [], [] 
    # 处理pathinfo
    keys = re.split(r'/|-', info.path)
    for i in keys:
        if dropItem(keys[i]): continue
        keysPath.append(keys[i])

    # 处理QueryString
    if degree < 3:
        kvs = urlparse.parse_qsl(info.query)
        for kv in kvs:
            if not kv: continue
            if keepPair(kv[0], kv[1], info.path): pass
            elif dropPair(kv[0], kv[1], info.path, degree) or dropItem(kv[0]): continue;
            kvStr = '%s=%s' % (kv[0], valueAbstract(kv[1]))
            keysQuery.append(kvStr)
        # 去重
        keysQuery = list(set(keysQuery))
    keysQuery.sort()

    hostname = polymerizeHostname(info.hostname)
    path = '/'.join(keysPath).strip('/')
    query = '&'.join(keysQuery).strip('&')

    urlCode = "%s/%s?%s" % (hostname, path, query)
    return urlCode.strip(' /?')

def valueAbstract(value):
    if re.search(r'^[\d,;]+$', value): return '%d'
    return '%s'

def dropPair(k, v, path = '', degree = 2):
    drop = False
    drop = drop or (type(v) != str)
    drop = drop or (len(v) < 3 or len(v) > 31)
    # 中度聚合
    drop = drop or (2 == degree and re.search(r'^[a-z]\w{2,23}$', v, re.I) is None)
    # ocp图片处理
    drop = drop or re.search(r'/ocp/', path)
    # 图片大小
    drop = drop or re.search(r'\d+(?:x|\*)\d*', v, re.I) or re.search(r'\d*(?:x|\*)\d+', v, re.I)
    # 网络类型
    drop = drop or re.search(r'^(?:c_)?nt$', k, re.I) and re.search(r'^(?:wifi|cell)$', v, re.I)
    # 追踪信息
    drop = drop or k in ['jsoncallback', 'callback', 'spm', 'lc', '_t_t_t', 't', '_t', '__', '_', 'abtest', 'v', 'mc']
    # 页码
    drop = drop or k in ['size', 'psize', 'page_size', 'pagesize', 'psize', 'page', 'pidx', 'p', 't'] and re.search(r'^[\.\d-]*$', v)
    drop = drop or re.search('page|limit|offset', k) and re.search(r'^[\d-]*$', v)
    drop = drop or ('size' == k and (v in ['small', 'big']))
    # 排序
    drop = drop or re.search(r'^a?sort$', k) and re.search(r'sort|default|asc|des', v, re.I)
    drop = drop or k in ['verify_code', 'app_ref', 'deviceno', 'device_no', 'deviceid', 'devid', 'msg', 'security_id'] and len(v) > 12
    drop = drop or re.search(r'(start|end)_price', k) and v.isdigit()
    drop = drop or re.search(r'time', k) and re.search(r'\d{10}|0', v)
    drop = drop or k in ['ajax'] and v.isdigit()
    drop = drop or re.search(r'^http', v)
    drop = drop or re.search(r'^(start|offset|limit)$', k, re.I) and re.search(r'search', path, re.I)
    drop = drop or re.search(r'^utm_.*$', k, re.I) and len(v) > 12

    return drop

def keepPair(k, v, path = '', degree = 2):
    keep = False
    keep = keep or k in ['api', 'method']
    return keep 

def dropItem(k):
    drop = False
    if (re.search(r'\.(php5?|htm|html5?|do|jsp|asp)$', k, re.I)):
        return False

    drop = drop or not re.search(r'^[a-z]\w{0,23}$', k, re.I)
    drop = drop or re.search(r'^c_(?:src|v|nt|aver)$', k, re.I)
    drop = drop or re.search(r'^\w+_(?:asc|desc)$', k, re.I)
    drop = drop or k in ['null', 'jsoncallback', 'callback', 'spm', 'lc', '_t_t_t', 't', '_t', '__', '_', 'abtest', 'v', 'ajax', 'mc']
    drop = drop or k in ['size', 'psize', 'page_size', 'pagesize', 'psize', 'page', 'pidx', 'p', 't', 'offset', 'limit', 'small'] 
    drop = drop or k in ['verify_code', 'app_ref', 'deviceno', 'device_no', 'deviceid', 'devid', 'msg', 'security_id']
    # 排序
    drop = drop or re.search(r'^a?sort$', k, re.I)
    drop = drop or re.search(r'^utm_.*$', k, re.I)

    #http://zhide.fanli.com/p{N}分页参数
    drop = drop or re.search(r'^p\d+$', k, re.I)
    if drop: return drop

    # 数字字母混杂
    numTimes = re.findall(r'(\d+|[a-z]+)', k)
    drop = drop or len(numTimes) >= 3

    numCount = sum(c.isdigit() for c in k)
    numRate = float(numCount)/len(k)
    #16进制字符串数字比例一般为0.625 上下浮动
    drop = drop or (len(k) > 3 and numRate >= .5 and numRate <= .75)

    return drop

def polymerizeHostname(hostname):
    hostname = hostname.replace('51fanli', 'fanli')
    hostname = re.sub('^l\d+\.', 'l%d.', hostname)
    hostname = re.sub('^\d+\.wx', '%d.wx', hostname)

    match = re.match(r'((\d+\.){3})\d+', hostname)
    if match: hostname = '%s%s' % (match.group(1), '%d')

    return hostname

