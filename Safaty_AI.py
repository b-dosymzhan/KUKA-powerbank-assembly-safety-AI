import cv2
import numpy as np
from ultralytics import YOLO
import math
from robodk.robolink import *      # import the robolink library
from robodk.robomath import *


# === RoboDK connection ===
RDK = Robolink()
# Set the maximum number of lines per program segment to 4000
RDK.Command("ProgMaxLines", 4000)
robot = RDK.Item('KUKA KR 10 R1100-2', ITEM_TYPE_ROBOT)  # Update with your robot's name
robot_program_name = RDK.Item('Assembly_powerbank', ITEM_TYPE_PROGRAM)
robot_program_name.RunProgram()
robot_running = True

# --- Marker Detection Helper Functions (No longer used for circle definition) ---
# Kept here in case you want to reuse them later, but commented out related parts below.
def find_fourth_point(pts):
    """Predicts the 4th point of a parallelogram given 3 points."""
    if pts.shape != (3, 2): return None
    centroid = np.mean(pts, axis=0)
    distances = np.sum((pts - centroid)**2, axis=1)
    idx_far = np.argmax(distances)
    p_far = pts[idx_far]
    p_others = np.delete(pts, idx_far, axis=0)
    p1 = p_others[0]
    p2 = p_others[1]
    p_missing = (p1.astype(np.float32) + p2.astype(np.float32)) - p_far.astype(np.float32)
    return p_missing.astype(np.int32)

def order_points(pts):
    """Orders 4 points: top-left, top-right, bottom-right, bottom-left."""
    if pts.shape != (4, 2): return None
    y_sorted = pts[np.argsort(pts[:, 1]), :]
    top_points = y_sorted[:2, :]
    bottom_points = y_sorted[2:, :]
    top_points = top_points[np.argsort(top_points[:, 0]), :]
    bottom_points = bottom_points[np.argsort(bottom_points[:, 0]), :]
    ordered = np.array([top_points[0], top_points[1], bottom_points[1], bottom_points[0]], dtype=np.int32)
    return ordered

# --- Person Segmentation Detection Helper Function ---

def is_mask_in_circle(mask_points, circle_center_x, circle_center_y, radius):
    """
    Check if any point of the segmentation mask polygon is inside the circle.
    A simple check, could be made more sophisticated (e.g., centroid or bounding box of mask).
    """
    if mask_points is None or len(mask_points) == 0 or circle_center_x is None or circle_center_y is None or radius <= 0:
        return False

    # Check if any vertex of the polygon mask is inside the circle
    for pt in mask_points:
        # Ensure pt has two elements
        if len(pt) == 2:
            dist_sq = (pt[0] - circle_center_x)**2 + (pt[1] - circle_center_y)**2
            if dist_sq <= radius**2:
                return True # At least one point is inside
        # else:
            # print(f"Warning: Invalid point format in mask: {pt}") # Optional debug print

    # Optional: Add check if circle center is inside polygon (more complex)
    # Optional: Add check if polygon edges intersect circle (more complex)

    return False # No points inside

# --- Main Setup ---

# === IMPORTANT: Use a segmentation model ===
try:
    # model = YOLO('yolov8n-seg.pt') # Use nano segmentation model
    # Or choose a larger one if needed:
    model = YOLO('yolov8s-seg.pt') # Use small segmentation model
except Exception as e:
    print(f"Error loading YOLO segmentation model: {e}")
    print("Ensure you have a 'yolov8*-seg.pt' model file.")
    exit()

target_class = 'person'
yolo_confidence_threshold = 0.5

# Initialize video capture
cap = cv2.VideoCapture(0)# Use camera index 0, change if needed
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()
    

# --- Manual Circle Control Setup ---
current_circle_center = None
current_circle_radius = 0
initial_radius = 100
move_step = 15 # Pixels to move center per key press
radius_step = 10 # Pixels to change radius per key press

cv2.namedWindow('Manual Danger Zone & Segmentation', cv2.WINDOW_NORMAL)

print("Starting detection loop...")
print("Controls:")
print("  'c' - Create/Reset Circle at center")
print("  'w' - Move Circle Up")
print("  's' - Move Circle Down")
print("  'a' - Move Circle Left")
print("  'd' - Move Circle Right")
print("  '+' - Increase Radius")
print("  '-' - Decrease Radius")
print("  'q' - Quit")
print("\nDetecting and segmenting people...")

