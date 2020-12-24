#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import datetime
from danjuan import Danjuan
from fof import Fof
from indexs import index_list


class Policy(Fof):
    """ 从东方基金获取基金价格，从蛋卷获取指数估值，并加载基金净值和基金购买日志。
    """

    def __init__(self, fid):
        Fof.__init__(self, fid)
        self.buylog = []
        self.index = index_list[fid]

    def init_index_pbe(self, time='all'):
        """ 获取pe/pb的通用接口，time可以为1y, 3y """
        self.trade_days = set(self.price_list.keys())
        if self.index['code'] == '':
            return None
        self.dj = Danjuan(self.index['code'], self.index['vq'])
        self.index_pbe = self.dj.init_pbe(time)
        self.trade_days = set(self.index_pbe.keys()) & self.trade_days
        return self.index_pbe

    def get_weight_pe(self, cur_pe, pe30, n=2):
        """ 获取 pe 权重，以30水位线做基准，超过30水位线则不买。否则越低越买。
            经回测上证50，此参数对购买影响不大，故取n=2
        """
        if cur_pe > pe30 or cur_pe <= 0:
            return 0
        # 加强 pe 的权重，越低越买
        return (pe30/cur_pe) ** n

    def get_weight_price(self, cur_price, avg_price, n=4):
        """ 获取 price 权重，实际采用前365天的平均价格。
            超过该价格，则不买，否则多买。
        """
        if cur_price > avg_price or cur_price <= 0:
            return 0
        # 加强 price 的权重，越低越买
        return (avg_price/cur_price) ** n

    def get_dt_price(self, dt, avgdays):
        """ 获取基金指定日期的价格
            dt 为 None，返回当天估值。
        """
        # 非今天申购，且非交易日，则不予购买。
        res = {}
        if dt is not None and dt not in self.price_list.keys():
            res['price'] = (0, 0)
            res['avg_price'] = (0, 0)
            return res
        # 如果当天购买，则采用实时最新估值。
        if dt is None:
            dt = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
            res['price'] = self.get_gz()
            # 如果取估值有问题，可能是假日，不申购。
            if res['price'][0] * 10 <= 0:
                res['price'] = (0, 0)
                res['avg_price'] = (0, 0)
                return res
        # 否则采用当天的净值来计算
        else:
            res['price'] = self.price_list.get(dt)
        res['avg_price'] = self.get_avg_price(dt, 50, avgdays)
        return res

    def fetch_price_info(self, dt, avgdays):
        """ 获取基金价格在 avgdays 中的排名
            dt 为 None，使用当天估值。
        """
        res = {
            'capital': 0,
            'amount': 0,
        }
        price_info = self.get_dt_price(dt, avgdays)
        res.update(price_info)
        if dt is None:
            dt = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
        price60 = []
        for i in range(1, avgdays):
            d = dt - datetime.timedelta(days=i)
            if d in self.price_list:
                price60.append(self.price_list.get(d)[1])
        price60.append(res['price'][1])
        price60.sort(reverse=True)
        res['rank'] = (round(1 - (price60.index(res['price'][1]) + 1) * 1.0 / len(price60), 4), len(price60))
        res['price60'] = price60
        return res

    def save_buylog(self, newlog):
        """ 保存新购买的日志，用以衡量本次购买的水位线。
        """
        buylog = {}
        try:
            fr = open(self.buylog_path, 'r')
            for line in fr.readlines():
                arr = line.strip().split(',')
                d = datetime.datetime.strptime(arr[1], '%Y-%m-%d')
                buylog[d] = {}
                buylog[d]['capital'] = int(arr[2])
                buylog[d]['amount'] = float(arr[3])
            fr.close()
            buylog.update(newlog)
            with open(self.buylog_path, 'w') as fw:
                for d in sorted(buylog.keys()):
                    result = []
                    result.append(self.fid)
                    result.append(d.strftime('%Y-%m-%d'))
                    result.append(str(buylog[d]['capital']))
                    result.append(str(buylog[d]['amount']))
                    line = ','.join(result)
                    fw.write(line)
                    fw.write('\n')
            return buylog
        except Exception:
            print('First create buylog')
            with open(self.buylog_path, 'w') as fw:
                for d in sorted(newlog.keys()):
                    result = []
                    result.append(self.fid)
                    result.append(d.strftime('%Y-%m-%d'))
                    result.append(str(newlog[d]['capital']))
                    result.append(str(newlog[d]['amount']))
                    line = ','.join(result)
                    fw.write(line)
                    fw.write('\n')
            return newlog

    def load_buylog(self, buyfunc, avgdays, begin_date, end_date, n, days=365*5, base=100):
        """ 加载 5 年购买的日志，用以衡量本次购买的水位线。
        """
        buylog = {}
        if end_date is None:
            now = datetime.datetime.now() - datetime.timedelta(days=1)
            end_date = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
        if begin_date is None:
            begin_date = end_date - datetime.timedelta(days=days)
        max_dt = datetime.datetime(1970, 1, 1)
        try:
            fr = open(self.buylog_path, 'r')
            for line in fr.readlines():
                arr = line.strip().split(',')
                d = datetime.datetime.strptime(arr[1], '%Y-%m-%d')
                max_dt = d if d > max_dt else max_dt
                buylog[d] = {}
                buylog[d]['capital'] = int(arr[2])
                buylog[d]['amount'] = float(arr[3])
            fr.close()
            if end_date <= max_dt:
                self.buylog = buylog
                return buylog
            else:
                print('Need fetch new buylog')
                newlog = {}
                for i in range((end_date - max_dt).days + 1):
                    dt = max_dt + datetime.timedelta(days=i)
                    res = getattr(self, buyfunc)(dt, avgdays, n, base)
                    newlog[dt] = {
                        'capital': res['capital'],
                        'amount': res['amount']
                    }
                buylog = self.save_buylog(newlog)
                self.buylog = buylog
                return buylog
        except Exception:
            print('First fetch buylog')
            newlog = {}
            for i in range((end_date - begin_date).days + 1):
                dt = begin_date + datetime.timedelta(days=i)
                if dt not in self.price_list.keys():
                    newlog[dt] = {'capital': 0, 'amount': 0}
                else:
                    res = getattr(self, buyfunc)(dt, avgdays, n, base)
                    newlog[dt] = {'capital': res['capital'], 'amount': res['amount']}
            self.buylog = self.save_buylog(newlog)
            return self.buylog

    def fetch_buylog_list(self, end_date=None, days=365*5):
        """ 长期购买一段时间，返回购买列表。
        """
        buylog = self.buylog
        buylist = []
        if end_date is None:
            end_date = datetime.datetime.combine(
                datetime.date.today(), datetime.datetime.min.time()) - datetime.timedelta(days=1)
        begin_date = end_date - datetime.timedelta(days=days)
        dt = begin_date
        for i in range(days + 1):
            dt = begin_date + datetime.timedelta(days=i)
            if dt not in self.trade_days or dt not in buylog:
                continue
            if buylog[dt]['capital'] > 0:
                buylist.append(buylog[dt]['capital'])
        return buylist

    def fetch_buylog_water(self, buylog_list):
        """ 长期购买一段时间，计算当前购买的水位线。利用水位线进一步提高购买比例，事实证明没用。
        """
        if len(buylog_list) <= 20:
            return (0, len(buylog_list))
        else:
            fprice = buylog_list[-1]
            if fprice == 0:
                return (0, len(buylog_list))
            sorted_log = sorted(buylog_list)
            weight = 1.0 * sorted_log.index(fprice) / len(sorted_log)
            return (round(weight, 4), len(buylog_list))

    def buy_1day1(self, dt, avgdays, n, base=100):
        """ 对指定的某一天进行购买，用于测试，默认买100块钱。
            n_price 为幂。本次主要考虑基金净值与60天均值的比，未考虑净值在60天的排位。
            n_pe 为幂。本策略中无用。
            dt is None，表示今天购买，否则校验是否为交易日。
        """
        res = self.fetch_price_info(dt, avgdays)
        cur_price = res['price'][1]
        if cur_price > res['avg_price'][1]:
            return res
        if cur_price > 0:
            res['capital'] = int(math.ceil((res['avg_price'][1] / cur_price) ** n['price'] * base))
            res['amount'] = round(res['capital'] / cur_price, 2)
        return res

    def buy_1day2(self, dt, avgdays, n, base=100):
        """ 对指定的某一天进行购买，用于测试，默认买100块钱。
            主要考虑净值在60天的排位，未考虑价格。
            n_price 为幂。本策略中无用。
            n_pe 为幂。本策略中无用。
            对于 000215 这种波动不大的基金，考虑当前排位收益更高。
            dt is None，表示今天购买，否则校验是否为交易日。
        """
        res = self.fetch_price_info(dt, avgdays)
        (cur_price, price60) = (res['price'][1], res['price60'])
        weight = ((price60.index(cur_price) + 1) * 1.0 / len(price60)) / 0.5
        if int(weight) < 1:
            weight = 0
        if cur_price > 0:
            res['capital'] = int(math.ceil(base * weight ** 2))
            res['amount'] = round(res['capital'] / cur_price, 2)
        return res

    def buy_1day3(self, dt, avgdays, n, base=100):
        """ 对指定的某一天进行购买，用于测试，默认买100块钱。
            dt is None，表示今天购买，否则校验是否为交易日。
        """
        res = self.fetch_price_info(dt, avgdays)
        cur_price = res['price'][1]

        if dt is None:
            dt = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
        # 计算 pe 权重，由于 pe 无法预估，因此采用前一天的 pe 计算
        # 考虑到波动周期性，pe 标准改用最近5年的30水位线（好买评估依据），也可以采用10年，保证指数经历一轮牛熊（蛋卷评估依据）
        # 不宜采用1-2年方案，受行业周期影响较大。
        res['pe30'] = self.dj.get_pbe_nwater(dt, 30, 365*5)
        res['pe50'] = self.dj.get_pbe_nwater(dt, 50, 365*5)
        res['pe70'] = self.dj.get_pbe_nwater(dt, 70, 365*5)
        res['pe90'] = self.dj.get_pbe_nwater(dt, 90, 365*5)
        for i in range(30):
            res['pe'] = self.index_pbe.get(dt - datetime.timedelta(days=i), -1)
            if res['pe'] > 0:
                break
        weight_pe = self.get_weight_pe(res['pe'], res['pe30'], n['pe'])
        # 为更安全，price 标准采用最近1年的均值，时间过长，可能无法申购。也可以考虑采用最近1年，2年均值的最小值。
        weight_price = self.get_weight_price(cur_price, res['avg_price'][1], n['price'])
        weight = weight_pe * weight_price

        res['capital'] = int(math.ceil(base * weight))
        # 以累计净值计算购买数量，不准确。
        if cur_price > 0:
            res['amount'] = round(res['capital'] / cur_price, 2)
        return res

    def buy_longtime(self, buyfunc, avgdays, begin_date, end_date, n, base=100):
        """ 长期购买一段时间，用于测试。默认买100块钱。以最后一天累计净值为基准计算盈利。
        """
        buylog = self.load_buylog(buyfunc, avgdays, begin_date, end_date, n, 365*5, base)
        b_capital = 0
        b_amount = 0
        # 获取最高盈利点
        maxg = [0, begin_date]
        for i in range((end_date - begin_date).days + 1):
            dt = begin_date + datetime.timedelta(days=i)
            if dt not in self.trade_days:
                continue
            # 按购买金额的水位线加权购买，效果略有提升。
            # 可参考水位线进行一次性投入，不宜作为长期购买指标。
            # buylist = self.get_buylog(dt)
            # buylist.append(buylog[dt]['capital'])
            # buyw = int(self.get_buylog_water(buylist)[0] * 100)
            # if buyw <= 40:
            #     weight = 0
            # elif 40 < buyw and buyw < 70:
            #     weight = 2
            # elif buyw >= 70:
            #     weight = 4
            weight = 1
            b_capital = b_capital + buylog[dt]['capital'] * weight
            b_amount = b_amount + buylog[dt]['amount'] * weight
            fprice = float(self.price_list[dt][1])
            if b_capital > 0:
                g = round((fprice * b_amount - b_capital) / b_capital * 100, 2)
                if g > maxg[0]:
                    maxg[0] = g
                    maxg[1] = dt.strftime('%Y-%m-%d')
        if b_capital == 0:
            win = 0
        else:
            win = (b_amount * fprice - b_capital) * 100 / b_capital
        win = str(round(win, 2)) + '%'
        avg_price = 0 if b_amount == 0 else (b_capital / b_amount)
        return (round(b_capital, 2), round(b_amount, 2), maxg, win, round(avg_price, 4))


if __name__ == '__main__':
    index_code = 'njbqg'
    p = Policy(index_code)
    p.load_fundprice()
    p.init_index_pbe()
    params = p.index['params']
    begin_date = datetime.datetime(2020, 1, 1, 0, 0, 0)
    end_date = datetime.datetime(2020, 9, 30, 0, 0, 0)
    print(p.buy_longtime(params['buyfunc'], params['avgdays'], begin_date, end_date, params['n'], 100))
