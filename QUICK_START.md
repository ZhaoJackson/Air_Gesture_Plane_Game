# 🚀 Quick Start Guide

## Installation

1. **Install Dependencies**
```bash
pip install opencv-python mediapipe numpy
```

2. **Verify Installation**
```bash
python -c "import cv2, mediapipe, numpy; print('All packages installed successfully!')"
```

## Running the Games

1. **Start Main Menu**
```bash
python main.py
```

2. **Choose Your Game**
   - `1` - Air Gesture Game (Single Hand)
   - `2` - Air Gesture Game (Dual Hand)
   - `3` - Plane Attack Game (Single Hand)
   - `4` - Plane Attack Game (Dual Hand)
   - `5` - Camera Tracking Demo
   - `0` - Exit

## Basic Controls

### Air Gesture Game
- **Move Hand** → Control player ship
- **👌 Pinch** → Shoot bullets
- **👍 Thumbs Up** → Activate shield
- **✌️ Peace Sign** → Special attack
- **👊 Fist** → Power punch

### Plane Attack Game
- **Move Hand** → Control plane flight
- **👌 Pinch** → Machine gun
- **☝️ Point** → Fire missile
- **🖐️ Open Palm** → Drop bomb
- **✌️ Peace Sign** → Barrel roll attack

## Tips for Best Performance

1. **Lighting**: Ensure good lighting on your hands
2. **Distance**: Keep hands 1-2 feet from camera
3. **Background**: Use a plain background for better detection
4. **Gestures**: Make clear, deliberate hand movements
5. **Camera**: Close other applications using the camera

## Troubleshooting

- **Camera not found**: Check camera permissions
- **Poor hand detection**: Improve lighting conditions
- **Laggy performance**: Close other camera-using apps
- **Import errors**: Reinstall dependencies

## Quick Test

Run this to test everything works:
```bash
python -c "
from air_gesture_game import AirGestureGame
from dual_hand_plane_game import DualHandPlaneGame
print('✅ All games ready to play!')
"
```

Enjoy playing! 🎮