while True:
    # Read a frame from the camera
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    frame_height, frame_width = frame.shape[:2]
    output_frame = frame.copy()

    # --- 1. Manual Circle Control ---
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('c'):
        # Create or reset circle to center
        current_circle_center = (frame_width // 2, frame_height // 2)
        current_circle_radius = initial_radius
        print(f"Circle created/reset at {current_circle_center} with radius {current_circle_radius}")
    elif current_circle_center is not None: # Only allow adjustments if circle exists
        cx, cy = current_circle_center
        if key == ord('w'): # Move Up
            cy = max(0, cy - move_step)
            current_circle_center = (cx, cy)
        elif key == ord('s'): # Move Down
            cy = min(frame_height, cy + move_step)
            current_circle_center = (cx, cy)
        elif key == ord('a'): # Move Left
            cx = max(0, cx - move_step)
            current_circle_center = (cx, cy)
        elif key == ord('d'): # Move Right
            cx = min(frame_width, cx + move_step)
            current_circle_center = (cx, cy)
        elif key == ord('+') or key == ord('='): # Increase Radius
            current_circle_radius += radius_step
        elif key == ord('-'): # Decrease Radius
            current_circle_radius = max(5, current_circle_radius - radius_step) # Keep radius at least 5

    # Draw the manually controlled circle if it exists
    if current_circle_center is not None and current_circle_radius > 0:
        cv2.circle(output_frame, current_circle_center, current_circle_radius, (255, 255, 0), 2) # Cyan danger circle


    # --- 2. Human Segmentation & Intersection Check ---
    # Run YOLO segmentation
    results = model(frame, verbose=False) # Use original frame for detection
    warning = False

    # Process results
    if results and results[0].masks is not None: # Check if masks are present
        # Iterate through detected objects
        for i, box in enumerate(results[0].boxes.data.tolist()):
            x1, y1, x2, y2, score, class_id = box
            class_name = model.names[int(class_id)]

            # Filter for 'person' class with sufficient confidence
            if class_name == target_class and score > yolo_confidence_threshold:
                # --- Get Segmentation Mask ---
                mask_data = results[0].masks[i]
                # Extract polygon points (xy format expected)
                if mask_data.xy is not None and len(mask_data.xy) > 0:
                    polygon = mask_data.xy[0] # Get the first (usually only) polygon
                    mask_points = polygon.astype(np.int32) # Convert to integer points

                    # --- Draw Segmentation Mask ---
                    # Default color (e.g., orange)
                    mask_color = (0, 165, 255)

                    # --- Check Intersection ---
                    intersects = False
                    if current_circle_center is not None: # Only check if circle is defined
                        intersects = is_mask_in_circle(mask_points,
                                                       current_circle_center[0], current_circle_center[1],
                                                       current_circle_radius)
                        if intersects:
                            warning = True
                            mask_color = (0, 0, 255) # Change color to red if intersecting

                    # Draw the polygon outline
                    cv2.polylines(output_frame, [mask_points], isClosed=True, color=mask_color, thickness=2)

                    # --- Add Label (optional) near the top of the bounding box ---
                    label = f"{class_name}: {score:.2f}"
                    text_x, text_y = int(x1), int(y1) - 10 # Use box coordinates for label placement
                    # Ensure label stays within frame bounds
                    text_y = max(text_y, 15)
                    cv2.putText(output_frame, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, mask_color, 2)
                # else:
                #     print(f"Warning: No mask polygon data found for detected person {i}")


    # --- 3. Display Status/Warning ---
    info_text = ""
    info_color = (0, 255, 255) # Yellow for info
    if warning:
        info_text = "WARNING: Person in Zone!"
        info_color = (0, 0, 255) # Red for warning
        if robot_running:
            robot_program_name.Stop()
            #robot.Stop()
            # Disable drives to pause robot (motors off, program stays in place)
            #robot.setParam("KUKA KRC2", 'SET $DRIVES_ENABLE FALSE')
            #robot.Disconnect()
            #robot.Disconnect()  # Second call ensures the driver is killed
            robot_running = False
            #robot.setParam("COM_ACTION", 99)
            print("🔴 Robot PAUSED")
    elif current_circle_center is None:
         info_text = "Press 'c' to create danger zone"
    else:
        info_text = "Zone Active. Use WASD/+- to adjust."
        info_color = (0, 255, 0) # Green for active zone
        if not robot_running:
            #robot.setParam("KUKA KRC2", 'SET $DRIVES_ENABLE TRUE')   # resume
            robot_running = True
            robot_program_name.RunProgram()
            print("🟢 Robot RESUMED")

    cv2.putText(output_frame, info_text, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, info_color, 2, cv2.LINE_AA)

    # Display control help text (optional, can be disabled if too cluttered)
    help_text_y = frame_height - 10
    cv2.putText(output_frame, "Controls: c=Create, WASD=Move, +/-=Resize, q=Quit", (10, help_text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)


    # --- 4. Display Combined Frame ---
    cv2.imshow('Manual Danger Zone & Segmentation', output_frame)

    # --- 5. Exit Condition (already handled by 'q' check earlier) ---
    # (no additional check needed here)

# --- Release Resources ---
cap.release()
cv2.destroyAllWindows()
print("Processing finished.")
