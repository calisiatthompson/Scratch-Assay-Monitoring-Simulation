
const experimentSelect =
    document.getElementById("experimentSelect");

const timeSelect =
    document.getElementById("timeSelect");

const message =
    document.getElementById("message");

let captureRecords = [];
let currentExperiment = null;


// Retrieve data from FastAPI
async function getData(url) {

    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(
            `Request failed: ${response.status}`
        );
    }

    return response.json();
}


// Load available experiments
async function loadExperiments() {

    try {

        const experiments =
            await getData("/experiments");

        experimentSelect.innerHTML = "";

        if (experiments.length === 0) {
            message.textContent =
                "No experiments available.";
            return;
        }

        experiments.forEach(experiment => {

            const option =
                document.createElement("option");

            option.value =
                experiment.experiment_id;

            option.textContent =
                experiment.experiment_id;

            experimentSelect.appendChild(option);
        });

        await loadExperiment(
            experimentSelect.value
        );

    } catch (error) {

        message.textContent =
            "Unable to load experiments: " +
            error.message;
    }
}


// Load selected experiment
async function loadExperiment(experimentId) {

    try {

        message.textContent = "";

        currentExperiment = experimentId;

        const experiment = await getData(
            `/experiments/${experimentId}`
        );

        captureRecords = await getData(
            `/experiments/${experimentId}/captures`
        );

        document.getElementById(
            "experimentStatus"
        ).textContent = experiment.status;

        document.getElementById(
            "captureCount"
        ).textContent =
            `${experiment.completed_captures} / ` +
            `${experiment.expected_captures}`;

        // Populate capture times
        timeSelect.innerHTML = "";

        captureRecords.forEach(capture => {

            const option =
                document.createElement("option");

            option.value = capture.time_hours;

            option.textContent =
                `${capture.time_hours} hours`;

            timeSelect.appendChild(option);
        });

        // Update results table
        updateTable();

        if (captureRecords.length > 0) {

            // Automatically select latest capture
            const latest = captureRecords[
                captureRecords.length - 1
            ];

            timeSelect.value = latest.time_hours;

            displayCapture(latest);

            // Load graph from Azure through FastAPI
            document.getElementById(
                "closureGraph"
            ).src =
                `/experiments/${experimentId}/graph` +
                `?t=${Date.now()}`;

        } else {

            clearCaptureDisplay();

            message.textContent =
                "Waiting for the first capture.";
        }

    } catch (error) {

        message.textContent =
            "Unable to load experiment: " +
            error.message;
    }
}


// Display selected capture
function displayCapture(capture) {

    document.getElementById(
        "closure"
    ).textContent =
        capture.scratch_closure_percent
            .toFixed(2) + "%";

    document.getElementById(
        "width"
    ).textContent =
        capture.average_width_px
            .toFixed(2) + " px";

    document.getElementById(
        "area"
    ).textContent =
        capture.scratch_area_px2
            .toLocaleString() + " px²";

    const imagePath =
        `/experiments/${currentExperiment}` +
        `/captures/${capture.time_hours}/image`;

    document.getElementById(
        "originalImage"
    ).src = `${imagePath}/original`;

    document.getElementById(
        "processedImage"
    ).src = `${imagePath}/processed`;
}


// Clear previous capture when none exists
function clearCaptureDisplay() {

    document.getElementById(
        "closure"
    ).textContent = "--%";

    document.getElementById(
        "width"
    ).textContent = "-- px";

    document.getElementById(
        "area"
    ).textContent = "-- px²";

    document.getElementById(
        "originalImage"
    ).removeAttribute("src");

    document.getElementById(
        "processedImage"
    ).removeAttribute("src");

    document.getElementById(
        "closureGraph"
    ).removeAttribute("src");
}


// Generate results table
function updateTable() {

    const table =
        document.getElementById("resultsTable");

    table.innerHTML = "";

    captureRecords.forEach(capture => {

        const row =
            document.createElement("tr");

        const values = [
            capture.time_hours,
            capture.scratch_area_px2,
            capture.average_width_px.toFixed(2),
            capture.scratch_closure_percent.toFixed(2)
        ];

        values.forEach(value => {

            const cell =
                document.createElement("td");

            cell.textContent = value;

            row.appendChild(cell);
        });

        table.appendChild(row);
    });
}


// Change experiment
experimentSelect.addEventListener(
    "change",
    () => loadExperiment(experimentSelect.value)
);


// Change capture time
timeSelect.addEventListener(
    "change",
    () => {

        const capture = captureRecords.find(
            record =>
                record.time_hours ===
                Number(timeSelect.value)
        );

        if (capture) {
            displayCapture(capture);
        }
    }
);



// Initialize dashboard
loadExperiments();

// Automatically refresh experiment data
let refreshing = false;

setInterval(async () => {

    if (!currentExperiment || refreshing) {
        return;
    }

    refreshing = true;

    try {

        const experimentId = currentExperiment;

        const experiment = await getData(
            `/experiments/${experimentId}`
        );

        const latestRecords = await getData(
            `/experiments/${experimentId}/captures`
        );

        // Ignore results if the selected experiment changed
        if (currentExperiment !== experimentId) {
            return;
        }

        // Update experiment status
        document.getElementById(
            "experimentStatus"
        ).textContent = experiment.status;

        // Update capture count
        document.getElementById(
            "captureCount"
        ).textContent =
            `${experiment.completed_captures} / ` +
            `${experiment.expected_captures}`;

        // Check if a new image has arrived
        if (latestRecords.length > captureRecords.length) {

            captureRecords = latestRecords;

            // Update available time points
            timeSelect.innerHTML = "";

            captureRecords.forEach(capture => {

                const option =
                    document.createElement("option");

                option.value = capture.time_hours;

                option.textContent =
                    `${capture.time_hours} hours`;

                timeSelect.appendChild(option);
            });

            // Display latest capture
            const latest = captureRecords[
                captureRecords.length - 1
            ];

            timeSelect.value = latest.time_hours;

            displayCapture(latest);

            // Update measurements table
            updateTable();

            // Refresh graph
            document.getElementById(
                "closureGraph"
            ).src =
                `/experiments/${experimentId}/graph` +
                `?t=${Date.now()}`;

            message.textContent = "";

            console.log("New capture received");
        }

    } catch (error) {

        console.error("Refresh failed:", error);

    } finally {

        refreshing = false;
    }

}, 5000);

