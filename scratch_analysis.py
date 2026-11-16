
import csv
import matplotlib.pyplot as plt
import cv2
import numpy as np
from pathlib import Path

# Define project directory
base_folder = Path(__file__).resolve().parent

# Create output folders
sample_folder = base_folder / "sample_images"
processed_folder = base_folder / "processed_images"
results_folder = base_folder / "results"

processed_folder.mkdir(exist_ok=True)
results_folder.mkdir(exist_ok=True)


# ==========================================
# SCRATCH DETECTION FUNCTION
# ==========================================

def detect_scratch(filename):

    # Load image
    image = cv2.imread(str(filename))

    if image is None:
        raise FileNotFoundError(filename)

    # Keep the same dimensions for all images
    image = image[:446, :377]

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = gray.astype(np.float32)

    # Detect differences in cell texture
    blur = cv2.GaussianBlur(gray, (0, 0), 2)
    texture = np.abs(gray - blur)

    texture = cv2.GaussianBlur(
        texture,
        (0, 0),
        sigmaX=6,
        sigmaY=18
    )

    height, width = gray.shape
    center = width // 2

    scratch_mask = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    left_points = []
    right_points = []

    # Detect scratch boundaries row by row
    for y in range(50, height - 30):

        row = texture[y]

        middle = np.median(
            row[center-15:center+15]
        )

        left_cells = np.median(
            row[20:80]
        )

        right_cells = np.median(
            row[width-80:width-20]
        )

        left_threshold = (middle + left_cells) / 2
        right_threshold = (middle + right_cells) / 2

        # Find left boundary
        left = next(
            (
                x for x in range(center, 9, -1)
                if row[x] > left_threshold
            ),
            10
        )

        # Find right boundary
        right = next(
            (
                x for x in range(center, width-10)
                if row[x] > right_threshold
            ),
            width - 11
        )

        if right > left + 1:

            scratch_mask[y, left+1:right] = 255

            left_points.append(left + 1)
            right_points.append(right - 1)

    # Calculate scratch area
    area = cv2.countNonZero(scratch_mask)

    if area == 0 or not left_points:
        raise ValueError(
            f"No scratch detected in {filename}"
        )

    # Calculate average boundary positions
    left_x = int(round(np.mean(left_points)))
    right_x = int(round(np.mean(right_points)))

    # Calculate average scratch width
    scratch_width = float(
        np.mean(
            np.array(right_points)
            - np.array(left_points) + 1
        )
    )

    # Highlight detected scratch in green
    overlay = image.copy()
    overlay[scratch_mask == 255] = (0, 255, 0)

    result = cv2.addWeighted(
        image,
        0.75,
        overlay,
        0.25,
        0
    )

    # Draw straight yellow boundary lines
    cv2.line(
        result,
        (left_x, 0),
        (left_x, height - 1),
        (0, 255, 255),
        2
    )

    cv2.line(
        result,
        (right_x, 0),
        (right_x, height - 1),
        (0, 255, 255),
        2
    )

    # Draw double-headed measurement arrow
    middle_y = height // 2

    cv2.arrowedLine(
        result,
        (left_x, middle_y),
        (right_x, middle_y),
        (255, 255, 255),
        2,
        tipLength=0.08
    )

    cv2.arrowedLine(
        result,
        (right_x, middle_y),
        (left_x, middle_y),
        (255, 255, 255),
        2,
        tipLength=0.08
    )

    # Display scratch width
    label = f"{scratch_width:.1f} px"

    text_size = cv2.getTextSize(
        label,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        1
    )[0]

    text_x = (
        left_x + right_x - text_size[0]
    ) // 2

    cv2.putText(
        result,
        label,
        (max(0, text_x), middle_y - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    return area, scratch_width, result


# ==========================================
# ANALYSE SCRATCH ASSAY IMAGES
# ==========================================

hours = [0, 12, 24]

areas = []
widths = []

for hour in hours:

    filename = sample_folder / f"scratch_{hour}h.png"

    area, scratch_width, result = detect_scratch(
        filename
    )

    areas.append(area)
    widths.append(scratch_width)

    # Add time label
    cv2.putText(
        result,
        f"{hour} hours",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2
    )

    # Save processed image
    output_image = (
        processed_folder / f"detected_{hour}h_lines.png"
    )

    if not cv2.imwrite(str(output_image), result):
        raise IOError(
            f"Could not save {output_image}"
        )

    print(f"\n{hour} HOURS")
    print(f"Scratch area: {area} px²")
    print(f"Average width: {scratch_width:.2f} px")
    print(f"Processed image saved: {output_image.name}")


# ==========================================
# CALCULATE SCRATCH CLOSURE
# ==========================================

initial_area = areas[0]

closures = [
    ((initial_area - area) / initial_area) * 100
    for area in areas
]

print("\nSCRATCH CLOSURE RESULTS")

for hour, area, width, closure in zip(
    hours, areas, widths, closures
):

    print(f"\n{hour} hours:")
    print(f"  Area: {area} px²")
    print(f"  Width: {width:.2f} px")
    print(f"  Scratch closure: {closure:.2f}%")


# ==========================================
# SAVE RESULTS TO CSV
# ==========================================

csv_file = results_folder / "scratch_results.csv"

with open(
    csv_file,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "Time (hours)",
        "Scratch Area (px2)",
        "Average Width (px)",
        "Scratch Closure (%)"
    ])

    for hour, area, width, closure in zip(
        hours, areas, widths, closures
    ):

        writer.writerow([
            hour,
            area,
            round(width, 2),
            round(closure, 2)
        ])

print(f"\nResults saved to: {csv_file}")


# ==========================================
# GENERATE SCRATCH CLOSURE GRAPH
# ==========================================

plt.figure(figsize=(8, 5))

plt.plot(
    hours,
    closures,
    marker="o",
    color="green",
    linewidth=2
)

plt.title("Scratch Closure Over Time")
plt.xlabel("Time (hours)")
plt.ylabel("Scratch Closure (%)")

plt.xticks(hours)
plt.grid(True, alpha=0.3)

# Add space for graph labels
plt.margins(x=0.08, y=0.15)

# Label each data point
for hour, closure in zip(hours, closures):

    plt.annotate(
        f"{closure:.1f}%",
        (hour, closure),
        textcoords="offset points",
        xytext=(0, 10),
        ha="center"
    )

plt.tight_layout()

# Save graph in results folder
graph_file = (
    results_folder / "scratch_closure_graph.png"
)

plt.savefig(
    graph_file,
    dpi=300,
    bbox_inches="tight"
)

print(f"Graph saved to: {graph_file}")

print("\nScratch assay analysis completed successfully.")

# Display graph
plt.show()
