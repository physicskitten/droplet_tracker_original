import cv2
import os
import sys
import numpy as np

# Path to the video file
video_path = 'E:/USB/Documents/VTestVid_9.mp4'

# Extract the file name from the path
video_name = os.path.basename(video_path)
# Get the name of the current script file
script_name = os.path.basename(__file__)
# Create the window title
window_title = f"{video_name} ({script_name})"

# Create a named window with the ability to resize
cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)

# Create a VideoCapture object
cap = cv2.VideoCapture(video_path)

# Check if the video opened successfully
if not cap.isOpened():
    print("Error: Could not open video.")
    cv2.imshow(window_title, cv2.imread(''))  # Display an empty frame
    while True:
        if cv2.waitKey(25) != -1 or cv2.getWindowProperty(window_title, cv2.WND_PROP_VISIBLE) < 1:
            break
    cv2.destroyAllWindows()
    sys.exit()

# Get the total number of frames and FPS of the video
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)
duration_seconds = total_frames / fps

# Function to detect the circle and calculate the crop coordinates
def get_crop_coordinates(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=100,
        param1=100, param2=30, minRadius=0, maxRadius=0
    )

    if circles is not None:
        circles2 = circles[0, :].astype("int")
        x, y, r = circles2[0] # The ith detected circle that centres the crop
        x1, y1, r1 = circles2[40] # The ith detected circle that determines the radius of the red circle and mask

        # Adjust the crop to center around the black circle within the copper circle
        black_circle_r = int(0.51 * r1)  # Precentage of originally detected circle
        side_length = 2 * black_circle_r
        start_x = max(0, x - black_circle_r)
        start_y = max(0, y - black_circle_r)
        end_x = start_x + side_length
        end_y = start_y + side_length

        height, width, _ = frame.shape
        if end_x > width:
            start_x = width - side_length
        if end_y > height:
            start_y = height - side_length

        return start_x, start_y, side_length, x, y, black_circle_r
    return None

# Function to crop the frame and apply the circular mask
def crop_and_mask_frame(frame, crop_coords):
    start_x, start_y, side_length, circle_x, circle_y, circle_r = crop_coords
    cropped_frame = frame[start_y:start_y + side_length, start_x:start_x + side_length]
    
    # Create a mask with a filled black circle
    mask = np.zeros_like(cropped_frame)
    cv2.circle(mask, (circle_x - start_x, circle_y - start_y), circle_r, (255, 255, 255), -1)

    # Apply the mask to the frame
    masked_frame = cv2.bitwise_and(cropped_frame, mask)
    
    # Draw a bright red line around the black circle
    cv2.circle(masked_frame, (circle_x - start_x, circle_y - start_y), circle_r, (0, 0, 255), 3)
    
    return masked_frame

# Read the first frame and determine the crop coordinates
ret, first_frame = cap.read()
if not ret:
    print("Error: Could not read the first frame.")
    cap.release()
    cv2.destroyAllWindows()
    sys.exit()

crop_coords = get_crop_coordinates(first_frame)
if not crop_coords:
    print("Error: Could not detect the circle in the first frame.")
    cap.release()
    cv2.destroyAllWindows()
    sys.exit()

# Apply the crop and mask to the first frame
first_frame_masked = crop_and_mask_frame(first_frame, crop_coords)

# Define the codec and create a VideoWriter object
output_filename = f"Crop_{video_name}"
output_path = os.path.join(os.path.dirname(__file__), output_filename)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, fps, (first_frame_masked.shape[1], first_frame_masked.shape[0]))

# Function to handle trackbar movement
def on_trackbar_move(pos):
    # Set the video capture to the position defined by the trackbar
    cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
    # Read the frame at the new position
    ret, frame = cap.read()
    if ret:
        # Crop and mask the frame
        frame_masked = crop_and_mask_frame(frame, crop_coords)
        # Calculate current time and duration
        current_time = pos / fps
        current_minutes = int(current_time // 60)
        current_seconds = int(current_time % 60)
        current_time_str = f"{current_minutes:02}:{current_seconds:02}"
        total_minutes = int(duration_seconds // 60)
        total_seconds = int(duration_seconds % 60)
        total_hours = int(total_minutes // 60)
        total_minutes %= 60
        total_duration_str = f"{total_hours:02}:{total_minutes:02}:{total_seconds:02}"
        # Add text overlay with current time and total duration
        text_overlay = f"Time: {current_time_str} / Duration: {total_duration_str}"
        cv2.putText(frame_masked, text_overlay, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        # Display the resulting frame
        cv2.imshow(window_title, frame_masked)

# Create a trackbar for navigation
cv2.createTrackbar('Position', window_title, 0, total_frames - 1, on_trackbar_move)

paused = False

# Read and display video frames
while True:
    if not paused:
        ret, frame = cap.read()
    
    if not ret:
        print("Reached the end of the video.")
        break

    # Crop and mask the frame
    frame_masked = crop_and_mask_frame(frame, crop_coords)
    
    # Calculate current time and duration
    current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    current_time = current_frame / fps
    current_minutes = int(current_time // 60)
    current_seconds = int(current_time % 60)
    current_time_str = f"{current_minutes:02}:{current_seconds:02}"
    total_minutes = int(duration_seconds // 60)
    total_seconds = int(duration_seconds % 60)
    total_hours = int(total_minutes // 60)
    total_minutes %= 60
    total_duration_str = f"{total_hours:02}:{total_minutes:02}:{total_seconds:02}"

    # Add text overlay with current time and total duration
    #text_overlay = f"Time: {current_time_str} / Duration: {total_duration_str}"
    #cv2.putText(frame_masked, text_overlay, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
   
    # Write the masked frame to the output video file
    out.write(frame_masked)

    # Display the resulting frame
    cv2.imshow(window_title, frame_masked)
    
    key = cv2.waitKey(25)
    if key == 32:  # Space bar to pause/resume
        paused = not paused
    elif key != -1 or cv2.getWindowProperty(window_title, cv2.WND_PROP_VISIBLE) < 1:
        break

# Show the last frame indefinitely until a key is pressed or window is closed
if not ret:
    cv2.imshow(window_title, frame_masked)
    print("Paused on the last frame. Press any key to exit.")
    while True:
        if cv2.waitKey(25) != -1 or cv2.getWindowProperty(window_title, cv2.WND_PROP_VISIBLE) < 1:
            break

# Release the video capture and writer objects and close display windows
cap.release()
out.release()
cv2.destroyAllWindows()
