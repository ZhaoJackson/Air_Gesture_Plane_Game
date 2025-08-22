import cv2, time, math
import numpy as np
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils

# Camera following parameters
camera_pan = 0.0    # Horizontal camera rotation (-180 to 180 degrees)
camera_tilt = 0.0   # Vertical camera rotation (-90 to 90 degrees)
smooth_pan, smooth_tilt = 0.0, 0.0
FOLLOW_SPEED = 2.0  # How fast camera follows (higher = more responsive)
DEAD_ZONE = 0.1     # Center dead zone where camera doesn't move
MAX_PAN = 45.0      # Maximum pan angle in degrees
MAX_TILT = 30.0     # Maximum tilt angle in degrees

# Hand tracking smoothing
smooth_x, smooth_y = None, None
gesture_detected = False
PINCH_THRESH = 0.05  # Pinch threshold for gesture detection

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)  # Set consistent frame rate

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

            # Key points: Index finger tip(8), Thumb tip(4), Wrist(0)
            ix, iy = lm[8].x, lm[8].y  # Index finger tip
            tx, ty = lm[4].x, lm[4].y  # Thumb tip
            wx, wy = lm[0].x, lm[0].y  # Wrist (center of hand)

            # Use wrist as the main tracking point for camera following
            hand_center_x, hand_center_y = wx, wy

            # Calculate hand position relative to frame center
            # Convert from normalized coordinates (0-1) to centered coordinates (-0.5 to 0.5)
            hand_offset_x = hand_center_x - 0.5  # Negative = left, Positive = right
            hand_offset_y = hand_center_y - 0.5  # Negative = up, Positive = down

            # Apply dead zone - don't move camera if hand is near center
            if abs(hand_offset_x) > DEAD_ZONE:
                target_pan = hand_offset_x * MAX_PAN * 2  # Scale to max pan range
                target_pan = max(-MAX_PAN, min(MAX_PAN, target_pan))  # Clamp to limits
            else:
                target_pan = smooth_pan  # Stay at current position

            if abs(hand_offset_y) > DEAD_ZONE:
                target_tilt = -hand_offset_y * MAX_TILT * 2  # Invert Y (up = negative tilt)
                target_tilt = max(-MAX_TILT, min(MAX_TILT, target_tilt))  # Clamp to limits
            else:
                target_tilt = smooth_tilt  # Stay at current position

            # Smooth camera movement
            alpha = 0.1  # Lower alpha = smoother movement
            smooth_pan = alpha * target_pan + (1 - alpha) * smooth_pan
            smooth_tilt = alpha * target_tilt + (1 - alpha) * smooth_tilt

            # Detect pinch gesture for special actions
            pinch_dist = math.hypot(ix - tx, iy - ty)
            if pinch_dist < PINCH_THRESH and not gesture_detected:
                gesture_detected = True
                print(f"Gesture detected! Camera position: Pan={smooth_pan:.1f}°, Tilt={smooth_tilt:.1f}°")
            elif pinch_dist >= PINCH_THRESH * 1.3 and gesture_detected:
                gesture_detected = False

            # Create virtual camera view with perspective transformation
            # Simulate camera rotation by applying perspective transformation
            frame_height, frame_width = frame.shape[:2]
            
            # Calculate perspective transformation matrix based on camera angles
            pan_rad = math.radians(smooth_pan)
            tilt_rad = math.radians(smooth_tilt)
            
            # Create perspective transformation points
            # This simulates the camera rotating to follow the hand
            offset_x = int(smooth_pan * 3)  # Scale pan to pixel offset
            offset_y = int(smooth_tilt * 3)  # Scale tilt to pixel offset
            
            # Define source and destination points for perspective transform
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
            
            # Apply perspective transformation to simulate camera movement
            try:
                perspective_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
                frame = cv2.warpPerspective(frame, perspective_matrix, (frame_width, frame_height))
            except:
                pass  # Skip transformation if points are invalid

            # Visual feedback - draw tracking information
            center_x, center_y = frame_width // 2, frame_height // 2
            
            # Draw center crosshair
            cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (255, 255, 255), 2)
            cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (255, 255, 255), 2)
            
            # Draw hand position
            hand_pixel_x = int(hand_center_x * frame_width)
            hand_pixel_y = int(hand_center_y * frame_height)
            cv2.circle(frame, (hand_pixel_x, hand_pixel_y), 15, (0, 255, 255), 3)  # Yellow circle for hand center
            
            # Draw finger tips
            cv2.circle(frame, (int(ix * frame_width), int(iy * frame_height)), 8, (0, 255, 0), -1)  # Green for index
            cv2.circle(frame, (int(tx * frame_width), int(ty * frame_height)), 8, (255, 0, 0), -1)  # Blue for thumb
            
            # Draw hand landmarks
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
            
            # Draw camera status
            status_text = f"Camera: Pan={smooth_pan:.1f}° Tilt={smooth_tilt:.1f}°"
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if gesture_detected:
                cv2.putText(frame, "GESTURE DETECTED!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                
        else:
            # No hand detected - gradually return camera to center
            smooth_pan *= 0.95
            smooth_tilt *= 0.95

        cv2.imshow("Camera Hand Tracking - ESC to exit", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC 退出
            break

cap.release()
cv2.destroyAllWindows()