#include <WiFi.h>
#include <WebSocketsServer.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

const char* ssid = "shehin's S23";
const char* password = "shehiiiin";

WebSocketsServer webSocket = WebSocketsServer(81);
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40, Wire);

#define SERVOMIN  150
#define SERVOMAX  600
#define SERVO_FREQ 50

int servoChannels[5] = {0,1,2,3,4};
int currentAngles[5] = {0,0,0,0,0};
int targetAngles[5]  = {0,0,0,0,0};

void setServo(int channel, int angle){
  angle = constrain(angle,0,180);
  int pulselength = map(angle,0,180,SERVOMIN,SERVOMAX);
  pwm.setPWM(channel,0,pulselength);
}

void onWebSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length){
  if(type==WStype_TEXT){
    StaticJsonDocument<256> doc;
    if(!deserializeJson(doc,payload,length)){
      if(doc.containsKey("angles")){
        JsonArray arr = doc["angles"];
        for(int i=0;i<5;i++) targetAngles[i] = arr[i];
      }
    }
  }
}

void setup(){
  Serial.begin(115200);
  WiFi.begin(ssid,password);
  while(WiFi.status()!=WL_CONNECTED){delay(500); Serial.print(".");}
  Serial.println("\nWiFi connected"); Serial.println(WiFi.localIP());

  pwm.begin();
  pwm.setPWMFreq(SERVO_FREQ);
  delay(10);

  for(int i=0;i<5;i++) setServo(servoChannels[i],currentAngles[i]);

  webSocket.begin();
  webSocket.onEvent(onWebSocketEvent);
}

void loop(){
  webSocket.loop();

  for(int i=0;i<5;i++){
    int minAngle = (i<4)?0:0;     // Joints 0–3 min 0, gripper min 0
    int maxAngle = (i<4)?90:180;  // Joints 0–3 max 90, gripper max 180

    targetAngles[i] = constrain(targetAngles[i], minAngle, maxAngle);

    if(currentAngles[i]<targetAngles[i]) currentAngles[i]++;
    else if(currentAngles[i]>targetAngles[i]) currentAngles[i]--;
    setServo(servoChannels[i], currentAngles[i]);
  }

  delay(30);
}

