#!/usr/bin/env python
"""
Xbox Controller Arm Control
Controls: LStick=base/shoulder, RStick=elbow/wrist, Triggers=wrist_rot, Bumpers=gripper
D-Pad=speed, A=center, B=e-stop, Start=quit
"""

import sys
import os
import time

os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame

sys.path.append("..")
from scservo_sdk import *

# CONFIG
DEVICENAME = '/dev/ttyACM0'
BAUDRATE = 1000000

SERVO_CONFIG = {
    'base':        1,
    'shoulder':    2,
    'elbow':       3,
    'wrist_pitch': 4,
    'wrist_rot':   5,
    'gripper':     6,
}

SERVO_LIMITS = {
    1: [500, 3500, 2048],
    2: [500, 3500, 2048],
    3: [500, 3500, 2048],
    4: [500, 3500, 2048],
    5: [500, 3500, 2048],
    6: [1500, 2500, 2048],
}

# Movement
DEFAULT_SPEED = 1000
MAX_SPEED = 2500
MIN_SPEED = 200
SPEED_STEP = 150
MOVING_ACC = 40
DEADZONE = 0.15
UPDATE_RATE = 100
STEP_SIZE = 4  # Position change per update (smoother, same overall speed)

# Axis/button mapping
AXIS_LX, AXIS_LY, AXIS_LT = 0, 1, 2
AXIS_RX, AXIS_RY, AXIS_RT = 3, 4, 5
BTN_A, BTN_B, BTN_LB, BTN_RB, BTN_START = 0, 1, 4, 5, 7


def apply_deadzone(value, deadzone):
    if abs(value) < deadzone:
        return 0.0
    sign = 1 if value > 0 else -1
    return sign * (abs(value) - deadzone) / (1.0 - deadzone)


def normalize_trigger(value):
    return (value + 1.0) / 2.0


class ArmController:
    def __init__(self, port_handler, packet_handler):
        self.servo = packet_handler
        self.positions = {sid: SERVO_LIMITS[sid][2] for sid in SERVO_LIMITS}
        self.speed = DEFAULT_SPEED
        self.emergency_stop = False

    def update_servo(self, servo_id, position):
        if servo_id is None:
            return
        limits = SERVO_LIMITS.get(servo_id, [0, 4095, 2048])
        position = max(limits[0], min(limits[1], int(position)))
        self.positions[servo_id] = position
        try:
            self.servo.WritePosEx(servo_id, position, self.speed, MOVING_ACC)
        except Exception as e:
            print(f"Servo {servo_id} error: {e}")

    def move_servo(self, servo_id, delta):
        """Move servo by delta amount"""
        if servo_id is None or delta == 0:
            return
        current = self.positions.get(servo_id, 2048)
        self.update_servo(servo_id, current + delta)

    def center_all(self):
        print("Centering all servos...")
        for servo_id in SERVO_LIMITS:
            self.update_servo(servo_id, SERVO_LIMITS[servo_id][2])

    def adjust_speed(self, delta):
        self.speed = max(MIN_SPEED, min(MAX_SPEED, self.speed + delta))
        print(f"Speed: {self.speed}")


def print_status(joystick, arm):
    os.system('clear' if os.name != 'nt' else 'cls')
    
    lx = apply_deadzone(joystick.get_axis(AXIS_LX), DEADZONE)
    ly = apply_deadzone(-joystick.get_axis(AXIS_LY), DEADZONE)
    rx = apply_deadzone(joystick.get_axis(AXIS_RX), DEADZONE)
    ry = apply_deadzone(-joystick.get_axis(AXIS_RY), DEADZONE)
    lt = normalize_trigger(joystick.get_axis(AXIS_LT))
    rt = normalize_trigger(joystick.get_axis(AXIS_RT))
    
    print("=" * 55)
    print("XBOX ARM CONTROL")
    print("=" * 55)
    print(f"Speed: {arm.speed}  |  E-Stop: {'ON' if arm.emergency_stop else 'OFF'}")
    print(f"\nInput: LStick({lx:+.2f},{ly:+.2f}) RStick({rx:+.2f},{ry:+.2f}) Trig({lt:.2f},{rt:.2f})")
    print("\nServos:")
    for name, sid in SERVO_CONFIG.items():
        if sid:
            pos = arm.positions.get(sid, 0)
            limits = SERVO_LIMITS.get(sid, [0, 4095, 2048])
            pct = (pos - limits[0]) / (limits[1] - limits[0]) * 100
            bar = "#" * int(pct / 5) + "-" * (20 - int(pct / 5))
            print(f"  {name:12} [{bar}] {pos:4d}")
    print("-" * 55)
    print("D-Pad=speed | A=center | B=e-stop | Start=quit")


