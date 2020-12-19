# -*- coding:utf-8 -*-

import requests
import datetime
import time
import json
import re
import math
from eastfund import EastFund
from danjuan import Danjuan


class Wwxf(EastFund):
    """ 从东方基金获取基金价格

    Attributes:
        fid 为基金编码，nav为基金净值，nav2为累计净值。
    """

    def __init__(self):
        self.record_path = './record.wwxf'
        self.price_list = {}
        self.xnjz = {}
        self.funds = [
            {'fid': '519718', 'p': 12.9},
            {'fid': '164902', 'p': 11.92},
            {'fid': '519723', 'p': 11.92},
            {'fid': '519782', 'p': 9.91},
            {'fid': '006793', 'p': 6.4},
            {'fid': '008204', 'p': 5.96},
            {'fid': '519755', 'p': 12.78},
            {'fid': '519752', 'p': 10.41},
            {'fid': '519738', 'p': 9.7},
            {'fid': '519772', 'p': 3.62},
            {'fid': '519704', 'p': 2.68},
            {'fid': '005001', 'p': 1.8},
        ]

    def init_xnjz(self):
        fr = open(self.record_path, 'r')
        for line in fr.readlines():
            arr = line.strip().split(',')
            d = datetime.datetime.strptime(arr[1], '%Y-%m-%d')
            self.price_list[d] = (float(arr[2]), float(arr[3]))
        fr.close()
        jz = {}
        prices = []
        for f in self.funds:
            east = EastFund(f['fid'])
            fprice = east.load_fundprice()
            for k in fprice.keys():
                if k not in jz:
                    jz[k] = [0, 0]
                jz[k][0] = jz[k][0] + fprice[k][0] * f['p'] / 100
                jz[k][1] = jz[k][1] + fprice[k][1] * f['p'] / 100
        for k in jz:
            jz[k][0] = round(jz[k][0], 4)
            jz[k][1] = round(jz[k][1], 4)
        self.xnjz = jz
        return jz

    def get_gz(self):
        gz = [0, 0]
        for f in self.funds:
            east = EastFund(f['fid'])
            fprice = east.get_gz()
            if fprice[0] == 0:
                continue
            gz[0] = gz[0] + fprice[0] * f['p'] / 100
            gz[1] = gz[1] + fprice[1] * f['p'] / 100
        for i in range(1, 30):
            d = datetime.datetime.now()
            d = datetime.datetime(d.year, d.month, d.day, 0, 0, 0) - datetime.timedelta(days=i)
            if d in self.xnjz and d in self.price_list:
                ratio0 = self.xnjz[d][0] / self.price_list[d][0]
                ratio1 = self.xnjz[d][1] / self.price_list[d][1]
                break
        gz[0] = round(gz[0] / ratio0, 4)
        gz[1] = round(gz[1] / ratio1, 4)
        return gz

    def get_buylog(self, end_date=None, days=350, n=10, base=100):
        buy_log = []
        if end_date is None:
            end_date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time()) - datetime.timedelta(days=1)
        begin_date = end_date - datetime.timedelta(days=days)
        dt = begin_date
        for i in range(days):
            dt = dt + datetime.timedelta(days=1)
            if dt not in self.price_list.keys():
                continue
            res = self.buy_1day(dt, n, base, avgdays=30)
            if int(res['capital']) > 0:
                buy_log.append(res['capital'])
        return buy_log

    def buy_longtime(self, begin_date, end_date, n=6, base=100):
        """ 长期购买一段时间，用于测试。默认买100块钱。以最后一天累计净值为基准计算盈利。
            此处采用均值作为购买指标，效果好于净值区间作为购买指标。
        """
        days = (end_date - begin_date).days
        b_capital = 0
        b_amount = 0
        dt = begin_date - datetime.timedelta(days=1)
        buy_log = []
        for i in range(days):
            dt = dt + datetime.timedelta(days=1)
            if dt not in self.price_list.keys():
                continue
            fprice = self.price_list[dt][1]
            res = self.buy_1day(dt, n, avgdays=30)
            buy_log.append(res['capital'])
            b_capital = b_capital + res['capital']
            b_amount = b_amount + res['amount']
            # if res['capital'] > 0:
            #     print(dt, res['capital'], res['amount'])
        win = 0 if b_capital == 0 else (
            b_amount * fprice - b_capital) * 100 / b_capital
        win = str(round(win, 2)) + '%'
        avg_price = 0 if b_amount == 0 else (b_capital/b_amount)
        return (round(b_capital, 2), round(b_amount, 2), win, round(avg_price, 4), fprice)


if __name__ == '__main__':
    n = Wwxf()
    n.init_xnjz()
    begin_date = datetime.datetime(2017, 7, 1, 0, 0, 0)
    end_date = datetime.datetime(2020, 7, 1, 0, 0, 0)
    # begin_date = datetime.datetime(2018, 1, 1, 0, 0, 0)
    # end_date = datetime.datetime(2019, 1, 1, 0, 0, 0)
    print(n.buy_longtime(begin_date, end_date, 10, 100))
    # today = n.buy_1day(n=10)
    buy_log = n.get_buylog()
    # buy_log.append(today['capital'])
    # print(today)
    print(n.get_buylog_water(buy_log))

