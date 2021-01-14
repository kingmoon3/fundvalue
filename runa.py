# -*- coding:utf-8 -*-

from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE, formatdate
from email.header import Header
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
import datetime
import os

from policy import Policy
from indexs import index_list
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
        # att = MIMEText(open(att, 'rb').read(), 'base64', 'utf-8')
        msg_att = MIMEApplication(open(att, 'rb').read())
        # msg_att["Content-Type"] = 'application/octet-stream'
        # msg_att["Content-Disposition"] = 'attachment; filename="%s"' % att_name
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
        print(u"邮件发送失败，请检查邮件配置:{}".format(ex))
        return False


def create_email(values):
    res = values
    if int(res['capital']) == 0:
        subject = ''
        content = u'''<h4> {}指数 </h4>'''.format(res['name'])
    else:
        subject = u' {} 申购 {} 元，'.format(res['fid'], res['capital'])
        content = u'''<h4> {}指数（{} 申购 {} 元）</h4>'''.format(res['name'], res['fid'], res['capital'])
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
        '''.format(
            res['name'], res['pe'],
            res['pe30'], res['pe50'], res['pe70'], res['pe90'],
            res['fid'], res['price'][0], res['price'][1],
            round(res['avg_price'][0], 4), round(res['avg_price'][1], 4),
            res['buy_water'][0], res['buy_water'][1])
    return (subject, content)


def create_1fund_email(values):
    res = values
    if int(res['capital']) == 0:
        subject = ''
        content = u'''<h4> {} </h4>'''.format(res['name'])
    else:
        subject = u' {} 申购 {} 元，'.format(res['name'], res['capital'])
        content = u'''<h4>{} 申购 {} 元</h4>'''.format(res['name'], res['capital'])
    content = content + u'''基金 {} 当前估值为：{}，{} <br />
        该基金的年度平均净值为：{}，{} <br />
        该基金净值排名水位线为：{}，{} 次 <br />
        该基金五年购买水位线为：{}，{} 次 <br />
        <br />
        '''.format(
            res['fid'], round(res['price'][0], 4), round(res['price'][1], 4),
            round(res['avg_price'][0], 4), round(res['avg_price'][1], 4),
            res['rank'][0], res['rank'][1],
            round(res['buy_water'][0], 4), res['buy_water'][1])
    return (subject, content)


base = 100
dt = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())

subject1 = u'【基金申购】'
subject = ''
content = ''

for index_code in (
        '100038', '001594', '001548', '530015', '003986', '000948',
        '003765', '090010', '004069', '000248', '001631', '161725',
        '001550', '162412', '000215', 'njbqg', 'wwxf'):
    p = Policy(index_code)
    p.load_fundprice()
    p.init_index_pbe()
    params = p.index['params']
    today = getattr(p, params['buyfunc'])(None, params['avgdays'], params['n'], 100)
    today['name'] = index_list[index_code]['name']
    today['fid'] = index_code
    p.load_buylog(params['buyfunc'], params['avgdays'], None, None, params['n'])
    today['buy_water'] = p.fetch_buylog_water(today['capital'], None, days=365*5)
    if today['capital'] > 0:
        cmd = 'echo {},{},{} >>~/buy_fund_log.csv'.format(
            datetime.datetime.now().strftime('%Y-%m-%d'), index_code, today['capital'])
        os.system(cmd)
    if p.index['code'] == '':
        (sub, con) = create_1fund_email(today)
    else:
        (sub, con) = create_email(today)
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