def main():
    print("Xbox Arm Controller")
    
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("No controller found!")
        return 1
    
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Controller: {joystick.get_name()}")
    
    portHandler = PortHandler(DEVICENAME)
    packetHandler = sms_sts(portHandler)
    
    if not portHandler.openPort():
        print(f"Failed to open {DEVICENAME}")
        pygame.quit()
        return 1
    
    if not portHandler.setBaudRate(BAUDRATE):
        print("Failed to set baudrate")
        portHandler.closePort()
        pygame.quit()
        return 1
    
    print(f"Connected to {DEVICENAME}")
    
    arm = ArmController(portHandler, packetHandler)
    prev_a, prev_b, prev_dpad = False, False, (0, 0)
    last_display = 0
    
    try:
        while True:
            pygame.event.pump()
            
            if joystick.get_button(BTN_START):
                print("Quitting...")
                break
            
            # A = center
            a = joystick.get_button(BTN_A)
            if a and not prev_a:
                arm.center_all()
            prev_a = a
            
            # B = e-stop toggle
            b = joystick.get_button(BTN_B)
            if b and not prev_b:
                arm.emergency_stop = not arm.emergency_stop
                print("E-STOP" if arm.emergency_stop else "E-Stop released")
            prev_b = b
            
            # D-pad = speed
            dpad = joystick.get_hat(0) if joystick.get_numhats() > 0 else (0, 0)
            if dpad[1] == 1 and prev_dpad[1] != 1:
                arm.adjust_speed(SPEED_STEP)
            elif dpad[1] == -1 and prev_dpad[1] != -1:
                arm.adjust_speed(-SPEED_STEP)
            prev_dpad = dpad
            
            if not arm.emergency_stop:
                cfg = SERVO_CONFIG
                
                # Sticks control incremental movement
                lx = apply_deadzone(joystick.get_axis(AXIS_LX), DEADZONE)
                ly = apply_deadzone(-joystick.get_axis(AXIS_LY), DEADZONE)
                rx = apply_deadzone(joystick.get_axis(AXIS_RX), DEADZONE)
                ry = apply_deadzone(-joystick.get_axis(AXIS_RY), DEADZONE)
                
                arm.move_servo(cfg['base'], lx * STEP_SIZE)
                arm.move_servo(cfg['shoulder'], ly * STEP_SIZE)
                arm.move_servo(cfg['elbow'], rx * STEP_SIZE)
                arm.move_servo(cfg['wrist_pitch'], ry * STEP_SIZE)
                
                # Triggers for wrist rotation
                if cfg['wrist_rot']:
                    lt = normalize_trigger(joystick.get_axis(AXIS_LT))
                    rt = normalize_trigger(joystick.get_axis(AXIS_RT))
                    if rt > 0.1:
                        arm.move_servo(cfg['wrist_rot'], rt * STEP_SIZE)
                    elif lt > 0.1:
                        arm.move_servo(cfg['wrist_rot'], -lt * STEP_SIZE)
                
                # Bumpers for gripper
                if cfg['gripper']:
                    limits = SERVO_LIMITS.get(cfg['gripper'], [0, 4095, 2048])
                    if joystick.get_button(BTN_RB):
                        arm.update_servo(cfg['gripper'], limits[1])
                    elif joystick.get_button(BTN_LB):
                        arm.update_servo(cfg['gripper'], limits[0])
            
            if time.time() - last_display > 0.2:
                print_status(joystick, arm)
                last_display = time.time()
            
            time.sleep(1.0 / UPDATE_RATE)
            
    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        portHandler.closePort()
        pygame.quit()
        print("Done")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
