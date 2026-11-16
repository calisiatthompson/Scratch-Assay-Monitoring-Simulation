
import cv2
import time
from datetime import datetime
from pathlib import Path

# Image folders
sample_image = Path("sample_images/scratch_0h.png")
output_folder = Path("captured_images")

output_folder.mkdir(exist_ok=True)

# Simulation settings
capture_interval = 10
number_of_images = 5

for i in range(number_of_images):

    print(f"\nCapture {i + 1} of {number_of_images}")

    # Turn on illumination
    print("LED ring ON")
    time.sleep(3)

    # Simulate camera capture
    print("Capturing scratch assay image...")
    image = cv2.imread(str(sample_image))

    if image is not None:

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        filename = output_folder / f"scratch_{timestamp}.jpg"

        if cv2.imwrite(str(filename), image):
            print("Image saved:", filename)
        else:
            print("Error saving image")

    else:
        print("Error: Image not found")

    # Turn off illumination
    print("LED ring OFF")

    # Wait before next capture
    if i < number_of_images - 1:
        print("Waiting for next capture...")
        time.sleep(capture_interval)

print("\nCapture session completed.")
