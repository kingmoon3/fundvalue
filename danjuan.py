# -*- coding:utf-8 -*-

import requests
import datetime
import json


class Danjuan():
    """ 从蛋卷基金获取指数估值。

    Attributes:
        index_code: 指数编码
        index_vq: 指数估值依据，index_vq 为 pb 或者 pe
        pbe: 字典，保存指数的历史pe/pb，{datetime: pe}
    """

    def __init__(self, index_code, index_vq):
        """ 初始化数据结构 """
        self.index_code = index_code
        self.index_vq = index_vq
        self.pbe = {}

    def init_pbe(self, time='all'):
        """ 获取pe/pb的通用接口，time可以为1y, 3y """
        pedict = {}
        header = {}
        header['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        header['User-Agent'] += 'AppleWebKit/537.36 (KHTML, like Gecko) '
        header['User-Agent'] += 'Chrome/79.0.3945.130 Safari/537.36'
        url = 'https://danjuanapp.com/djapi/'
        url += 'index_eva/{}_history/{}?day={}'.format(
            self.index_vq,
            self.index_code,
            time)
        res = requests.get(url=url, headers=header)
        pbe_name = 'index_eva_' + self.index_vq + '_growths'
        for pe in json.loads(res.content)['data'][pbe_name]:
            pe['ts'] = datetime.datetime.fromtimestamp(pe['ts'] // 1000)
            pedict.setdefault(pe['ts'], pe[self.index_vq])
        min_tradeday = min(pedict.keys())
        max_tradeday = max(pedict.keys())
        for i in range((max_tradeday - min_tradeday).days):
            d = min_tradeday + datetime.timedelta(days=i)
            if d not in pedict.keys():
                yesterday = d - datetime.timedelta(days=1)
                pedict[d] = pedict[yesterday]
        self.pbe = pedict
        return pedict

    def get_pbe_nwater(self, end_date, n=30, day=365*5):
        """ 获取指定日期的水位线，默认向前搜索5年
        """
        if end_date is None:
            end_date = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
            end_date = end_date - datetime.timedelta(days=1)
        pe_value = [
            self.pbe.get(end_date-datetime.timedelta(days=i), -1)
            for i in range(0, day)]
        while -1 in pe_value:
            pe_value.remove(-1)
        pe_value.sort()
        index = len(pe_value) * n // 100
        return pe_value[index]


if __name__ == '__main__':

    index_code = 'SH000300'

    fv = Danjuan(index_code, 'pe')
    fv.init_pbe()
    n = datetime.datetime.now()
    print(fv.get_pbe_nwater(datetime.datetime(n.year, n.month, n.day, 0, 0, 0)))
