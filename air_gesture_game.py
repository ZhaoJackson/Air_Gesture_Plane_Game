import cv2
import numpy as np
import mediapipe as mp
import math
import random
import time

# Ensure cv2 constants are available
try:
    # Try to access cv2 constants
    _ = cv2.CAP_PROP_FRAME_WIDTH
except AttributeError:
    # If constants are not available, import them
    import cv2.cv2 as cv2

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

class AirGestureGame:
    def __init__(self, dual_hand_mode=False):
        # Game settings
        self.width = 800
        self.height = 600
        self.running = True
        self.score = 0
        self.lives = 3
        self.level = 1
        self.dual_hand_mode = dual_hand_mode
        
        # Player settings
        self.player_x = self.width // 2
        self.player_y = self.height - 100
        self.player_size = 30
        self.player_color = (0, 255, 0)  # Green
        
        # Hand tracking
        self.hand_x = 0.5
        self.hand_y = 0.5
        self.gesture_state = "none"
        self.last_gesture_time = 0
        
        # Dual hand tracking (for dual hand mode)
        self.left_hand = None
        self.right_hand = None
        self.left_gesture = "none"
        self.right_gesture = "none"
        
        # Game objects
        self.bullets = []
        self.enemies = []
        self.collectibles = []
        self.particles = []
        self.power_ups = []
        self.shields = []
        
        # Enhanced game features
        self.shield_active = False
        self.shield_time = 0
        self.rapid_fire_active = False
        self.rapid_fire_time = 0
        self.freeze_active = False
        self.freeze_time = 0
        self.mega_blast_ready = True
        self.last_mega_blast = 0
        
        # Gesture combo system
        self.gesture_history = []
        self.combo_window = 2.0  # seconds
        self.current_combo = ""
        
        # Timing
        self.last_enemy_spawn = time.time()
        self.last_collectible_spawn = time.time()
        self.enemy_spawn_rate = 2.0  # seconds
        self.collectible_spawn_rate = 3.0  # seconds
        
        # Gesture detection thresholds
        self.pinch_threshold = 0.05
        self.palm_open_threshold = 0.15
        self.fist_threshold = 0.08
        
        # Find and connect to laptop camera
        self.cap = self.find_laptop_camera()
        if self.cap is None:
            print("❌ Error: Could not find laptop camera!")
            print("Please ensure:")
            print("1. Your laptop camera is not being used by other apps")
            print("2. Camera permissions are granted")
            print("3. No external cameras are interfering")
            exit(1)
            
        print(f"✅ Connected to laptop camera successfully!")
    
    def find_laptop_camera(self):
        """Find and connect to laptop's built-in camera (not phone camera)"""
        print("🔍 Searching for laptop's built-in camera...")
        print("   (Avoiding phone/external cameras)")
        
        # Based on your test results, we know cameras 0 and 1 work
        # Let's try them in order and prefer the actual laptop camera
        camera_candidates = [0, 1, 2, 3]  # Try in this order
        
        for camera_index in camera_candidates:
            print(f"   Trying camera index {camera_index}...")
            
            try:
                cap = cv2.VideoCapture(camera_index)
                
                if cap.isOpened():
                    # Test if we can read a frame
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # Get camera info
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        print(f"   📹 Found working camera at index {camera_index}")
                        print(f"      Original: {width}x{height} @ {fps}fps")
                        
                        # Set optimal settings for hand tracking
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        cap.set(cv2.CAP_PROP_FPS, 30)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        
                        # Disable auto-exposure for consistent lighting
                        try:
                            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
                        except:
                            pass
                        
                        # Test the optimized settings
                        ret, test_frame = cap.read()
                        if ret and test_frame is not None:
                            final_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            final_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            print(f"   ✅ Camera {camera_index} optimized: {final_width}x{final_height}")
                            print(f"   🎯 Using this camera for the game!")
                            return cap
                        else:
                            print(f"   ❌ Camera {camera_index} failed with optimized settings")
                            cap.release()
                    else:
                        print(f"   ❌ Camera {camera_index} can't read frames")
                        cap.release()
                else:
                    print(f"   ❌ Camera {camera_index} not accessible")
                    
            except Exception as e:
                print(f"   ❌ Error with camera {camera_index}: {e}")
                
        print("❌ No suitable laptop camera found!")
        print("💡 Try closing other apps that might be using the camera")
        return None
        
    def detect_gestures(self, landmarks):
        """Advanced gesture detection with multiple hand poses"""
        if not landmarks:
            return "none"
            
        # Get all key landmarks
        wrist = landmarks[0]
        thumb_cmc = landmarks[1]
        thumb_mcp = landmarks[2]
        thumb_ip = landmarks[3]
        thumb_tip = landmarks[4]
        
        index_mcp = landmarks[5]
        index_pip = landmarks[6]
        index_dip = landmarks[7]
        index_tip = landmarks[8]
        
        middle_mcp = landmarks[9]
        middle_pip = landmarks[10]
        middle_dip = landmarks[11]
        middle_tip = landmarks[12]
        
        ring_mcp = landmarks[13]
        ring_pip = landmarks[14]
        ring_dip = landmarks[15]
        ring_tip = landmarks[16]
        
        pinky_mcp = landmarks[17]
        pinky_pip = landmarks[18]
        pinky_dip = landmarks[19]
        pinky_tip = landmarks[20]
        
        # Helper function to check if finger is extended
        def is_finger_extended(tip, pip, mcp):
            tip_to_wrist = math.hypot(tip.x - wrist.x, tip.y - wrist.y)
            pip_to_wrist = math.hypot(pip.x - wrist.x, pip.y - wrist.y)
            return tip_to_wrist > pip_to_wrist
        
        # Helper function to check if thumb is extended
        def is_thumb_extended():
            return thumb_tip.x > thumb_ip.x if thumb_tip.x > wrist.x else thumb_tip.x < thumb_ip.x
        
        # Check which fingers are extended
        thumb_up = is_thumb_extended()
        index_up = is_finger_extended(index_tip, index_pip, index_mcp)
        middle_up = is_finger_extended(middle_tip, middle_pip, middle_mcp)
        ring_up = is_finger_extended(ring_tip, ring_pip, ring_mcp)
        pinky_up = is_finger_extended(pinky_tip, pinky_pip, pinky_mcp)
        
        fingers_extended = [thumb_up, index_up, middle_up, ring_up, pinky_up]
        fingers_count = sum(fingers_extended)
        
        # Calculate key distances for specific gestures
        thumb_index_dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
        thumb_middle_dist = math.hypot(thumb_tip.x - middle_tip.x, thumb_tip.y - middle_tip.y)
        index_middle_dist = math.hypot(index_tip.x - middle_tip.x, index_tip.y - middle_tip.y)
        
        # Advanced gesture detection
        
        # 1. Pinch gestures (precise actions)
        if thumb_index_dist < 0.03:
            return "precision_pinch"  # Super accurate shooting
        elif thumb_index_dist < 0.06:
            return "pinch"  # Regular shooting
        elif thumb_middle_dist < 0.05:
            return "thumb_middle_pinch"  # Rapid fire mode
            
        # 2. Pointing gestures
        elif index_up and not middle_up and not ring_up and not pinky_up:
            # Check pointing direction
            if index_tip.y < wrist.y - 0.1:
                return "point_up"  # Launch missile upward
            elif index_tip.y > wrist.y + 0.1:
                return "point_down"  # Drop bomb
            elif index_tip.x < wrist.x - 0.1:
                return "point_left"  # Dash left
            elif index_tip.x > wrist.x + 0.1:
                return "point_right"  # Dash right
            else:
                return "point_forward"  # Forward blast
                
        # 3. Number gestures
        elif thumb_up and not any([index_up, middle_up, ring_up, pinky_up]):
            return "thumbs_up"  # Activate shield
        elif not thumb_up and index_up and middle_up and not ring_up and not pinky_up:
            return "peace_sign"  # Special ability
        elif not thumb_up and index_up and middle_up and ring_up and not pinky_up:
            return "three_fingers"  # Triple shot
        elif not thumb_up and all([index_up, middle_up, ring_up, pinky_up]):
            return "four_fingers"  # Quad shot
        elif all(fingers_extended):
            return "open_palm"  # Mega shield
            
        # 4. Fist and claw gestures
        elif fingers_count == 0:
            return "fist"  # Power punch / charge up
        elif not any([thumb_up, index_up, middle_up]) and ring_up and pinky_up:
            return "rock_horns"  # Rock and roll - destroy all enemies
            
        # 5. L-shape and gun gestures
        elif thumb_up and index_up and not any([middle_up, ring_up, pinky_up]):
            # Check if it forms an L or gun shape
            thumb_index_angle = math.atan2(index_tip.y - thumb_tip.y, index_tip.x - thumb_tip.x)
            if abs(thumb_index_angle) > math.pi/3:  # Roughly 60 degrees
                return "gun_shape"  # Sniper shot
            else:
                return "l_shape"  # Laser beam
                
        # 6. Claw/paw gestures
        elif thumb_up and middle_up and pinky_up and not index_up and not ring_up:
            return "claw_spread"  # Spread shot
        elif not thumb_up and not index_up and middle_up and ring_up and not pinky_up:
            return "middle_ring"  # Double beam
            
        # 7. OK sign
        elif thumb_index_dist < 0.08 and middle_up and ring_up and pinky_up:
            return "ok_sign"  # Perfect shot - high damage
            
        # 8. Spiderman web shooter
        elif not thumb_up and not middle_up and not ring_up and index_up and pinky_up:
            return "web_shooter"  # Web trap enemies
            
        # 9. Call me gesture
        elif thumb_up and pinky_up and not any([index_up, middle_up, ring_up]):
            return "call_me"  # Summon power-up
            
        # 10. Finger gun variations
        elif index_up and thumb_up and not any([middle_up, ring_up, pinky_up]):
            if thumb_tip.y < index_mcp.y:
                return "finger_gun_up"  # Upward shot
            else:
                return "finger_gun"  # Standard shot
        
        return "none"
    
    def detect_hand_type(self, hand_landmarks, handedness):
        """Determine if hand is left or right"""
        return handedness.classification[0].label
    
    def update_player_position(self, hand_landmarks):
        """Update player position based on hand position"""
        if hand_landmarks:
            # Use wrist position for player control
            wrist = hand_landmarks[0]
            
            # Map hand position to game area
            self.player_x = int(wrist.x * self.width)
            self.player_y = int(wrist.y * self.height)
            
            # Keep player within bounds
            self.player_x = max(self.player_size, min(self.width - self.player_size, self.player_x))
            self.player_y = max(self.player_size, min(self.height - self.player_size, self.player_y))
    
    def handle_gesture(self, gesture):
        """Handle all the enhanced gestures"""
        current_time = time.time()
        
        # Add to gesture history for combos
        if gesture != "none" and (not self.gesture_history or 
                                 self.gesture_history[-1][0] != gesture or 
                                 current_time - self.gesture_history[-1][1] > 0.3):
            self.gesture_history.append((gesture, current_time))
            
        # Clean old gestures from history
        self.gesture_history = [(g, t) for g, t in self.gesture_history 
                               if current_time - t < self.combo_window]
        
        if gesture != self.gesture_state or current_time - self.last_gesture_time > 0.3:
            # Basic shooting gestures
            if gesture == "pinch":
                self.shoot_bullet()
            elif gesture == "precision_pinch":
                self.precision_shot()
            elif gesture == "thumb_middle_pinch":
                self.rapid_fire()
            elif gesture == "finger_gun":
                self.finger_gun_shot()
            elif gesture == "finger_gun_up":
                self.upward_shot()
            elif gesture == "gun_shape":
                self.sniper_shot()
                
            # Multi-shot gestures
            elif gesture == "three_fingers":
                self.triple_shot()
            elif gesture == "four_fingers":
                self.quad_shot()
            elif gesture == "claw_spread":
                self.spread_shot()
            elif gesture == "middle_ring":
                self.double_beam()
                
            # Directional attacks
            elif gesture == "point_up":
                self.launch_missile()
            elif gesture == "point_down":
                self.drop_bomb()
            elif gesture == "point_left":
                self.dash_left()
            elif gesture == "point_right":
                self.dash_right()
            elif gesture == "point_forward":
                self.forward_blast()
            elif gesture == "l_shape":
                self.laser_beam()
                
            # Special abilities
            elif gesture == "thumbs_up":
                self.activate_shield()
            elif gesture == "open_palm":
                self.mega_shield()
            elif gesture == "peace_sign":
                self.special_ability()
            elif gesture == "ok_sign":
                self.perfect_shot()
            elif gesture == "web_shooter":
                self.web_trap()
            elif gesture == "call_me":
                self.summon_powerup()
            elif gesture == "rock_horns":
                self.rock_and_roll_destroy()
                
            # Power gestures
            elif gesture == "fist":
                self.power_punch()
                
            self.gesture_state = gesture
            self.last_gesture_time = current_time
            
        # Check for gesture combos
        self.check_gesture_combos()
    
    def shoot_bullet(self):
        """Create a standard bullet"""
        bullet = {
            'x': self.player_x,
            'y': self.player_y - 20,
            'speed': 8,
            'size': 5,
            'color': (255, 255, 0),  # Yellow
            'type': 'normal',
            'damage': 1
        }
        self.bullets.append(bullet)
    
    def precision_shot(self):
        """High-accuracy, high-damage shot"""
        bullet = {
            'x': self.player_x,
            'y': self.player_y - 20,
            'speed': 12,
            'size': 8,
            'color': (255, 0, 255),  # Magenta
            'type': 'precision',
            'damage': 3
        }
        self.bullets.append(bullet)
        self.score += 5  # Bonus for precision
    
    def rapid_fire(self):
        """Activate rapid fire mode"""
        self.rapid_fire_active = True
        self.rapid_fire_time = time.time() + 3.0  # 3 seconds
        for i in range(3):
            bullet = {
                'x': self.player_x + (i-1) * 10,
                'y': self.player_y - 20,
                'speed': 10,
                'size': 4,
                'color': (255, 100, 100),  # Light red
                'type': 'rapid',
                'damage': 1
            }
            self.bullets.append(bullet)
    
    def finger_gun_shot(self):
        """Finger gun - straight shot"""
        bullet = {
            'x': self.player_x,
            'y': self.player_y - 20,
            'speed': 15,
            'size': 6,
            'color': (0, 255, 255),  # Cyan
            'type': 'finger_gun',
            'damage': 2
        }
        self.bullets.append(bullet)
    
    def upward_shot(self):
        """Upward angled shot"""
        for angle in [-0.3, 0, 0.3]:  # Three angles
            bullet = {
                'x': self.player_x,
                'y': self.player_y - 20,
                'speed': 10,
                'size': 5,
                'color': (100, 255, 100),  # Light green
                'type': 'angled',
                'damage': 1,
                'angle': angle
            }
            self.bullets.append(bullet)
    
    def sniper_shot(self):
        """High-damage, piercing shot"""
        bullet = {
            'x': self.player_x,
            'y': self.player_y - 20,
            'speed': 20,
            'size': 10,
            'color': (255, 0, 0),  # Red
            'type': 'sniper',
            'damage': 5,
            'piercing': True
        }
        self.bullets.append(bullet)
    
    def triple_shot(self):
        """Three bullets in spread pattern"""
        for i, angle in enumerate([-0.5, 0, 0.5]):
            bullet = {
                'x': self.player_x + (i-1) * 15,
                'y': self.player_y - 20,
                'speed': 9,
                'size': 5,
                'color': (255, 255, 100),  # Light yellow
                'type': 'triple',
                'damage': 1,
                'angle': angle
            }
            self.bullets.append(bullet)
    
    def quad_shot(self):
        """Four bullets in cross pattern"""
        angles = [-0.7, -0.2, 0.2, 0.7]
        for i, angle in enumerate(angles):
            bullet = {
                'x': self.player_x + (i-1.5) * 12,
                'y': self.player_y - 20,
                'speed': 8,
                'size': 4,
                'color': (100, 255, 255),  # Light cyan
                'type': 'quad',
                'damage': 1,
                'angle': angle
            }
            self.bullets.append(bullet)
    
    def spread_shot(self):
        """Wide spread shot like a claw"""
        for i in range(7):
            angle = (i - 3) * 0.3
            bullet = {
                'x': self.player_x,
                'y': self.player_y - 20,
                'speed': 7,
                'size': 4,
                'color': (255, 150, 0),  # Orange
                'type': 'spread',
                'damage': 1,
                'angle': angle
            }
            self.bullets.append(bullet)
    
    def double_beam(self):
        """Two parallel laser beams"""
        for offset in [-15, 15]:
            bullet = {
                'x': self.player_x + offset,
                'y': self.player_y - 20,
                'speed': 12,
                'size': 8,
                'color': (0, 255, 0),  # Green
                'type': 'beam',
                'damage': 2
            }
            self.bullets.append(bullet)
    
    def launch_missile(self):
        """Launch homing missile upward"""
        bullet = {
            'x': self.player_x,
            'y': self.player_y - 20,
            'speed': 6,
            'size': 12,
            'color': (255, 100, 0),  # Dark orange
            'type': 'missile',
            'damage': 4,
            'homing': True
        }
        self.bullets.append(bullet)
    
    def drop_bomb(self):
        """Drop explosive bomb"""
        bullet = {
            'x': self.player_x,
            'y': self.player_y + 20,
            'speed': -5,  # Negative speed (downward)
            'size': 15,
            'color': (100, 100, 100),  # Gray
            'type': 'bomb',
            'damage': 6,
            'explosive': True
        }
        self.bullets.append(bullet)
    
    def dash_left(self):
        """Quick dash to the left"""
        self.player_x = max(50, self.player_x - 100)
        # Create dash particles
        for i in range(8):
            particle = {
                'x': self.player_x + 50,
                'y': self.player_y + random.randint(-10, 10),
                'vx': random.uniform(2, 5),
                'vy': random.uniform(-2, 2),
                'life': 15,
                'color': (0, 255, 255),
                'size': 3
            }
            self.particles.append(particle)
    
    def dash_right(self):
        """Quick dash to the right"""
        self.player_x = min(self.width - 50, self.player_x + 100)
        # Create dash particles
        for i in range(8):
            particle = {
                'x': self.player_x - 50,
                'y': self.player_y + random.randint(-10, 10),
                'vx': random.uniform(-5, -2),
                'vy': random.uniform(-2, 2),
                'life': 15,
                'color': (0, 255, 255),
                'size': 3
            }
            self.particles.append(particle)
    
    def forward_blast(self):
        """Powerful forward blast"""
        for i in range(5):
            bullet = {
                'x': self.player_x,
                'y': self.player_y - 20 - i * 10,
                'speed': 15 + i * 2,
                'size': 8 + i,
                'color': (255, 255, 255),  # White
                'type': 'blast',
                'damage': 3
            }
            self.bullets.append(bullet)
    
    def laser_beam(self):
        """Continuous laser beam"""
        for i in range(10):
            bullet = {
                'x': self.player_x,
                'y': self.player_y - 20 - i * 15,
                'speed': 25,
                'size': 6,
                'color': (0, 255, 0),  # Green laser
                'type': 'laser',
                'damage': 2
            }
            self.bullets.append(bullet)
    
    def perfect_shot(self):
        """Perfect shot with guaranteed hit"""
        if self.enemies:
            target = min(self.enemies, key=lambda e: math.hypot(e['x'] - self.player_x, e['y'] - self.player_y))
            bullet = {
                'x': self.player_x,
                'y': self.player_y - 20,
                'speed': 20,
                'size': 12,
                'color': (255, 215, 0),  # Gold
                'type': 'perfect',
                'damage': 10,
                'target': target
            }
            self.bullets.append(bullet)
    
    def web_trap(self):
        """Create web to trap enemies"""
        for enemy in self.enemies:
            if math.hypot(enemy['x'] - self.player_x, enemy['y'] - self.player_y) < 150:
                enemy['speed'] *= 0.3  # Slow down trapped enemies
                enemy['webbed'] = True
                # Create web particles
                for i in range(6):
                    particle = {
                        'x': enemy['x'] + random.randint(-20, 20),
                        'y': enemy['y'] + random.randint(-20, 20),
                        'vx': 0,
                        'vy': 0,
                        'life': 60,
                        'color': (200, 200, 200),  # Light gray
                        'size': 2
                    }
                    self.particles.append(particle)
    
    def summon_powerup(self):
        """Summon a random power-up"""
        powerup = {
            'x': self.player_x,
            'y': self.player_y - 50,
            'type': random.choice(['health', 'score', 'weapon', 'shield']),
            'size': 20,
            'color': (255, 215, 0),  # Gold
            'life': 300  # Lasts 5 seconds at 60 FPS
        }
        self.power_ups.append(powerup)
    
    def rock_and_roll_destroy(self):
        """Destroy all enemies on screen - ultimate ability"""
        current_time = time.time()
        if current_time - self.last_mega_blast > 10:  # 10 second cooldown
            enemies_destroyed = len(self.enemies)
            self.score += enemies_destroyed * 50
            
            # Create massive explosion for each enemy
            for enemy in self.enemies:
                for i in range(15):
                    angle = i * (2 * math.pi / 15)
                    particle = {
                        'x': enemy['x'],
                        'y': enemy['y'],
                        'vx': math.cos(angle) * 8,
                        'vy': math.sin(angle) * 8,
                        'life': 30,
                        'color': (255, 0, 0),  # Red explosion
                        'size': 8
                    }
                    self.particles.append(particle)
            
            self.enemies = []  # Clear all enemies
            self.last_mega_blast = current_time
    
    def power_punch(self):
        """Charge up and release energy punch"""
        # Create energy buildup
        for i in range(20):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(20, 60)
            particle = {
                'x': self.player_x + math.cos(angle) * distance,
                'y': self.player_y + math.sin(angle) * distance,
                'vx': -math.cos(angle) * 3,
                'vy': -math.sin(angle) * 3,
                'life': 25,
                'color': (255, 0, 255),  # Magenta energy
                'size': 5
            }
            self.particles.append(particle)
        
        # Damage nearby enemies
        for i, enemy in enumerate(self.enemies):
            if math.hypot(enemy['x'] - self.player_x, enemy['y'] - self.player_y) < 100:
                self.enemies.pop(i)
                self.score += 30
                break
    
    def check_gesture_combos(self):
        """Check for gesture combinations"""
        if len(self.gesture_history) >= 2:
            recent_gestures = [g[0] for g in self.gesture_history[-2:]]
            
            # Combo: Peace -> Fist = Super Blast
            if recent_gestures == ["peace_sign", "fist"]:
                self.super_blast_combo()
                self.current_combo = "Super Blast!"
            
            # Combo: Thumbs Up -> Gun Shape = Shield Shot
            elif recent_gestures == ["thumbs_up", "gun_shape"]:
                self.shield_shot_combo()
                self.current_combo = "Shield Shot!"
            
            # Combo: Three Fingers -> Four Fingers = Mega Multi-shot
            elif recent_gestures == ["three_fingers", "four_fingers"]:
                self.mega_multishot_combo()
                self.current_combo = "Mega Multi-shot!"
    
    def super_blast_combo(self):
        """Super blast combo effect"""
        for angle in range(0, 360, 15):  # 24 bullets in circle
            rad = math.radians(angle)
            bullet = {
                'x': self.player_x,
                'y': self.player_y,
                'speed': 12,
                'size': 8,
                'color': (255, 0, 255),  # Magenta
                'type': 'combo_blast',
                'damage': 3,
                'angle': rad
            }
            self.bullets.append(bullet)
    
    def shield_shot_combo(self):
        """Protected powerful shot"""
        self.activate_shield()
        self.sniper_shot()
    
    def mega_multishot_combo(self):
        """Ultimate multi-directional shot"""
        for i in range(12):
            angle = i * (math.pi / 6)
            bullet = {
                'x': self.player_x,
                'y': self.player_y,
                'speed': 10,
                'size': 6,
                'color': (255, 215, 0),  # Gold
                'type': 'mega_combo',
                'damage': 4,
                'angle': angle
            }
            self.bullets.append(bullet)
    
    def activate_shield(self):
        """Activate shield effect"""
        self.shield_active = True
        self.shield_time = time.time() + 5.0  # 5 seconds
        # Create shield particles around player
        for i in range(12):
            angle = i * (2 * math.pi / 12)
            particle = {
                'x': self.player_x + math.cos(angle) * 40,
                'y': self.player_y + math.sin(angle) * 40,
                'vx': math.cos(angle) * 2,
                'vy': math.sin(angle) * 2,
                'life': 30,
                'color': (0, 255, 255),  # Cyan
                'size': 3
            }
            self.particles.append(particle)
    
    def mega_shield(self):
        """Mega shield with extended protection"""
        self.shield_active = True
        self.shield_time = time.time() + 8.0  # 8 seconds
        # Create larger shield effect
        for i in range(20):
            angle = i * (2 * math.pi / 20)
            particle = {
                'x': self.player_x + math.cos(angle) * 60,
                'y': self.player_y + math.sin(angle) * 60,
                'vx': math.cos(angle) * 1,
                'vy': math.sin(angle) * 1,
                'life': 40,
                'color': (0, 255, 255),  # Cyan
                'size': 6
            }
            self.particles.append(particle)
    
    def special_ability(self):
        """Special ability - clear nearby enemies"""
        enemies_to_remove = []
        for i, enemy in enumerate(self.enemies):
            dist = math.hypot(enemy['x'] - self.player_x, enemy['y'] - self.player_y)
            if dist < 100:
                enemies_to_remove.append(i)
                self.score += 20
                
                # Create explosion particles
                for j in range(6):
                    angle = j * (2 * math.pi / 6)
                    particle = {
                        'x': enemy['x'],
                        'y': enemy['y'],
                        'vx': math.cos(angle) * 4,
                        'vy': math.sin(angle) * 4,
                        'life': 15,
                        'color': (255, 100, 0),  # Orange
                        'size': 6
                    }
                    self.particles.append(particle)
        
        # Remove destroyed enemies
        for i in reversed(enemies_to_remove):
            self.enemies.pop(i)
    
    def spawn_enemy(self):
        """Spawn a new enemy"""
        enemy = {
            'x': random.randint(20, self.width - 20),
            'y': -20,
            'speed': random.uniform(2, 5),
            'size': random.randint(15, 25),
            'color': (255, 0, 0),  # Red
            'type': random.choice(['normal', 'fast', 'big'])
        }
        
        if enemy['type'] == 'fast':
            enemy['speed'] *= 1.5
            enemy['color'] = (255, 100, 100)
        elif enemy['type'] == 'big':
            enemy['size'] *= 1.5
            enemy['speed'] *= 0.7
            enemy['color'] = (200, 0, 0)
            
        self.enemies.append(enemy)
    
    def spawn_collectible(self):
        """Spawn a collectible item"""
        collectible = {
            'x': random.randint(30, self.width - 30),
            'y': -20,
            'speed': 3,
            'size': 12,
            'color': (0, 255, 255),  # Cyan
            'type': random.choice(['coin', 'star', 'heart'])
        }
        
        if collectible['type'] == 'star':
            collectible['color'] = (255, 255, 0)  # Yellow
        elif collectible['type'] == 'heart':
            collectible['color'] = (255, 0, 255)  # Magenta
            
        self.collectibles.append(collectible)
    
    def update_game_objects(self):
        """Update all game objects"""
        current_time = time.time()
        
        # Spawn enemies
        if current_time - self.last_enemy_spawn > self.enemy_spawn_rate:
            self.spawn_enemy()
            self.last_enemy_spawn = current_time
            
        # Spawn collectibles
        if current_time - self.last_collectible_spawn > self.collectible_spawn_rate:
            self.spawn_collectible()
            self.last_collectible_spawn = current_time
        
        # Update bullets with enhanced movement
        bullets_to_remove = []
        for i, bullet in enumerate(self.bullets):
            # Handle different bullet types
            if 'angle' in bullet:
                # Angled bullets
                bullet['x'] += bullet['speed'] * math.sin(bullet['angle'])
                bullet['y'] -= bullet['speed'] * math.cos(bullet['angle'])
            elif bullet.get('type') == 'bomb':
                # Bombs fall down
                bullet['y'] += abs(bullet['speed'])
            elif bullet.get('homing') and self.enemies:
                # Homing missiles
                target = min(self.enemies, key=lambda e: math.hypot(e['x'] - bullet['x'], e['y'] - bullet['y']))
                dx = target['x'] - bullet['x']
                dy = target['y'] - bullet['y']
                dist = math.hypot(dx, dy)
                if dist > 0:
                    bullet['x'] += (dx / dist) * bullet['speed']
                    bullet['y'] += (dy / dist) * bullet['speed']
            else:
                # Normal bullets
                bullet['y'] -= bullet['speed']
            
            # Remove bullets that are off-screen
            if (bullet['y'] < -50 or bullet['y'] > self.height + 50 or 
                bullet['x'] < -50 or bullet['x'] > self.width + 50):
                bullets_to_remove.append(i)
        
        for i in reversed(bullets_to_remove):
            self.bullets.pop(i)
        
        # Update enemies
        enemies_to_remove = []
        for i, enemy in enumerate(self.enemies):
            enemy['y'] += enemy['speed']
            if enemy['y'] > self.height + 50:
                enemies_to_remove.append(i)
        
        for i in reversed(enemies_to_remove):
            self.enemies.pop(i)
        
        # Update collectibles
        collectibles_to_remove = []
        for i, collectible in enumerate(self.collectibles):
            collectible['y'] += collectible['speed']
            if collectible['y'] > self.height + 50:
                collectibles_to_remove.append(i)
        
        for i in reversed(collectibles_to_remove):
            self.collectibles.pop(i)
        
        # Update particles
        particles_to_remove = []
        for i, particle in enumerate(self.particles):
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            if particle['life'] <= 0:
                particles_to_remove.append(i)
        
        for i in reversed(particles_to_remove):
            self.particles.pop(i)
    
    def check_collisions(self):
        """Check for collisions"""
        # Bullet-enemy collisions
        bullets_to_remove = []
        enemies_to_remove = []
        
        for i, bullet in enumerate(self.bullets):
            for j, enemy in enumerate(self.enemies):
                dist = math.hypot(bullet['x'] - enemy['x'], bullet['y'] - enemy['y'])
                if dist < bullet['size'] + enemy['size']:
                    bullets_to_remove.append(i)
                    enemies_to_remove.append(j)
                    self.score += 10
                    
                    # Create explosion
                    for k in range(5):
                        angle = k * (2 * math.pi / 5)
                        particle = {
                            'x': enemy['x'],
                            'y': enemy['y'],
                            'vx': math.cos(angle) * 3,
                            'vy': math.sin(angle) * 3,
                            'life': 12,
                            'color': (255, 150, 0),
                            'size': 4
                        }
                        self.particles.append(particle)
        
        # Remove collided objects
        for i in reversed(sorted(set(bullets_to_remove))):
            if i < len(self.bullets):
                self.bullets.pop(i)
        for i in reversed(sorted(set(enemies_to_remove))):
            if i < len(self.enemies):
                self.enemies.pop(i)
        
        # Player-enemy collisions
        for i, enemy in enumerate(self.enemies):
            dist = math.hypot(enemy['x'] - self.player_x, enemy['y'] - self.player_y)
            if dist < enemy['size'] + self.player_size:
                self.lives -= 1
                self.enemies.pop(i)
                break
        
        # Player-collectible collisions
        collectibles_to_remove = []
        for i, collectible in enumerate(self.collectibles):
            dist = math.hypot(collectible['x'] - self.player_x, collectible['y'] - self.player_y)
            if dist < collectible['size'] + self.player_size:
                collectibles_to_remove.append(i)
                
                if collectible['type'] == 'coin':
                    self.score += 20
                elif collectible['type'] == 'star':
                    self.score += 50
                elif collectible['type'] == 'heart':
                    self.lives += 1
        
        for i in reversed(collectibles_to_remove):
            self.collectibles.pop(i)
    
    def draw_game(self, frame):
        """Draw game elements on the frame"""
        # Create game overlay
        overlay = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Draw player
        cv2.circle(overlay, (self.player_x, self.player_y), self.player_size, self.player_color, -1)
        cv2.circle(overlay, (self.player_x, self.player_y), self.player_size, (255, 255, 255), 2)
        
        # Draw bullets
        for bullet in self.bullets:
            cv2.circle(overlay, (int(bullet['x']), int(bullet['y'])), bullet['size'], bullet['color'], -1)
        
        # Draw enemies
        for enemy in self.enemies:
            cv2.circle(overlay, (int(enemy['x']), int(enemy['y'])), int(enemy['size']), enemy['color'], -1)
            cv2.circle(overlay, (int(enemy['x']), int(enemy['y'])), int(enemy['size']), (255, 255, 255), 1)
        
        # Draw collectibles
        for collectible in self.collectibles:
            if collectible['type'] == 'star':
                # Draw star shape
                points = []
                for i in range(10):
                    angle = i * math.pi / 5
                    radius = int(collectible['size']) if i % 2 == 0 else int(collectible['size']) // 2
                    x = int(collectible['x'] + radius * math.cos(angle))
                    y = int(collectible['y'] + radius * math.sin(angle))
                    points.append([x, y])
                cv2.fillPoly(overlay, [np.array(points)], collectible['color'])
            else:
                cv2.circle(overlay, (int(collectible['x']), int(collectible['y'])), int(collectible['size']), collectible['color'], -1)
        
        # Draw particles
        for particle in self.particles:
            alpha = particle['life'] / 30.0
            color = tuple(int(c * alpha) for c in particle['color'])
            cv2.circle(overlay, (int(particle['x']), int(particle['y'])), int(particle['size']), color, -1)
        
        # Draw UI
        cv2.putText(overlay, f"Score: {self.score}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(overlay, f"Lives: {self.lives}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Show mode and gesture info
        mode_text = "DUAL HAND MODE" if self.dual_hand_mode else "SINGLE HAND MODE"
        cv2.putText(overlay, mode_text, (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        if self.dual_hand_mode:
            cv2.putText(overlay, f"Left: {self.left_gesture}", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(overlay, f"Right: {self.right_gesture}", (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        else:
            cv2.putText(overlay, f"Gesture: {self.gesture_state}", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Game over check
        if self.lives <= 0:
            cv2.putText(overlay, "GAME OVER", (self.width//2 - 100, self.height//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
            cv2.putText(overlay, "Press R to restart", (self.width//2 - 120, self.height//2 + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return overlay
    
    def reset_game(self):
        """Reset game to initial state"""
        self.score = 0
        self.lives = 3
        self.bullets = []
        self.enemies = []
        self.collectibles = []
        self.particles = []
        self.last_enemy_spawn = time.time()
        self.last_collectible_spawn = time.time()
    
    def run(self):
        """Main game loop"""
        max_hands = 2 if self.dual_hand_mode else 1
        with mp_hands.Hands(
            max_num_hands=max_hands,
            model_complexity=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        ) as hands:
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                frame_height, frame_width = frame.shape[:2]
                
                # Process hand detection
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)
                
                # Handle hand tracking
                if results.multi_hand_landmarks:
                    if self.dual_hand_mode and results.multi_handedness:
                        # Dual hand mode - handle left and right hands separately
                        self.left_hand = None
                        self.right_hand = None
                        self.left_gesture = "none"
                        self.right_gesture = "none"
                        
                        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                            hand_type = self.detect_hand_type(hand_landmarks, handedness)
                            landmarks = hand_landmarks.landmark
                            
                            if hand_type == "Left":
                                self.left_hand = landmarks
                                self.left_gesture = self.detect_gestures(landmarks)
                                self.update_player_position(landmarks)  # Left hand controls movement
                                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                                
                            elif hand_type == "Right":
                                self.right_hand = landmarks
                                self.right_gesture = self.detect_gestures(landmarks)
                                self.handle_gesture(self.right_gesture)  # Right hand controls weapons
                                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    else:
                        # Single hand mode - use first detected hand for everything
                        hand_landmarks = results.multi_hand_landmarks[0].landmark
                        
                        # Update player position
                        self.update_player_position(hand_landmarks)
                        
                        # Detect and handle gestures
                        gesture = self.detect_gestures(hand_landmarks)
                        self.handle_gesture(gesture)
                        
                        # Draw hand landmarks on camera feed
                        mp_draw.draw_landmarks(frame, results.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)
                
                # Update game logic (only if alive)
                if self.lives > 0:
                    self.update_game_objects()
                    self.check_collisions()
                
                # Resize camera feed to fit in corner
                small_frame = cv2.resize(frame, (200, 150))
                
                # Create game display
                game_display = self.draw_game(frame)
                
                # Overlay small camera feed in corner
                game_display[10:160, self.width-210:self.width-10] = small_frame
                
                # Show instructions
                if self.dual_hand_mode:
                    instructions = [
                        "DUAL HAND CONTROLS:",
                        "LEFT HAND: Move player position",
                        "RIGHT HAND: All weapon gestures",
                        "Pinch = Shoot | Tight pinch = Precision shot",
                        "Thumbs up = Shield | Open palm = Mega shield", 
                        "Point up/down/left/right = Directional attacks",
                        "Peace sign = Special | 3/4 fingers = Multi-shot",
                        "Fist = Power punch | Rock horns = Destroy all",
                        "Gun shape = Sniper | L-shape = Laser beam",
                        "OK sign = Perfect shot | Web = Trap enemies",
                        "Call me = Summon powerup",
                        "COMBOS: Peace->Fist, Thumbs->Gun, 3->4 fingers",
                        "ESC=Quit | R=Restart"
                    ]
                else:
                    instructions = [
                        "SINGLE HAND CONTROLS:",
                        "Move hand = Move player",
                        "Pinch = Shoot | Tight pinch = Precision shot",
                        "Thumbs up = Shield | Open palm = Mega shield", 
                        "Point up/down/left/right = Directional attacks",
                        "Peace sign = Special | 3/4 fingers = Multi-shot",
                        "Fist = Power punch | Rock horns = Destroy all",
                        "Gun shape = Sniper | L-shape = Laser beam",
                        "OK sign = Perfect shot | Web = Trap enemies",
                        "Call me = Summon powerup",
                        "COMBOS: Peace->Fist, Thumbs->Gun, 3->4 fingers",
                        "ESC=Quit | R=Restart"
                    ]
                
                for i, instruction in enumerate(instructions):
                    cv2.putText(game_display, instruction, (10, self.height - 140 + i * 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                
                cv2.imshow("Air Gesture Game", game_display)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
                elif key == ord('r') or key == ord('R'):
                    self.reset_game()
        
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    print("🎮 ENHANCED AIR GESTURE GAME 🎮")
    print("=" * 50)
    print("LAPTOP CAMERA OPTIMIZED")
    print("=" * 50)
    print("🎯 GESTURE CONTROLS:")
    print("✋ Move hand = Control player")
    print("👌 Pinch = Shoot bullets")
    print("🤏 Tight pinch = Precision shot")
    print("👍 Thumbs up = Activate shield") 
    print("🖐️ Open palm = Mega shield")
    print("☝️ Point up/down/left/right = Directional attacks")
    print("✌️ Peace sign = Special ability")
    print("🤟 Rock horns = Destroy all enemies")
    print("👊 Fist = Power punch")
    print("🔫 Gun shape = Sniper shot")
    print("👌 OK sign = Perfect shot")
    print("🕷️ Web shooter = Trap enemies")
    print("🤙 Call me = Summon powerup")
    print("📱 3/4 fingers = Multi-shot")
    print("")
    print("🔥 COMBO ATTACKS:")
    print("✌️➡️👊 Peace->Fist = Super Blast")
    print("👍➡️🔫 Thumbs->Gun = Shield Shot")
    print("📱➡️🖐️ 3->4 fingers = Mega Multi-shot")
    print("")
    print("⌨️ KEYBOARD: ESC=Quit | R=Restart")
    print("=" * 50)
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    game = AirGestureGame()
    game.run()
