from database import (
    create_experiment,
    save_capture,
    complete_experiment
)
import cv2
import time
from datetime import datetime
from pathlib import Path

from scratch_analysis import (
    detect_scratch,
    save_processed_image,
    calculate_closure,
    save_csv,
    generate_graph
)

from cloud_storage import upload_file


# ==========================================
# PROJECT SETTINGS
# ==========================================

base_folder = Path(__file__).resolve().parent

sample_folder = base_folder / "sample_images"

# Create unique experiment ID
experiment_id = datetime.now().strftime(
    "experiment_%Y%m%d_%H%M%S_%f"
)

# Create experiment folders
captured_folder = (
    base_folder / "captured_images" / experiment_id
)

processed_folder = (
    base_folder / "processed_images" / experiment_id
)

results_folder = (
    base_folder / "results" / experiment_id
)

captured_folder.mkdir(
    parents=True, exist_ok=True
)

processed_folder.mkdir(
    parents=True, exist_ok=True
)

results_folder.mkdir(
    parents=True, exist_ok=True
)

# Simulated experiment time points
hours = [0, 12, 24]

# Simulation delays
capture_interval = 10
illumination_delay = 3

# Store measurements
records = []

initial_area = None


# ==========================================
# SIMULATED ILLUMINATION
# ==========================================

def light_on():
    print("LED ring ON")


def light_off():
    print("LED ring OFF")


# ==========================================
# SIMULATED CAMERA CAPTURE
# ==========================================

def capture_image(hour):

    source = (
        sample_folder / f"scratch_{hour}h.png"
    )

    image = cv2.imread(str(source))

    if image is None:
        raise FileNotFoundError(
            f"Sample image not found: {source}"
        )

    capture_time = datetime.now()

    timestamp = capture_time.strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        captured_folder
        / f"scratch_{hour}h_{timestamp}.png"
    )

    if not cv2.imwrite(str(filename), image):
        raise IOError(
            f"Could not save image: {filename}"
        )

    return filename, capture_time


# ==========================================
# UPLOAD EXPERIMENT FILES
# ==========================================

def upload_experiment_files(
    captured_file,
    processed_file,
    csv_file,
    graph_file
):

    print("\nUploading files to Azure...")

    files_to_upload = [
        (
            captured_file,
            f"{experiment_id}/captured_images/"
            f"{captured_file.name}"
        ),
        (
            processed_file,
            f"{experiment_id}/processed_images/"
            f"{processed_file.name}"
        ),
        (
            csv_file,
            f"{experiment_id}/results/"
            f"{csv_file.name}"
        ),
        (
            graph_file,
            f"{experiment_id}/results/"
            f"{graph_file.name}"
        )
    ]

    failures = 0

    for local_file, blob_name in files_to_upload:

        try:

            upload_file(local_file, blob_name)

        except Exception as error:

            failures += 1

            print(
                f"Upload failed: {local_file.name}"
            )

            print(error)

    if failures == 0:

        print("Azure upload completed successfully.")

    else:

        print(f"{failures} upload(s) failed.")
        print("All files remain saved locally.")


# ==========================================
# START EXPERIMENT
# ==========================================

print("\nSCRATCH ASSAY MONITORING SYSTEM")
print("Experiment ID:", experiment_id)
print("Simulation mode")
print("--------------------------------")

# Register experiment in MongoDB
create_experiment(experiment_id)

for index, hour in enumerate(hours):

    print(f"\nTIME POINT: {hour} HOURS")

    # Turn on illumination
    light_on()

    try:

        time.sleep(illumination_delay)

        # Simulate camera capture
        print("Capturing image...")

        captured_file, capture_time = capture_image(
            hour
        )

        print(
            "Original image saved:",
            captured_file.name
        )

    finally:

        # Turn off illumination
        light_off()

    # Analyse captured image
    print("Analysing scratch...")

    area, width, result = detect_scratch(
        captured_file
    )

    # Establish initial scratch area
    if initial_area is None:
        initial_area = area

    # Calculate scratch closure
    closure = calculate_closure(
        initial_area,
        area
    )

    # Save processed image
    processed_file = save_processed_image(
        result,
        hour,
        processed_folder
    )

    # Store measurements
    record = {
        "hour": hour,
        "timestamp": capture_time.isoformat(
            timespec="seconds"
        ),
        "area": area,
        "width": width,
        "closure": closure
    }

    records.append(record)

    # Update CSV file
    csv_file = save_csv(
        records,
        results_folder
    )

    # Update graph
    graph_file = generate_graph(
        records,
        results_folder
    )

    # Display results
    print(f"Scratch area: {area} px2")
    print(f"Average width: {width:.2f} px")
    print(f"Scratch closure: {closure:.2f}%")

    print("Processed image saved")
    print("CSV results updated")
    print("Graph updated")

    # Upload all files to Azure
    upload_experiment_files(
        captured_file,
        processed_file,
        csv_file,
        graph_file
    )


    # Save capture measurements to MongoDB
    original_blob = (
        f"{experiment_id}/captured_images/"
        f"{captured_file.name}"
    )

    processed_blob = (
        f"{experiment_id}/processed_images/"
        f"{processed_file.name}"
    )

    save_capture(
        experiment_id,
        record,
        original_blob,
        processed_blob
    )


    # Wait before next capture
    if index < len(hours) - 1:

        print("\nWaiting for next capture...")

        time.sleep(capture_interval)


# ==========================================
# EXPERIMENT COMPLETE
# ==========================================

# Update experiment status in MongoDB
complete_experiment(experiment_id)

print("\n================================")
print("EXPERIMENT COMPLETED")
print("================================")

print("Total captures:", len(records))

print("\nFinal scratch closure results:")

for record in records:

    print(
        f"{record['hour']} hours: "
        f"{record['closure']:.2f}%"
    )

print("\nCaptured images:")
print(captured_folder)

print("\nProcessed images:")
print(processed_folder)

print("\nCSV results:")
print(csv_file)

print("\nScratch closure graph:")
print(graph_file)

print("\nAzure experiment folder:")
print(experiment_id)
