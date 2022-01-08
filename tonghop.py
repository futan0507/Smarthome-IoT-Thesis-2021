'''
    Raspberry /pi GpiO Status and Control
'''
import RPi.GPIO as GpiO
import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe
from flask import Flask, render_template, request
import time
import Adafruit_DHT
#import cho firebase
from time import sleep
import datetime
from firebase import firebase
import Adafruit_DHT
import urllib.request as urllib2
import urllib, http.client  
import json
import os 
from functools import partial
import threading    #chạy multithread để tăng tốc các cảm biến
#định nghĩa firebase
firebase = firebase.FirebaseApplication('https://khoaluantotnghiep-huu-thanh-default-rtdb.firebaseio.com/', None)

#định nghĩa flask
app = Flask(__name__)
GpiO.setmode(GpiO.BCM)
GpiO.setwarnings(False)
#khai báo các GPIO 
gpio_nhietdo= 23
gpio_denbep= 7
##gpio_denkhach = 8   trên 8266
gpio_dencua= 10
gpio_dencauthang=12
gpio_dentolet=16
gpio_denngu1=20
gpio_denngu2=25
#gpio_quatkhach=10   bỏ 
#gpio_quatbep=9     bỏ
#gpio_quatngu=11   trên 8266

MQTT_SERVER = "192.168.43.56"    #ip raspberry
#MQTT_SERVER = "192.168.1.9" 
topic = "topic"

# Define led /pins as output
GpiO.setup(gpio_denbep, GpiO.OUT)   
GpiO.setup(gpio_dencua, GpiO.OUT)
GpiO.setup(gpio_dencauthang, GpiO.OUT)   
GpiO.setup(gpio_dentolet, GpiO.OUT) 
GpiO.setup(gpio_denngu1, GpiO.OUT)
GpiO.setup(gpio_denngu2, GpiO.OUT)   
#GpiO.setup(gpio_quatbep, GpiO.OUT)   bỏ
#GpiO.setup(gpio_quatngu, GpiO.OUT)    trên 8266
# tắt đèn, quạt
GpiO.setup(gpio_denbep, GpiO.LOW)    
GpiO.setup(gpio_dencua, GpiO.LOW)
GpiO.setup(gpio_dencauthang, GpiO.LOW)   
GpiO.setup(gpio_dentolet, GpiO.LOW) 
GpiO.setup(gpio_denngu1, GpiO.LOW)
GpiO.setup(gpio_denngu2, GpiO.LOW)   
#GpiO.setup(gpio_quatbep, GpiO.LOW)   bỏ
#GpiO.setup(gpio_quatngu, GpiO.LOW)    trên 8266
# định nghĩa các trạng thái ngược, tức là nếu đèn đang bật th nút trangthai chuyen thanh 'tắt'
trangthai_denbep ="OFF"
trangthai_denkhach="OFF"
trangthai_dencua="OFF"
trangthai_dencauthang="OFF"
trangthai_dentolet="OFF"
trangthai_denngu1="OFF"
trangthai_denngu2="OFF"
#trangthai_quatkhach="OFF"    bỏ
#trangthai_quatbep="OFF"    bỏ
trangthai_quatngu="OFF"

duongdan_denbep ="/pi/denbep/on"
duongdan_denkhach="/8266/denkhach/on"
duongdan_dencua="/pi/dencua/on"
duongdan_dencauthang="/pi/dencauthang/on"
duongdan_dentolet="/pi/dentolet/on"
duongdan_denngu1="/pi/denngu1/on"
duongdan_denngu2="/pi/denngu2=/on"
#duongdan_quatkhach="/8266/quatkhach/on"     bỏ
#duongdan_quatbep="/pi/quatbep/on"      bỏ
duongdan_quatngu="/8266/quatngu/on"
duongdancua="/8266/cua/on"

