//주변환경의 온도와 습도를 측정하여 LCD에 출력하기
#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>
#include <DHT.h>
#include <DHT_U.h>

#define DHTPIN 8
#define DHTTYPE DHT11

hd44780_I2Cexp lcd; //LCD 객체
DHT dht(DHTPIN, DHTTYPE);

int red = 5, blue = 6;

void setup() {
  //시리얼, LCD, 온습도 센서 통신 설정
  Serial.begin(9600);
  lcd.begin(16, 2); //LCD 통신 사용
  dht.begin();
  //핀 모드 설정
  pinMode(red, OUTPUT);
  pinMode(blue, OUTPUT);
}

void loop() {
  //온도와 습도 값을 측정하고 변수에 저장하기
  float humi, temp;
  temp = dht.readTemperature();
  humi = dht.readHumidity();
  Serial.print("온도 : ");
  Serial.println(temp);
  Serial.print("습도 : ");
  Serial.println(humi);
  //센서가 측정하지 못 할 경우 측정 종료
  if(isnan(humi) || isnan(temp)){
    Serial.println("Failed to read from DHT sensor!!");
    return;
  }
  //온도와 습도 값 map 함수로 LED 전압 값으로 변환
  int tempValue, humiValue;
  tempValue = map(temp, -10, 40, 0, 255);
  humiValue = map(humi, 0, 100, 0, 255);

  //온 습도에 따른 LED 밝기 조절
  analogWrite(red, tempValue);
  analogWrite(blue, humiValue);
  
  //측정된 온도와 습도 출력하기
  lcd.clear (); //LCD 출력내용 지우기
  lcd.setCursor (0, 0);
  lcd.print("Temp: ");
  lcd.print (temp);
  lcd.setCursor (0, 1);
  lcd.print("Humi: ");
  lcd.print (humi);
  delay(300);
}
