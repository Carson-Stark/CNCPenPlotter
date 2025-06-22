#include <Servo.h>

byte EN = 8;
//Direction pin
byte X_DIR = 5;
byte Y_DIR = 6;
byte Z_DIR = 7;
//Step pin
byte X_STP = 2;
byte Y_STP = 3;
byte Z_STP = 4;
//limits
byte X_limit = 9;
byte Y_limit = 10;
//servo
byte servo = 11;
byte servoEn = 12;

int machinePosX = 0;
int machinePosY = 0;

bool drawing;
bool drawingPath;
bool moving;

Servo penServo;
int pos = 0;

int currentX = 0;
int currentY = 0;

void moveHome (int Speed) {
  bool Xhomed = false;
  bool Yhomed = false;
  int stepsX = 0;
  int stepsY = 0;

  digitalWrite(X_DIR, false);
  digitalWrite(Y_DIR, false);
  delay(100); //allow time for direction change
  
  while (!Xhomed || !Yhomed) {
    if (!Xhomed) {
      if (digitalRead(X_limit) == HIGH)
        Xhomed = true;
      else {
        digitalWrite(X_STP, HIGH);
        stepsX++;
      }
    }
    if (!Yhomed) {
      if (digitalRead(Y_limit) == HIGH)
        Yhomed = true;
      else {
        digitalWrite(Y_STP, HIGH);
        stepsY++;
      }
    }
    delayMicroseconds(Speed);
    digitalWrite(X_STP, LOW);
    digitalWrite(Y_STP, LOW);
    delayMicroseconds(Speed); 
  }

  currentX = 0;
  currentY = 0;
  delay (100);
}

int* calculateSpeeds (int speeds[2], int dist1, int dist2, int max_speed) {
  int speed1 = max_speed;
  int speed2 = max_speed;
  
  if (dist1 > dist2) {
    if (dist2 > 0)
      speed2 = 1/(dist2 / (dist1 / (1/(float)max_speed)));
    else
      speed2 = 0;
  }
  else {
    if (dist1 > 0)
      speed1 = 1/(dist1 / (dist2 / (1/(float)max_speed)));
    else
      speed1 = 0;
  }
  speeds[0] = speed1;
  speeds[1] = speed2;
}

void moveToPosition (int x, int y, int min_speed, int max_speed, int accelerationTime) {
  unsigned long prevStepX = 0;
  unsigned long prevStepY = 0;
  bool DirX = x > currentX;
  bool DirY = y > currentY;

  digitalWrite (X_DIR, DirX);
  digitalWrite (Y_DIR, DirY);
  int stepsInAcceleration = (1000/((float)(min_speed+max_speed)/2)) * (float)accelerationTime;
  int decelDistance = stepsInAcceleration;
  if (stepsInAcceleration > max(abs(currentX-x),abs(currentY-y))/2)
    decelDistance = max(abs(currentX-x),abs(currentY-y))/2;
  float speedDelta = float((min_speed - max_speed))/(float)accelerationTime*2;
  unsigned long startTime = millis();
  int speeds[2] = {500,500};
  float currentSpeed = min_speed;
  calculateSpeeds(speeds, abs(currentX-x), abs(currentY-y), round(currentSpeed));
  unsigned long lastSpeedCalc = millis();
  while (currentX != x || currentY != y) {
    if (millis()-lastSpeedCalc > 1) {
      if (currentSpeed > max_speed && max(abs(currentX-x),abs(currentY-y)) > decelDistance)
        currentSpeed -= speedDelta;
      else if (currentSpeed < min_speed && max(abs(currentX-x),abs(currentY-y)) < decelDistance)
        currentSpeed += speedDelta;
      calculateSpeeds(speeds, abs(currentX-x), abs(currentY-y), round(currentSpeed));
      lastSpeedCalc = millis();
    }
    if (micros() - prevStepX >= speeds[0] && currentX != x) {
      digitalWrite(X_STP, HIGH);
      digitalWrite(X_STP, LOW);
      currentX = currentX+(DirX ? 1 : -1);
      prevStepX = micros();
    }
    if (micros() - prevStepY >= speeds[1] && currentY != y) {
      digitalWrite(Y_STP, HIGH);
      digitalWrite(Y_STP, LOW);
      currentY = currentY+(DirY ? 1 : -1);
      prevStepY = micros();
    }
  }
}

