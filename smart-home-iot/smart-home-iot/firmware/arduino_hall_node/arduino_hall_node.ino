/*
 * Hallway node (Arduino Uno/Nano): PIR motion sensor, light relay/LED, servo door lock.
 * Talks to the Raspberry Pi over USB serial (9600 baud); smarthome/serial_bridge.py relays it to MQTT.
 *
 * Protocol, one text line per message:  key:value
 *   Out: motion:0|1   light:ON|OFF   lock:LOCKED|UNLOCKED
 *   In : light:ON|OFF   lock:LOCK|UNLOCK   sync:1  (resend all states)
 */
#include <Servo.h>

const uint8_t PIR_PIN = 2;
const uint8_t LIGHT_PIN = 8;
const uint8_t SERVO_PIN = 9;
const int SERVO_LOCKED = 0;      // adjust to your mechanism
const int SERVO_UNLOCKED = 90;

Servo lockServo;
bool lastMotion = false, lightOn = false, locked = true;
String line;

void reportLight() { Serial.println(lightOn ? "light:ON" : "light:OFF"); }
void reportLock()  { Serial.println(locked ? "lock:LOCKED" : "lock:UNLOCKED"); }

void setLight(bool on) { lightOn = on; digitalWrite(LIGHT_PIN, on ? HIGH : LOW); reportLight(); }
void setLock(bool lock) { locked = lock; lockServo.write(lock ? SERVO_LOCKED : SERVO_UNLOCKED); reportLock(); }

void handleLine(const String& msg) {
  int sep = msg.indexOf(':');
  if (sep < 1) return;
  String key = msg.substring(0, sep), val = msg.substring(sep + 1);
  if (key == "light" && (val == "ON" || val == "OFF")) setLight(val == "ON");
  else if (key == "lock" && (val == "LOCK" || val == "UNLOCK")) setLock(val == "LOCK");
  else if (key == "sync") { reportLight(); reportLock(); Serial.println(lastMotion ? "motion:1" : "motion:0"); }
}

void setup() {
  Serial.begin(9600);
  pinMode(PIR_PIN, INPUT);
  pinMode(LIGHT_PIN, OUTPUT);
  lockServo.attach(SERVO_PIN);
  setLight(false);
  setLock(true);
}

void loop() {
  bool motion = digitalRead(PIR_PIN) == HIGH;
  if (motion != lastMotion) {
    lastMotion = motion;
    Serial.println(motion ? "motion:1" : "motion:0");
  }
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') { handleLine(line); line = ""; }
    else if (c != '\r' && line.length() < 32) line += c;
  }
}
