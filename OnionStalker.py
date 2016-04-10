'''
OnionStalker - Tor Relay Monitoring Service

This service will allow Tor relay operators to set up alerts similar to the now discontinued Tor Weather service.

This program is released into the public domain!
'''

import pymysql

from flask import render_template   # Used to render HTML pages
from flask import Flask   # Used to render pages and deal with requests
from flask import request   # Used to process POST requests
from flask import redirect # Used to handle redirecting
from flask import send_from_directory   # Used to send files from directories

import uuid    # Used to generate user IDs and confirmation codes
import onionQuery   # Used to get the status of Tor relays

from validate_email import validate_email   # Used to validate email address of registering users

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


app = Flask(__name__)   # Defines Flask Application

sqlhost = '127.0.0.1'
sqluser = 'onionstalker'
sqlpass = 'SQL Password'
sqldb = 'onionstalker'
sqlcharset = 'utf8mb4'


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/register', methods=['GET'])
def registerGet():
    return render_template("register.html")


@app.route('/register', methods=['POST'])
def registerPost():
    fingerprint = request.form["fingerprint"]
    email = request.form["email"]
    if not validate_email(email):
        return render_template('register.html', message='invalidEmail')
    lowbandwidth = request.form["lowbandwidth"]
    if lowbandwidth == '':
        lowbandwidth = 0
    try:
        downmonitor = request.form["downmonitor"]
        downmonitor = True

    except:
        downmonitor = False

    try:
        lowbandwidth = float(lowbandwidth) * 1024.0
    except:
        return render_template('register.html', message='invalidBandwidth')

    if onionQuery.running(fingerprint) == 'na':
        return render_template('register.html', message='relayNotFound')

    connection = pymysql.connect(host=sqlhost,
                                     user=sqluser,
                                     password=sqlpass,
                                     db=sqldb,
                                     charset=sqlcharset,
                                     cursorclass=pymysql.cursors.DictCursor)


    c = connection.cursor(pymysql.cursors.DictCursor)

    c.execute("SELECT * FROM relays WHERE fingerprint = %s AND email = %s", (fingerprint, str(email).lower()))
    results = c.fetchone()

    if not results == None:
        c.close()
        connection.close()
        return render_template('register.html', message='alreadyRegistered')

    id = str(uuid.uuid4())
    c.execute("INSERT INTO relays VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", (id, fingerprint, str(email).lower(), False, lowbandwidth, downmonitor, False, False))
    connection.commit()
    c.close()
    connection.close()
    torRelayNickname = onionQuery.getnickname(fingerprint)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "OnionStalk[er]: Registration Confirmation"
    msg['From'] = 'torstatus@cavefox.net'
    msg['To'] = email
    msgBody = MIMEText("Hello,<br><br>This is an automated message from the OnionStalk[er] service.<br><br>You requested alerts on the Tor relay " + torRelayNickname + ".<br><br> To confirm this request please visit https://torstatus.cavefox.net/api/confirm/" + id + ".<br><br>If you did not request this you can safely disregard this message.<br><br>Sincerely,<br>The OnionStalk[er] System", 'html')
    msg.attach(msgBody)
    server = smtplib.SMTP('127.0.0.1')
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()
    return render_template('success.html')


@app.route('/favicon.ico')
def send_icon():
    return send_from_directory('static/images', 'favicon.ico')


@app.route('/css/<path:path>')
def send_css(path):
    return redirect('/static/css/' + path)


@app.route('/fonts/<path:path>')
def send_fonts(path):
    return redirect('/static/fonts/' + path)


@app.route('/js/<path:path>')
def send_js(path):
    return redirect('/static/js/' + path)


@app.route('/api/unsubscribe/<string:ident>')
def unsubscribePost(ident):
    connection = pymysql.connect(host=sqlhost,
                                 user=sqluser,
                                 password=sqlpass,
                                 db=sqldb,
                                 charset=sqlcharset,
                                 cursorclass=pymysql.cursors.DictCursor)

    c = connection.cursor(pymysql.cursors.DictCursor)

    if not c.execute("SELECT * FROM relays WHERE uuid=%s;", str(ident)):
        c.close()
        connection.close()
        return 'Error: Your ID is invalid!'
    else:
        c.execute("SELECT * FROM relays WHERE uuid=%s;", str(ident))
        temp_info = c.fetchone()
        c.execute("DELETE FROM relays WHERE uuid=%s;", str(ident))
        connection.commit()
        email = temp_info['email']
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "OnionStalk[er]: Unsubscribed Successfully"
        msg['From'] = 'torstatus@cavefox.net'
        msg['To'] = email
        msgBody = MIMEText("Hello,<br><br>This is an automated message from the OnionStalk[er] service.<br><br>Your subscription to alerts on the Tor relay " + onionQuery.getnickname(temp_info['fingerprint']) + " has been canceled.<br><br>Sincerely,<br>The OnionStalk[er] System", 'html')
        msg.attach(msgBody)
        server = smtplib.SMTP('127.0.0.1')
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        c.close()
        connection.close()
        return 'Your registration to OnionStalk[er] has been canceled'


