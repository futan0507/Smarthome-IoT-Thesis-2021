#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <AccelStepper.h>


#define HALFSTEP 8
#define gpio_loa  D0
#define gpio_den  D1  
#define gpio_quat 4 //D2
//#define gas_digital  D3  chuyển qua pi
//#define gas_analog  D1  chuyển qua pi
#define motorPin1  D5     // IN1 on the ULN2003 driver 1
#define motorPin2  D6    // IN2 on the ULN2003 driver 1
#define motorPin3  D7     // IN3 on the ULN2003 driver 1
#define motorPin4  D8     // IN4 on the ULN2003 driver 1

AccelStepper stepper1(HALFSTEP, motorPin1, motorPin3, motorPin2, motorPin4);
int khoangcachdichuyen=-1000;  // tương đương xoay 90 độ

const char* ssid = "Lenovo TAB3 8"; // Nhập tên WiFi 
const char* password = "haicot111"; // Nhập Mật khẩu WiFi 
const char* mqttServer = "192.168.43.56"; // Nhập địa chỉ của server MQTT

//const char* ssid = "KSBT 2"; // Nhập tên WiFi 
//const char* password = "123456789"; // Nhập Mật khẩu WiFi 
//const char* ssid = "ttbvsk-nhan vien 3"; // Nhập tên WiFi 
//const char* password = "123456789"; // Nhập Mật khẩu WiFi 
//const char* mqttServer = "172.16.16.48"; // Nhập địa chỉ của server MQTT

//const char* ssid = "emptyx"; // Nhập tên WiFi 
//const char* password = "@dmin31&"; // Nhập Mật khẩu WiFi 
//const char* mqttServer = "192.168.1.9"; // Nhập địa chỉ của server MQTT

