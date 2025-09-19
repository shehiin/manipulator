#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <Servo.h>

const char* ssid = "ssid";
const char* password = "pass";

ESP8266WebServer server(80);

Servo servos[5];
const int servoPins[5] = {D1, D2, D3, D4, D5};
int angles[5] = {90, 90, 90, 90, 90};
const int step = 5;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  
  Serial.println("Connected to Wi-Fi");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  for (int i = 0; i < 5; i++) servos[i].attach(servoPins[i]);
  for (int i = 0; i < 5; i++) servos[i].write(angles[i]);

  server.on("/", HTTP_GET, handleRoot);
  server.on("/cmd", HTTP_GET, handleCmd);
  server.begin();
}

void loop() {
  server.handleClient();
}

void handleRoot() {
  String html = "<!DOCTYPE html><html><head><title>Robot Arm Control</title></head><body>";
  html += "<h1>Control Robot Arm</h1>";

  // Buttons for each servo direction
  html += "<button onclick=\"sendCmd('Q')\">Base +</button>";
  html += "<button onclick=\"sendCmd('A')\">Base -</button><br>";

  html += "<button onclick=\"sendCmd('W')\">Joint2 +</button>";
  html += "<button onclick=\"sendCmd('S')\">Joint2 -</button><br>";

  html += "<button onclick=\"sendCmd('E')\">Joint3 +</button>";
  html += "<button onclick=\"sendCmd('D')\">Joint3 -</button><br>";

  html += "<button onclick=\"sendCmd('R')\">Joint4 +</button>";
  html += "<button onclick=\"sendCmd('F')\">Joint4 -</button><br>";

  html += "<button onclick=\"sendCmd('T')\">Gripper +</button>";
  html += "<button onclick=\"sendCmd('G')\">Gripper -</button><br>";

  html += R"(
    <script>
      function sendCmd(cmd) {
        fetch('/cmd?key=' + cmd);
      }
    </script>
  )";

  html += "</body></html>";

  server.send(200, "text/html", html);
}

void handleCmd() {
  String key = server.arg("key");
  if (key.length() == 1) {
    processCommand(key.charAt(0));
  }
  server.send(200, "text/plain", "OK");
}

void processCommand(char cmd) {
  switch (cmd) {
    case 'Q': incrementServo(0, 1); break;
    case 'A': incrementServo(0, -1); break;
    case 'W': incrementServo(1, 1); break;
    case 'S': incrementServo(1, -1); break;
    case 'E': incrementServo(2, 1); break;
    case 'D': incrementServo(2, -1); break;
    case 'R': incrementServo(3, 1); break;
    case 'F': incrementServo(3, -1); break;
    case 'T': incrementServo(4, 1); break;
    case 'G': incrementServo(4, -1); break;
  }
}

void incrementServo(int index, int direction) {
  angles[index] += step * direction;
  if (angles[index] > 180) angles[index] = 180;
  if (angles[index] < 0) angles[index] = 0;
  servos[index].write(angles[index]);
}
