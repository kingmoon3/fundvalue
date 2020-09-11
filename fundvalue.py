# -*- coding:utf-8 -*-

import requests
import datetime
import time
import json
import re
import math
from eastfund import EastFund
from danjuan import Danjuan


class FundValue():
    """ 从蛋卷基金获取指数信息。

    Attributes:
        index_list: 字典，保存所有指数和对应基金的信息，key为助记符
        index_pbe: 字典，保存指数的历史pe/pb，{datetime: pe}
        fund_jz: 字典, 保存基金的历史价格，{datetime: (nav, nav2)}
        fid 为基金编码，nav为基金净值，nav2为累计净值。
        trade_days: 所有交易日的集合，各个基金可能不同，每计算一个基金则需要取一次交集。
        east: 对象，根据 fid 和东方财富 api 获取基金净值信息。
        dj: 对象，根据 index_code 和蛋卷 api 获取指数估值信息。
    """

    def __init__(self, index_key):
        """ 初始化数据结构 """
        index_list = {
            'hs300': {
                'index': {'code': 'SH000300', 'name': u'沪深300', 'vq': 'pe'},
                'fund': {'fid': '100038', 'fee': 0.12, 'byear': 2011 }},
            'sh50': {
                'index': {'code': 'SH000016', 'name': u'上证50', 'vq': 'pe'},
                'fund': {'fid': '001548', 'fee': 0.1, 'byear': 2016 }},
            'zzbonus': {
                'index': {'code': 'SH000922', 'name': u'中证红利', 'vq': 'pe'},
                'fund': {'fid': '100032', 'fee': 0.15, 'byear': 2011 }},
            'gem': {
                'index': {'code': 'SZ399006', 'name': u'创业板', 'vq': 'pe'},
                'fund': {'fid': '003765', 'fee': 0.12, 'byear': 2018 }},
            'zz500': {
                'index': {'code': 'SH000905', 'name': u'中证500', 'vq': 'pe'},
                'fund': {'fid': '003986', 'fee': 0.12, 'byear': 2018 }},
            'zzbank': {
                'index': {'code': 'SZ399986', 'name': u'中证银行', 'vq': 'pb'},
                'fund': {'fid': '001594', 'fee': 0.1, 'byear': 2016 }},
            'zzhouse': {
                'index': {'code': 'SZ399393', 'name': u'国证地产', 'vq': 'pb'},
                'fund': {'fid': '160218', 'fee': 0.1, 'byear': 2014 }},
            'zzzq': {
                'index': {'code': 'SZ399975', 'name': u'全指证券', 'vq': 'pb'},
                'fund': {'fid': '160633', 'fee': 0.12, 'byear': 2016 }},
            'zzxf': {
                'index': {'code': 'SH000932', 'name': u'主要消费', 'vq': 'pe'},
                'fund': {'fid': '000248', 'fee': 0.1, 'byear': 2016 }},
            'zzwine': {
                'index': {'code': 'SZ399997', 'name': u'中证白酒', 'vq': 'pe'},
                'fund': {'fid': '161725', 'fee': 0.1, 'byear': 2016 }},
            'hkhs': {
                'index': {'code': 'HKHSI', 'name': u'香港恒生', 'vq': 'pe'},
                'fund': {'fid': '000948', 'fee': 0.12, 'byear': 2016 }},
            'sz60': {
                'index': {'code': 'SZ399701', 'name': u'深证基本面60', 'vq': 'pe'},
                'fund': {'fid': '530015', 'fee': 0.15, 'byear': 2012 }},
            'yy100': {
                'index': {'code': 'SH000978', 'name': u'医药100', 'vq': 'pe'},
                'fund': {'fid': '001550', 'fee': 0.1, 'byear': 2016 }},
            'zzyl': {
                'index': {'code': 'SZ399989', 'name': u'中证医疗', 'vq': 'pe'},
                'fund': {'fid': '162412', 'fee': 0.12, 'byear': 2016 }},
            '300value': {
                'index': {'code': 'SH000919', 'name': u'300价值', 'vq': 'pe'},
                'fund': {'fid': '310398', 'fee': 0.12, 'byear': 2011 }},
            'zz100': {
                'index': {'code': 'SH000903', 'name': u'中证100', 'vq': 'pe'},
                'fund': {'fid': '213010', 'fee': 0.12, 'byear': 2011 }},
            'base50': {
                'index': {'code': 'SH000925', 'name': u'基本面50', 'vq': 'pe'},
                'fund': {'fid': '160716', 'fee': 0.12, 'byear': 2011 }},
        }
        self.index_pbe = {}
        self.fund_jz = {}
        self.trade_days = {}
        self.index = index_list[index_key]['index']
        self.fund = index_list[index_key]['fund']
        self.fid = self.fund['fid']
        self.dj = Danjuan(self.index['code'], self.index['vq'])
        self.east = EastFund(self.fid)

    def init_index_pbe(self, time='all'):
        """ 获取pe/pb的通用接口，time可以为1y, 3y """
        self.index_pbe = self.dj.init_pbe()
        if self.trade_days == {}:
            self.trade_days = set(self.index_pbe.keys())
        else:
            self.trade_days = self.trade_days & set(self.index_pbe.keys())
        return self.index_pbe

    def init_fund_jz(self):
        """ 获取指定基金的价格，可以获取当前净值和累计净值 """
        self.fund_jz = self.east.load_fundprice()
        if self.trade_days == {}:
            self.trade_days = set(self.fund_jz.keys())
        else:
            self.trade_days = self.trade_days & set(self.fund_jz.keys())
        return self.fund_jz

    def get_yesterday(self, dt):
        """ 获取指定日期的前一个交易日 """
        dt = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0, 0)
        for i in range(1, 30):
            dt = dt - datetime.timedelta(days=i)
            if dt in self.trade_days:
                return dt

    def get_weight_pe(self, cur_pe, w30, n=2):
        """ 获取 pe 权重，以30水位线做基准，超过30水位线则不买。否则越低越买。
            经回测上证50，此参数对购买影响不大。
        """
        if n < 0:
            return 1
        if cur_pe > w30:
            return 0
        # 加强 pe 的权重，越低越买
        return (w30/cur_pe) ** n

    def get_weight_price(self, cur_price, wprice, n=4):
        """ 获取 price 权重，实际采用前365天的平均价格。
            超过该价格，则不买，否则多买。
        """
        if cur_price > wprice:
            return 0
        # 加强 price 的权重，越低越买
        return (wprice/cur_price) ** n
 
    def get_buylog_water(self, buy_log):
        """ 长期购买一段时间，计算当前购买的水位线。利用水位线进一步提高购买比例，事实证明没用。
        """
        if len(buy_log) <= 50:
            return (0, len(buy_log))
        else:
            fprice = buy_log[-1]
            if fprice == 0:
                return (0, len(buy_log)) 
            sorted_log = sorted(buy_log)
            weight = 1.0 * sorted_log.index(fprice) / len(sorted_log)
            return (weight, len(buy_log))

    def get_buylog(self, end_date=None, days=365*5, n_pe=2, n_price=4, base=100):
        buy_log = []
        if end_date is None:
            end_date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time()) - datetime.timedelta(days=1)
        begin_date = end_date - datetime.timedelta(days=days)
        dt = begin_date
        for i in range(days):
            dt = dt + datetime.timedelta(days=1)
            if dt not in self.trade_days:
                continue
            res = self.buy_1day(dt, n_pe, n_price, base)
            if int(res[0]) > 0:
                buy_log.append(res[0])
        return buy_log

    def buy_1day(self, bdt=None, n_pe=2, n_price=4, base=100):
        """ 对指定的某一天进行购买，用于测试，默认买100块钱。
            dt is None，表示今天购买，否则校验是否为交易日。
        """
        fid = self.fid
        if len(self.trade_days) < 650:
            return (-1, -1)
        dt = bdt
        # 非今天申购，且非交易日，则不予购买。
        if dt is not None and dt not in self.trade_days:
            return (0, 0)
        # 如果当天购买，则采用实时最新估值。
        if dt is None:
            dt = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
            (real_price, cur_price) = self.east.get_gz()
            # 如果取估值有问题，可能是假日，不申购。
            if real_price < 0:
                return (0, 0)
        # 否则采用当天的净值来计算
        else:
            real_price = self.fund_jz.get(dt)[0]
            cur_price = self.fund_jz.get(dt)[1]

        # 计算 pe 权重，由于 pe 无法预估，因此采用前一天的 pe 计算
        # 考虑到波动周期性，pe 标准改用最近5年的30水位线（好买评估依据），也可以采用10年，保证指数经历一轮牛熊（蛋卷评估依据）
        # 不宜采用1-2年方案，受行业周期影响较大。
        wpe = self.dj.get_pbe_nwater(dt, 30, 365*5)
        cur_pe = self.index_pbe.get(self.get_yesterday(dt))
        weight_pe = self.get_weight_pe(cur_pe, wpe, n_pe)

        # 为更安全，price 标准采用最近1年的均值，时间过长，可能无法申购。也可以考虑采用最近1年，2年均值的最小值。
        # wprice = min(self.get_avg_price(fid, dt)[1], self.get_avg_price(fid, dt, 50, 365*2)[1])
        wprice = self.east.get_avg_price(dt)[1]
        weight_price = self.get_weight_price(cur_price, wprice, n_price)

        weight = weight_pe * weight_price

        capital = int(math.ceil(base*weight))
        # 以累计净值计算购买数量，不准确。
        amount = round(capital/cur_price, 2)
        return (capital, amount, (real_price, cur_price))

    def buy_longtime(self, begin_date, end_date, n_pe=2, n_price=4, fee=0, base=100):
        """ 长期购买一段时间，用于测试。默认买100块钱。以最后一天累计净值为基准计算盈利。
            fee=申购费率*100，在实测中基本可以忽略费率对收益的影响。
        """
        fid = self.fid
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
            res = self.buy_1day(dt, n_pe, n_price, base)
            b_capital = b_capital + res[0]
            b_amount = b_amount + res[1]
            fprice = float(self.fund_jz[dt][1])
            if int(b_capital) > 0:
                g = round((fprice*b_amount-b_capital)/b_capital*100, 2)
                if g > maxg[0]:
                    maxg[0] = g
                    maxg[1] = dt.strftime('%Y-%m-%d')
        fprice = float(self.fund_jz.get(self.get_yesterday(end_date))[1])
        win = 0 if b_capital == 0 else (
            b_amount*fprice-b_capital-b_capital*fee/100) * 100 / b_capital
        win = str(round(win, 2)) + '%'
        avg_price = 0 if b_amount == 0 else (b_capital/b_amount)
        return (round(b_capital, 2), round(b_amount, 2), maxg, win, round(avg_price, 4), fprice)


if __name__ == '__main__':

    index_code = 'hs300'

    fv = FundValue(index_code)
    fv.init_index_pbe()
    fv.init_fund_jz()
    t = fv.fund['byear']
    fee = fv.fund['fee']

    end_year = 2020
    for i in range(t, end_year):
        j = i + 1
        print(i)
        bd = datetime.datetime(i, 1, 1)
        ed = datetime.datetime(j, 1, 1)
        print(fv.buy_longtime(bd, ed, 2, 4))
    bd = datetime.datetime(t, 1, 1)
    ed = datetime.datetime(end_year, 1, 1)
    print(fv.buy_longtime(bd, ed, 2, 4, fee))
    print(fv.buy_1day(n_pe=2, n_price=4, base=100))
    # print(fv.bs_longtime2(fid, bd, ed, 2, 4, fee))
