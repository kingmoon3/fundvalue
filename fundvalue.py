import operator
import requests
import datetime
import json

class FundValue():
    def __init__(self):
        self.peinfo = {}
        self.f_info = {}
        self.trade_days = {}

    def init_s50_peinfo(self, time='all'):
        pedict = {}
        url = 'https://danjuanapp.com/djapi/index_eva/pe_history/SH000016?day=' + time
        header = {}
        header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
        res = requests.get(url=url, headers=header)
        peinfo = json.loads(res.content)['data']['index_eva_pe_growths']
        for pe in peinfo:
            pe['ts'] = datetime.datetime.fromtimestamp(pe['ts'] // 1000)
            pedict.setdefault(pe['ts'], pe['pe'])
        self.peinfo = pedict
        if self.trade_days == {}:
            self.trade_days = set(pedict.keys())
        else:
            self.trade_days = self.trade_days & set(pedict.keys())
        return pedict

    def init_f_info(self, fid):
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
        self.f_info[fid] = fdict
        if self.trade_days == {}:
            self.trade_days = set(fdict.keys())
        else:
            self.trade_days = self.trade_days & set(fdict.keys())
        return fdict

    def get_yesterday(self, dt):
        for i in range(1, 30):
            dt = dt - datetime.timedelta(days=i)
            if dt in self.trade_days:
                return dt

    def get_today(self, dt):
        for i in range(0, 30):
            dt = dt - datetime.timedelta(days=i)
            if dt in self.trade_days:
                return dt

    def get_nwater(self, n, end_date, day=365):
        pe_value = [ self.peinfo.get(end_date-datetime.timedelta(days=i)) for i in range(1, day)\
            if end_date-datetime.timedelta(days=i) in self.trade_days ]
        pe_value.sort()
        index = len(pe_value)*n//100-1
        return pe_value[index]

    def get_weight(self, cur_pe, w30, w50=0, w70=0):
        if cur_pe > w30:
            return 0
        return w30/cur_pe

    def buy_1day(self, dt, fid, base=100):
        if dt not in self.trade_days:
            return (0, 0)
        w30 = self.get_nwater(30, dt)
        cur_pe = self.peinfo.get(self.get_yesterday(dt))
        capital = round(base*self.get_weight(cur_pe, w30), 2)
        amount = round(capital/float(self.f_info[fid][dt]), 2)
        print(dt, cur_pe, w30, capital)
        return (capital, amount)

    def buy_longtime(self, fid, begin_date, end_date):
        t_capital = 0
        t_amount = 0
        days = (end_date - begin_date).days
        dt = begin_date
        for i in range(days):
            res = self.buy_1day(dt, fid)
            dt = dt + datetime.timedelta(days=1)
            t_capital = t_capital + res[0]
            t_amount = t_amount + res[1]
        fprice = float(self.f_info[fid].get(self.get_today(end_date)))
        win = (t_amount * fprice - t_capital) * 100 / t_capital
        win = str(round(win, 2)) + '%'
        return (t_capital, t_amount, win)


if __name__ == '__main__':
    fid = '001548'
    fv = FundValue()
    fv.init_s50_peinfo()
    fv.init_f_info(fid)
    bd = datetime.datetime(2019, 2, 13)
    ed = datetime.datetime(2020, 2, 13)
    print(fv.buy_longtime(fid, bd, ed))
