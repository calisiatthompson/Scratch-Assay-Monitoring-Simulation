from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from azure.core.exceptions import ResourceNotFoundError

from database import experiments, captures
from cloud_storage import container_client


app = FastAPI(
    title="Scratch Assay Monitoring API",
    description="API for remote scratch assay monitoring",
    version="1.0.0"
)

# Dashboard files
base_folder = Path(__file__).resolve().parent

static_folder = base_folder / "static"

app.mount(
    "/static",
    StaticFiles(directory=str(static_folder)),
    name="static"
)


@app.get("/dashboard")
def dashboard():

    return FileResponse(
        static_folder / "index.html"
    )

# ==========================================
# HOME ENDPOINT
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Scratch Assay Monitoring API",
        "status": "online"
    }


# ==========================================
# GET ALL EXPERIMENTS
# ==========================================

@app.get("/experiments")
def get_experiments():

    results = list(
        experiments.find(
            {},
            {"_id": 0}
        ).sort("start_time", -1)
    )

    return results


# ==========================================
# GET A SPECIFIC EXPERIMENT
# ==========================================

@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str):

    experiment = experiments.find_one(
        {"experiment_id": experiment_id},
        {"_id": 0}
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found"
        )

    return experiment


# ==========================================
# GET ALL CAPTURES
# ==========================================

@app.get("/experiments/{experiment_id}/captures")
def get_captures(experiment_id: str):

    get_experiment(experiment_id)

    results = list(
        captures.find(
            {"experiment_id": experiment_id},
            {"_id": 0}
        ).sort("time_hours", 1)
    )

    return results


# ==========================================
# GET LATEST CAPTURE
# ==========================================

@app.get("/experiments/{experiment_id}/latest")
def get_latest_capture(experiment_id: str):

    capture = captures.find_one(
        {"experiment_id": experiment_id},
        {"_id": 0},
        sort=[("time_hours", -1)]
    )

    if capture is None:
        raise HTTPException(
            status_code=404,
            detail="No captures found"
        )

    return capture


# ==========================================
# GET SCRATCH CLOSURE GRAPH
# ==========================================

@app.get("/experiments/{experiment_id}/graph")
def get_graph(experiment_id: str):

    get_experiment(experiment_id)

    blob_name = (
        f"{experiment_id}/results/"
        "scratch_closure_graph.png"
    )

    try:

        blob = container_client.get_blob_client(
            blob_name
        )

        image = blob.download_blob().readall()

        return Response(
            content=image,
            media_type="image/png"
        )

    except ResourceNotFoundError:

        raise HTTPException(
            status_code=404,
            detail="Graph not found"
        )


# ==========================================
# GET ORIGINAL OR PROCESSED IMAGE
# ==========================================

@app.get(
    "/experiments/{experiment_id}/captures/"
    "{hour}/image/{image_type}"
)
def get_image(
    experiment_id: str,
    hour: int,
    image_type: str
):

    capture = captures.find_one({
        "experiment_id": experiment_id,
        "time_hours": hour
    })

    if capture is None:
        raise HTTPException(
            status_code=404,
            detail="Capture not found"
        )

    if image_type == "original":

        blob_name = capture["original_image"]

    elif image_type == "processed":

        blob_name = capture["processed_image"]

    else:

        raise HTTPException(
            status_code=400,
            detail="Use original or processed"
        )

    try:

        blob = container_client.get_blob_client(
            blob_name
        )

        image = blob.download_blob().readall()

        return Response(
            content=image,
            media_type="image/png"
        )

    except ResourceNotFoundError:

        raise HTTPException(
            status_code=404,
            detail="Image not found in Azure"
        )
