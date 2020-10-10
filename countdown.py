from shutil import rmtree
from signal import SIGTERM
import ssl
from threading import Thread
from time import sleep
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from hashlib import sha3_512
from flask import Flask, redirect, render_template, url_for, request, flash, jsonify
from time import time
from lxml import etree
from os import kill, getpid, mkdir
#from pyzipper import AESZipFile, ZIP_LZMA, WZ_AES    #this does not work with the long password in SHA3_512?
from py7zr import SevenZipFile
from os import path, walk
from json import loads
from secure_delete import secure_delete
from socket import socket, AF_INET, SOCK_DGRAM

#get the local IP address
def getIP():
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    IP = s.getsockname()[0]
    s.close()
    return IP


class Countdown(Thread):
    def __init__(self):
        super().__init__()

    def shutdown(self):
        #print(getpid())
        #kill(getpid(), SIGINT)
        kill(getpid(), SIGTERM) 

    def run(self):

        interface = Interface()  #launch the web interface.
        if not interface.is_alive():
            interface.start()

        try:  # if the config file does not exist or is otherwise missing elements, recreate it
            tree = etree.parse("data.xml")
            list = []
            list.append(tree.find("lastcheck").text)
            list.append(tree.find("alerted").text)
            list.append(tree.find("wiped").text)
