# -*- coding:utf-8 -*-

from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE, formatdate
from email.header import Header
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib

from mailconfig import *

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

if __name__ == '__main__':
    sendmail(["user@domain.com"], "你好", "html")
