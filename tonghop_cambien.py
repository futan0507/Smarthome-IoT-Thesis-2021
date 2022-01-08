''' lấy nhiệt độ đưa lên firebase, đưa lên thingspeak, nếu nhiệt độ quá ngưỡng sẽ bật quạt '''
import RPi.GPIO as GPIO
from time import sleep
import datetime
import time
from firebase import firebase
import Adafruit_DHT
import urllib.request as urllib2
import urllib, http.client  
import json
import os 
from functools import partial
import threading    #chạy multithread để tăng tốc các cảm biến

GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
GPIO.setwarnings(False)
#dịnh nghĩa đo khoang cách
GPIO_TRIGGER = 4
GPIO_ECHO = 3
GPIO.setup(GPIO_TRIGGER , GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
#dịnh nghĩa đo nhiệt độ
gpio_dht=23

#định nghĩa phát hiện chuyển động
gpio_chuyendong=22
GPIO.setup(gpio_chuyendong,GPIO.IN) 
#dịnh nghĩa firebase
firebase = firebase.FirebaseApplication('https://khoaluantotnghiep-huu-thanh-default-rtdb.firebaseio.com/', None)
#dịnh nghĩa đèn
gpio_dencua= 10
gpio_dencauthang= 12
gpio_denbep= 7
gpio_gasdigital = 26
gpio_gasanalog=19
GPIO.setup(gpio_gasdigital, GPIO.IN)
GPIO.setup(gpio_gasanalog, GPIO.IN)
GPIO.setup(gpio_dencua, GPIO.OUT)
GPIO.setup(gpio_dencauthang, GPIO.OUT)
GPIO.setup(gpio_denbep, GPIO.OUT)
nhietdo=0
# định nghĩa các ngưỡng
thoigiantatdencauthang=10   #phát hiện chuyển động, bật đèn, sau 'thoigiantatdencauthang' thì tắt
khoangcachbatden=5  #khi khoảng cách nhỏ hơn 'khoangcachbatden' thì sẽ bật đèn cửa
thoigianbatdaulaythongtin=time.time()
thoigianlaylaicauhinhtufirebase=30   #5 phút lấy thông tin cấu hình 1 lần
def update_firebase():
    global nhietdo  #đưa nhiệt độ ra ngoài để đo khoang cach dùng
    while True:
        doam, nhietdo = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, gpio_dht)
        if doam is not None and nhietdo is not None:
           # sleep(1)
            str_temp = ' {0:0.2f} *C '.format(nhietdo)  
            str_hum  = ' {0:0.2f} %'.format(doam)
            print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(nhietdo, doam))            
        else:
            print('Failed to get reading. Try again!')  
            
        data = {"nhietdo": nhietdo, "doam": doam}    
        unix = int(time.time())
        date = str(datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S'))
        #cập nhật dữ liệu giá trị hiện tại của nhiệt độ, độ ẩm: 1 vùng giá trị duy nhất
        firebase.put('nhietdodoam','thoigiancapnhat', date)
        sleep(0.1) 
        firebase.put('nhietdodoam','nhietdo', nhietdo)
        sleep(0.1) 
        firebase.put('nhietdodoam','doam', doam)
        sleep(0.1)  
        #cập nhật nhiệt độ, độ ẩm, nhiều vùng dữ liệu, mỗi vùng dữ liệu sẽ được phát sinh 1 tên ngau nhiên, vi2 vậy không thể get được chnh xác giá trị hien tai
        firebase.post('/nhietdodoam/lientuc', data)
        sleep(5)  
def laycauhinhtufirebase():
    global thoigiantatdencauthang,khoangcachbatden
    while True:
        khoangcachbatden = firebase.get('/cauhinh/khoangcach', None) 
        thoigiantatdencauthang = firebase.get('/cauhinh/thoigiantatdencauthang', None)
        sleep(3)
        #doam = firebase.get('/sensor/doam', None)      
def khoangcach():
    while True:
        speedsound = 33100 + (0.6*nhietdo)
        GPIO.output(GPIO_TRIGGER , False)
        time.sleep(0.5)
        GPIO.output(GPIO_TRIGGER , True)
        start = time.time()
        time.sleep(0.00001)
        GPIO.output(GPIO_TRIGGER , False)
        while GPIO.input(GPIO_ECHO)==0:
            start = time.time()
        stop = time.time()
        while GPIO.input(GPIO_ECHO)==1:
            stop = time.time()
        elapsed = stop-start
        distance = elapsed * speedsound
        distance = distance/2
        print(str,end="khoang cach: ")
        print(distance)
        print(str, end="khoang cach bat den: ")
        print(khoangcachbatden)
        if distance<=khoangcachbatden:
            GPIO.output(gpio_dencua, GPIO.HIGH)
        else:
            GPIO.output(gpio_dencua, GPIO.LOW)
        sleep(1)
def chuyendong():
    while True:
        i=GPIO.input(gpio_chuyendong)
        if i == 1: # để tránh trường hợp đèn cầu thang tắt khi bật trên web, nên định thời gian tắt đèn
            print("....")
            GPIO.output(gpio_dencauthang,1)
            time.sleep(thoigiantatdencauthang)
            GPIO.output(gpio_dencauthang,0)
        sleep(1)
def gas():    
    while True:       
        #digGas = GPIO.input(gpio_gasdigital) # Gas sensor digital output
        anaGas = GPIO.input(gpio_gasanalog)
        if anaGas == 1: # test only gas
            GPIO.output(gpio_denbep,1)
            print("phat hien gas")
        else :
            sleep(5)
            GPIO.output(gpio_denbep,0)
            print(".....................")
            
        sleep(1)

if __name__ == "__main__":

    t1=threading.Thread(target=laycauhinhtufirebase)            
    t2=threading.Thread(target=khoangcach)        
    t3=threading.Thread(target=chuyendong)
    t4=threading.Thread(target=update_firebase)
    t5=threading.Thread(target=gas)
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
