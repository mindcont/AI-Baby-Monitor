"""Sleep, motion and safety monitoring module."""
import cv2
import time
from config.settings import config
from utils.helpers import log_line
from services.notification.notification_service import get_notification_service

notification_service = get_notification_service()


class MotionActivityDetector:
    """Detect motion, optionally restricted to a tracked target bounding box."""

    def __init__(self):
        self.background = cv2.createBackgroundSubtractorMOG2(
            history=200,
            varThreshold=config.MOTION_THRESHOLD,
            detectShadows=True,
        )
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    def update(self, frame, bbox=None):
        """Return (motion_detected, changed_area) for the current frame."""
        mask = self.background.apply(frame)
        _, mask = cv2.threshold(mask, 244, 255, cv2.THRESH_BINARY)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel)

        if bbox is not None:
            x1, y1, x2, y2 = [int(v) for v in bbox]
            height, width = mask.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(width, x2), min(height, y2)
            if x2 <= x1 or y2 <= y1:
                return False, 0
            mask = mask[y1:y2, x1:x2]

        changed_area = int(cv2.countNonZero(mask))
        return changed_area >= config.MOTION_MIN_AREA, changed_area


class SleepMonitor:
    """Sleep detection and monitoring"""
    
    def __init__(self):
        """Initialize sleep monitor"""
        self.child_last_position = None
        self.last_movement_time = None
        self.child_is_sleeping = False
        self.last_wake_notification = 0.0
        self.stationary_start_time = None
        self.wake_alert_display_time = 0.0
        self.enabled = config.SLEEP_DETECTION_ENABLED
        self.child_detected = False  # Track if child is currently detected
        self.frames_without_detection = 0  # Track consecutive frames without detection
        self.max_frames_without_detection = config.CHILD_MISSING_GRACE_FRAMES
        self.motion_confirmation_frames = config.MOTION_CONFIRMATION_FRAMES
        self.pending_motion_frames = 0
        
    def update(self, child_center, motion_detected=None, motion_area=0):
        """Update sleep monitoring state"""
        if not self.enabled:
            return
            
        # Update child detection status with persistence
        if child_center is not None:
            # Child detected - reset frame counter and mark as detected
            self.child_detected = True
            self.frames_without_detection = 0
        else:
            # No child detected this frame - increment counter
            self.frames_without_detection += 1
            # Only mark as not detected after a grace period for occlusion/dropouts.
            if self.frames_without_detection >= self.max_frames_without_detection:
                self.child_detected = False
        
        # If no child detected, reset some states but keep detection status
        if child_center is None:
            # Preserve sleep state and stationary time during a short occlusion.
            # After the grace period, clear the position but keep the last sleep state
            # until a new target is confirmed.
            if not self.child_detected:
                self.child_last_position = None
                self.stationary_start_time = None
                self.pending_motion_frames = 0
            return
            
        current_time = time.time()
        
        # Calculate movement from last known position
        movement_detected = False
        if self.child_last_position is not None:
            distance = ((child_center[0] - self.child_last_position[0]) ** 2 + 
                       (child_center[1] - self.child_last_position[1]) ** 2) ** 0.5
            center_motion = distance > config.MOVEMENT_THRESHOLD
            if motion_detected is None:
                motion_detected = center_motion

            if center_motion or motion_detected:
                self.pending_motion_frames += 1
            else:
                self.pending_motion_frames = 0

            movement_detected = self.pending_motion_frames >= self.motion_confirmation_frames
            if movement_detected:
                self.last_movement_time = current_time
                
                # If child was sleeping and now moving, wake up detected!
                if (self.child_is_sleeping and 
                    (current_time - self.last_wake_notification) > config.WAKE_NOTIFICATION_COOLDOWN):
                    self.child_is_sleeping = False
                    self.stationary_start_time = None
                    self.last_wake_notification = current_time
                    self.wake_alert_display_time = current_time  # Show wake alert for 5 seconds
                    log_line("[WAKE] Child is now moving after sleep")
                    notification_service.dispatch_notification("[WAKE] Child Awake", "Child has woken up and started moving!")
        
        # Update position tracking
        self.child_last_position = child_center

        # Start the stationary clock once a target has been confirmed, even if
        # the first observed frames contain no large movement.
        if self.last_movement_time is None:
            self.last_movement_time = current_time
        
        # Check for sleep state (no movement for specified time)
        if self.last_movement_time is not None:
            if not movement_detected and not self.child_is_sleeping:
                # Start tracking stationary time
                if self.stationary_start_time is None:
                    self.stationary_start_time = current_time
                elif (current_time - self.stationary_start_time) >= config.SLEEP_TIME_SEC:
                    # Child has been stationary long enough - mark as sleeping
                    self.child_is_sleeping = True
                    log_line(f"[SLEEP] Child has been stationary for {config.SLEEP_TIME_SEC} seconds")
                    notification_service.dispatch_notification("[SLEEP] Child Sleeping", 
                          f"Child appears to be sleeping (no movement for {config.SLEEP_TIME_SEC//60}+ minutes)")
            
            elif movement_detected:
                # Reset stationary timer if movement detected
                self.stationary_start_time = None
    
    def reset(self):
        """Reset sleep monitoring state"""
        self.child_last_position = None
        self.last_movement_time = None
        self.child_is_sleeping = False
        self.stationary_start_time = None
        self.wake_alert_display_time = 0.0
        self.child_detected = False
        self.frames_without_detection = 0
        self.pending_motion_frames = 0
        log_line("Sleep detection reset.")
    
    def toggle_enabled(self):
        """Toggle sleep detection on/off"""
        self.enabled = not self.enabled
        status = "enabled" if self.enabled else "disabled"
        print(f"[SLEEP] Sleep detection {status}")
        log_line(f"Sleep/wake detection {status}")
        # Reset state when toggling
        if not self.enabled:
            self.child_is_sleeping = False
            self.stationary_start_time = None
            self.wake_alert_display_time = 0.0
            self.child_detected = False
            self.frames_without_detection = 0
            self.pending_motion_frames = 0
        return self.enabled

    def get_state(self):
        """Get current sleep state"""
        if not self.enabled:
            return "Disabled"
        if not self.child_detected:
            return "No child"
        return "Sleep" if self.child_is_sleeping else "Awake"
    
    def get_sleep_time(self):
        """Get current sleep duration"""
        if not self.enabled or not self.child_detected or not self.child_is_sleeping or self.stationary_start_time is None:
            return "0m"
        
        current_time = time.time()
        sleep_duration = current_time - self.stationary_start_time
        
        hours = int(sleep_duration // 3600)
        minutes = int((sleep_duration % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
        

class SafetyMonitor:
    """Safety monitoring for fall risk detection"""
    
    def __init__(self):
        """Initialize safety monitor"""
        self.outside_count = 0
        self.last_alert_time = 0.0
    
    def get_safe_zone(self, bed_box):
        """Calculate safe zone from bed bounding box"""
        if not config.USE_BED_SAFE_ZONE or bed_box is None:
            return None
            
        bx1, by1, bx2, by2 = bed_box
        # Safe zone shrunk inside bed
        mx = int(config.SAFE_MARGIN_RATIO * (bx2 - bx1))
        my = int(config.SAFE_MARGIN_RATIO * (by2 - by1))
        return (bx1 + mx, by1 + my, bx2 - mx, by2 - my)
    
    def check_fall_risk(self, child_center, safe_zone):
        """Check for fall risk based on child position"""
        if child_center is None or safe_zone is None:
            self.outside_count = 0
            return False
            
        sx1, sy1, sx2, sy2 = safe_zone
        cx, cy = child_center
        inside = (sx1 <= cx <= sx2) and (sy1 <= cy <= sy2)
        
        current_time = time.time()
        
        if inside:
            self.outside_count = 0
            return False
        else:
            self.outside_count += 1
            # Issue alert if persistently outside & cooldown elapsed
            if (self.outside_count >= config.RISK_FRAMES_THRESHOLD and 
                (current_time - self.last_alert_time) > config.ALERT_COOLDOWN_SEC):
                self.last_alert_time = current_time
                log_line("[ALERT] Child near edge (outside safe zone)")
                notification_service.dispatch_notification("[WARNING] Fall Risk", "Child is near the bed edge!")
                return True
        
        return False
    
    def reset(self):
        """Reset safety monitoring state"""
        self.outside_count = 0
