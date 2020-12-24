# -*- coding:utf-8 -*-

import datetime
from eastfund import EastFund


class Fof(EastFund):
    """ 从东方基金获取基金组合价格，并利用组合成分对组合进行估值。

    Attributes:
        fid 为基金组合代码
    """

    def __init__(self, fid=''):
        EastFund.__init__(self, fid)
        self.xnjz = {}
        if fid == 'njbqg':
            self.funds = [
                {'fid': '001975', 'p': 12},
                {'fid': '005354', 'p': 11},
                {'fid': '009277', 'p': 11},
                {'fid': '450009', 'p': 11},
                {'fid': '163415', 'p': 11},
                {'fid': '180031', 'p': 11},
                {'fid': '206009', 'p': 11},
                {'fid': '001714', 'p': 11},
                {'fid': '160133', 'p': 11},
            ]
        elif fid == 'wwxf':
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
        else:
            self.funds = []

    def load_fundprice(self, end_date=None):
        if self.funds == []:
            return EastFund.load_fundprice(self, end_date)
        else:
            fr = open(self.record_path, 'r')
            for line in fr.readlines():
                arr = line.strip().split(',')
                d = datetime.datetime.strptime(arr[1], '%Y-%m-%d')
                self.price_list[d] = (float(arr[2]), float(arr[2]))
            fr.close()
            jz = {}
            for f in self.funds:
                east = EastFund(f['fid'])
                fprice = east.load_fundprice(end_date)
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
        if self.funds == []:
            return EastFund.get_gz(self)
        else:
            gz = [0, 0]
            for f in self.funds:
                east = EastFund(f['fid'])
                east.load_fundprice()
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


if __name__ == '__main__':
    n = Fof('njbqg')
    n.load_fundprice()
    begin_date = datetime.datetime(2020, 1, 1, 0, 0, 0)
    end_date = datetime.datetime(2020, 9, 30, 0, 0, 0)
