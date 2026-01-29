#!/usr/bin/env python
"""
Replay Recorded Motions
Loads 'motion_record.json' and replays the sequence of servo positions.
"""

import sys
import os
import time
import json

sys.path.append("..")
from scservo_sdk import *

# CONFIG
DEVICENAME = '/dev/ttyACM0'
BAUDRATE = 1000000

def main():
    print("Motion Replay Tool")
    
    # Default to latest recording
    filename = os.path.join("recordings", "latest.json")
    
    # Allow command line override
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        
    if not os.path.exists(filename):
        print(f"Error: {filename} not found!")
        print("Please record a motion first using record.py (Press Y to record)")
        return 1
        
    print(f"Loading {filename}...")
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load data: {e}")
        return 1
        
    if not data:
        print("No data in file!")
        return 1
        
    print(f"Loaded {len(data)} frames. Duration: {data[-1]['time']:.2f}s")
    
    # Connect to Servos
    portHandler = PortHandler(DEVICENAME)
    packetHandler = sms_sts(portHandler)
    
    if not portHandler.openPort():
        print(f"Failed to open {DEVICENAME}")
        return 1
    
    if not portHandler.setBaudRate(BAUDRATE):
        print("Failed to set baudrate")
        portHandler.closePort()
        return 1
    
    print(f"Connected to {DEVICENAME}")
    
    try:
        # Initial Move to Start Position (slowly)
        print("Moving to start position...")
        start_pos = data[0]['positions']
        for sid_str, pos in start_pos.items():
            packetHandler.WritePosEx(int(sid_str), int(pos), 1000, 40)
        time.sleep(2.0)
        
        print("Starting Replay...")
        start_time = time.time()
        
        for i, frame in enumerate(data):
            # Synchronization
            target_time = frame['time']
            current_time = time.time() - start_time
            
            # Use max to prevent negative sleep if falling behind
            sleep_time = max(0, target_time - current_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                # If we are behind, busy wait/skip? No, just run as fast as possible.
                pass
            
            # Send positions
            positions = frame['positions']
            speed = frame.get('speed', 1000)
            acc = frame.get('acc', 40)
            
            for sid_str, pos in positions.items():
                sid = int(sid_str)
                packetHandler.WritePosEx(sid, int(pos), int(speed), int(acc))
                
            if i % 10 == 0:
                print(f"Time: {target_time:.2f}s / {data[-1]['time']:.2f}s", end='\r')
                
        print(f"\nReplay complete!")
        
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        portHandler.closePort()
        print("Done")
        
    return 0

if __name__ == '__main__':
    sys.exit(main())
