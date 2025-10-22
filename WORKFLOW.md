# 🔄 System Workflow Diagram

## Overall System Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Camera Feed   │───▶│  MediaPipe Hand  │───▶│ Gesture Detection│
│   (OpenCV)      │    │    Detection     │    │   Algorithm     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             ▼
│   Game Objects  │◀───│  Game Logic      │    ┌─────────────────┐
│   Rendering     │    │  Processing      │◀───│  Hand Gestures  │
└─────────────────┘    └──────────────────┘    │   Recognition   │
         │                       │              └─────────────────┘
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│   Visual        │    │   Game State     │
│   Display       │    │   Updates        │
└─────────────────┘    └──────────────────┘
```

## Hand Detection Pipeline

```
Camera Frame → RGB Conversion → MediaPipe Processing → Hand Landmarks → Gesture Classification
     ↓              ↓                    ↓                   ↓                ↓
  Capture       Color Space        AI Detection       21 Points per      Action Mapping
  (640x480)     Conversion         (Real-time)        Hand              to Game Events
```

## Game Mode Logic

### Single Hand Mode
```
Single Hand Detection → Movement Control + Weapon Gestures → Combined Actions
         ↓                        ↓                              ↓
    One Hand Input           Player Position              All Game Actions
                         + Gesture Recognition
```

### Dual Hand Mode
```
Left Hand Detection → Movement Control → Player Position
         ↓                    ↓              ↓
    Left Hand Input       Flight Control    Position Updates

Right Hand Detection → Weapon Gestures → Combat Actions
         ↓                   ↓               ↓
    Right Hand Input    Weapon Recognition   Bullets/Attacks
```

## Gesture Recognition Flow

```
Hand Landmarks → Finger Analysis → Distance Calculations → Gesture Classification
       ↓               ↓                    ↓                      ↓
   21 Points      Extension Check      Pinch Detection       Action Mapping
   per Hand       (Finger Counting)    (Thumb-Index)        (Game Events)
```

## Game Object Lifecycle

```
Spawn → Update → Collision Detection → Effects → Cleanup
  ↓        ↓            ↓                ↓         ↓
Create   Movement    Hit Detection    Particles   Remove
Objects  Physics     Score Updates    Explosions  Off-screen
```

## Main Menu System

```
Program Start → File Check → Menu Display → User Selection → Game Launch
      ↓             ↓            ↓             ↓              ↓
   Initialize   Validate      Show Options   Input Handling   Load Game
   System       Dependencies  Interactive    Error Check     Mode Setup
```

## Performance Optimization

```
Camera Setup → Frame Processing → Hand Tracking → Game Logic → Rendering
      ↓              ↓                ↓             ↓           ↓
  Optimize       Real-time        Efficient      Fast         Smooth
  Resolution     Processing       Detection      Updates      Display
  & FPS          Pipeline         Algorithm     & Physics    & Effects
```
