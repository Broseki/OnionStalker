from onion_py.manager import Manager
from onion_py.caching import OnionSimpleCache
import pymysql
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

manager = Manager(OnionSimpleCache())

sqlhost = '127.0.0.1'
sqluser = 'onionstalker'
sqlpass = 'AqfJL7WSmuP43Acd'
sqldb = 'onionstalker'
sqlcharset = 'utf8mb4'

mail_username = 'torserveralertservice@gmail.com'

print 'Fetching'
details = manager.query('details')
print 'Parsing'

def getnickname(fingerprint):
    x = 0
    while True:
        if details.relays[x].fingerprint == fingerprint:
            return details.relays[x].nickname
        else:
            x += 1

def running(fingerprint):
    x = 0
    try:
        while True:
            if details.relays[x].fingerprint == fingerprint:
                return details.relays[x].running
            else:
                x += 1
    except:
        return "na"

def getbandwidth(fingerprint):
    x = 0
    while True:
        if details.relays[x].fingerprint == fingerprint:
            return details.relays[x].bandwidth
        else:
            x += 1


connection = pymysql.connect(host=sqlhost,
                                     user=sqluser,
                                     password=sqlpass,
                                     db=sqldb,
                                     charset=sqlcharset,
                                     cursorclass=pymysql.cursors.DictCursor)
c = connection.cursor(pymysql.cursors.DictCursor)
c.execute("SELECT * FROM relays WHERE monitorFailure=TRUE AND confirmed=TRUE;")
checkList = c.fetchall()
c.close()
connection.close()
print checkList
for relay in checkList:
    status = running(relay['fingerprint'])
    ident = relay['uuid']
    if status == True:
        if relay['failedLastCheck'] == True:
            connection = pymysql.connect(host=sqlhost,
                                         user=sqluser,
                                         password=sqlpass,
                                         db=sqldb,
                                         charset=sqlcharset,
                                         cursorclass=pymysql.cursors.DictCursor)
            c = connection.cursor(pymysql.cursors.DictCursor)
            c.execute("UPDATE relays SET failedLastCheck=FALSE WHERE uuid=%s;", relay['uuid'])
            connection.commit()
            c.close()
            connection.close()


            torRelayNickname = getnickname(relay['fingerprint'])

            msg = MIMEMultipart('alternative')
            msg['Subject'] = "OnionStalk[er]: " + torRelayNickname + " is online!"
            msg['From'] = mail_username
            msg['To'] = relay['email']
            msgBody = MIMEText(
            "Hello,<br><br>This is an automated message from the OnionStalk[er] service.<br><br>The relay " + torRelayNickname + " is back online!<br><br>To update your preferences please visit https://torstatus.cavefox.net/api/update/" + ident + ".<br><br>To cancel these alerts please visit https://torstatus.cavefox.net/api/unsubscribe/" + ident + ".<br><br>Sincerely,<br>The OnionStalk[er] System",'html')
            msg.attach(msgBody)
            server = smtplib.SMTP('127.0.0.1')
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()
        else:
            pass

    elif status == False:
        if relay['failedLastCheck'] == True:
            pass
        else:
            connection = pymysql.connect(host=sqlhost,
                                         user=sqluser,
                                         password=sqlpass,
                                         db=sqldb,
                                         charset=sqlcharset,
                                         cursorclass=pymysql.cursors.DictCursor)
            c = connection.cursor(pymysql.cursors.DictCursor)

            c.execute("UPDATE relays SET failedLastCheck=1 WHERE uuid=%s;", relay['uuid'])
            connection.commit()
            c.close()
            connection.close()

            torRelayNickname = getnickname(relay['fingerprint'])

            msg = MIMEMultipart('alternative')
            msg['Subject'] = "OnionStalk[er]: " + torRelayNickname + " is offline!"
            msg['From'] = mail_username
            msg['To'] = relay['email']
            msgBody = MIMEText("Hello,<br><br>This is an automated message from the OnionStalk[er] service.<br><br>The relay " + torRelayNickname + " is currently offline!<br><br>To update your preferences please visit https://torstatus.cavefox.net/api/update/" + ident + ".<br><br>To cancel these alerts please visit https://torstatus.cavefox.net/api/unsubscribe/" + ident + ".<br><br>Sincerely,<br>The OnionStalk[er] System", 'html')
            msg.attach(msgBody)
            server = smtplib.SMTP('127.0.0.1')
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()
    else:
        pass

