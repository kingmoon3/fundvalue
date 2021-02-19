#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 基金列表
# key: 基金代码
# code: 基金所对应的指数代码
# name：指数名称或者基金组合名称
# vq：指数估值依据，为 pe 或者 pb
# buyfunc: 基金购买策略。n: 幂，扩大基金购买份额。avgdays: avgdays天的均价，用以和基金价格进行比较。

index_list = {
    '100038': {
        'code': 'SH000300', 'name': u'沪深300', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '001548': {
        'code': 'SH000016', 'name': u'上证50', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '090010': {
        'code': 'SH000922', 'name': u'中证红利', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '003765': {
        'code': 'SZ399006', 'name': u'创业板', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '003986': {
        'code': 'SH000905', 'name': u'中证500', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '001594': {
        'code': 'SZ399986', 'name': u'中证银行', 'vq': 'pb',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '160218': {
        'code': 'SZ399393', 'name': u'国证地产', 'vq': 'pb',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '004069': {
        'code': 'SZ399975', 'name': u'全指证券', 'vq': 'pb',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '000248': {
        'code': 'SH000932', 'name': u'主要消费', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '001631': {
        'code': 'SZ399396', 'name': u'食品饮料', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '161725': {
        'code': 'SZ399997', 'name': u'中证白酒', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '000948': {
        'code': 'HKHSI',    'name': u'香港恒生', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '530015': {
        'code': 'SZ399701', 'name': u'深证基本面60', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '001550': {
        'code': 'SH000978', 'name': u'医药100', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '162412': {
        'code': 'SZ399989', 'name': u'中证医疗', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '310398': {
        'code': 'SH000919', 'name': u'300价值', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '213010': {
        'code': 'SH000903', 'name': u'中证100', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '160716': {
        'code': 'SH000925', 'name': u'基本面50', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '501057': {
        'code': 'SZ399417', 'name': u'新能源车', 'vq': 'pe',
        'params': {'buyfunc': 'buy_1day3', 'n':{'price': 4, 'pe':2}, 'avgdays': 365}
    },
    '000215': {
        'code': '', 'name': u'广发趋势', 'vq': '',
        'params': {'buyfunc': 'buy_1day2', 'n':{'price': 100, 'pe':1}, 'avgdays': 60}
    },
    'njbqg': {
        'code': '', 'name': u'牛基宝全股型', 'vq': '',
        'params': {'buyfunc': 'buy_1day1', 'n':{'price': 10, 'pe':1}, 'avgdays': 60}
    },
    'njbcz': {
        'code': '', 'name': u'牛基宝成长型', 'vq': '',
        'params': {'buyfunc': 'buy_1day1', 'n':{'price': 10, 'pe':1}, 'avgdays': 60}
    },
    'wwxf': {
        'code': '', 'name': u'我要稳稳的幸福', 'vq': '',
        'params': {'buyfunc': 'buy_1day1', 'n':{'price': 150, 'pe':1}, 'avgdays': 60}
    },
}
