
import csv
import cv2
import numpy as np
import matplotlib

# Prevent graph windows from interrupting the simulation
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from pathlib import Path


# ==========================================
# SCRATCH DETECTION FUNCTION
# ==========================================

def detect_scratch(filename):

    # Load image
    image = cv2.imread(str(filename))

    if image is None:
        raise FileNotFoundError(filename)

    # Keep consistent image dimensions
    image = image[:446, :377]

    # Convert to grayscale
    gray = cv2.cvtColor(
        image, cv2.COLOR_BGR2GRAY
    ).astype(np.float32)

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

        left_threshold = (
            middle + left_cells
        ) / 2

        right_threshold = (
            middle + right_cells
        ) / 2

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
# SAVE PROCESSED IMAGE
# ==========================================

def save_processed_image(result, hour, folder):

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    # Add experiment time label
    cv2.putText(
        result,
        f"{hour} hours",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2
    )

    # Define output filename
    filename = (
        folder / f"detected_{hour}h_lines.png"
    )

    # Save processed image
    if not cv2.imwrite(str(filename), result):
        raise IOError(
            f"Could not save {filename}"
        )

    return filename


# ==========================================
# CALCULATE SCRATCH CLOSURE
# ==========================================

def calculate_closure(initial_area, current_area):

    if initial_area <= 0:
        raise ValueError(
            "Initial scratch area must be greater than zero"
        )

    closure = (
        (initial_area - current_area)
        / initial_area
    ) * 100

    return closure


# ==========================================
# SAVE CSV RESULTS
# ==========================================

def save_csv(records, folder):

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    csv_file = folder / "scratch_results.csv"

    with open(
        csv_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Time (hours)",
            "Capture Timestamp",
            "Scratch Area (px2)",
            "Average Width (px)",
            "Scratch Closure (%)"
        ])

        for record in records:

            writer.writerow([
                record["hour"],
                record["timestamp"],
                record["area"],
                round(record["width"], 2),
                round(record["closure"], 2)
            ])

    return csv_file


# ==========================================
# GENERATE SCRATCH CLOSURE GRAPH
# ==========================================

def generate_graph(records, folder):

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    # Extract measurements
    hours = [
        record["hour"] for record in records
    ]

    closures = [
        record["closure"] for record in records
    ]

    # Create graph
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
    plt.xlim(-1, 25)

    plt.grid(True, alpha=0.3)
    plt.margins(y=0.15)

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

    # Save graph
    graph_file = (
        folder / "scratch_closure_graph.png"
    )

    plt.savefig(
        graph_file,
        dpi=300,
        bbox_inches="tight"
    )

    # Close figure without displaying a window
    plt.close()

    return graph_file