void latch () {
  for (pos = 0; pos <= 270; pos += 1) { // goes from 180 degrees to 0 degrees
    penServo.write(pos);
    delay (1);                     
  }
  delay(1000);
  for (pos = 270; pos >= 0; pos -= 1) { // goes from 180 degrees to 0 degrees
    penServo.write(pos);
    delay (1);                     
  }
}

void penUp () {
  for (pos = 50; pos >= 0; pos -= 1) { // goes from 180 degrees to 0 degrees
    penServo.write(pos);
    delay (1);                     
  }
}

void penDown () {
  for (pos = 0; pos <= 50; pos += 1) { // goes from 0 degrees to 180 degrees
    penServo.write(pos);
    delay(3);            
  }
}

void setup(){
  pinMode(X_DIR, OUTPUT); 
  pinMode(X_STP, OUTPUT);
  pinMode(Y_DIR, OUTPUT); 
  pinMode(Y_STP, OUTPUT);
  pinMode(EN, OUTPUT);
  digitalWrite(EN, HIGH);

  pinMode (X_limit, INPUT_PULLUP);
  pinMode (Y_limit, INPUT_PULLUP);

  pinMode (servo, OUTPUT);
  pinMode (servoEn, OUTPUT);
  penServo.attach (servo);
  digitalWrite (servoEn, LOW);

  drawing = false;
  drawingPath = false;

  Serial.begin (9600);
}

unsigned long lastRest = 0;
bool newData = false;
String command = "";
void loop(){  
  while (Serial.available() > 0 && !newData){
    char newChar = char(Serial.read());
    command += newChar;
    if (command.indexOf(">") > -1) {
      newData = true;
      Serial.println ("ready");
    }
  }

  /*if (drawing) {
    if (millis() - lastRest > 60000) {
      digitalWrite (EN, HIGH);
      if (!drawingPath)
        penDown(); 
      delay (60000);
      if (!drawingPath)
        penUp(false);
      digitalWrite (EN, LOW);
      lastRest = millis();
    }
  }*/

  if (newData) {
    command = command.substring (0, command.indexOf (">"));
    command = command.substring (command.indexOf ("<")+1);
    if (command == "start") {
       digitalWrite(EN, LOW);
       digitalWrite (servoEn, HIGH);
       delay (200);
       penUp();
       delay (100);
       moveHome (200);
       Serial.println ("start");
       drawing = true;
       lastRest = millis();
    }
    else if (command == "pause") {
      penUp();
      drawing = false;
      drawingPath = false;
      delay (1000);
      digitalWrite(EN, HIGH);
      digitalWrite (servoEn, LOW);
      lastRest = 0;
    }
    else if (command == "unpause") {
       digitalWrite(EN, LOW);
       digitalWrite (servoEn, HIGH);
       delay (200);
       penUp();
       delay (100);
       drawing = true;
       lastRest = millis();
    }
    else if (command == "path") {
      penUp();
      delay (100);
      drawingPath = false;
    }
    else if (command == "stop") {
      penUp();
      drawing = false;
      drawingPath = false;
      delay (1000);
      digitalWrite(EN, HIGH);
      digitalWrite (servoEn, LOW);
      lastRest = 0;
    }
    else if (command.indexOf (",") > -1) {
      long points[2]; 
      //flip to account to origin change
      points[0] = 19150 - command.substring(0,command.indexOf(",")).toInt();
      points[1] = 15364 - command.substring(command.indexOf(",") + 1).toInt();
      moveToPosition (points[0], points[1], 800, 200, 250);
      if (!drawingPath) {
        penDown();
        delay (100);
        drawingPath = true;
      }
    }
    newData = false;
    command = "";
  }
}
