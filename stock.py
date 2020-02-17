import operator
import requests
import datetime
import json

# peinfo = [{pe:10, ts:datetime}]
def get_peinfo(time='all'):
    pedict = {}
    url = 'https://danjuanapp.com/djapi/index_eva/pe_history/SH000016?day=' + time
    header = {}
    header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    res = requests.get(url=url, headers=header)
    peinfo = json.loads(res.content)['data']['index_eva_pe_growths']
    for pe in peinfo:
        pe['ts'] = datetime.datetime.fromtimestamp(pe['ts'] // 1000)
        pedict.setdefault(pe['ts'], pe['pe'])
    return (peinfo, pedict)

def get_fundinfo(fid):
    fdict = {}
    url = 'https://danjuanapp.com/djapi/fund/nav/history/' + str(fid) + '?page=1&size=10'
    header = {}
    header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    res = requests.get(url=url, headers=header)
    total_item_number = json.loads(res.content)['data']['total_items']
    url = 'https://danjuanapp.com/djapi/fund/nav/history/' + str(fid) + '?page=1&size=' + str(total_item_number)
    res = requests.get(url=url, headers=header)
    finfo = json.loads(res.content)['data']['items']
    for f in finfo:
        f['date'] = datetime.datetime.strptime(f['date'], '%Y-%m-%d')
        fdict.setdefault(f['date'], f['nav'])
    return (finfo, fdict)

def get_yesterday(dt, pedict, peinfo):
    dt = dt - datetime.timedelta(days=1)
    if dt in pedict:
        for pe in peinfo:
            if pe['ts'] == dt:
                return pe
    else:
        for i in range(len(peinfo)):
            if peinfo[i]['ts'] < dt and peinfo[i+1]['ts'] > dt:
                return peinfo[i]
    return {'pe': 0}

def sort_peinfo(peinfo):
    return sorted(peinfo, key=operator.itemgetter('pe'))

def get_nwater(n, s_peinfo):
    l = len(s_peinfo)
    index = l*n//100 - 1
    return s_peinfo[index]

def get_weight(cur_pe, w30, w50=0, w70=0):
    if cur_pe > w30:
        return 0
    base = 100
    i = w30/cur_pe
    return base * i

def buy(dt, peinfo, pedict, fdict):
    if dt not in fdict:
        return (0, 0)
    begin_dt = dt - datetime.timedelta(days=365)
    pe_partinfo= []
    for pe in peinfo:
        if pe['ts'] >= begin_dt and pe['ts'] < dt:
            pe_partinfo.append(pe)
    s_pe_partinfo = sort_peinfo(pe_partinfo)
    w30 = get_nwater(30, s_pe_partinfo)
    cur_pe = get_yesterday(dt, pedict, peinfo)
    capital = round(get_weight(cur_pe['pe'], w30['pe']), 2)
    amount = round(capital/float(fdict[dt]), 2)
    #print(w30)
    #print(cur_pe)
    print(capital)
    #print(fdict[dt])
    #print(amount)
    return (capital, amount)

def buy_longtime(peinfo, pedict, fdict):
    end_dt = datetime.datetime(2020, 2, 15)
    begin_dt = end_dt - datetime.timedelta(days=365)
    t_capital = 0
    t_amount = 0
    dt = begin_dt
    for i in range(365):
        res = buy(dt, peinfo, pedict, fdict)
        dt = dt + datetime.timedelta(days=1)
        t_capital = t_capital + res[0]
        t_amount = t_amount + res[1]
    fprice = float(fdict.get(get_yesterday(dt, pedict, peinfo)['ts']))
    fprice = 1.2284
    win = (t_amount * fprice - t_capital) * 100 / t_capital
    win = str(round(win, 2)) + '%'
    return (t_capital, t_amount, win)

(peinfo, pedict) = get_peinfo()
(finfo, fdict) = get_fundinfo('001548')

#dt = datetime.datetime(2020, 2, 13)
#print(buy(dt, peinfo, fdict))
res = buy_longtime(peinfo, pedict, fdict)
print(res)
