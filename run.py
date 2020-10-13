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
from njb import Njb
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
        '''.format(res['index_name'], res['pe'], res['pe30'], res['pe50'], res['pe70'],
            res['pe90'], res['fid'], res['price'][0], res['price'][1], res['avg_price'][0],
            res['avg_price'][1], res['buy_water'][0], res['buy_water'][1])
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
        该基金净值排名水位线为：{}，{} 次 <br />
        该基金五年购买水位线为：{}，{} 次 <br />
        <br />
        '''.format(res['fid'], round(res['price'][0], 4), round(res['price'][1], 4),
            round(res['avg_price'][0], 4), round(res['avg_price'][1], 4),
            res['rank'][0], res['rank'][1],
            round(res['buy_water'][0], 4), res['buy_water'][1])
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
    today = fv.buy_1day(base=base)
    buylog = fv.get_buylog()
    buylog.append(today['capital'])
    today['buy_water'] = fv.get_buylog_water(buylog)
    if today['capital'] > 0:
        cmd = 'echo {},{},{} >>~/buy_fund_log.csv'.format(datetime.datetime.now().strftime('%Y-%m-%d'), fv.fid, today['capital'])
        os.system(cmd)
    (sub, con) = create_email(today)
    subject += sub
    content += con

for i in ('000215', '519062'):
    ef = EastFund(i)
    ef.load_fundprice()
    today = ef.buy_1day2(base=base)
    buylog = ef.get_buylog()
    buylog.append(today['capital'])
    today['buy_water'] = ef.get_buylog_water(buylog)
    today['fid'] = i
    (sub, con) = create_1fund_email(today)
    subject += sub
    content += con

for i in ('qg',):
    n = Njb('qg')
    n.init_xnjz()
    today = n.buy_1day(n=10, base=base)
    buy_log = n.get_buylog()
    buy_log.append(today['capital'])
    today['buy_water'] = n.get_buylog_water(buylog)
    today['fid'] = u'牛基宝全股型'
    (sub, con) = create_1fund_email(today)
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
