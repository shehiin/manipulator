# Manipulator

Open-source 5-DOF robotic arm for embodied AI research.

- **Frame**: 2020 Aluminum Extrusions.
- **Motors**: STS3215 Serial Bus Servos.
- **Software**: LeRobot / Python.
[Hardware](./hardware) | [Control](./control)

## Usage

### Setup
```bash
git clone https://github.com/shehiin/manipulator.git
cd manipulator/control/STServo_Python
pip install -r requirements.txt
```

### Testing Servos
To manually test individual servos:
```bash
python stservo-env/sms_sts/test.py
```

### Configuration
For changing servo IDs, refer to the [official SO-100 documentation](https://huggingface.co/docs/lerobot/so101) or use the included utility:
```bash
python stservo-env/sms_sts/change_id.py
```
