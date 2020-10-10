from signal import SIGINT
import ssl
from threading import Thread
from time import sleep, strftime, time
from smtplib import SMTP, SMTPException
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from hashlib import sha3_512
from flask import Flask, redirect, render_template, url_for, request, session, flash, Response, send_file
from time import time
from lxml import etree, objectify
from os import kill, getpid, mkdir

from py7zr import SevenZipFile
#from pyzipper import AESZipFile, ZIP_LZMA, WZ_AES
from os import path, walk
from secure_delete import secure_delete
from shutil import rmtree

from socket import socket, AF_INET, SOCK_DGRAM

#pw = '7fb65aaa7a9f921b7be873b4864003c9b80832454eae4778617d59f3273c1c9b54aa8f15828abe2a0759141e5063929e5cc0d435feeb9c13b3a08bf08a8c08d4'

def encrypt():          #zip all the directories from data.xml into a passworded archive
        fileNumber = 0
        zippedFileNumber = 0
        errors = 0
        errortext = []
        tree = etree.parse("data.xml")

        pw = tree.find("password").text      #only way to not have the password in clear text here, or use a reversible algorithm.
        #print(pw)
        try:
            mkdir(tree.find('storage').text + '/temp')
        except FileExistsError:
            pass
        for i in tree.getroot():  # locations MUST be directories, not single files, otherwise will not be backed up.
            if i.tag.startswith('loc'):
                for target in i.getiterator():
                    print(target.text)
                    with SevenZipFile(tree.find('storage').text + '/temp/' + target.text.replace('/', '.') + '.zip', 'w', password=pw) as archive:
                                try:
                                    fileNumber += 1
                                    archive.writeall(target.text, 'base')
                                    zippedFileNumber += 1
                                except Exception as e:
                                    print(e)
                                    errors += 1         #initial tests show two types or possible errors : 1/ no permission (should be avoided by running the program as root
                                    errortext.append(str(e)) #and making sure the filesystem for storing the zip archive isn't read-only).
                                    pass
                    with SevenZipFile(tree.find('storage').text + '/encrypted_data.7z', 'w', password=pw) as archive:
                        archive.writeall(tree.find('storage').text + '/temp/', 'base')

        wipe()


def wipe():
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
                                print(e)
                                errortext.append(str(e))
                                pass
        try: #now let's delete the temporary archives.
            secure_delete.secure_delete(tree.find('storage').text + '/temp')
            secure_delete.os_force_remove(tree.find('storage').text + '/temp')
            secure_delete.upset_inodes(tree.find('storage').text + '/temp')
            rmtree(tree.find('storage').text + '/temp')
        except Exception as e:
            print(e)
            errortext.append(str(e))
            pass


encrypt()