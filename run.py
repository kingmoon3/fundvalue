# -*- coding:utf-8 -*-

from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE, formatdate
from email.header import Header
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
import datetime
import os

from fundvalue import FundValue
from eastfund import EastFund
from mailconfig import smtphost, userfrom, userpassword, userto

def sendmail(receiver, subject, html, att=None, att_name=None):
    if att is None:
        msg = MIMEMultipart('alternative')
    else:
        msg = MIMEMultipart('mixed')
    # 解决邮件弹出通知框乱码问题
    if not isinstance(subject, str):
        subject = subject.encode('utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
    else:
        msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = userfrom
    msg['To'] = COMMASPACE.join(receiver)
    msg['Date'] = formatdate(localtime=True)
    # Create the body of the message (a plain-text and an HTML version).
    part2 = MIMEText(html, 'html', 'utf-8')
    msg.attach(part2)
    # 构造附件
    if att is not None:
        #att = MIMEText(open(att, 'rb').read(), 'base64', 'utf-8')
        msg_att = MIMEApplication(open(att, 'rb').read())
        #msg_att["Content-Type"] = 'application/octet-stream'
        #msg_att["Content-Disposition"] = 'attachment; filename="%s"' % att_name
        msg_att.add_header('Content-Disposition', 'attachment', filename=att_name)
        msg.attach(msg_att)
    try:
        smtp = smtplib.SMTP()
        smtp.connect(host=smtphost)
        smtp.login(userfrom, userpassword)
        smtp.sendmail(userfrom, receiver, msg.as_string())
        smtp.quit()
        return True
    except smtplib.SMTPException as ex:
        logging.error(u"邮件发送失败，请检查邮件配置:{}".format(ex))
        return False

def get_value(fv, base):
    result = {}
    res1day = fv.buy_1day(base=base)
    result['fid'] = res1day['fid']
    result['index_name'] = res1day['index_name']
    result['w30'] = res1day['pe30']
    result['w50'] = res1day['pe50']
    result['w70'] = res1day['pe70']
    result['w90'] = res1day['pe90']
    result['yday_pe'] = res1day['pe']
    result['wprice'] = res1day['avg_price']
    (capital, amount) = (res1day['capital'], res1day['amount'])
    result['buy_water'] = 0
    result['buy_water_length'] = 0
    if capital > 0:
        buylist = fv.get_buylog()
        buylist.append(capital)
        result['buy_water'] = fv.get_buylog_water(buylist)[0]
        result['buy_water_length'] = fv.get_buylog_water(buylist)[1]
    result['gz_price'] = res1day['price']
    if capital > 0:
        cmd = 'echo {},{},{} >>~/buy_fund_log.csv'.format(datetime.datetime.now().strftime('%Y-%m-%d'), fv.fid, capital)
        os.system(cmd)
    result['capital'] = capital
    return result

def create_email(values):
    res = values
    if int(res['capital']) == 0:
        subject = ''
        content = u'''<h4> {}指数 </h4>'''.format(res['index_name'])
    else:
        subject = u' {} 申购 {} 元，'.format(res['fid'], res['capital'])
        content = u'''<h4> {}指数（{} 申购 {} 元）</h4>'''.format(res['index_name'], res['fid'], res['capital'])
    content = content + u'''昨日{}的 pe 为：{} <br /><br />
        pe 30分水位线为：{} <br />
        pe 50分水位线为：{} <br />
        pe 70分水位线为：{} <br />
        pe 90分水位线为：{} <br />
        <br />
        基金 {} 当前估值为：{}，{} <br />
        该基金的年度平均净值为：{}，{} <br />
        该基金五年购买水位线为：{}，{} 次<br />
        <br />
        '''.format(res['index_name'], res['yday_pe'], res['w30'], res['w50'], res['w70'], res['w90'], res['fid'], res['gz_price'][0], res['gz_price'][1], res['wprice'][0], res['wprice'][1], res['buy_water'], res['buy_water_length'])
    return (subject, content)

def create_1fund_email(values):
    res = values
    if int(res['capital']) == 0:
        subject = ''
        content = u'''<h4> {} </h4>'''.format(res['fid'])
    else:
        subject = u' {} 申购 {} 元，'.format(res['fid'], res['capital'])
        content = u'''<h4>{} 申购 {} 元</h4>'''.format(res['fid'], res['capital'])
    content = content + u'''基金 {} 当前估值为：{}，{} <br />
        该基金的年度平均净值为：{}，{} <br />
        该基金五年购买水位线为：{}，{} 次 <br />
        <br />
        '''.format(res['fid'], round(res['gz_price'][0], 4), round(res['gz_price'][1], 4),round(res['wprice'][0], 4), round(res['wprice'][1], 4), round(res['water'], 4), res['water_length'])
    return (subject, content)


base = 100
dt = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())

subject1 = u'【基金申购】'
subject = ''
content = ''

for i in ('hs300', 'zzbank', 'sh50', 'zzbonus', 'hkhs', 'gem', 'zzxf', 'zzwine', 'zz500', 'sz60', 'yy100', 'zzyl'):
    fv = FundValue(i)
    fv.init_index_pbe()
    fv.init_fund_jz()
    res = get_value(fv, base)
    (sub, con) = create_email(res)
    subject += sub
    content += con

for i in ('000215', '519062'):
    res = {}
    res['fid'] = i
    ef = EastFund(i)
    ef.load_fundprice()
    today = ef.buy_1day()
    buy_log = ef.get_buylog()
    buy_log.append(today[0])
    res['capital'] = today[0]
    res['amount'] = today[1]
    res['gz_price'] = today[2]
    res['wprice'] = today[3]
    res['water'] = ef.get_buylog_water(buy_log)[0]
    res['water_length'] = ef.get_buylog_water(buy_log)[1]
    (sub, con) = create_1fund_email(res)
    subject += sub
    content += con

if subject == '':
    subject = u'无需申购任何基金'
else:
    slist = list(subject)
    slist.pop(-1)
    subject = ''.join(slist)

subject = subject1 + subject
sendmail(userto, subject, content)
