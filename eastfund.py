# -*- coding:utf-8 -*-

import requests
import datetime
import time
import json
import re
import math


class EastFund():
    """ 从东方基金获取基金价格

    Attributes:
        fid 为基金编码，nav为基金净值，nav2为累计净值。
    """

    def __init__(self, fid):
        self.fid = str(fid)
        self.price_list = {}
        self.record_path = './record.' + str(fid)

    def parse_jsonp(self, response):
        return json.loads(
            re.match(
                r'[^(]*[(]({.*})[)][^)]*',
                response.content.decode('utf-8'),
                re.S).group(1))

    def get_fundprice(self, start_date=None, end_date=None):
        """ 获取指定基金的净值，可以获取当前净值和累计净值 """
        sdate = '' if start_date is None else start_date.strftime('%Y-%m-%d')
        edate = '' if end_date is None else end_date.strftime('%Y-%m-%d')
        fid = self.fid
        result = []
        url = 'http://api.fund.eastmoney.com/f10/lsjz?callback=jQuery&pageIndex=1&'
        url += 'pageSize=20&startDate={}&endDate={}&fundCode={}'.format(sdate, edate, fid)
        header = {}
        header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        header['User-Agent'] += 'AppleWebKit/537.36 (KHTML, like Gecko) '
        header['User-Agent'] += 'Chrome/79.0.3945.130 Safari/537.36'
        header['Referer'] = 'http://fundf10.eastmoney.com/jjjz_' + fid + '.html'
        res = requests.get(url=url, headers=header)
        total_number = self.parse_jsonp(res)['TotalCount']
        if total_number > 20:
            url = 'http://api.fund.eastmoney.com/f10/lsjz?callback=jQuery&pageIndex=1&'
            url += 'pageSize={}&startDate={}&endDate={}&fundCode={}'.format(str(total_number), sdate, edate, fid)
            res = requests.get(url=url, headers=header)
        finfo = self.parse_jsonp(res)['Data']['LSJZList']
        for f in finfo:
            result.append((fid, f['FSRQ'], float(f['DWJZ']), float(f['LJJZ'])))
        return result

    def save_fundprice(self, fprice):
        """ 保存基金的净值，可以获取当前净值和累计净值 """
        with open(self.record_path, 'w') as fw:
            for d in sorted(fprice.keys()):
                result = []
                result.append(self.fid)
                result.append(d.strftime('%Y-%m-%d'))
                result.append(str(fprice[d][0]))
                result.append(str(fprice[d][1]))
                line = ','.join(result)
                fw.write(line)
                fw.write('\n')

    def load_fundprice(self, end_date=None):
        result = {}
        if end_date is None:
            n = datetime.datetime.now() - datetime.timedelta(days=1)
            end_date = datetime.datetime(n.year, n.month, n.day, 0, 0, 0)
        max_dt = datetime.datetime(1970, 1, 1)
        try:
            fr = open(self.record_path, 'r')
            for line in fr.readlines():
                arr = line.strip().split(',')
                d = datetime.datetime.strptime(arr[1], '%Y-%m-%d')
                max_dt = d if d > max_dt else max_dt
                result[d] = (float(arr[2]), float(arr[3]))
            fr.close()
            if end_date <= max_dt:
                print('No need fetch new record')
                self.price_list = result
                return result
            else:
                print('Need fetch new record')
                fprice = self.get_fundprice(max_dt, end_date)
                for arr in fprice:
                    d = datetime.datetime.strptime(arr[1], '%Y-%m-%d')
                    result[d] = (float(arr[2]), float(arr[3]))
                self.save_fundprice(result)
                self.price_list = result
                return result
        except Exception as e:
            print(e)
            print('First fetch record')
            fprice = self.get_fundprice()
            for arr in fprice:
                d = datetime.datetime.strptime(arr[1], '%Y-%m-%d')
                result[d] = (float(arr[2]), float(arr[3]))
            self.save_fundprice(result)
            self.price_list = result
            return result

    def get_delta_price(self, end_date=None):
        price = self.load_fundprice(end_date)
        max_dt = max(price.keys())
        delta_price = price[max_dt][1] - price[max_dt][0]
        return delta_price

    def get_gz(self):
        """ 获取当前时间的估值 """
        fid = self.fid
        url = 'http://fundgz.1234567.com.cn/js/' + fid + '.js'
        header = {}
        header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        header['User-Agent'] += ' AppleWebKit/537.36 (KHTML, like Gecko)'
        header['User-Agent'] += ' Chrome/79.0.3945.130 Safari/537.36'
        delta_price = self.get_delta_price()
        try:
            res = requests.get(url=url, headers=header)
            gz_dict = self.parse_jsonp(res)
            dnow = datetime.datetime.now().strftime('%Y-%m-%d')
            if dnow != gz_dict['gztime'].split(' ')[0]:
                return (-1, -1)
            return (float(gz_dict['gsz']), float(gz_dict['gsz']) + delta_price)
        except Exception as e:
            print(e)
            return (-1, -1)

    def get_avg_price(self, end_date, n=50, day=365):
        """ 获取1年的均值。
        """
        total = [0, 0]
        dwjz = []
        ljjz = []
        prices = [
            self.price_list[end_date-datetime.timedelta(days=i)]
            for i in range(1, day)
            if end_date-datetime.timedelta(days=i) in self.price_list]
        for i in prices:
            dwjz.append(i[0])
            ljjz.append(i[1])
            total[0] = total[0] + i[0]
            total[1] = total[1] + i[1]
        if n == 50:
            return (total[0]/len(prices), total[1]/len(prices))
        else:
            dwjz.sort()
            ljjz.sort()
            index = len(dwjz)*n//100-1
            return (dwjz[index], ljjz[index])

    def buy_1day(self, bdt=None, n=80, base=100):
        """ 对指定的某一天进行购买，用于测试，默认买100块钱。
            dt is None，表示今天购买，否则校验是否为交易日。
        """
        dt = bdt
        # 非今天申购，且非交易日，则不予购买。
        if dt is not None and dt not in self.price_list.keys():
            return (0, 0)
        # 如果当天购买，则采用实时最新估值。
        if dt is None:
            dt = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
            (real_price, cur_price) = self.get_gz()
            # 如果取估值有问题，可能是假日，不申购。
            if real_price < 0:
                return (0, 0)
        # 否则采用当天的净值来计算
        else:
            real_price = self.price_list.get(dt)[0]
            cur_price = self.price_list.get(dt)[1]
        avg_price = self.get_avg_price(dt, 50, 60)
        if cur_price > avg_price[1]:
            return (0, 0, (0, 0))
        capital = int(math.ceil((avg_price[1] / cur_price) ** n * base))
        # print(dt, capital)
        # 以累计净值计算购买数量，不准确。
        amount = round(capital/cur_price, 2)
        return (capital, amount, (real_price, cur_price), avg_price)

    def get_buylog_water(self, buy_log):
        """ 长期购买一段时间，计算当前购买的水位线。利用水位线进一步提高购买比例，事实证明没用。
        """
        if len(buy_log) <= 50:
            return (0, len(buy_log))
        else:
            fprice = buy_log[-1]
            sorted_log = sorted(buy_log)
            # print(sorted_log)
            weight = 1.0 * sorted_log.index(fprice) / len(sorted_log)
            return (weight, len(buy_log))

    def get_buylog(self, end_date=None, days=365*5, n=80, base=100):
        buy_log = []
        if end_date is None:
            end_date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time()) - datetime.timedelta(days=1)
        begin_date = end_date - datetime.timedelta(days=days)
        dt = begin_date
        for i in range(days):
            dt = dt + datetime.timedelta(days=1)
            if dt not in self.price_list.keys():
                continue
            res = self.buy_1day(dt, n, base)
            if int(res[0]) > 0:
                buy_log.append(res[0])
        return buy_log

    def buy_longtime(self, begin_date, end_date, n=80, base=100):
        """ 长期购买一段时间，用于测试。默认买100块钱。以最后一天累计净值为基准计算盈利。
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
            res = self.buy_1day(dt, n)
            buy_log.append(res[0])
            b_capital = b_capital + res[0]
            b_amount = b_amount + res[1]
        win = 0 if b_capital == 0 else (
            b_amount*fprice-b_capital) * 100 / b_capital
        win = str(round(win, 2)) + '%'
        avg_price = 0 if b_amount == 0 else (b_capital/b_amount)
        return (round(b_capital, 2), round(b_amount, 2), win, round(avg_price, 4), fprice)

if __name__ == '__main__':

    index_code = '000215'

    ef = EastFund(index_code)
    ef.load_fundprice()
    begin_date = datetime.datetime(2015, 6, 30, 0, 0, 0)
    end_date = datetime.datetime(2020, 6, 30, 0, 0, 0)
    print(ef.buy_longtime(begin_date, end_date, 100))
    today = ef.buy_1day()
    buy_log = ef.get_buylog()
    buy_log.append(today[0])
    print(today)
    print(ef.get_buylog_water(buy_log))
