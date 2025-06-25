# ArmWebPad

Manual web control interface for 4-DOF arm using ESP8266.

## Usage

1. Flash `control_web.ino` to your ESP8266.
2. Open Serial Monitor and note the IP address.
3. Edit `webpad.html` → replace the IP inside the `send(cmd)` function with the one from Serial Monitor.
4. Open `webpad.html` in any browser.

Done.
