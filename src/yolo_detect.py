import os
import csv
import logging
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_image_category(detected_classes):
    """
    Categorizes images based on YOLO output:
    - promotional: person + any product (bottle/cup) [cite: 3000]
    - product_display: product class (bottle/cup/bowl), no person [cite: 3001]
    - lifestyle: person, no product [cite: 3002]
    - other: none of the above [cite: 3003]
    """
    has_person = 'person' in detected_classes
    has_product = any(item in detected_classes for item in ['bottle', 'cup', 'bowl', 'box', 'vase'])
    
    if has_person and has_product:
        return 'promotional' [cite: 3000]
    elif has_product and not has_person:
        return 'product_display' [cite: 3001]
    elif has_person and not has_product:
        return 'lifestyle' [cite: 3002]
    return 'other' [cite: 3003]

def run_detection():
    logging.info("Loading YOLOv8 nano model...")
    model = YOLO("yolov8n.pt") 
    
    image_base_dir = "data/raw/images"
    output_csv = "data/yolo_detections.csv"
    os.makedirs("data", exist_ok=True)
    
    csv_headers = ["message_id", "channel_name", "image_path", "detected_class", "confidence_score", "image_category"]
    
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        
        if not os.path.exists(image_base_dir):
            logging.warning("No image path exists.")
            return

        for channel_name in os.listdir(image_base_dir):
            channel_path = os.path.join(image_base_dir, channel_name)
            if not os.path.isdir(channel_path):
                continue
                
            for image_file in os.listdir(channel_path):
                if not image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue
                
                image_path = os.path.join(channel_path, image_file)
                message_id = os.path.splitext(image_file)[0]
                
                try:
                    results = model(image_path, verbose=False) [cite: 2995]
                    detected_classes = []
                    detections = []
                    
                    for r in results:
                        for box in r.boxes:
                            cls_name = model.names[int(box.cls[0])]
                            conf = float(box.conf[0])
                            detected_classes.append(cls_name)
                            detections.append((cls_name, conf))
                    
                    category = get_image_category(detected_classes) [cite: 2999]
                    
                    # If nothing was detected, write an 'other' row [cite: 3003]
                    if not detections:
                        writer.writerow([message_id, channel_name, image_path, "none", 0.0, "other"]) [cite: 3003]
                    else:
                        for cls_name, conf in detections:
                            writer.writerow([message_id, channel_name, image_path, cls_name, conf, category])
                            
                except Exception as e:
                    logging.error(f"Error processing {image_path}: {e}")
                    
    logging.info("YOLO inference CSV generated successfully!")

if __name__ == "__main__":
    run_detection()