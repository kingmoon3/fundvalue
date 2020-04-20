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

def get_value(fv):
    result = {}
    fid = fv.index_info['index_fids'][0]['fid']
    fv.init_f_info2(fid)
    result['fid'] = fid
    result['index_name'] = fv.index_info['index_name']
    result['w30'] = fv.get_nwater(dt, 30)
    result['w50'] = fv.get_nwater(dt, 50)
    result['w70'] = fv.get_nwater(dt, 70)
    result['yday_pe'] = fv.pbeinfo.get(fv.get_yesterday(dt))
    wprice = list(fv.get_avg_price(fid, dt))
    wprice[0] = round(wprice[0], 4)
    wprice[1] = round(wprice[1], 4)
    result['wprice'] = wprice
    gz_price = fv.get_gz(fid)
    delta_price = fv.get_delta_price(fid)
    result['gz_price'] = [gz_price, round(gz_price+delta_price, 4)]
    (capital, amount) = fv.buy_1day(fid, base=base)
    if capital > 0:
        cmd = 'echo {},{},{} >>~/buy_fund_log.csv'.format(datetime.datetime.now().strftime('%Y-%m-%d'),fid,capital)
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
        <br />
        基金 {} 当前估值为：{}，{} <br />
        该基金的年度平均净值为：{}，{} <br />
        <br />
        '''.format(res['index_name'], res['yday_pe'], res['w30'], res['w50'], res['w70'], res['fid'], res['gz_price'][0], res['gz_price'][1], res['wprice'][0], res['wprice'][1])
    return (subject, content)


base = 100
dt = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())

subject1 = u'【基金申购】'
subject = ''
content = ''

for i in ('hs300', 'zzbank', 'sh50', 'zzbonus', 'hkhs', 'gem', 'zzxf', 'zzwine', 'zz500', 'sz60', 'yy100'):
    fv = FundValue(i)
    fv.init_index_pbeinfo()
    res = get_value(fv)
    (sub, con) = create_email(res)
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
