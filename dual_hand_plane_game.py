#!/usr/bin/env python3
"""
DUAL-HAND PLANE ATTACK GAME
Left Hand: Controls plane movement and direction
Right Hand: Controls weapons and attacks
Aviation-themed graphics and gameplay
"""

import cv2
import numpy as np
import mediapipe as mp
import math
import random
import time
import subprocess

# Ensure cv2 constants are available
try:
    # Try to access cv2 constants
    _ = cv2.CAP_PROP_FRAME_WIDTH
except AttributeError:
    # If constants are not available, import them
    import cv2.cv2 as cv2

def find_facetime_camera():
    """Find the FaceTime HD Camera specifically"""
    print("🔍 Connecting to FaceTime HD Camera...")
    
    for camera_index in [0, 1, 2, 3]:
        try:
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Test HD capability
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    ret2, frame2 = cap.read()
                    
                    if ret2:
                        new_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        if new_width >= 1280:  # HD capable = FaceTime camera
                            # Optimize for game
                            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                            cap.set(cv2.CAP_PROP_FPS, 30)
                            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                            print(f"✅ FaceTime HD Camera connected at index {camera_index}")
                            return cap
                cap.release()
        except:
            continue
    return None

class DualHandPlaneGame:
    """Plane attack game with single or dual hand control"""
    
    def __init__(self, dual_hand_mode=True):
        self.dual_hand_mode = dual_hand_mode
        mode_text = "DUAL-HAND" if dual_hand_mode else "SINGLE-HAND"
        print(f"✈️ {mode_text} PLANE ATTACK GAME ✈️")
        print("=" * 60)
        if dual_hand_mode:
            print("🎮 DUAL HAND CONTROLS:")
            print("👈 LEFT HAND: Plane movement & direction")
            print("👉 RIGHT HAND: Weapons & attacks")
        else:
            print("🎮 SINGLE HAND CONTROLS:")
            print("✋ ONE HAND: Movement + weapons")
        print("=" * 60)
        
        # Camera setup
        self.cap = find_facetime_camera()
        if self.cap is None:
            print("❌ Could not find FaceTime HD Camera!")
            exit(1)
        
        # MediaPipe setup for dual hands
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        
        # Game settings
        self.width = 1000
        self.height = 700
        self.running = True
        self.score = 0
        self.lives = 3
        self.level = 1
        self.altitude = 5000  # Flight altitude in feet
        
        # Plane settings
        self.plane_x = self.width // 2
        self.plane_y = self.height - 150
        self.plane_size = 25
        self.plane_angle = 0  # Banking angle
        self.plane_speed = 0
        self.max_speed = 8
        
        # Hand tracking
        self.left_hand = None
        self.right_hand = None
        self.left_gesture = "none"
        self.right_gesture = "none"
        self.last_gesture_time = 0
        
        # Game objects
        self.bullets = []
        self.missiles = []
        self.enemy_planes = []
        self.clouds = []
        self.explosions = []
        self.powerups = []
        
        # Weapon system
        self.current_weapon = "bullets"  # bullets, missiles, bombs
        self.ammo = {"bullets": 999, "missiles": 10, "bombs": 5}
        self.weapon_cooldown = 0
        
        # Background and environment
        self.cloud_drift = 0
        self.terrain_scroll = 0
        self.sky_color = (135, 206, 235)  # Sky blue
        
        # Timing
        self.last_enemy_spawn = time.time()
        self.last_cloud_spawn = time.time()
        
        # Initialize background elements
        self.init_clouds()
        
        print("✅ Dual-hand plane game initialized!")
    
    def init_clouds(self):
        """Initialize background clouds"""
        for i in range(8):
            cloud = {
                'x': random.randint(0, self.width),
                'y': random.randint(50, self.height // 2),
                'size': random.randint(30, 80),
                'speed': random.uniform(0.5, 2.0),
                'opacity': random.randint(100, 200)
            }
            self.clouds.append(cloud)
    
    def detect_hand_type(self, hand_landmarks, handedness):
        """Determine if hand is left or right"""
        return handedness.classification[0].label
    
    def detect_single_hand_gesture(self, landmarks):
        """Detect gestures for single hand mode (movement + weapons)"""
        if not landmarks:
            return "none"
        
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        wrist = landmarks[0]
        
        # Calculate pinch distance for shooting
        pinch_dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
        
        # Count extended fingers
        fingers_up = 0
        finger_tips = [index_tip, middle_tip, ring_tip, pinky_tip]
        for tip in finger_tips:
            if abs(tip.y - wrist.y) > 0.08:
                fingers_up += 1
        
        # Single hand gestures (simplified from dual hand)
        if pinch_dist < 0.04:
            return "shoot_bullets"
        elif fingers_up == 1 and abs(index_tip.y - wrist.y) > 0.1:
            return "shoot_missile"
        elif fingers_up >= 4:
            return "bomb_mode"
        elif fingers_up <= 1:
            return "weapon_switch"
        elif fingers_up == 2:
            return "special_attack"
        else:
            return "movement"  # Default to movement control
    
    def detect_left_hand_gesture(self, landmarks):
        """Detect left hand gestures for movement control"""
        if not landmarks:
            return "none"
        
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        wrist = landmarks[0]
        
        # Calculate hand orientation for plane direction
        hand_vector_x = index_tip.x - wrist.x
        hand_vector_y = index_tip.y - wrist.y
        
        # Count extended fingers for speed control
        fingers_up = 0
        finger_tips = [landmarks[8], landmarks[12], landmarks[16], landmarks[20]]
        for tip in finger_tips:
            if abs(tip.y - wrist.y) > 0.08:  # Finger extended
                fingers_up += 1
        
        # Determine gesture based on hand position and finger count
        if fingers_up >= 4:
            return "full_throttle"  # All fingers = max speed
        elif fingers_up >= 2:
            return "cruise"  # Some fingers = normal speed
        elif fingers_up <= 1:
            return "slow"  # Fist = slow/hover
        else:
            return "none"
    
    def detect_right_hand_gesture(self, landmarks):
        """Detect right hand gestures for weapon control"""
        if not landmarks:
            return "none"
        
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        wrist = landmarks[0]
        
        # Calculate pinch distance for shooting
        pinch_dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
        
        # Count extended fingers for weapon selection
        fingers_up = 0
        finger_tips = [index_tip, middle_tip, ring_tip, pinky_tip]
        for tip in finger_tips:
            if abs(tip.y - wrist.y) > 0.08:
                fingers_up += 1
        
        # Weapon gestures
        if pinch_dist < 0.04:
            return "shoot_bullets"  # Pinch = shoot bullets
        elif fingers_up == 1 and abs(index_tip.y - wrist.y) > 0.1:
            return "shoot_missile"  # Point = shoot missile
        elif fingers_up >= 4:
            return "bomb_mode"  # Open palm = bomb mode
        elif fingers_up <= 1:
            return "weapon_switch"  # Fist = switch weapon
        elif fingers_up == 2:
            return "special_attack"  # Peace = special attack
        else:
            return "none"
    
    def update_plane_from_left_hand(self, landmarks, gesture):
        """Update plane position and movement from left hand"""
        if not landmarks:
            return
        
        wrist = landmarks[0]
        index_tip = landmarks[8]
        
        # Map hand position to plane position
        target_x = int(wrist.x * self.width)
        target_y = int(wrist.y * self.height)
        
        # Smooth plane movement
        alpha = 0.3
        self.plane_x = int(alpha * target_x + (1 - alpha) * self.plane_x)
        self.plane_y = int(alpha * target_y + (1 - alpha) * self.plane_y)
        
        # Keep plane in bounds
        self.plane_x = max(50, min(self.width - 50, self.plane_x))
        self.plane_y = max(50, min(self.height - 50, self.plane_y))
        
        # Calculate banking angle from hand tilt
        hand_angle = math.atan2(index_tip.y - wrist.y, index_tip.x - wrist.x)
        self.plane_angle = math.degrees(hand_angle) * 0.5  # Reduce sensitivity
        
        # Update speed based on gesture
        if gesture == "full_throttle":
            self.plane_speed = min(self.max_speed, self.plane_speed + 0.5)
        elif gesture == "cruise":
            self.plane_speed = min(self.max_speed * 0.7, self.plane_speed + 0.3)
        elif gesture == "slow":
            self.plane_speed = max(1, self.plane_speed - 0.3)
        else:
            self.plane_speed = max(0, self.plane_speed - 0.1)
    
    def update_plane_from_single_hand(self, landmarks, gesture):
        """Update plane position and handle weapons from single hand"""
        if not landmarks:
            return
        
        wrist = landmarks[0]
        index_tip = landmarks[8]
        
        # Map hand position to plane position (same as left hand logic)
        target_x = int(wrist.x * self.width)
        target_y = int(wrist.y * self.height)
        
        # Smooth plane movement
        alpha = 0.3
        self.plane_x = int(alpha * target_x + (1 - alpha) * self.plane_x)
        self.plane_y = int(alpha * target_y + (1 - alpha) * self.plane_y)
        
        # Keep plane in bounds
        self.plane_x = max(50, min(self.width - 50, self.plane_x))
        self.plane_y = max(50, min(self.height - 50, self.plane_y))
        
        # Calculate banking angle from hand tilt
        hand_angle = math.atan2(index_tip.y - wrist.y, index_tip.x - wrist.x)
        self.plane_angle = math.degrees(hand_angle) * 0.5
        
        # Auto-cruise speed in single hand mode
        self.plane_speed = min(self.max_speed * 0.8, self.plane_speed + 0.2)
        
        # Handle weapon gestures
        self.handle_right_hand_weapons(landmarks, gesture)
    
    def handle_right_hand_weapons(self, landmarks, gesture):
        """Handle weapon controls from right hand"""
        current_time = time.time()
        
        if current_time < self.weapon_cooldown:
            return
        
        if gesture == "shoot_bullets":
            self.shoot_bullets()
            self.weapon_cooldown = current_time + 0.1  # Fast fire rate
        elif gesture == "shoot_missile":
            self.shoot_missile()
            self.weapon_cooldown = current_time + 0.8  # Slower missile rate
        elif gesture == "bomb_mode":
            self.drop_bomb()
            self.weapon_cooldown = current_time + 1.5  # Slow bomb rate
        elif gesture == "weapon_switch":
            self.switch_weapon()
            self.weapon_cooldown = current_time + 1.0
        elif gesture == "special_attack":
            self.special_attack()
            self.weapon_cooldown = current_time + 3.0  # Long cooldown
    
    def shoot_bullets(self):
        """Shoot machine gun bullets"""
        if self.ammo["bullets"] > 0:
            # Twin guns on plane wings
            for offset in [-15, 15]:
                bullet = {
                    'x': self.plane_x + offset,
                    'y': self.plane_y - 30,
                    'vx': math.sin(math.radians(self.plane_angle)) * 2,
                    'vy': -12,
                    'size': 3,
                    'color': (255, 255, 0),  # Yellow bullets
                    'type': 'bullet',
                    'damage': 1
                }
                self.bullets.append(bullet)
            self.ammo["bullets"] -= 2
    
    def shoot_missile(self):
        """Shoot homing missile"""
        if self.ammo["missiles"] > 0 and self.enemy_planes:
            # Find nearest enemy
            target = min(self.enemy_planes, 
                        key=lambda e: math.hypot(e['x'] - self.plane_x, e['y'] - self.plane_y))
            
            missile = {
                'x': self.plane_x,
                'y': self.plane_y - 20,
                'vx': 0,
                'vy': -8,
                'size': 8,
                'color': (255, 0, 0),  # Red missile
                'type': 'missile',
                'damage': 5,
                'target': target,
                'fuel': 200  # Limited fuel for homing
            }
            self.missiles.append(missile)
            self.ammo["missiles"] -= 1
    
    def drop_bomb(self):
        """Drop bomb"""
        if self.ammo["bombs"] > 0:
            bomb = {
                'x': self.plane_x,
                'y': self.plane_y + 20,
                'vx': self.plane_speed * 0.5,
                'vy': 3,
                'size': 12,
                'color': (50, 50, 50),  # Gray bomb
                'type': 'bomb',
                'damage': 10,
                'gravity': 0.2
            }
            self.bullets.append(bomb)  # Use bullets list for simplicity
            self.ammo["bombs"] -= 1
    
    def switch_weapon(self):
        """Switch between weapon types"""
        weapons = ["bullets", "missiles", "bombs"]
        current_index = weapons.index(self.current_weapon)
        self.current_weapon = weapons[(current_index + 1) % len(weapons)]
    
    def special_attack(self):
        """Barrel roll special attack that destroys nearby enemies"""
        # Create barrel roll effect
        for i in range(20):
            explosion = {
                'x': self.plane_x + random.randint(-50, 50),
                'y': self.plane_y + random.randint(-50, 50),
                'size': random.randint(5, 15),
                'life': 15,
                'color': (255, random.randint(100, 255), 0)
            }
            self.explosions.append(explosion)
        
        # Destroy nearby enemies
        enemies_to_remove = []
        for i, enemy in enumerate(self.enemy_planes):
            dist = math.hypot(enemy['x'] - self.plane_x, enemy['y'] - self.plane_y)
            if dist < 100:
                enemies_to_remove.append(i)
                self.score += 50
        
        for i in reversed(enemies_to_remove):
            self.enemy_planes.pop(i)
    
    def spawn_enemy_plane(self):
        """Spawn enemy aircraft"""
        enemy_types = ["fighter", "bomber", "interceptor"]
        enemy_type = random.choice(enemy_types)
        
        enemy = {
            'x': random.randint(50, self.width - 50),
            'y': -50,
            'vx': random.uniform(-2, 2),
            'vy': random.uniform(2, 5),
            'size': 20 if enemy_type == "fighter" else 30,
            'color': (200, 0, 0) if enemy_type == "fighter" else (150, 0, 0),
            'type': enemy_type,
            'health': 1 if enemy_type == "fighter" else 3,
            'last_shot': 0
        }
        self.enemy_planes.append(enemy)
    
    def spawn_cloud(self):
        """Spawn background clouds"""
        cloud = {
            'x': self.width + 50,
            'y': random.randint(30, self.height // 2),
            'size': random.randint(40, 100),
            'speed': random.uniform(1, 3),
            'opacity': random.randint(80, 150)
        }
        self.clouds.append(cloud)
    
    def update_game_objects(self):
        """Update all game objects"""
        current_time = time.time()
        
        # Spawn enemies
        if current_time - self.last_enemy_spawn > 3.0 - (self.level * 0.2):
            self.spawn_enemy_plane()
            self.last_enemy_spawn = current_time
        
        # Spawn clouds
        if current_time - self.last_cloud_spawn > 5.0:
            self.spawn_cloud()
            self.last_cloud_spawn = current_time
        
        # Update bullets and missiles
        for projectile in self.bullets + self.missiles:
            if projectile['type'] == 'missile' and 'target' in projectile:
                # Homing behavior
                target = projectile['target']
                if target in self.enemy_planes and projectile['fuel'] > 0:
                    dx = target['x'] - projectile['x']
                    dy = target['y'] - projectile['y']
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        projectile['vx'] += (dx / dist) * 0.5
                        projectile['vy'] += (dy / dist) * 0.5
                    projectile['fuel'] -= 1
            
            if projectile['type'] == 'bomb':
                projectile['vy'] += projectile['gravity']  # Gravity effect
            
            projectile['x'] += projectile['vx']
            projectile['y'] += projectile['vy']
        
        # Remove off-screen projectiles
        self.bullets = [b for b in self.bullets if -50 < b['y'] < self.height + 50]
        self.missiles = [m for m in self.missiles if -50 < m['y'] < self.height + 50]
        
        # Update enemy planes
        for enemy in self.enemy_planes:
            enemy['x'] += enemy['vx']
            enemy['y'] += enemy['vy']
            
            # Simple AI - occasionally change direction
            if random.random() < 0.02:
                enemy['vx'] = random.uniform(-2, 2)
        
        # Remove off-screen enemies
        self.enemy_planes = [e for e in self.enemy_planes if e['y'] < self.height + 50]
        
        # Update clouds
        for cloud in self.clouds:
            cloud['x'] -= cloud['speed']
        self.clouds = [c for c in self.clouds if c['x'] > -100]
        
        # Update explosions
        for explosion in self.explosions:
            explosion['life'] -= 1
            explosion['size'] += 1
        self.explosions = [e for e in self.explosions if e['life'] > 0]
        
        # Update background drift
        self.cloud_drift += 0.5
        self.terrain_scroll += self.plane_speed * 0.1
        
        # Check collisions
        self.check_collisions()
    
    def check_collisions(self):
        """Check all collision types"""
        # Projectile vs enemy collisions
        projectiles_to_remove = []
        enemies_to_remove = []
        
        for i, projectile in enumerate(self.bullets + self.missiles):
            for j, enemy in enumerate(self.enemy_planes):
                dist = math.hypot(projectile['x'] - enemy['x'], projectile['y'] - enemy['y'])
                if dist < projectile['size'] + enemy['size']:
                    projectiles_to_remove.append(i)
                    enemy['health'] -= projectile['damage']
                    
                    if enemy['health'] <= 0:
                        enemies_to_remove.append(j)
                        self.score += 100
                        
                        # Create explosion
                        for k in range(8):
                            explosion = {
                                'x': enemy['x'] + random.randint(-20, 20),
                                'y': enemy['y'] + random.randint(-20, 20),
                                'size': random.randint(5, 15),
                                'life': 20,
                                'color': (255, random.randint(0, 255), 0)
                            }
                            self.explosions.append(explosion)
        
        # Remove destroyed objects
        for i in reversed(sorted(set(projectiles_to_remove))):
            if i < len(self.bullets):
                self.bullets.pop(i)
            else:
                self.missiles.pop(i - len(self.bullets))
        
        for i in reversed(sorted(set(enemies_to_remove))):
            if i < len(self.enemy_planes):
                self.enemy_planes.pop(i)
        
        # Player vs enemy collisions
        for i, enemy in enumerate(self.enemy_planes):
            dist = math.hypot(enemy['x'] - self.plane_x, enemy['y'] - self.plane_y)
            if dist < enemy['size'] + self.plane_size:
                self.lives -= 1
                self.enemy_planes.pop(i)
                
                # Create crash explosion
                for k in range(15):
                    explosion = {
                        'x': self.plane_x + random.randint(-30, 30),
                        'y': self.plane_y + random.randint(-30, 30),
                        'size': random.randint(8, 20),
                        'life': 25,
                        'color': (255, random.randint(0, 100), 0)
                    }
                    self.explosions.append(explosion)
                break
    
    def draw_background(self, canvas):
        """Draw aviation background"""
        # Sky gradient
        for y in range(self.height):
            color_ratio = y / self.height
            sky_r = int(135 + (25 * color_ratio))  # Lighter at bottom
            sky_g = int(206 + (25 * color_ratio))
            sky_b = int(235 + (20 * color_ratio))
            cv2.line(canvas, (0, y), (self.width, y), (sky_b, sky_g, sky_r), 1)
        
        # Draw clouds
        for cloud in self.clouds:
            cloud_color = (255, 255, 255, cloud['opacity'])
            # Draw fluffy cloud shape
            for i in range(5):
                offset_x = random.randint(-cloud['size']//3, cloud['size']//3)
                offset_y = random.randint(-cloud['size']//4, cloud['size']//4)
                cv2.circle(canvas, 
                          (int(cloud['x'] + offset_x), int(cloud['y'] + offset_y)), 
                          cloud['size']//2, (255, 255, 255), -1)
        
        # Draw terrain at bottom (mountains/ground)
        terrain_points = []
        for x in range(0, self.width + 50, 50):
            terrain_y = self.height - 100 + math.sin((x + self.terrain_scroll) * 0.01) * 30
            terrain_points.append([x, int(terrain_y)])
        terrain_points.append([self.width, self.height])
        terrain_points.append([0, self.height])
        
        if len(terrain_points) > 2:
            cv2.fillPoly(canvas, [np.array(terrain_points)], (34, 139, 34))  # Forest green
    
    def draw_plane(self, canvas):
        """Draw player plane with banking effect"""
        # Plane body (triangle shape)
        plane_points = np.array([
            [self.plane_x, self.plane_y - 15],  # Nose
            [self.plane_x - 12, self.plane_y + 15],  # Left wing
            [self.plane_x + 12, self.plane_y + 15],  # Right wing
        ])
        
        # Apply banking rotation
        if abs(self.plane_angle) > 5:
            center = np.array([self.plane_x, self.plane_y])
            angle_rad = math.radians(self.plane_angle * 0.3)
            cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
            rotation_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            
            rotated_points = []
            for point in plane_points:
                relative_point = point - center
                rotated_point = rotation_matrix.dot(relative_point) + center
                rotated_points.append(rotated_point.astype(int))
            plane_points = np.array(rotated_points)
        
        # Draw plane
        cv2.fillPoly(canvas, [plane_points], (0, 100, 255))  # Blue plane
        cv2.polylines(canvas, [plane_points], True, (255, 255, 255), 2)  # White outline
        
        # Draw engine trail based on speed
        if self.plane_speed > 3:
            trail_length = int(self.plane_speed * 5)
            cv2.line(canvas, 
                    (self.plane_x, self.plane_y + 15),
                    (self.plane_x, self.plane_y + 15 + trail_length),
                    (255, 100, 0), 3)  # Orange engine trail
    
    def draw_enemies(self, canvas):
        """Draw enemy planes"""
        for enemy in self.enemy_planes:
            # Enemy plane shape (different from player)
            enemy_points = np.array([
                [int(enemy['x']), int(enemy['y'] + 10)],  # Nose pointing down
                [int(enemy['x'] - 15), int(enemy['y'] - 10)],  # Left wing
                [int(enemy['x'] + 15), int(enemy['y'] - 10)],  # Right wing
            ])
            
            cv2.fillPoly(canvas, [enemy_points], enemy['color'])
            cv2.polylines(canvas, [enemy_points], True, (255, 255, 255), 1)
    
    def draw_projectiles(self, canvas):
        """Draw all projectiles"""
        # Draw bullets
        for bullet in self.bullets:
            cv2.circle(canvas, (int(bullet['x']), int(bullet['y'])), 
                      bullet['size'], bullet['color'], -1)
        
        # Draw missiles with trail
        for missile in self.missiles:
            cv2.circle(canvas, (int(missile['x']), int(missile['y'])), 
                      missile['size'], missile['color'], -1)
            # Missile trail
            cv2.line(canvas,
                    (int(missile['x']), int(missile['y'])),
                    (int(missile['x'] - missile['vx'] * 3), int(missile['y'] - missile['vy'] * 3)),
                    (255, 200, 0), 2)
    
    def draw_explosions(self, canvas):
        """Draw explosion effects"""
        for explosion in self.explosions:
            alpha = explosion['life'] / 20.0
            color = tuple(int(c * alpha) for c in explosion['color'])
            cv2.circle(canvas, (int(explosion['x']), int(explosion['y'])), 
                      explosion['size'], color, -1)
    
    def draw_hud(self, canvas):
        """Draw heads-up display"""
        # Background panel for HUD
        cv2.rectangle(canvas, (10, 10), (400, 200), (0, 0, 0, 128), -1)
        
        # Flight info
        cv2.putText(canvas, f"ALTITUDE: {self.altitude}ft", (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(canvas, f"SPEED: {int(self.plane_speed * 50)}kts", (20, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(canvas, f"BANK: {int(self.plane_angle)}°", (20, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Score and lives
        cv2.putText(canvas, f"SCORE: {self.score}", (20, 140), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(canvas, f"LIVES: {self.lives}", (20, 170), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Weapon info
        weapon_color = (0, 255, 255) if self.current_weapon == "bullets" else (255, 255, 255)
        cv2.putText(canvas, f"WEAPON: {self.current_weapon.upper()}", (220, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, weapon_color, 2)
        cv2.putText(canvas, f"AMMO: {self.ammo[self.current_weapon]}", (220, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, weapon_color, 2)
        
        # Mode and hand status
        mode_text = "DUAL HAND MODE" if self.dual_hand_mode else "SINGLE HAND MODE"
        cv2.putText(canvas, mode_text, (220, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        if self.dual_hand_mode:
            left_status = "CONNECTED" if self.left_hand else "MISSING"
            right_status = "CONNECTED" if self.right_hand else "MISSING"
            left_color = (0, 255, 0) if self.left_hand else (0, 0, 255)
            right_color = (0, 255, 0) if self.right_hand else (0, 0, 255)
            
            cv2.putText(canvas, f"LEFT HAND: {left_status}", (220, 140), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, left_color, 2)
            cv2.putText(canvas, f"RIGHT HAND: {right_status}", (220, 170), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, right_color, 2)
        else:
            hand_status = "CONNECTED" if (self.left_hand or self.right_hand) else "MISSING"
            hand_color = (0, 255, 0) if (self.left_hand or self.right_hand) else (0, 0, 255)
            cv2.putText(canvas, f"HAND: {hand_status}", (220, 140), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, hand_color, 2)
        
        # Current gestures
        cv2.putText(canvas, f"L: {self.left_gesture}", (450, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(canvas, f"R: {self.right_gesture}", (450, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Game over
        if self.lives <= 0:
            cv2.putText(canvas, "AIRCRAFT DOWN!", (self.width//2 - 150, self.height//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
            cv2.putText(canvas, "Press R to respawn", (self.width//2 - 120, self.height//2 + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    def draw_game(self, camera_frame):
        """Draw complete game scene"""
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Draw background first
        self.draw_background(canvas)
        
        # Draw game objects
        self.draw_explosions(canvas)
        self.draw_projectiles(canvas)
        self.draw_enemies(canvas)
        self.draw_plane(canvas)
        
        # Draw HUD on top
        self.draw_hud(canvas)
        
        # Add camera feed in corner
        if camera_frame is not None:
            small_frame = cv2.resize(camera_frame, (160, 120))
            canvas[self.height-130:self.height-10, self.width-170:self.width-10] = small_frame
        
        return canvas
    
    def reset_game(self):
        """Reset game state"""
        self.score = 0
        self.lives = 3
        self.level = 1
        self.plane_x = self.width // 2
        self.plane_y = self.height - 150
        self.plane_speed = 0
        self.bullets = []
        self.missiles = []
        self.enemy_planes = []
        self.explosions = []
        self.ammo = {"bullets": 999, "missiles": 10, "bombs": 5}
        self.last_enemy_spawn = time.time()
    
    def run(self):
        """Main game loop with dual hand tracking"""
        mode_text = "Dual-Hand" if self.dual_hand_mode else "Single-Hand"
        print(f"✈️ Starting {mode_text} Plane Attack Game...")
        print("\n🎮 FLIGHT CONTROLS:")
        
        if self.dual_hand_mode:
            print("👈 LEFT HAND:")
            print("   • Position = Plane movement")
            print("   • Tilt = Banking/turning")
            print("   • All fingers = Full throttle")
            print("   • Some fingers = Cruise speed")
            print("   • Fist = Slow/hover")
            print("\n👉 RIGHT HAND:")
            print("   • Pinch = Shoot bullets")
            print("   • Point = Fire missile")
            print("   • Open palm = Drop bombs")
            print("   • Fist = Switch weapons")
            print("   • Peace = Special barrel roll attack")
        else:
            print("✋ SINGLE HAND:")
            print("   • Position = Plane movement")
            print("   • Pinch = Shoot bullets")
            print("   • Point = Fire missile")
            print("   • Open palm = Drop bombs")
            print("   • Fist = Switch weapons")
            print("   • Peace = Special barrel roll attack")
            print("   • Auto-cruise speed")
        
        print("\n⌨️ KEYBOARD: ESC=Quit | R=Restart")
        print("=" * 60)
        
        max_hands = 2 if self.dual_hand_mode else 1
        with self.mp_hands.Hands(
            max_num_hands=max_hands,
            model_complexity=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        ) as hands:
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Lost camera connection")
                    break
                
                # Process frame
                frame = cv2.flip(frame, 1)  # Mirror effect
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)
                
                # Reset hand tracking
                self.left_hand = None
                self.right_hand = None
                self.left_gesture = "none"
                self.right_gesture = "none"
                
                # Process detected hands
                if results.multi_hand_landmarks:
                    if self.dual_hand_mode and results.multi_handedness:
                        # Dual hand mode
                        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                            hand_type = self.detect_hand_type(hand_landmarks, handedness)
                            landmarks = hand_landmarks.landmark
                            
                            if hand_type == "Left":
                                self.left_hand = landmarks
                                self.left_gesture = self.detect_left_hand_gesture(landmarks)
                                self.update_plane_from_left_hand(landmarks, self.left_gesture)
                                # Draw left hand landmarks
                                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                                
                            elif hand_type == "Right":
                                self.right_hand = landmarks
                                self.right_gesture = self.detect_right_hand_gesture(landmarks)
                                self.handle_right_hand_weapons(landmarks, self.right_gesture)
                                # Draw right hand landmarks
                                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    else:
                        # Single hand mode - use first detected hand for everything
                        hand_landmarks = results.multi_hand_landmarks[0]
                        landmarks = hand_landmarks.landmark
                        
                        # Set as left hand for compatibility with HUD
                        self.left_hand = landmarks
                        self.right_hand = None
                        
                        # Detect gesture and update plane
                        gesture = self.detect_single_hand_gesture(landmarks)
                        self.left_gesture = gesture
                        self.right_gesture = gesture
                        
                        self.update_plane_from_single_hand(landmarks, gesture)
                        
                        # Draw hand landmarks
                        self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # Update game
                if self.lives > 0:
                    self.update_game_objects()
                
                # Draw game
                game_display = self.draw_game(frame)
                
                cv2.imshow("Dual-Hand Plane Attack Game", game_display)
                
                # Handle keyboard
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
                elif key == ord('r') or key == ord('R'):
                    self.reset_game()
        
        self.cap.release()
        cv2.destroyAllWindows()
        print("✈️ Flight ended - Safe landing!")

if __name__ == "__main__":
    print("✈️ DUAL-HAND PLANE ATTACK GAME ✈️")
    print("=" * 70)
    print("🎯 Advanced dual-hand flight simulation")
    print("👈 Left hand controls plane movement and speed")
    print("👉 Right hand controls weapons and attacks")
    print("🎮 Realistic aviation graphics and physics")
    print("=" * 70)
    
    try:
        game = DualHandPlaneGame()
        game.run()
    except KeyboardInterrupt:
        print("\n✈️ Flight interrupted - Emergency landing!")
    except Exception as e:
        print(f"\n❌ Flight system error: {e}")