nhietdo=0
doam=0
nhietdomax=25
thoigiandongcua="1" #tương đương với thời gian chờ đóng cửa=5s
thoigiancapnhat=str(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

def laycauhinhtufirebase():
    global nhietdomax,thoigiandongcua #,khoangcachbatden
    #while True:
    nhietdomax= firebase.get('/cauhinh/nhietdo', None)
    thoigiandongcua = str(firebase.get('/cauhinh/thoigiandongcua', None))[0] #lấy ký tự đầu tiên gán cho thoigiandongcua
#đưa dữ liệu lên firebase
def laynhietdodoam():
       
    #while True:
    global nhietdo,doam,thoigiancapnhat 
    doam, nhietdo = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, gpio_nhietdo)
    thoigiancapnhat = str(datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S'))        
    if nhietdo>nhietdomax and trangthai_quatngu=="OFF":
        chuoigui="221"
        publish.single(topic, chuoigui, hostname=MQTT_SERVER)
    elif nhietdo<nhietdomax and trangthai_quatngu=="ON":
        chuoigui="220"
        publish.single(topic, chuoigui, hostname=MQTT_SERVER)
    #sleep(10)  # mỗi 10s sẽ lấy lại nhietdo
"""def laynhietdodoamtufirebase():
    global nhietdo,doam,thoigiancapnhat    
    thoigiancapnhat = firebase.get('/sensor/thoigiancapnhat', None) 
    nhietdo = firebase.get('/sensor/nhietdo', None)
    doam = firebase.get('/sensor/doam', None)    """
#cập nhật đường dẫn, trạng thái các đèn, quạt trên 8266
def capnhatduongdan8266():
    #sử dụng global để trong hàm này có thể thay đổi giá trị các biến đó
    global trangthai_denkhach, trangthai_quatngu, duongdan_denkhach, duongdan_quatngu
    #gửi yêu cầu đến 8266 để nhận thông tin về chân đèn, quạt có mở ko?
    chuoigui="can thong tin"
    publish.single(topic, chuoigui, hostname=MQTT_SERVER)
    #nhận thông tin trả lời của 8266
    msg = subscribe.simple(topic, hostname=MQTT_SERVER)
    nhan=str(msg.payload.decode(encoding='UTF-8'))
    if nhan=='1020':
        trangthai_denkhach="OFF"
        trangthai_quatngu="OFF"
        duongdan_denkhach="/8266/denkhach/on"
        duongdan_quatngu="/8266/quatngu/on"
    elif nhan=='1021':
        trangthai_denkhach="OFF"
        trangthai_quatngu="ON"
        duongdan_denkhach="/8266/denkhach/on"
        duongdan_quatngu="/8266/quatngu/off"
    elif nhan=='1120':
        trangthai_denkhach="ON"
        trangthai_quatngu="OFF"
        duongdan_denkhach="/8266/denkhach/off"
        duongdan_quatngu="/8266/quatngu/on"
    elif nhan=='1121':
        trangthai_denkhach="ON"
        trangthai_quatngu="ON"
        duongdan_denkhach="/8266/denkhach/off"
        duongdan_quatngu="/8266/quatngu/off"
    else :
        trangthai_denkhach="OFF"
        trangthai_quatngu="OFF"
        duongdan_denkhach="/8266/denkhach/off"
        duongdan_quatngu="/8266/quatngu/off"
def capnhatduongdanpi():
    #sử dụng global để trong hàm này có thể thay đổi giá trị các biến đó
    global trangthai_denbep,trangthai_dencua,trangthai_dencauthang,trangthai_dentolet,trangthai_denngu1,trangthai_denngu2 #,trangthai_quatbep,trangthai_quatngu
    global duongdan_denbep,duongdan_dencua,duongdan_dencauthang,duongdan_dentolet,duongdan_denngu1,duongdan_denngu2 #,duongdan_quatbep,duongdan_quatngu
    if GpiO.input(gpio_denbep)==0 :
        trangthai_denbep = "OFF"
        duongdan_denbep="/pi/denbep/on"
    else :
        trangthai_denbep="ON"
        duongdan_denbep="/pi/denbep/off"
    if GpiO.input(gpio_dencua)==0 :
        trangthai_dencua = "OFF"
        duongdan_dencua="/pi/dencua/on"
    else :
        trangthai_dencua="ON"
        duongdan_dencua="/pi/dencua/off"      
    if GpiO.input(gpio_dencauthang)==0 :
        trangthai_dencauthang = "OFF"
        duongdan_dencauthang="/pi/dencauthang/on"
    else :
        trangthai_dencauthang="ON"
        duongdan_dencauthang="/pi/dencauthang/off"
    if GpiO.input(gpio_dentolet)==0 :
        trangthai_dentolet = "OFF"
        duongdan_dentolet="/pi/dentolet/on"
    else :
        trangthai_dentolet="ON"
        duongdan_dentolet="/pi/dentolet/off"
    if GpiO.input(gpio_denngu1)==0 :
        trangthai_denngu1 = "OFF"
        duongdan_denngu1="/pi/denngu1/on"
    else :
        trangthai_denngu1="ON"
        duongdan_denngu1="/pi/denngu1/off"    
    if GpiO.input(gpio_denngu2)==0 :
        trangthai_denngu2 = "OFF"
        duongdan_denngu2="/pi/denngu2/on"
    else :
        trangthai_denngu2="ON"
        duongdan_denngu2="/pi/denngu2/off"    
    '''if GpiO.input(gpio_quatbep)==0 :
        trangthai_quatbep = "OFF"
        duongdan_quatbep="/pi/quatbep/on"
    else :
        trangthai_quatbep="ON"
        duongdan_quatbep="/pi/quatbep/off"    
    if GpiO.input(gpio_quatngu)==0 :
        trangthai_quatngu = "OFF"
        duongdan_quatngu="/pi/quatngu/on"
    else :
        trangthai_quatngu="ON"
        duongdan_quatngu="/pi/quatngu/off"   '''
    
@app.route("/")
def index(): 
    laycauhinhtufirebase()  #sẽ lấy cấu hình mỗi khi load vào trang chính
    laynhietdodoam()
    capnhatduongdan8266()    #cập nhật trạng thái đèn, quạt trên 8266
    capnhatduongdanpi()    
    templateData = {
            'title' : 'Nguyen Tuan Huu - Tran Phu Thanh',
            'denbep'  : trangthai_denbep,
            'denkhach'  : trangthai_denkhach,
            'dencua'  : trangthai_dencua,
            'dencauthang'  : trangthai_dencauthang,
            'dentolet'  : trangthai_dentolet,
            'denngu1'  : trangthai_denngu1,
            'denngu2'  : trangthai_denngu2,            
            'quatngu'  : trangthai_quatngu,
            'duongdan_denbep'  : duongdan_denbep,
            'duongdan_denkhach'  : duongdan_denkhach,
            'duongdan_dencua'  : duongdan_dencua,
            'duongdan_dencauthang'  : duongdan_dencauthang,
            'duongdan_dentolet'  : duongdan_dentolet,
            'duongdan_denngu1'  : duongdan_denngu1,
            'duongdan_denngu2'  : duongdan_denngu2,
            'duongdan_quatngu'  : duongdan_quatngu,                   
            'nhietdo':nhietdo,
            'doam':doam,
            'thoigiancapnhat':thoigiancapnhat,
            'duongdancua':duongdancua,
        }
    return render_template('index.html', **templateData)
    
@app.route("/<thietbi>/<deviceName>/<action>")
def action(thietbi, deviceName, action):
    global trangthai_denkhach, trangthai_quatngu, duongdan_denkhach, duongdan_quatngu
    
    # hành động cho lần này
    if thietbi=='8266': #gửi tín hiệu đi
        if deviceName == 'cua':            
            chuoigui="1"+thoigiandongcua
            publish.single(topic, chuoigui, hostname=MQTT_SERVER)            
        if deviceName == 'denkhach':           
            if action=="on":
                chuoigui="211"
                publish.single(topic, chuoigui, hostname=MQTT_SERVER)
                trangthai_denkhach="ON"    
                duongdan_denkhach="/8266/denkhach/off"
            else:
                chuoigui="210"
                publish.single(topic, chuoigui, hostname=MQTT_SERVER)
                trangthai_denkhach="OFF"   
                duongdan_denkhach="/8266/denkhach/on"
        if deviceName == 'quatngu':           
            if action=="on":
                chuoigui="221"
                publish.single(topic, chuoigui, hostname=MQTT_SERVER)
                trangthai_quatngu="ON"
                duongdan_quatngu="/8266/quatngu/off"
            else:
                chuoigui="220"
                publish.single(topic, chuoigui, hostname=MQTT_SERVER)
                trangthai_quatngu="OFF"
                duongdan_quatngu="/8266/quatngu/on"
    else: # điều khiển các thiết bị trên /pi
        actuator=gpio_denngu2
        if deviceName == 'denbep':
            actuator = gpio_denbep
        elif deviceName == 'dencua':
            actuator = gpio_dencua
        elif deviceName == 'dencauthang':
            actuator = gpio_dencauthang
        elif deviceName == 'dentolet':
            actuator = gpio_dentolet
        elif deviceName == 'denngu1':
            actuator = gpio_denngu1
                             
        if action == "on" :
            GpiO.output(actuator, GpiO.HIGH)
        if action == "off" :
            GpiO.output(actuator, GpiO.LOW)
    capnhatduongdanpi()   # không cập nhật duongdan 8266 de tranh gui lien tuc MQTT dan den loadweb cham
    #duongdancua="/8266/cua/on"   #luôn luôn là vậy vì cửa mở xong tự đóng  
    #laynhietdodoam()
    # gửi dữ liệu vào web                           
    templateData = {
            'title' : 'Nguyen Tuan Huu - Tran Phu Thanh',
            'denbep'  : trangthai_denbep,
            'denkhach'  : trangthai_denkhach,
            'dencua'  : trangthai_dencua,
            'dencauthang'  : trangthai_dencauthang,
            'dentolet'  : trangthai_dentolet,
            'denngu1'  : trangthai_denngu1,
            'denngu2'  : trangthai_denngu2,            
            'quatngu'  : trangthai_quatngu,
            'duongdan_denbep'  : duongdan_denbep,
            'duongdan_denkhach'  : duongdan_denkhach,
            'duongdan_dencua'  : duongdan_dencua,
            'duongdan_dencauthang'  : duongdan_dencauthang,
            'duongdan_dentolet'  : duongdan_dentolet,
            'duongdan_denngu1'  : duongdan_denngu1,
            'duongdan_denngu2'  : duongdan_denngu2,
            'duongdan_quatngu'  : duongdan_quatngu,                   
            'nhietdo':nhietdo,
            'doam':doam,
            'thoigiancapnhat':thoigiancapnhat,
            'duongdancua':duongdancua,
        }
    return render_template('index.html', **templateData)
if __name__ == "__main__":
    #t1=threading.Thread(target=laycauhinhtufirebase)
    #t1.start()
    #t2=threading.Thread(target=laynhietdodoam)
    #t2.start()
    app.run(host=MQTT_SERVER, port=5014, debug=True)
    #t1.join()
    #t2.join()