#            for i in tree.getroot():
                #if i.text == None:
                #    raise Exception  #normally, no field should be None. Defaults to zero.
 #               list.append(i.text)
            lastcheck, alerted, wiped  = int(list[0]),int(list[1]),int(list[2])

            if wiped == 1:
                self.shutdown()   #data wiped already, exit.

            if alerted == 0 and int(time()) - lastcheck > 604800: #if more than 7 days since last check-in, warn

                for child in tree.getroot():
                    if child.tag == "alerted":
                        child.text = "1"
                    tree.write("data.xml")
                self.sendmail("alert", 1)

                if not interface.is_alive():  #if somehow the interface isn't running, start it.
                    interface = Interface()
                    interface.start()

                sleep(21600) #sleep 6 hours

            elif alerted == 1 and int(time()) - lastcheck > 691200: #if more than 8 days since last check-in (1 day since first warning)
                for child in tree.getroot():
                    if child.tag == "alerted":
                        child.text = "2"
                    elif child.tag == "warning_date":
                        child.text = str(int(time()))   #set warning timestamp.
                tree.write("data.xml")
                self.sendmail("alert", 2)

                if not interface.is_alive():  # if somehow the interface isn't running, start it.
                    interface = Interface()
                    interface.start()

                sleep(21600)  # sleep 6 hours

            elif alerted == 2 and int(time()) - lastcheck > 777600:  # if more than 9 days since last check-in (1 day since second warning).
                for child in tree.getroot():
                    if child.tag == "wiped":
                        child.text = "1"
                    #elif child.tag == "lastcheck":
                    #    child.text = str(int(time()))   #set wiping timestamp. Not much point doing that.
                tree.write("data.xml")
                self.sendmail("alert", 3)
                self.encrypt()   #I'm dead, encrypt and wipe all the data.

        # different option: if any exception, send to the configuration page (typical situation: first run).
        except Exception as e:
            print(e)
            pass

    def sendmail(self, status, info):
        message = MIMEMultipart('alternative')
        #message['From'] = "Countdown"
        sender = "countdown@jackson.com"
        recipient = etree.parse("data.xml").find("email").text
        message['To'] = recipient

        if status == "alert":

            message['Subject'] = "Countdown Alert | Level {0}".format(info)

            if info == 1:
                delay = '48 hours'
            elif info == 2:
                delay = '24 hours'
            else:
                delay = 0
            if not delay == 0:
                text = "<br>Warning: data will be wiped in {0}.".format(delay)
            else:
                text = "<br>Wiping data."
            text = MIMEText(text, 'html')
            message.attach(text)

        elif status == "encrypt":
            if info == 0:
                message['Subject'] = "Data was encrypted"
            else:
                message['Subject'] = "DATA WAS ENCRYPTED WITH ERRORS"
                message.attach(info)

        elif status == "wiped":
            if len(info) == 178:
                message['Subject'] = "Data was wiped."
                text = MIMEText(info, 'html')
                message.attach(text)

            else:
                message['Subject'] = "Error while wiping. Data may still be present."
                text = MIMEText(info, 'html')
                message.attach(text)

        mailer = SMTP('localhost')
        mailer.sendmail(sender, recipient, message.as_string())
        mailer.quit()

    def encrypt(self):          #zip all the directories from data.xml into a passworded archive
        fileNumber = 0
        zippedFileNumber = 0
        errors = 0
        errortext = []
        tree = etree.parse("data.xml")
        ###########    WARNING  #############
        #To avoid having the password stored in plaintext, the zip archived will be locked with the password
        #in its HASHED FORM. The algorithm is SHA3_512.
        #to decrypt the archive, one will need to hash his password and use the output.
        #or just read it in data.xml if the root password is known.
        #####################################
        pw = tree.find("password").text      #only way to not have the password in clear text here, or use a reversible algorithm.
        try:        #py7zr doesn't support 'append', so next directory in archive will overwrite the previous.
            mkdir(tree.find('storage').text + '/temp')   #solution is to create an archive for each directory, then zip them all in the final .7z
        except FileExistsError:   #this results in the final .7z archive being passworded and containing a number of passworded .7z.
            pass
        for i in tree.getroot():  # locations MUST be directories, not single files, otherwise will not be backed up.
            if i.tag.startswith('loc'):
                for target in i.getiterator():
                    print(target.text)
                    with SevenZipFile(tree.find('storage').text + '/temp/' + target.text.replace('/', '.') + '.7z',
                                      'w', password=pw) as archive:
                        try:
                            fileNumber += 1
                            archive.writeall(target.text, 'base')
                            zippedFileNumber += 1
                        except Exception as e:
                            #print(e)
                            errors += 1  #not sure what errors to expect with py7zr.
                            errortext.append(str(e))
                            pass
        with SevenZipFile(tree.find('storage').text + '/encrypted_data.7z', 'w', password=pw) as archive:
            archive.writeall(tree.find('storage').text + '/temp/', 'base')
        #TODO : manage the various exeption types to abort or ignore.
        if errors == 0:
            self.sendmail("encrypt", 0)
        else:
            text = ""
            for i in errortext:
                text = text + str(i) + '<br>'
            text = MIMEText(text, 'html')
            self.sendmail("encrypt", text)

        if zippedFileNumber / fileNumber > 0.9:  # if more than 90% of the directories were backed up in the encrypted archive ? Maybe set max number of errors, too ?
            print("wiping")
            #Countdown.wipe(self)  #now, secure delete the original directories.

    def wipe(self):
        errortext = []
        secure_delete.secure_random_seed_init()
        tree = etree.parse("data.xml")
        for i in tree.getroot():
            if i.tag.startswith('loc'):
                for target in i.getiterator():
                    for (root, dirs, files) in walk(target.text):           #wipe each file (3 passes by default) then remove directory
                        for f in files:                                     #if there is an error, log it and move on to the next file
                            try:
                                secure_delete.secure_delete(path.join(root, f))
                                secure_delete.os_force_remove(path.join(root, f))
                                secure_delete.upset_inodes(path.join(root, f))
                                rmtree(target.text)
                            except Exception as e:
                                # print(e)
                                errortext.append(str(e))
                                pass
        try: #now let's delete the temporary archives.
            secure_delete.secure_delete(tree.find('storage').text + '/temp')
            secure_delete.os_force_remove(tree.find('storage').text + '/temp')
            secure_delete.upset_inodes(tree.find('storage').text + '/temp')
            rmtree(tree.find('storage').text + '/temp')
        except: # Exception as e:
            # print(e)
            #errortext.append(str(e))
            pass

        if not errortext:
            text = "<strong>WARNING: the archive can be decrypted with the password in its <u>HASHED FORM</u>.</strong><br>Use any online tool to obtain it, selecting the algorithm SHA3_512."
            self.sendmail("wiped", text)
        else:           #if there were errors, add them to the report email. Which I won't read, since I'm dead.
            text = "<strong>WARNING: the archive can be decrypted with the password in its <u>HASHED FORM</u>.</strong><br>Use any online tool to obtain it, selecting the algorithm SHA3_512.<br><br>"
            for i in errortext:
                text = text + str(i) + '<br>'
            self.sendmail("wiped", text)

        self.shutdown()


