import cv2
import numpy as np
from collections import deque

# =============================
# CONFIGURATION
# =============================
BRIGHTNESS_THRESHOLD = 200
MIN_CONTOUR_AREA = 120
MAX_CONTOUR_AREA = 4000

BLINK_HISTORY = 18
BLINK_MIN_RATIO = 0.25
BLINK_MAX_RATIO = 0.75

# Blink buffers PER COLOR
blink_red = deque(maxlen=BLINK_HISTORY)
blink_blue = deque(maxlen=BLINK_HISTORY)
blink_amber = deque(maxlen=BLINK_HISTORY)

# =============================
# COLOR RANGES (HSV)
# =============================

RED_RANGES = [
    ((0, 120, 180), (10, 255, 255)),
    ((170, 120, 180), (180, 255, 255))
]

BLUE_RANGE = ((90, 120, 180), (130, 255, 255))
AMBER_RANGE = ((10, 120, 180), (28, 255, 255))

# White headlights (to EXCLUDE)
WHITE_RANGE = ((0, 0, 200), (180, 40, 255))

# =============================
# FUNCTIONS
# =============================

def get_mask(hsv, ranges):
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for low, high in ranges:
        mask |= cv2.inRange(hsv, np.array(low), np.array(high))
    return mask


def blinking(buffer):
    if len(buffer) < BLINK_HISTORY:
        return False
    ratio = sum(buffer) / BLINK_HISTORY
    return BLINK_MIN_RATIO < ratio < BLINK_MAX_RATIO


def valid_light_shape(w, h):
    aspect = w / float(h)
    return 0.4 < aspect < 3.5   # light-bar like shape


# =============================
# MAIN
# =============================

cap = cv2.VideoCapture("traffic_video5.mp4")

print("[INFO] Improved siren light detection started...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, None, fx=0.75, fy=0.75)

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    _, bright = cv2.threshold(gray, BRIGHTNESS_THRESHOLD, 255, cv2.THRESH_BINARY)

    # Color masks
    red_mask = get_mask(hsv, RED_RANGES)
    blue_mask = cv2.inRange(hsv, np.array(BLUE_RANGE[0]), np.array(BLUE_RANGE[1]))
    amber_mask = cv2.inRange(hsv, np.array(AMBER_RANGE[0]), np.array(AMBER_RANGE[1]))
    white_mask = cv2.inRange(hsv, np.array(WHITE_RANGE[0]), np.array(WHITE_RANGE[1]))

    # Remove white headlights
    red_mask = cv2.bitwise_and(red_mask, cv2.bitwise_not(white_mask))
    blue_mask = cv2.bitwise_and(blue_mask, cv2.bitwise_not(white_mask))
    amber_mask = cv2.bitwise_and(amber_mask, cv2.bitwise_not(white_mask))

    # Combine with brightness
    red_mask = cv2.bitwise_and(red_mask, bright)
    blue_mask = cv2.bitwise_and(blue_mask, bright)
    amber_mask = cv2.bitwise_and(amber_mask, bright)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
    blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_OPEN, kernel)
    amber_mask = cv2.morphologyEx(amber_mask, cv2.MORPH_OPEN, kernel)

    # Detect contours PER COLOR
    detected_red = False
    detected_blue = False
    detected_amber = False

    for mask, color_name in [
        (red_mask, "RED"),
        (blue_mask, "BLUE"),
        (amber_mask, "AMBER")
    ]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if not (MIN_CONTOUR_AREA < area < MAX_CONTOUR_AREA):
                continue

            x, y, w, h = cv2.boundingRect(c)
            if not valid_light_shape(w, h):
                continue

            if color_name == "RED":
                detected_red = True
                box_color = (0,0,255)
            elif color_name == "BLUE":
                detected_blue = True
                box_color = (255,0,0)
            else:
                detected_amber = True
                box_color = (0,165,255)

            cv2.rectangle(frame, (x,y), (x+w,y+h), box_color, 2)

    # Update blink buffers
    blink_red.append(1 if detected_red else 0)
    blink_blue.append(1 if detected_blue else 0)
    blink_amber.append(1 if detected_amber else 0)

    # Blinking logic
    red_blink = blinking(blink_red)
    blue_blink = blinking(blink_blue)
    amber_blink = blinking(blink_amber)

    # =============================
    # DECISION LOGIC
    # =============================
    siren = False
    label = ""

    if red_blink and blue_blink:
        siren = True
        label = "POLICE (RED+BLUE)"
    elif blue_blink:
        siren = True
        label = "POLICE (BLUE)"
    elif red_blink:
        siren = True
        label = "FIRE / AMBULANCE"
    elif amber_blink:
        siren = True
        label = "VIP / ESCORT"

    # =============================
    # DISPLAY
    # =============================
    if siren:
        cv2.putText(frame, f"SIREN DETECTED: {label}",
                    (20,40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (0,255,255), 3)
    else:
        cv2.putText(frame, "No siren detected",
                    (20,40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (200,200,200), 2)

    cv2.imshow("Improved Siren Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
