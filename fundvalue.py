# -*- coding:utf-8 -*-

import requests
import datetime
import json
import re


class FundValue():
    """ 从蛋卷基金获取指数信息。

    Attributes:
        index_list: 字典，保存所有指数和对应基金的信息，key为助记符
        pbeinfo: 字典，保存指数的历史pe/pb，{datetime: pe}
        f_info: 字典, 保存基金的历史价格，{fid: {datetime: (nav, nav2)}}
        fid 为基金编码，nav为基金净值，nav2为累计净值。
        trade_days: 所有交易日的集合，各个基金可能不同，每计算一个基金则需要取一次交集。
        index_info: 字典，根据 index_key 获取指定指数和对应基金的基础信息。
    """

    def __init__(self, index_key):
        """ 初始化数据结构 """
        index_list = {
            's50': {
                'index_code': 'SH000016', 'index_name': u'上证50',
                'index_fids': ['001548', ], 'index_vq': 'pe'},
            'hs300': {
                'index_code': 'SH000300', 'index_name': u'沪深300',
                'index_fids': ['100038', ], 'index_vq': 'pe'},
            'hsbonus': {
                'index_code': 'SH000922', 'index_name': u'中证红利',
                'index_fids': ['100032', ], 'index_vq': 'pe', },
            'sbonus': {
                'index_code': 'SH000015', 'index_name': u'上证红利',
                'index_fids': ['510880', ], 'index_vq': 'pe', },
            'gem': {
                'index_code': 'SZ399006', 'index_name': u'创业板',
                'index_fids': ['003765', ], 'index_vq': 'pe'},
            'hs500': {
                'index_code': 'SH000905', 'index_name': u'中证500',
                'index_fids': ['000478', ], 'index_vq': 'pe'},
            'bank': {
                'index_code': 'SZ399986', 'index_name': u'中证银行',
                'index_fids': ['001594', ], 'index_vq': 'pb'},
            'hsxf': {
                'index_code': 'SH000932', 'index_name': u'中证消费',
                'index_fids': ['000248', ], 'index_vq': 'pe'},
            'hswine': {
                'index_code': 'SZ399997', 'index_name': u'中证白酒',
                'index_fids': ['161725', ], 'index_vq': 'pe'},
            'hshouse': {
                'index_code': 'SZ399393', 'index_name': u'国证地产',
                'index_fids': ['160218', ], 'index_vq': 'pb'},
        }
        self.pbeinfo = {}
        self.f_info = {}
        self.trade_days = {}
        self.index_info = index_list[index_key]

    def init_index_pbeinfo(self, time='all'):
        """ 获取pe/pb的通用接口，time可以为1y, 3y """
        pedict = {}
        header = {}
        header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/79.0.3945.130 Safari/537.36'
        url = 'https://danjuanapp.com/djapi/' +\
            'index_eva/{}_history/{}?day={}'.format(
                self.index_info['index_vq'],
                self.index_info['index_code'],
                time)
        res = requests.get(url=url, headers=header)
        pbe_name = 'index_eva_' + self.index_info['index_vq'] + '_growths'
        pbeinfo = json.loads(res.content)['data'][pbe_name]
        for pe in pbeinfo:
            pe['ts'] = datetime.datetime.fromtimestamp(pe['ts'] // 1000)
            pedict.setdefault(pe['ts'], pe.get(self.index_info['index_vq']))
        self.pbeinfo = pedict
        if self.trade_days == {}:
            self.trade_days = set(pedict.keys())
        else:
            self.trade_days = self.trade_days & set(pedict.keys())
        return pedict

    def init_f_info(self, fid):
        """ 获取指定基金的价格，只能获取当前净值 """
        fdict = {}
        header = {}
        header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/79.0.3945.130 Safari/537.36'
        url = 'https://danjuanapp.com/djapi/fund/nav/history/'\
            + str(fid) + '?page=1&size=10'
        res = requests.get(url=url, headers=header)
        total_item_number = json.loads(res.content)['data']['total_items']
        url = 'https://danjuanapp.com/djapi/fund/nav/history/'\
            + str(fid) + '?page=1&size=' + str(total_item_number)
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
        return json.loads(
            re.match(
                r'[^(]*[(]({.*})[)][^)]*',
                response.content.decode('utf-8'),
                re.S).group(1))

    def init_f_info2(self, fid):
        """ 获取指定基金的价格，可以获取当前净值和累计净值 """
        fdict = {}
        url = 'http://api.fund.eastmoney.com/f10/lsjz?callback=jQuery\
            &pageIndex=1&pageSize=20&startDate=&endDate=&fundCode=' + fid
        header = {}
        header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/79.0.3945.130 Safari/537.36'
        header['Referer'] = 'http://fundf10.eastmoney.com/jjjz_'\
            + fid + '.html'
        res = requests.get(url=url, headers=header)
        total_item_number = self.parse_jsonp(res)['TotalCount']
        url = 'http://api.fund.eastmoney.com/f10/lsjz?callback=jQuery\
            &pageIndex=1&pageSize=' + str(total_item_number)\
            + '&startDate=&endDate=&fundCode=' + fid
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
        header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/79.0.3945.130 Safari/537.36'
        try:
            res = requests.get(url=url, headers=header)
            gz_dict = self.parse_jsonp(res)
            dnow = datetime.datetime.now().strftime('%Y-%m-%d')
            if dnow != gz_dict['gztime'].split(' ')[0]:
                return -1
            return float(gz_dict['gsz'])
        except Exception as e:
            print(e)
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
        pe_value = [self.pbeinfo.get(end_date-datetime.timedelta(days=i))
                    for i in range(1, day)
                    if end_date-datetime.timedelta(days=i) in self.trade_days]
        pe_value.sort()
        index = len(pe_value)*n//100-1
        return pe_value[index]

    def get_avg_price(self, fid, end_date, day=365):
        """ 获取 price 均值。
        """
        total = [0, 0]
        price_list = [
            self.f_info[fid].get(end_date-datetime.timedelta(days=i))
            for i in range(1, day)
            if end_date-datetime.timedelta(days=i) in self.trade_days]
        for i in price_list:
            total[0] = total[0] + i[0]
            total[1] = total[1] + i[1]
        return (total[0]/len(price_list), total[1]/len(price_list))

    def get_weight_pe(self, cur_pe, w30, n=2):
        """ 获取 pe 权重，以30水位线做基准，超过30水位线则不买。否则越低越买。
            经回测上证50，此参数对购买影响不大。
        """
        if n == 0:
            return 1
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
        # 如果当天购买，则采用实时最新估值。
        if dt is None:
            dt = datetime.datetime.combine(
                datetime.date.today(), datetime.datetime.min.time())
            real_price = self.get_gz(fid)
            # 如果取估值有问题，可能是假日，不申购。
            if real_price < 0:
                return (0, 0)
            delta_price = self.get_delta_price(fid)
            cur_price = real_price + delta_price
        # 否则采用当天的净值来计算
        else:
            real_price = self.f_info[fid].get(dt)[0]
            cur_price = self.f_info[fid].get(dt)[1]

        # 计算 pe 权重，由于 pe 无法预估，因此采用前一天的 pe 计算
        wpe = self.get_nwater(dt, 30)
        cur_pe = self.pbeinfo.get(self.get_yesterday(dt))
        weight_pe = self.get_weight_pe(cur_pe, wpe, n_pe)

        wprice = self.get_avg_price(fid, dt)[1]
        weight_price = self.get_weight_price(cur_price, wprice, n_price)

        weight = weight_pe * weight_price

        capital = round(base * weight, 2)
        # 以累计净值计算购买数量，不准确。
        amount = round(capital/cur_price, 2)
        # if dt.year == 2018:
        #    print(dt, weight, capital)
        return (capital, amount)

    def buy_longtime(
            self, fid, begin_date, end_date, n_pe=2, n_price=4, fee=0, base=100
            ):
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
        win = 0 if b_capital == 0 else (
            b_amount*fprice-b_capital-b_capital*fee/100) * 100 / b_capital
        win = str(round(win, 2)) + '%'
        return (round(b_capital, 2), round(b_amount, 2), maxg, win)

    def bs_fixed(self, fid, dt, bscapital):
        for i in range(10):
            dt = dt + datetime.timedelta(days=i)
            if dt in self.trade_days:
                fprice = float(self.f_info[fid].get(dt)[1])
                amount = round(bscapital/fprice, 2)
                return amount

    def rebalance(self, fprice, nprice, hold_amount, hold_capital, ratio):
        total_value = fprice*hold_amount+hold_capital
        cpratio = fprice*hold_amount/total_value
        bratio = 0.10
        sratio = 0.10
        if cpratio < (ratio*(1-bratio))/((ratio*(1-bratio))+(1-ratio)):
            b_capital = total_value*ratio - fprice*hold_amount
            b_capital = round(min(b_capital, hold_capital), 2)
            b_amount = round(b_capital/nprice, 2)
            return (b_capital, b_amount)
        if cpratio > (ratio*(1+sratio))/((ratio*(1+sratio))+(1-ratio)):
            s_capital = fprice*hold_amount - total_value*ratio
            s_amount = s_capital/fprice
            s_amount = round(min(s_amount, hold_amount), 2)
            s_capital = round(nprice*s_amount, 2)
            return (-s_capital, -s_amount)
        return (0, 0)

    def bs_longtime(self, fid, begin_date, end_date, n_pe=2, n_price=4, fee=0):
        """ 采用自动均衡机制，持仓和现金比例为1:1，盈利或亏损超过5%则调仓。
        """
        days = (end_date - begin_date).days
        base = 10000
        ratio = 0.8
        dt = begin_date - datetime.timedelta(days=1)
        hold_amount = self.bs_fixed(fid, begin_date, base*ratio)
        hold_capital = round(base*(1-ratio), 2)
        fee_cost = base*ratio*fee

        for i in range(7, days):
            dt = dt + datetime.timedelta(days=1)
            if dt not in self.trade_days:
                continue
            fprice = float(self.f_info[fid].get(self.get_yesterday(dt))[1])
            nprice = float(self.f_info[fid].get(dt)[1])
            # bs_capital, amount>0 为买，bs_capital, amount<0 为卖。
            (bs_capital, bs_amount) = self.rebalance(
                fprice, nprice, hold_amount, hold_capital, ratio)
            hold_capital = round(hold_capital - bs_capital, 2)
            hold_amount = round(hold_amount + bs_amount, 2)
            fee_cost = round(fee_cost + abs(bs_capital*fee/100), 2)
            if int(bs_capital) != 0:
                print((dt, bs_capital, bs_amount, hold_capital, hold_amount))
        fprice = float(self.f_info[fid].get(self.get_yesterday(end_date))[1])
        win = (hold_amount*fprice+hold_capital-base-fee_cost) * 100 / base
        win = str(round(win, 2)) + '%'
        return (
            round(hold_capital, 2),
            round(fprice*hold_amount, 2),
            -fee_cost,
            win)


if __name__ == '__main__':

    fv = FundValue('hs300')
    t = 2011
    fee = 0.15

    # fv = FundValue('s50')
    # t = 2016
    # fee = 0.1

    # fv = FundValue('hsbonus')
    # t = 2011
    # fee = 0.12

    # fv = FundValue('bank')
    # t = 2016
    # fee = 0.1

    # fv = FundValue('hs500')
    # t = 2015
    # fee = 0.12

    # fv = FundValue('gem')
    # t = 2018
    # fee = 0.12

    # fv = FundValue('hsxf')
    # t = 2016
    # fee = 0.1

    fv = FundValue('hswine')
    t = 2016
    fee = 0.1

    fv = FundValue('hshouse')
    t = 2014
    fee = 0.1

    fv.init_index_pbeinfo()
    fid = fv.index_info['index_fids'][0]
    fv.init_f_info2(fid)

    for i in range(t, 2020):
        j = i+1
        print(i)
        bd = datetime.datetime(i, 1, 1)
        ed = datetime.datetime(j, 1, 1)
        print(fv.buy_longtime(fid, bd, ed, 2, 4))
    bd = datetime.datetime(t, 1, 1)
    ed = datetime.datetime(2020, 1, 1)
    print(fv.buy_longtime(fid, bd, ed, 2, 4, fee))
    print(fv.buy_1day(fid, n_pe=2, n_price=4, base=100))
    # print(fv.bs_longtime(fid, bd, ed, 2, 4, fee))
