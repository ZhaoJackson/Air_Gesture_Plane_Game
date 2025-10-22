#!/usr/bin/env python3
"""
MAIN MENU - AIR GESTURE GAMES
Choose between different games and hand modes
"""

import cv2
import time
import sys
import os

def show_menu():
    """Display the main menu and get user choice"""
    print("🎮" + "=" * 60 + "🎮")
    print("           AIR GESTURE GAMES - MAIN MENU")
    print("🎮" + "=" * 60 + "🎮")
    print()
    print("🎯 AVAILABLE GAMES:")
    print()
    print("1️⃣  AIR GESTURE GAME (Single Hand)")
    print("    • Classic space shooter")
    print("    • One hand controls movement + weapons")
    print("    • 20+ different gesture attacks")
    print()
    print("2️⃣  AIR GESTURE GAME (Dual Hand)")
    print("    • Enhanced space shooter")
    print("    • Left hand: Movement")
    print("    • Right hand: Weapons")
    print()
    print("3️⃣  PLANE ATTACK GAME (Single Hand)")
    print("    • Aviation combat simulator")
    print("    • One hand controls flight + weapons")
    print("    • Realistic plane physics")
    print()
    print("4️⃣  PLANE ATTACK GAME (Dual Hand)")
    print("    • Advanced aviation combat")
    print("    • Left hand: Flight control")
    print("    • Right hand: Weapon systems")
    print()
    print("5️⃣  CAMERA TRACKING DEMO")
    print("    • Hand tracking demonstration")
    print("    • Camera follows hand movement")
    print("    • Gesture detection test")
    print()
    print("0️⃣  EXIT")
    print()
    print("🎮" + "=" * 60 + "🎮")
    print()
    
    while True:
        try:
            choice = input("👉 Enter your choice (0-5): ").strip()
            if choice in ['0', '1', '2', '3', '4', '5']:
                return choice
            else:
                print("❌ Invalid choice! Please enter 0-5.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return '0'
        except Exception:
            print("❌ Invalid input! Please enter 0-5.")

def run_air_gesture_game(dual_hand_mode=False):
    """Run the air gesture game"""
    try:
        from air_gesture_game import AirGestureGame
        print(f"\n🚀 Starting Air Gesture Game ({'Dual Hand' if dual_hand_mode else 'Single Hand'} Mode)...")
        time.sleep(2)
        
        game = AirGestureGame(dual_hand_mode=dual_hand_mode)
        game.run()
        
    except ImportError as e:
        print(f"❌ Error importing air_gesture_game: {e}")
        print("Make sure air_gesture_game.py is in the same directory.")
    except Exception as e:
        print(f"❌ Error running Air Gesture Game: {e}")
    
    print("\n🎮 Returning to main menu...")
    time.sleep(2)

def run_plane_game(dual_hand_mode=True):
    """Run the plane attack game"""
    try:
        from dual_hand_plane_game import DualHandPlaneGame
        print(f"\n✈️ Starting Plane Attack Game ({'Dual Hand' if dual_hand_mode else 'Single Hand'} Mode)...")
        time.sleep(2)
        
        game = DualHandPlaneGame(dual_hand_mode=dual_hand_mode)
        game.run()
        
    except ImportError as e:
        print(f"❌ Error importing dual_hand_plane_game: {e}")
        print("Make sure dual_hand_plane_game.py is in the same directory.")
    except Exception as e:
        print(f"❌ Error running Plane Attack Game: {e}")
    
    print("\n🎮 Returning to main menu...")
    time.sleep(2)

def run_camera_demo():
    """Run the camera tracking demo"""
    print("\n📹 Starting Camera Tracking Demo...")
    time.sleep(2)
    
    import mediapipe as mp
    import math
    import numpy as np
    
    # Ensure cv2 constants are available
    try:
        # Try to access cv2 constants
        _ = cv2.CAP_PROP_FRAME_WIDTH
    except AttributeError:
        # If constants are not available, import them
        import cv2.cv2 as cv2

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    # Camera following parameters
    camera_pan = 0.0
    camera_tilt = 0.0
    smooth_pan, smooth_tilt = 0.0, 0.0
    FOLLOW_SPEED = 2.0
    DEAD_ZONE = 0.1
    MAX_PAN = 45.0
    MAX_TILT = 30.0

    # Hand tracking smoothing
    gesture_detected = False
    PINCH_THRESH = 0.05

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("📹 Camera Tracking Demo Started!")
    print("✋ Move your hand to control the camera")
    print("👌 Pinch to trigger gesture detection")
    print("⌨️ Press ESC to return to menu")

    with mp_hands.Hands(
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    ) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)

            if res.multi_hand_landmarks:
                hand = res.multi_hand_landmarks[0]
                lm = hand.landmark

                # Key points
                ix, iy = lm[8].x, lm[8].y  # Index finger tip
                tx, ty = lm[4].x, lm[4].y  # Thumb tip
                wx, wy = lm[0].x, lm[0].y  # Wrist

                # Calculate hand position relative to frame center
                hand_offset_x = wx - 0.5
                hand_offset_y = wy - 0.5

                # Apply dead zone
                if abs(hand_offset_x) > DEAD_ZONE:
                    target_pan = hand_offset_x * MAX_PAN * 2
                    target_pan = max(-MAX_PAN, min(MAX_PAN, target_pan))
                else:
                    target_pan = smooth_pan

                if abs(hand_offset_y) > DEAD_ZONE:
                    target_tilt = -hand_offset_y * MAX_TILT * 2
                    target_tilt = max(-MAX_TILT, min(MAX_TILT, target_tilt))
                else:
                    target_tilt = smooth_tilt

                # Smooth camera movement
                alpha = 0.1
                smooth_pan = alpha * target_pan + (1 - alpha) * smooth_pan
                smooth_tilt = alpha * target_tilt + (1 - alpha) * smooth_tilt

                # Detect pinch gesture
                pinch_dist = math.hypot(ix - tx, iy - ty)
                if pinch_dist < PINCH_THRESH and not gesture_detected:
                    gesture_detected = True
                    print(f"🎯 Gesture detected! Camera: Pan={smooth_pan:.1f}°, Tilt={smooth_tilt:.1f}°")
                elif pinch_dist >= PINCH_THRESH * 1.3 and gesture_detected:
                    gesture_detected = False

                # Apply perspective transformation
                frame_height, frame_width = frame.shape[:2]
                offset_x = int(smooth_pan * 3)
                offset_y = int(smooth_tilt * 3)
                
                src_points = np.float32([
                    [0, 0],
                    [frame_width, 0],
                    [frame_width, frame_height],
                    [0, frame_height]
                ])
                
                dst_points = np.float32([
                    [0 + offset_x, 0 + offset_y],
                    [frame_width + offset_x, 0 - offset_y],
                    [frame_width - offset_x, frame_height - offset_y],
                    [0 - offset_x, frame_height + offset_y]
                ])
                
                try:
                    perspective_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
                    frame = cv2.warpPerspective(frame, perspective_matrix, (frame_width, frame_height))
                except:
                    pass

                # Visual feedback
                center_x, center_y = frame_width // 2, frame_height // 2
                
                # Draw center crosshair
                cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (255, 255, 255), 2)
                cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (255, 255, 255), 2)
                
                # Draw hand position
                hand_pixel_x = int(wx * frame_width)
                hand_pixel_y = int(wy * frame_height)
                cv2.circle(frame, (hand_pixel_x, hand_pixel_y), 15, (0, 255, 255), 3)
                
                # Draw finger tips
                cv2.circle(frame, (int(ix * frame_width), int(iy * frame_height)), 8, (0, 255, 0), -1)
                cv2.circle(frame, (int(tx * frame_width), int(ty * frame_height)), 8, (255, 0, 0), -1)
                
                # Draw hand landmarks
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
                
                # Draw status
                status_text = f"Camera: Pan={smooth_pan:.1f}° Tilt={smooth_tilt:.1f}°"
                cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                if gesture_detected:
                    cv2.putText(frame, "GESTURE DETECTED!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    
            else:
                # No hand detected - return camera to center
                smooth_pan *= 0.95
                smooth_tilt *= 0.95

            cv2.imshow("Camera Hand Tracking Demo - ESC to return to menu", frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

    cap.release()
    cv2.destroyAllWindows()
    
    print("\n🎮 Returning to main menu...")
    time.sleep(2)

def main():
    """Main menu loop"""
    print("🎮 Welcome to Air Gesture Games!")
    print("🔧 Initializing system...")
    time.sleep(1)
    
    # Check if game files exist
    games_available = {
        'air_gesture': os.path.exists('air_gesture_game.py'),
        'plane_game': os.path.exists('dual_hand_plane_game.py')
    }
    
    if not games_available['air_gesture']:
        print("⚠️  Warning: air_gesture_game.py not found!")
    if not games_available['plane_game']:
        print("⚠️  Warning: dual_hand_plane_game.py not found!")
    
    while True:
        try:
            choice = show_menu()
            
            if choice == '0':
                print("\n👋 Thanks for playing Air Gesture Games!")
                print("🎮 See you next time!")
                break
                
            elif choice == '1':
                if games_available['air_gesture']:
                    run_air_gesture_game(dual_hand_mode=False)
                else:
                    print("❌ Air Gesture Game not available!")
                    time.sleep(2)
                    
            elif choice == '2':
                if games_available['air_gesture']:
                    run_air_gesture_game(dual_hand_mode=True)
                else:
                    print("❌ Air Gesture Game not available!")
                    time.sleep(2)
                    
            elif choice == '3':
                if games_available['plane_game']:
                    run_plane_game(dual_hand_mode=False)
                else:
                    print("❌ Plane Attack Game not available!")
                    time.sleep(2)
                    
            elif choice == '4':
                if games_available['plane_game']:
                    run_plane_game(dual_hand_mode=True)
                else:
                    print("❌ Plane Attack Game not available!")
                    time.sleep(2)
                    
            elif choice == '5':
                run_camera_demo()
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            print("🔄 Returning to main menu...")
            time.sleep(2)

if __name__ == "__main__":
    main()