connection = pymysql.connect(host=sqlhost,
                            user=sqluser,
                            password=sqlpass,
                            db=sqldb,
                            charset=sqlcharset,
                            cursorclass=pymysql.cursors.DictCursor)
c = connection.cursor(pymysql.cursors.DictCursor)
c.execute("SELECT * FROM relays WHERE minimumBandwidth > 0 AND confirmed=TRUE;")
checkList = c.fetchall()
c.close()
connection.close()
print checkList
for relay in checkList:
    ident = relay['uuid']
    print running(relay['fingerprint'])
    if running(relay['fingerprint']) == True:
        currentBandwidth = int(getbandwidth(relay['fingerprint'])[2])
        if (currentBandwidth < relay['minimumBandwidth'] and relay['hadLowBandwidthAtLastCheck'] == False):
            connection = pymysql.connect(host=sqlhost,
                                         user=sqluser,
                                         password=sqlpass,
                                         db=sqldb,
                                         charset=sqlcharset,
                                         cursorclass=pymysql.cursors.DictCursor)
            c = connection.cursor(pymysql.cursors.DictCursor)

            c.execute("UPDATE relays SET hadLowBandwidthAtLastCheck=TRUE WHERE uuid=%s;", relay['uuid'])
            connection.commit()
            c.close()
            connection.close()
            torRelayNickname = getnickname(relay['fingerprint'])

            msg = MIMEMultipart('alternative')
            msg['Subject'] = "OnionStalk[er]: " + torRelayNickname + " has low bandwidth!"
            msg['From'] = mail_username
            msg['To'] = relay['email']
            msgBody = MIMEText("Hello,<br><br>This is an automated message from the OnionStalk[er] service.<br><br>The relay " + torRelayNickname + " is currently operating at " + str(currentBandwidth/1024.0) + "KB/s!<br><br>To update your preferences please visit https://torstatus.cavefox.net/api/update/" + ident + ".<br><br>To cancel these alerts please visit https://torstatus.cavefox.net/api/unsubscribe/" + ident + ".<br><br>Sincerely,<br>The OnionStalk[er] System", 'html')
            msg.attach(msgBody)
            server = smtplib.SMTP('127.0.0.1')
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()
        elif currentBandwidth >= relay['minimumBandwidth'] and relay['hadLowBandwidthAtLastCheck'] == True:
            connection = pymysql.connect(host=sqlhost,
                                         user=sqluser,
                                         password=sqlpass,
                                         db=sqldb,
                                         charset=sqlcharset,
                                         cursorclass=pymysql.cursors.DictCursor)
            c = connection.cursor(pymysql.cursors.DictCursor)

            c.execute("UPDATE relays SET hadLowBandwidthAtLastCheck=FALSE WHERE uuid=%s;", relay['uuid'])
            connection.commit()
            c.close()
            connection.close()
            torRelayNickname = getnickname(relay['fingerprint'])

            msg = MIMEMultipart('alternative')
            msg['Subject'] = "OnionStalk[er]: A normal bandwidth amount has been restored to " + torRelayNickname + "!"
            msg['From'] = mail_username
            msg['To'] = relay['email']
            msgBody = MIMEText(
            "Hello,<br><br>This is an automated message from the OnionStalk[er] service.<br><br>The relay " + torRelayNickname + " is currently operating at " + str(currentBandwidth/1024.0) + "KB/s!<br><br>To update your preferences please visit https://torstatus.cavefox.net/api/update/" + ident + ".<br><br>To cancel these alerts please visit https://torstatus.cavefox.net/api/unsubscribe/" + ident + ".<br><br>Sincerely,<br>The OnionStalk[er] System",
            'html')
            msg.attach(msgBody)
            server = smtplib.SMTP('127.0.0.1')
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()
    else:
        pass
