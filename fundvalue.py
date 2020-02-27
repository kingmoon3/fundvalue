# -*- coding:utf-8 -*-

import operator
import requests
import datetime
import json

class FundValue():
    """ 从蛋卷基金获取指数信息。

    Attributes:
        peinfo: 字典，保存指数的历史pe，{datetime: pe}
        f_info: 字典, 保存基金的历史价格，{fid: {datetime: nav}}，fid 为基金编码。
        trade_days: 所有交易日的集合，各个基金可能不同，每计算一个基金则需要取一次交集。
        fids: 不同指数基金对应的基金列表，目前只有一个。
        index: 不同指数基金对应的名字，如上证50等。
    """

    def __init__(self):
        """ 初始化数据结构 """
        self.peinfo = {}
        self.f_info = {}
        self.trade_days = {}
        self.fids = []
        self.index = ''

    def init_peinfo(self, url):
        """ 获取pe的通用接口 """
        pedict = {}
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

    def init_s50_peinfo(self, time='all'):
        """ 获取上证50的pe，time可以为1y, 3y """
        url = 'https://danjuanapp.com/djapi/index_eva/pe_history/SH000016?day=' + time
        self.fids = ['001548', ]
        self.index = u'上证50'
        return self.init_peinfo(url)

    def init_hs300_peinfo(self, time='all'):
        """ 获取沪深300的pe，time可以为1y, 3y """
        url = 'https://danjuanapp.com/djapi/index_eva/pe_history/SH000300?day=' + time
        self.fids = ['100038', ]
        self.index = u'沪深300'
        return self.init_peinfo(url)

    def init_hsbonus_peinfo(self, time='all'):
        """ 获取中证红利的pe，time可以为1y, 3y """
        url = 'https://danjuanapp.com/djapi/index_eva/pe_history/SH000922?day=' + time
        self.fids = ['100032', ]
        self.index = u'中证红利'
        return self.init_peinfo(url)

    def init_sbonus_peinfo(self, time='all'):
        """ 获取上证红利的pe，time可以为1y, 3y """
        url = 'https://danjuanapp.com/djapi/index_eva/pe_history/SH000015?day=' + time
        self.fids = ['510880', ]
        self.index = u'上证红利'
        return self.init_peinfo(url)

    def init_gem_peinfo(self, time='all'):
        """ 获取创业板的pe，time可以为1y, 3y """
        url = 'https://danjuanapp.com/djapi/index_eva/pe_history/SZ399006?day=' + time
        self.fids = ['003765', ]
        self.index = u'创业板'
        return self.init_peinfo(url)

    def init_f_info(self, fid):
        """ 获取指定基金的价格 """
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
            fdict.setdefault(f['date'], float(f['nav']))
        self.f_info[fid] = fdict
        if self.trade_days == {}:
            self.trade_days = set(fdict.keys())
        else:
            self.trade_days = self.trade_days & set(fdict.keys())
        return fdict

    def get_yesterday(self, dt):
        """ 获取指定日期的前一个交易日 """
        for i in range(1, 30):
            dt = dt - datetime.timedelta(days=i)
            if dt in self.trade_days:
                return dt

    def get_today(self, dt):
        """ 获取指定日期的当前交易日 """
        for i in range(0, 30):
            dt = dt - datetime.timedelta(days=i)
            if dt in self.trade_days:
                return dt

    def get_nwater(self, end_date, n=30, day=365*2):
        """ 获取指定日期的水位线，默认向前搜索2年
            1年风险高，获利高，3年太缓慢了
        """
        pe_value = [ self.peinfo.get(end_date-datetime.timedelta(days=i)) for i in range(1, day)\
            if end_date-datetime.timedelta(days=i) in self.trade_days ]
        pe_value.sort()
        index = len(pe_value)*n//100-1
        return pe_value[index]

    def get_nprice(self, fid, end_date, n=50, day=365):
        """ 获取 price 均值。
        """
        total = 0
        price_list = [ self.f_info[fid].get(end_date-datetime.timedelta(days=i)) for i in range(1, day)\
            if end_date-datetime.timedelta(days=i) in self.trade_days ]
        for i in price_list:
            total = total + i
        avg = total/len(price_list)
        return avg*n/50

    def get_weight_pe(self, cur_pe, w30, n=2):
        """ 获取 pe 权重，以30水位线做基准，超过30水位线则不买。否则越低越买。
            经回测上证50，此参数对购买影响不大。
        """
        if cur_pe > w30:
            return 0
        # 加强 pe 的权重，越低越买
        return (w30/cur_pe) ** n

    def get_weight_price(self, cur_price, wprice=1, n=4):
        """ 获取 price 权重，默认以1做基准，实际采用前365天的平均价格。
            超过该价格，则不买，否则多买。在有分红等情况下需考虑复权。
            经回测上证50，此参数影响较大。
        """
        if cur_price > wprice:
            return 0
        # 加强 price 的权重，越低越买
        return (wprice/cur_price) ** n

    def buy_1day(self, fid, bdt=None, n_pe=2, n_price=4, base=100):
        """ 对指定的某一天进行购买，用于测试，默认买100块钱。
            dt is None，表示今天购买，否则校验是否为交易日。
        """
        if len(self.trade_days) < 650:
            return (-1, -1)
        dt = bdt
        if dt is None:
            dt = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
        elif dt not in self.trade_days:
            return (0, 0)
        w30 = self.get_nwater(dt, 30)
        cur_pe = self.peinfo.get(self.get_yesterday(dt))
        weight_pe = self.get_weight_pe(cur_pe, w30, n_pe)
        wprice = self.get_nprice(fid, dt, 50)
        cur_price = self.f_info[fid].get(self.get_yesterday(dt))
        weight_price = self.get_weight_price(cur_price, wprice, n_price)
        weight = weight_pe * weight_price
        capital = round(base * weight, 2)
        #capital = base
        amount = 0 if bdt is None else round(capital / self.f_info[fid].get(dt,-1), 2)
        #print(dt, weight, capital)
        return (capital, amount)

    def buy_longtime(self, fid, begin_date, end_date, n_pe=2, n_price=4, base=100):
        """ 长期购买一段时间，用于测试。默认买100块钱。以最后一天价格为基准计算盈利。
        """
        days = (end_date - begin_date).days
        b_capital = 0.01
        b_amount = 0
        dt = begin_date
        for i in range(days):
            res = self.buy_1day(fid, dt, n_pe, n_price, base)
            dt = dt + datetime.timedelta(days=1)
            b_capital = b_capital + res[0]
            b_amount = b_amount + res[1]
        fprice = float(self.f_info[fid].get(self.get_today(end_date)))
        win = (b_amount * fprice - b_capital) * 100 / b_capital
        win = str(round(win, 2)) + '%'
        return (round(b_capital,2), round(b_amount,2), win)

    def bs_longtime(self, fid, begin_date, end_date, n_pe=2, n_price=4, base=100):
        """ 长期购买一段时间，用于测试。默认买100块钱。超过70水位线则卖出。
            为增加盈利，会将当前已赎回的钱再去申购基金，由于很难确定申购额度，导致最终盈利很难超过长期持有。
            回测结果显示如不缺钱，做波段不如长期买着不再赎回。
            不考虑申赎费，长期看回报率年化8%。
            另外，每天无脑定投固定金额毫无意义。
        """
        days = (end_date - begin_date).days
        sum_capital = 0
        earn_capital = 0
        b_capital = 0.01
        b_amount = 0
        dt = begin_date
        for i in range(days):
            if b_amount > 0 and self.peinfo.get(self.get_yesterday(dt)) > self.get_nwater(dt, 70):
                earn_capital = earn_capital + self.f_info[fid].get(self.get_yesterday(dt)) * b_amount
                print(dt, self.f_info[fid].get(self.get_yesterday(dt)), earn_capital)
                b_amount = 0
                b_capital = 0.01
            res = self.buy_1day(fid, dt, n_pe, n_price, base)
            dt = dt + datetime.timedelta(days=1)
            sum_capital = sum_capital + res[0]
            b_capital = b_capital + res[0]
            b_amount = b_amount + res[1]
            # 将已赎回的钱再去申购，每次申购额是当前申购额的3倍（此数字只适用于100038）。
            if earn_capital > res[0]*3 :
                b_capital = b_capital + res[0]*3
                b_amount = b_amount + res[1]*3
                earn_capital = earn_capital - res[0]*3
        fprice = float(self.f_info[fid].get(self.get_today(end_date)))
        win = (b_amount * fprice + earn_capital - sum_capital) * 100 / sum_capital
        win = str(round(win, 2)) + '%'
        return (round(sum_capital,2), round(b_amount,2), round(earn_capital, 2), round(b_amount*fprice, 2), win)


if __name__ == '__main__':
    fv = FundValue()

    #fv.init_s50_peinfo()
    #t = 2016

    #fv.init_hs300_peinfo()
    #t = 2011

    #fv.init_hsbonus_peinfo()
    #t = 2011

    fv.init_gem_peinfo()
    t = 2018

    fid = fv.fids[0]
    fv.init_f_info(fid)

    for i in range(t, 2020):
        j = i+1
        print(i)
        bd = datetime.datetime(i, 1, 1)
        ed = datetime.datetime(j, 1, 1)
        print(fv.buy_longtime(fid, bd, ed, 2, 4))
    bd = datetime.datetime(t, 1, 1)
    ed = datetime.datetime(2020, 1, 1)
    #print(fv.bs_longtime(fid, bd, ed, 2, 4))
    print(fv.buy_longtime(fid, bd, ed, 2, 4))
    print(fv.buy_1day(fid, n_pe=2, n_price=4, base=100))