@app.route('/api/confirm/<string:ident>')
def confirm_post(ident):
    connection = pymysql.connect(host=sqlhost,
                                 user=sqluser,
                                 password=sqlpass,
                                 db=sqldb,
                                 charset=sqlcharset,
                                 cursorclass=pymysql.cursors.DictCursor)

    c = connection.cursor(pymysql.cursors.DictCursor)

    if not c.execute("SELECT * FROM relays WHERE uuid=%s AND confirmed=0;", str(ident)):
        c.close()
        connection.close()
        return 'Error: Registration has already been completed, or ID is invalid!'
    else:
        c.execute("UPDATE relays SET confirmed=1 WHERE uuid=%s;", str(ident))
        connection.commit()
        c.execute("SELECT * FROM relays WHERE uuid=%s;", str(ident))
        temp_info = c.fetchone()
        email = temp_info['email']
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "OnionStalk[er]: Registration Confirmation"
        msg['From'] = 'torstatus@cavefox.net'
        msg['To'] = email
        msgBody = MIMEText("Hello,<br><br>This is an automated message from the OnionStalk[er] service.<br><br>Your subscription to alerts on the Tor relay " + onionQuery.getnickname(temp_info['fingerprint']) + " has been confirmed.<br><br>To update your preferences please visit https://torstatus.cavefox.net/api/update/" + ident + ".<br><br>To cancel these alerts please visit https://torstatus.cavefox.net/api/unsubscribe/" + ident + ".<br><br>Sincerely,<br>The OnionStalk[er] System", 'html')
        msg.attach(msgBody)
        server = smtplib.SMTP('127.0.0.1')
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        c.close()
        connection.close()
        return 'Your registration to OnionStalk[er] has been confirmed successfully!'


@app.route('/api/update/<string:ident>', methods=['GET'])
def update_get(ident):
    connection = pymysql.connect(host=sqlhost,
                                 user=sqluser,
                                 password=sqlpass,
                                 db=sqldb,
                                 charset=sqlcharset,
                                 cursorclass=pymysql.cursors.DictCursor)

    c = connection.cursor(pymysql.cursors.DictCursor)

    if not c.execute("SELECT * FROM relays WHERE uuid=%s;", str(ident)):
        c.close()
        connection.close()
        return 'Error: Your ID is invalid!'
    else:
        if c.execute("SELECT * FROM relays WHERE uuid=%s AND monitorFailure=1;", str(ident)):
            alertDown = "checked"
        else:
            alertDown = ""

        c.execute("SELECT * FROM relays WHERE uuid=%s;", str(ident))
        temp_var = c.fetchone()

        minimumBandwidth = temp_var['minimumBandwidth']

        relayNick = onionQuery.getnickname(temp_var['fingerprint'])

        c.close()
        connection.close()

        return render_template('update.html', uuid=ident, relayNickname=relayNick, bandwidth=(float(minimumBandwidth)/1024), checked=alertDown)

@app.route('/api/update/<string:ident>', methods=['POST'])
def update_post(ident):
    connection = pymysql.connect(host=sqlhost,
                                 user=sqluser,
                                 password=sqlpass,
                                 db=sqldb,
                                 charset=sqlcharset,
                                 cursorclass=pymysql.cursors.DictCursor)

    c = connection.cursor(pymysql.cursors.DictCursor)

    if not c.execute("SELECT * FROM relays WHERE uuid=%s;", str(ident)):
        c.close()
        connection.close()
        return 'Error: Your ID is invalid!'
    else:
        lowbandwidth = request.form["lowbandwidth"]
        c.execute("SELECT * FROM relays WHERE uuid=%s;", str(ident))
        tempVar = c.fetchone()
        email = tempVar['email']

        if lowbandwidth == '':
            lowbandwidth = 0
        try:
            downmonitor = request.form["downmonitor"]
            downmonitor = True

        except:
            downmonitor = False

        try:
            lowbandwidth = float(lowbandwidth)
            lowbandwidth = float(lowbandwidth) * 1024.0
        except:
            relayNick = onionQuery.getnickname(tempVar['fingerprint'])
            if c.execute("SELECT * FROM relays WHERE uuid=%s AND monitorFailure=1;", str(ident)):
                alertDown = "checked"
            else:
                alertDown = ""

            c.execute("SELECT * FROM relays WHERE uuid=%s;", str(ident))
            temp_var = c.fetchone()

            if temp_var['minimumBandwidth'] == 0:
                minimumBandwidth = ""
            else:
                minimumBandwidth = temp_var['minimumBandwidth']
            return render_template('update.html', uuid=ident, message='invalidBandwidth', relayNickname=relayNick, bandwidth=float(minimumBandwidth)/1024, checked=alertDown)

        c.execute("UPDATE relays SET minimumBandwidth=%s, monitorFailure=%s WHERE uuid=%s;", (lowbandwidth, downmonitor, str(ident)))
        connection.commit()
        c.close()
        connection.close()
        email = tempVar['email']
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "OnionStalk[er]: Update Confirmation"
        msg['From'] = 'torstatus@cavefox.net'
        msg['To'] = email
        msgBody = MIMEText(
            "Hello,<br><br>This is an automated message from the OnionStalk[er] service.<br><br>Your subscription to alerts on the Tor relay " + onionQuery.getnickname(tempVar['fingerprint']) + " has been updated successfully!<br><br>Sincerely,<br>The OnionStalk[er] System", 'html')
        msg.attach(msgBody)
        server = smtplib.SMTP('127.0.0.1')
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()

        return 'Your preferences have been updated successfully!'
