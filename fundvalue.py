# -*- coding:utf-8 -*-

import operator
import requests
import datetime
import json
import re

class FundValue():
    """ 从蛋卷基金获取指数信息。

    Attributes:
        peinfo: 字典，保存指数的历史pe，{datetime: pe}
        f_info: 字典, 保存基金的历史价格，{fid: {datetime: (nav, nav2)}}，fid 为基金编码，nav为基金净值，nav2为累计净值。
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
        """ 获取指定基金的价格，只能获取当前净值 """
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
            # 无法取得累计净值，以当前净值代替。
            fdict.setdefault(f['date'], (float(f['nav']), float(f['nav'])))
        self.f_info[fid] = fdict
        if self.trade_days == {}:
            self.trade_days = set(fdict.keys())
        else:
            self.trade_days = self.trade_days & set(fdict.keys())
        return fdict

    def parse_jsonp(self, response):
        return json.loads(re.match(r'[^(]*[(]({.*})[)][^)]*', response.content.decode('utf-8'), re.S).group(1))

    def init_f_info2(self, fid):
        """ 获取指定基金的价格，可以获取当前净值和累计净值 """
        fdict = {}
        url = 'http://api.fund.eastmoney.com/f10/lsjz?callback=jQuery&pageIndex=1&pageSize=20&startDate=&endDate=&fundCode=' + fid
        header = {}
        header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
        header['Referer'] = 'http://fundf10.eastmoney.com/jjjz_' + fid + '.html'
        res = requests.get(url=url, headers=header)
        total_item_number = self.parse_jsonp(res)['TotalCount']
        url = 'http://api.fund.eastmoney.com/f10/lsjz?callback=jQuery&pageIndex=1&pageSize=' + str(total_item_number) + '&startDate=&endDate=&fundCode=' + fid
        res = requests.get(url=url, headers=header)
        finfo = self.parse_jsonp(res)['Data']['LSJZList']
        for f in finfo:
            f['date'] = datetime.datetime.strptime(f['FSRQ'], '%Y-%m-%d')
            fdict.setdefault(f['date'], (float(f['DWJZ']), float(f['LJJZ'])))
        self.f_info[fid] = fdict
        if self.trade_days == {}:
            self.trade_days = set(fdict.keys())
        else:
            self.trade_days = self.trade_days & set(fdict.keys())
        return fdict

    def get_gz(self, fid):
        """ 获取当前时间的估值 """
        url = 'http://fundgz.1234567.com.cn/js/' + fid + '.js'
        header = {}
        header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
        try:
            res = requests.get(url=url, headers=header)
            gz_dict = self.parse_jsonp(res)
            return float(gz_dict['gsz'])
        except Exception as e:
            return -1

    def get_yesterday(self, dt):
        """ 获取指定日期的前一个交易日 """
        dt = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0, 0)
        for i in range(1, 30):
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

    def get_avg_price(self, fid, end_date, day=365):
        """ 获取 price 均值。
        """
        total = [0, 0]
        price_list = [ self.f_info[fid].get(end_date-datetime.timedelta(days=i)) for i in range(1, day)\
            if end_date-datetime.timedelta(days=i) in self.trade_days ]
        for i in price_list:
            total[0] = total[0] + i[0]
            total[1] = total[1] + i[1]
        return (total[0]/len(price_list), total[1]/len(price_list))

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
            超过该价格，则不买，否则多买。
        """
        if cur_price > wprice:
            return 0
        # 加强 price 的权重，越低越买
        return (wprice/cur_price) ** n

    def get_delta_price(self, fid, dt=None):
        if dt is None:
            dt = datetime.datetime.now()
        delta_price = self.f_info[fid].get(self.get_yesterday(dt))
        delta_price = delta_price[1] - delta_price[0]
        return delta_price

    def buy_1day(self, fid, bdt=None, n_pe=2, n_price=4, base=100):
        """ 对指定的某一天进行购买，用于测试，默认买100块钱。
            dt is None，表示今天购买，否则校验是否为交易日。
        """
        if len(self.trade_days) < 650:
            return (-1, -1)
        dt = bdt
        # 非今天申购，且非交易日，则不予购买。
        if dt is not None and dt not in self.trade_days:
            return (0, 0)
        # 默认采用当天的净值来计算，如果当天购买，则采用实时最新估值。
        if dt is None:
            dt = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
            real_price = self.get_gz(fid)
            delta_price = self.get_delta_price(fid)
            cur_price = real_price + delta_price
        else:
            real_price = self.f_info[fid].get(dt)[0]
            cur_price = self.f_info[fid].get(dt)[1]

        w30 = self.get_nwater(dt, 30)
        cur_pe = self.peinfo.get(self.get_yesterday(dt))
        weight_pe = self.get_weight_pe(cur_pe, w30, n_pe)

        wprice = self.get_avg_price(fid, dt)[1]
        weight_price = self.get_weight_price(cur_price, wprice, n_price)

        weight = weight_pe * weight_price

        capital = round(base * weight, 2)
        # 以累计净值计算购买数量，如当天购买，则不准确。
        amount = round(capital/cur_price, 2)
        #print(dt, weight, capital)
        return (capital, amount)

    def buy_longtime(self, fid, begin_date, end_date, n_pe=2, n_price=4, fee=0, base=100):
        """ 长期购买一段时间，用于测试。默认买100块钱。以最后一天累计净值为基准计算盈利。
            fee=申购费率*100，在实测中基本可以忽略费率对收益的影响。
        """
        days = (end_date - begin_date).days
        b_capital = 0
        b_amount = 0
        dt = begin_date - datetime.timedelta(days=1)
        # 获取最高盈利点
        maxg = [0, dt]
        for i in range(days):
            dt = dt + datetime.timedelta(days=1)
            if dt not in self.trade_days:
                continue
            res = self.buy_1day(fid, dt, n_pe, n_price, base)
            b_capital = b_capital + res[0]
            b_amount = b_amount + res[1]
            fprice = float(self.f_info[fid].get(dt)[1])
            if int(b_capital) > 0:
                g = round((fprice*b_amount-b_capital)/b_capital*100, 2)
                if g > maxg[0]:
                    maxg[0] = g
                    maxg[1] = dt.strftime('%Y-%m-%d')
        fprice = float(self.f_info[fid].get(self.get_yesterday(end_date))[1])
        avg_price = 0 if b_capital==0 else round(b_capital/b_amount, 4)
        win = 0 if b_capital==0 else (b_amount*fprice-b_capital-b_capital*fee/100) * 100 / b_capital
        win = str(round(win, 2)) + '%'
        return (round(b_capital,2), round(b_amount,2), maxg, win)

    def bs_longtime(self, fid, begin_date, end_date, n_pe=2, n_price=4, fee=0, base=100):
        """ 长期购买一段时间，用于测试。默认买100块钱。超过70水位线则卖出。
            为增加盈利，会将当前已赎回的钱再去申购基金，由于很难确定申购额度，导致最终盈利很难超过长期持有。
            回测结果显示做波段不如长期持有。
            每天无脑定投固定金额毫无意义。
        """
        days = (end_date - begin_date).days
        e_capital = 0
        t_capital = 0
        b_capital = 0
        b_amount = 0
        dt = begin_date - datetime.timedelta(days=1)
        for i in range(days):
            dt = dt + datetime.timedelta(days=1)
            if dt not in self.trade_days:
                continue
            res = self.buy_1day(fid, dt, n_pe, n_price, base)
            t_capital = t_capital + res[0]
            b_capital = b_capital + res[0]
            b_amount = b_amount + res[1]
            fprice = float(self.f_info[fid].get(dt)[1])
            if e_capital*0.01 > res[0] and int(res[0])>0:
                e_capital = e_capital * 0.99
                b_capital = b_capital + e_capital*0.01
                b_amount = b_amount + e_capital*0.01*res[1]/res[0]
            if fprice*b_amount > 1.1*b_capital:
                e_capital = e_capital + fprice*b_amount
                print((e_capital, dt))
                b_capital = 0
                b_amount = 0
        fprice = float(self.f_info[fid].get(self.get_yesterday(end_date))[1])
        win = 0 if b_capital+e_capital==0 else (b_amount*fprice+e_capital-t_capital) * 100 / t_capital
        win = str(round(win, 2)) + '%'
        return (round(t_capital,2), round(e_capital,2), round(b_amount, 2), win)


if __name__ == '__main__':
    fv = FundValue()

    #fv.init_s50_peinfo()
    #t = 2016
    #fee = 0.1

    fv.init_hs300_peinfo()
    t = 2011
    fee = 0.15

    #fv.init_hsbonus_peinfo()
    #t = 2011
    #fee = 0.12

    #fv.init_gem_peinfo()
    #t = 2018
    #fee = 0.12

    fid = fv.fids[0]
    fv.init_f_info2(fid)

    for i in range(t, 2020):
        j = i+1
        print(i)
        bd = datetime.datetime(i, 1, 1)
        ed = datetime.datetime(j, 1, 1)
        print(fv.buy_longtime(fid, bd, ed, 2, 4))
    bd = datetime.datetime(t, 1, 1)
    ed = datetime.datetime(2020, 1, 1)
    #print(fv.bs_longtime(fid, bd, ed, 2, 4))
    print(fv.buy_longtime(fid, bd, ed, 2, 4, fee))
    print(fv.buy_1day(fid, n_pe=2, n_price=4, base=100))