class Interface(Thread):

    def __init__(self):
        super().__init__()

    def restoreCountdown(self): #rewrite the xml file with current time.
        tree = etree.parse("data.xml")
        for child in tree.getroot():
            if child.tag == "alerted":
                child.text = "0"
            elif child.tag == "wiped":
                child.text = "0"
            elif child.tag == "lastcheck":
                child.text = str(int(time()))
            elif child.tag == "warning_date":
                child.text = '0' # reset warning timestamp.
        tree.write("data.xml")

    def configuration(self):
        data = {}
        try:
            tree = etree.parse("data.xml")
            for i in tree.getroot():
                if i.tag == 'storage' or i.tag == 'email':
                    if i.text == None:
                        data[i.tag] = ""
                    else:
                        data[i.tag] = i.text
                elif i.tag.startswith('loc'):
                    data[i.tag] = i.text

        except OSError: #file is missing. Create with necessary fields.
            basic_config = etree.Element("data")
            password = etree.SubElement(basic_config, 'password')
            lastcheck = etree.SubElement(basic_config, 'lastcheck')
            alerted = etree.SubElement(basic_config, 'alerted')
            wiped = etree.SubElement(basic_config, 'wiped')
            storage = etree.SubElement(basic_config, 'storage')
            email = etree.SubElement(basic_config, 'email')
            lastcheck.text = str(int(time()))
            wiped.text = "0"
            alerted.text = "0"
            et = etree.ElementTree(basic_config)
            et.write("data.xml", pretty_print=True, xml_declaration=True, encoding="utf-8")

        return data

    def run(self):

        context = ssl.SSLContext(protocol=ssl.PROTOCOL_SSLv23)  # ssl setup
        context.load_cert_chain('server.crt', 'server.key')

        app = Flask(__name__)

        @app.before_request
        def before_request():
            if not request.url.startswith('https://'):
                secure_url = request.url.replace('http://', 'https://', 1)  #this still does not work.
                code = 301
                return redirect(secure_url, code=code)

        @app.route('/', methods=['GET', 'POST'])
        def validate():

            conf_missing = 0 #bad solution but nothing else works.

            try:
                tree = etree.parse("data.xml") #check if the xml file exists and is readable.

                if request.method == 'POST':
                    if sha3_512(request.form['password'].encode('ascii')).hexdigest() == tree.xpath("/data/password")[0].text:
                        message = "Countdown restored. You may close this page."
                        flash(message)
                        self.restoreCountdown()
                        return render_template('noaction.html')

                    else:
                        message = "Wrong password."
                        flash(message)
                        return render_template('validate.html')

                else:
                    for i in tree.getroot(): #check whether any field is empty: shouldn't happen.
                        if i.text == None:
                            conf_missing = 1
                            break
                if conf_missing == 1:
                    if tree.xpath("/data/password")[0].text: #if a password was set up already
                        message = "Configuration is incomplete. "
                        flash(message)
                        return redirect(url_for('authConfig'))
                    else:
                        data = self.configuration()
                        #print(data)
                        message = "You must set a password. Please update."
                        flash(message)
                        return render_template('configuration.html', data=data)

                else:
                    if tree.xpath("/data/alerted")[0].text == "0":
                        return render_template('noaction.html')
                    else:
                        message = "Password must be entered to reset the timer."
                        flash(message)
                        return render_template('validate.html')

            except: #whatever the exception: update the config file and try again.
                self.configuration()
                #print(data)
                return redirect(url_for('validate'))

        @app.route('/validate', methods=['GET', 'POST'])  # that's for the "redirect(url_for('validate')" to work...just routes back to /.
        def validation_required():
            validate()

        @app.route('/authConfig', methods=['GET', 'POST'])
        def authConfig():
            try:
                tree = etree.parse("data.xml")
                if request.method == 'POST':
                    if sha3_512(request.form['password'].encode('ascii')).hexdigest() == tree.xpath("/data/password")[0].text:
                        data = self.configuration()
                        if (data['storage'] == "" or data['email'] == ""):
                            message = "Configuration items are missing. Please update."
                            flash(message)
                        return render_template('configuration.html', data=data)

                    else:
                        message = "Wrong password."
                        flash(message)
                        return redirect(url_for('authConfig'))

                else:
                    message = "Please enter your password to access the settings page."
                    flash(message)
                    return render_template('validate.html')

            except:
                data = self.configuration()
                message = "Configuration items are missing. Please update."
                flash(message)
                return render_template('configuration.html', data=data)

        @app.route('/configuration', methods=['GET', 'POST'])
        def configuration():
            if request.method == 'GET':
                return redirect(url_for('authConfig'))
            else:
                return render_template("configuration.html")

        @app.route('/noaction', methods=['GET'])
        def noaction():
            return render_template('noaction.html')

        @app.route('/_updateSource', methods=['POST'])
        def updateSource():
            id = loads(request.data)['id']
            value = loads(request.data)['value']
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse("data.xml", parser)
            for child in tree.getroot():
                if child.tag == id:                 #this is to remove a source directory
                    if not value:
                        child.getparent().remove(child)
                        tree.write("data.xml", pretty_print=True, xml_declaration=True, encoding="utf-8")
                        break
                    else:                           #this is to update a source directory
                        child.text = value
                        tree.write("data.xml", pretty_print=True, xml_declaration=True, encoding="utf-8")
                        break
                elif id == "temp":
                    index = 0
                    for child in tree.getroot():
                        if 'loc' in child.tag:
                            while int((child.tag.lstrip("loc"))) >= index:
                                index = int((child.tag.lstrip("loc"))) + 1
                        else:
                            index = 1
                    location = etree.SubElement(tree.getroot(), 'loc'+str(index))
                    location.text = value
                    tree.write("data.xml", pretty_print=True, xml_declaration=True, encoding="utf-8")
                    return jsonify('loc'+str(index))

            return render_template('configuration.html')

        @app.route('/updateConfig', methods=['POST'])
        def updateConfig():

            p = sha3_512(request.form['password'].encode('ascii')).hexdigest()
            s = request.form['storage']
            e = request.form['email']

            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse("data.xml", parser)
            for child in tree.getroot():
                if child.tag == 'email':
                    child.text = e
                elif child.tag == 'storage':
                    child.text = s
                elif child.tag == 'password':
                    if not p == 'a69f73cca23a9ac5c8b567dc185a756e97c982164fe25859e0d1dcc1475c80a615b2123af1f5f94c11e3e9402c3ac558f500199d95b6d3e301758586281dcd26':
                        #if the password value equals hashed form or null, don't update.
                        child.text = p

            tree.write("data.xml", pretty_print=True, xml_declaration=True, encoding="utf-8")

            return redirect(url_for('validate'))

        if __name__ == '__main__':

            app.config['SESSION_TYPE'] = 'filesystem'
            app.config['SECRET_KEY'] = '\xe1\x10\xce\x9c\xa0x\xe6+\xa1\x1e\x90\xa1+\xac\x8d\x98\xa1\xe0:\xca\x04K\xb2'
            app.config['SESSION_COOKIE_SECURE'] = True

            IP = getIP()

            app.run(host=IP, port=5010, ssl_context=context)


countdown = Countdown()
countdown.run()
