import os
import csv
from pathlib import Path
from ultralytics import YOLO
from PIL import Image
from tqdm import tqdm

# ---------------- CONFIG ----------------
IMAGE_ROOT = Path("data/raw/images")
OUTPUT_CSV = Path("data/processed/yolo_detections.csv")
MODEL_NAME = "yolov8n.pt"
CONF_THRESHOLD = 0.25

# YOLO class groups
PERSON_CLASS = "person"
PRODUCT_CLASSES = {
    "bottle", "cup", "wine glass", "vase",
    "handbag", "backpack", "box", "cell phone"
}

# ---------------------------------------

model = YOLO(MODEL_NAME)

OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

results_rows = []

def classify_image(detected_labels):
    has_person = PERSON_CLASS in detected_labels
    has_product = any(lbl in PRODUCT_CLASSES for lbl in detected_labels)

    if has_person and has_product:
        return "promotional"
    elif has_product and not has_person:
        return "product_display"
    elif has_person and not has_product:
        return "lifestyle"
    else:
        return "other"

image_files = list(IMAGE_ROOT.rglob("*.jpg"))

for image_path in tqdm(image_files, desc="Running YOLO detection"):
    try:
        image = Image.open(image_path)
    except Exception:
        continue

    message_id = image_path.stem
    channel_name = image_path.parent.name

    detections = model(image, conf=CONF_THRESHOLD, verbose=False)[0]

    detected_objects = []
    confidences = []

    for box in detections.boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        conf = float(box.conf[0])

        detected_objects.append(label)
        confidences.append(conf)

    image_category = classify_image(detected_objects)

    avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else None

    results_rows.append({
        "message_id": message_id,
        "channel_name": channel_name,
        "detected_objects": ",".join(set(detected_objects)),
        "image_category": image_category,
        "confidence_score": avg_confidence
    })

# Write CSV
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "message_id",
            "channel_name",
            "detected_objects",
            "image_category",
            "confidence_score"
        ]
    )
    writer.writeheader()
    writer.writerows(results_rows)

print(f"YOLO detection complete → {OUTPUT_CSV}")
