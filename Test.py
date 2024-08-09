import cv2
import numpy as np

# Load the sheet music image
image = cv2.imread('page3.jpg', cv2.IMREAD_GRAYSCALE)

# Binarize the image
_, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)


# Detect and remove staff lines
def remove_staff_lines(image):
    # Use morphological operations to detect staff lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    detected_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

    # Subtract staff lines from the binary image
    image_no_lines = cv2.subtract(image, detected_lines)
    return image_no_lines


image_no_lines = remove_staff_lines(binary)


# Detect note heads
def detect_note_heads(image):
    # Use connected components to detect note heads
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(image, connectivity=4)

    note_heads = []
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        # Filter based on aspect ratio and size to detect note heads
        if 0.5 < w / h < 1.5 and 100 < area < 500:
            note_heads.append((x, y, w, h))

    return note_heads


note_heads = detect_note_heads(image_no_lines)

# Draw detected note heads on the original image
output_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
for (x, y, w, h) in note_heads:
    cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

# Display the result
cv2.imshow('Detected Note Heads', output_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
