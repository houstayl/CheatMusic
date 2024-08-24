import cv2
import numpy as np

def detect_staff_lines(image_path, min_line_length=100, max_line_gap=10):
    # Load the image
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Apply Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(img, (5, 5), 0)

    # Use Canny edge detection
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)

    # Use Hough Line Transform to detect lines
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi / 180, threshold=100,
                            minLineLength=min_line_length, maxLineGap=max_line_gap)

    # Create a copy of the original image to draw the lines
    line_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    # Filter and draw detected lines
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                # Check if the line is roughly horizontal
                if abs(y2 - y1) < 10:  # Adjust this threshold as needed
                    cv2.line(line_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Display the result
    cv2.imshow("Detected Staff Lines", line_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return line_img

# Example usage
detected_lines_image = detect_staff_lines('page0.jpg', 5, 10)
