# -*- coding:utf-8 -*-

import requests
import datetime
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
        self.buylog_path = './buylog.' + str(fid)

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
        except Exception:
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
        # 基金分红
        delta_price = price[max_dt][1] - price[max_dt][0]
        flag = True
        # 基金分拆
        if self.fid in ('160218', '161725', '162412'):
            delta_price = price[max_dt][1] / price[max_dt][0]
            flag = False
        return (delta_price, flag)

    def get_gz(self):
        """ 获取当前时间的估值 """
        fid = self.fid
        url = 'http://fundgz.1234567.com.cn/js/' + fid + '.js'
        header = {}
        header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        header['User-Agent'] += ' AppleWebKit/537.36 (KHTML, like Gecko)'
        header['User-Agent'] += ' Chrome/79.0.3945.130 Safari/537.36'
        (delta_price, flag) = self.get_delta_price()
        try:
            res = requests.get(url=url, headers=header)
            gz_dict = self.parse_jsonp(res)
            dnow = datetime.datetime.now().strftime('%Y-%m-%d')
            if dnow != gz_dict['gztime'].split(' ')[0]:
                return (0, 0)
            if flag is True:
                return (float(gz_dict['gsz']), float(gz_dict['gsz']) + delta_price)
            else:
                return (float(gz_dict['gsz']), float(gz_dict['gsz']) * delta_price)
        except Exception as e:
            print(e)
            return (0, 0)

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
        if prices == []:
            return (0, 0)
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


if __name__ == '__main__':

    index_code = '000215'
    # index_code = '519062'
    ef = EastFund(index_code)
    ef.load_fundprice()
