/*
 * Living-room node (ESP32): DHT22 sensor + two relays (light, fan) over MQTT.
 *
 * Libraries (Arduino Library Manager): PubSubClient, "DHT sensor library" + Adafruit Unified Sensor.
 * Board: "ESP32 Dev Module". Copy secrets.h.example to secrets.h first.
 *
 * Topics published : home/livingroom/{temperature,humidity,light,fan}/state, home/devices/esp32-living/status
 * Topics subscribed: home/livingroom/{light,fan}/set   (payload ON | OFF)
 */
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include "secrets.h"

#define DHT_PIN   4
#define DHT_TYPE  DHT22
#define LIGHT_PIN 26
#define FAN_PIN   27
const bool RELAY_ACTIVE_LOW = true;          // most relay boards switch on a LOW signal
const unsigned long PUBLISH_MS = 10000;

const char* DEVICE_ID = "esp32-living";
const char* T_STATUS      = "home/devices/esp32-living/status";
const char* T_TEMP        = "home/livingroom/temperature/state";
const char* T_HUM         = "home/livingroom/humidity/state";
const char* T_LIGHT_STATE = "home/livingroom/light/state";
const char* T_LIGHT_SET   = "home/livingroom/light/set";
const char* T_FAN_STATE   = "home/livingroom/fan/state";
const char* T_FAN_SET     = "home/livingroom/fan/set";

WiFiClient net;
PubSubClient mqtt(net);
DHT dht(DHT_PIN, DHT_TYPE);
bool lightOn = false, fanOn = false;
unsigned long lastPublish = 0;

void setRelay(uint8_t pin, bool on) {
  digitalWrite(pin, (on != RELAY_ACTIVE_LOW) ? HIGH : LOW);
}

void publishRelays() {
  mqtt.publish(T_LIGHT_STATE, lightOn ? "ON" : "OFF", true);
  mqtt.publish(T_FAN_STATE, fanOn ? "ON" : "OFF", true);
}

void onMessage(char* topic, byte* payload, unsigned int len) {
  String p;
  for (unsigned int i = 0; i < len; i++) p += (char)payload[i];
  p.trim();
  p.toUpperCase();
  if (p != "ON" && p != "OFF") return;           // ignore anything unexpected
  bool on = (p == "ON");

  if (strcmp(topic, T_LIGHT_SET) == 0) { lightOn = on; setRelay(LIGHT_PIN, on); }
  else if (strcmp(topic, T_FAN_SET) == 0) { fanOn = on; setRelay(FAN_PIN, on); }
  publishRelays();                                // acknowledge with the new state
}

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}

void connectMqtt() {
  while (!mqtt.connected()) {
    // Last Will: the broker publishes "offline" if this node vanishes.
    if (mqtt.connect(DEVICE_ID, MQTT_USER, MQTT_PASS, T_STATUS, 1, true, "offline")) {
      mqtt.publish(T_STATUS, "online", true);
      mqtt.subscribe(T_LIGHT_SET, 1);
      mqtt.subscribe(T_FAN_SET, 1);
      publishRelays();
    } else {
      delay(3000);
    }
  }
}

void setup() {
  pinMode(LIGHT_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  setRelay(LIGHT_PIN, false);                     // safe state before networking starts
  setRelay(FAN_PIN, false);
  dht.begin();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMessage);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWifi();
  if (!mqtt.connected()) connectMqtt();
  mqtt.loop();

  if (millis() - lastPublish >= PUBLISH_MS) {
    lastPublish = millis();
    float t = dht.readTemperature(), h = dht.readHumidity();
    if (!isnan(t)) mqtt.publish(T_TEMP, String(t, 1).c_str());
    if (!isnan(h)) mqtt.publish(T_HUM, String(h, 0).c_str());
  }
}
