import cv2
import numpy as np

# Define color ranges in HSV color space
color_ranges = {
    'red': ((0, 100, 100), (10, 255, 255)),
    'orange': ((10, 100, 100), (20, 255, 255)),
    'yellow': ((20, 100, 100), (30, 255, 255)),
    'green': ((30, 100, 100), (50, 255, 255)),
    'blue': ((50, 100, 100), (70, 255, 255)),
    'purple': ((70, 100, 100), (140, 255, 255))
}

def detect_colors(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Loop over the color ranges and detect each color
    for color_name, (lower, upper) in color_ranges.items():
        lower_bound = np.array(lower)
        upper_bound = np.array(upper)
        
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        result = cv2.bitwise_and(frame, frame, mask=mask)

        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) > 500:  # Filter out small areas
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, color_name.capitalize(), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

def main():
    # Open the default camera
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            print("Error: Could not read frame.")
            break

        # Detect colors and annotate them
        detect_colors(frame)

        # Display the resulting frame
        cv2.imshow('Camera Feed', frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the capture and close windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