String clientId = "ClientESP8266";            // Client ID của mạch
const char* m_topic = "topic";             // Topic mình đã tạo ở trên
WiFiClient espClient;
PubSubClient client(espClient);
long lastMsg = 0;
char msg[50];
int value = 0;
void setup() {  
  Serial.begin(9600);
  //setup động cơ bước
  stepper1.setMaxSpeed(2000.0);
  stepper1.setAcceleration(2000.0);
  stepper1.setSpeed(2000);
  //khai báo cảm biến
  pinMode(gpio_loa,OUTPUT);
  digitalWrite(gpio_loa,HIGH);   //HIGH là tắt loa
  //analogWrite(gas_analog, LOW);  //tắt điện tại chân này trước khi chờ tín hiệu từ nó
//  pinMode(gas_analog, INPUT);
//  pinMode(gas_digital, INPUT);
//  digitalWrite(gas_digital,HIGH);//thiết lập chân gas_digital =1, tức là ko có gas
  pinMode(gpio_den, OUTPUT);
  digitalWrite(gpio_den,LOW);
  pinMode(gpio_quat, OUTPUT);
  digitalWrite(gpio_quat,LOW);
  //setup mqtt  
  client.setKeepAlive(15);
  client.setSocketTimeout(15);
  setup_wifi();
  /* Hàm start - read Callback client */
  client.setServer(mqttServer, 1883);
  client.setCallback(callback);
}
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    //coi(100);
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}
/* Ham call back nhan lai du lieu */
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message read [");
  Serial.print(topic);
  Serial.print("] ");
  String chuoinhan="";
  for (int i = 0; i < length; i++) {
    chuoinhan+=(char)payload[i];
  }
  Serial.println();
  xulidulieu(chuoinhan);
}
void coi(int thoigianphat){
  digitalWrite(D0,LOW);  //low là mở loa
   delay(thoigianphat);
   digitalWrite(D0,HIGH);
}
void mocua(int thoigianchodongcua){
    stepper1.moveTo(khoangcachdichuyen);   // di chuyển đến vị trí mới
    int kc=stepper1.distanceToGo();   
    //thiết lập lại các thông số vận tốc thấy động cơ quay nhanh hơn
    stepper1.setMaxSpeed(2000.0);
    stepper1.setAcceleration(2000.0);
    stepper1.setSpeed(2000);  
    while( stepper1.distanceToGo()!=0){     
//    Serial.print(" khoang cach di chuyen: ");      in 2 dòng sẽ làm vận tốc motor chậm hơn, không hiểu nguyên nhân
      Serial.println(stepper1.distanceToGo());          // phải in tối thiểu 1 dòng để tránh WDT   
      stepper1.runSpeed(false);     //di chuyển theo chiều kim đồng hồ
      yield();      // ngăn chặn WDT
    }   
    delay(thoigianchodongcua); //thời gian tạm ngưng trước khi đóng cửa
    stepper1.moveTo(0); //quay về vị trí ban đầu
    kc=stepper1.distanceToGo(); 
    //thiết lập lại các thông số vận tốc thấy động cơ quay nhanh hơn
    stepper1.setMaxSpeed(2000.0);
    stepper1.setAcceleration(2000.0);
    stepper1.setSpeed(2000);  
    while( stepper1.distanceToGo()!=0){     
      Serial.println(stepper1.distanceToGo());  // phải in tối thiểu 1 dòng để tránh WDT           
      stepper1.runSpeed();     //di chuyển ngược chiều kim đồng hồ
      yield();    // ngăn chặn WDT
    }      
}
//bool gas(){
//  int ana=analogRead(gas_analog);//analog=0 khi khong co gas; =1023 khi phát hiện
//  int digi=digitalRead(gas_digital);//digital=1 khi không có gas;  =0 khi phát hiện
//  Serial.print("digital:");
//  Serial.println(digi);
//  if(digi==0){  // kiểm tra tín hiệu digital, phát hiện gas
//    return true;
//  }else{
//    return false;    
//  }
//  kiểm tra theo analog
//Serial.print("analog:");
//Serial.println(ana);
//  if(ana==1023){  // kiểm tra tín hiệu digital, phát hiện gas
//    return true;
//  }else{
//    return false;    
//  }  
//}
void guitrangthaidenquat(){
  String tingui="1";
  tingui+=String(digitalRead(gpio_den));
  tingui+="2";    
  tingui+=String(digitalRead(gpio_quat));   
  client.publish(m_topic, tingui.c_str()); //tingui.c_str() chuyen tingui tu kieu String sang const char*
}
void xulidulieu(String data)  //thực thi điều gì khi nhận chuỗi lệnh từ mqtt
{
  if(data !=""){
    Serial.print("coi keu");
    Serial.println(data);
    coi(30);
  }  
  if (data.length() == 2) {   //mở cửa, ký tự đầu là 1, ký tự sau nhân với 5 là số giây chờ đóng cửa 
    char kytucuoi=data[1]; // lấy ký tự cuối
    int socuoi=(int)kytucuoi-48;  //chuyển ký tự cuối thành số
    mocua(socuoi*5*1000);   // thời gian chờ đóng cửa bằng socuoi*5 giây   
  }else if (data == "211") {
    digitalWrite(gpio_den,HIGH);
  }else if (data == "210") {
    digitalWrite(gpio_den,LOW);
  }else if (data == "221") {
    digitalWrite(gpio_quat,HIGH);
  }else if (data == "220") {
    digitalWrite(gpio_quat,LOW);
  }else if (data == "can thong tin") {
    guitrangthaidenquat();
  }    
}
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      client.publish(m_topic, "Reconnect");               // Gửi dữ liệu
      client.subscribe(m_topic);                          // Theo dõi dữ liệu
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      // Doi 1s
      delay(1000);
    }
  }
}

void loop() {

  if (!client.connected()) {
    Serial.println("mat ket noi");
    reconnect();
  } 
  client.loop();
  Serial.print(",");
//  if(gas()){
//    Serial.print("có gas");
//    coi(500);
//  }
  delay(1000);

}
