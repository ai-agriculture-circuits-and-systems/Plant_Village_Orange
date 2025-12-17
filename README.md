# Plant Village Orange Dataset

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/) 
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](#changelog)

Orange leaf disease detection dataset focusing on Huanglongbing (Citrus greening) disease. Suitable for object detection and disease classification tasks.

## TL;DR
- Task: detection, classification
- Modality: RGB 
- Platform: ground/handheld
- Real/Synthetic: real
- Images: Oranges 11,014; Backgrounds 2,286
- Resolution: 256×256 pixels
- Annotations: per-image CSV and JSON (x, y, width, height)
- License: CC BY 4.0 (see License)
- Citation: see below

## Table of contents
- [Download](#download)
- [Dataset structure](#dataset-structure)
- [Sample images](#sample-images)
- [Annotation schema](#annotation-schema)
- [Stats and splits](#stats-and-splits)
- [Quick start](#quick-start)
- [Evaluation and baselines](#evaluation-and-baselines)
- [Datasheet (data card)](#datasheet-data-card)
- [Known issues and caveats](#known-issues-and-caveats)
- [License](#license)
- [Citation](#citation)
- [Changelog](#changelog)
- [Contact](#contact)

## Download
- Original dataset: Plant Village Orange dataset
- This repo hosts standardized structure and conversion scripts; place the downloaded folders under this directory.
- Local license file: see `LICENSE` (Creative Commons Attribution 4.0).

## Dataset structure
```
Plant_Village_Orange/
├── oranges/
│   ├── csv/                   # CSV per image
│   ├── json/                  # JSON per image
│   ├── images/                # JPG images
│   ├── labelmap.json
│   └── sets/                  # train.txt / val.txt / test.txt / all.txt
├── backgrounds/
│   ├── csv/                   # CSV per image
│   ├── json/                  # JSON per image
│   ├── images/                # JPG images
│   ├── labelmap.json
│   └── sets/                  # train.txt / val.txt / test.txt / all.txt
├── annotations/               # COCO JSON output (generated)
├── scripts/
│   ├── convert_to_coco.py     # conversion utility
│   ├── reorganize_dataset.py  # dataset reorganization script
│   └── fix_splits.py          # split file fixing utility
└── README.md
```
- Splits: `sets/train.txt`, `sets/val.txt`, `sets/test.txt` (and also `all.txt`) list image basenames (no extension). If missing, all images are used.

## Sample images

Below are example images for each category in this dataset. Paths are relative to this README location.

<table>
  <tr>
    <th>Category</th>
    <th>Sample</th>
  </tr>
  <tr>
    <td><strong>Orange (Huanglongbing)</strong></td>
    <td>
      <img src="oranges/images/image (1000).JPG" alt="Orange example" width="260"/>
      <div align="center"><code>oranges/images/image (1000).JPG</code></div>
    </td>
  </tr>
  <tr>
    <td><strong>Background</strong></td>
    <td>
      <img src="backgrounds/images/image (1031).jpg" alt="Background example" width="260"/>
      <div align="center"><code>backgrounds/images/image (1031).jpg</code></div>
    </td>
  </tr>
</table>

## Annotation schema
- CSV per-image schemas (stored under each category's `csv/` folder):
  - Format: columns include `x, y, width, height` (bounding box coordinates in pixels).
  - Example:
    ```csv
    #item,x,y,width,height,label
    0,20,7,233,245,1
    1,80,160,33,16,1
    ```
- JSON per-image format (stored under each category's `json/` folder):
  - Each JSON file contains image metadata and annotations in COCO-like format.
  - Includes original filename and Plant Village filename mappings.
- COCO-style (generated):
```json
{
  "info": {"year": 2025, "version": "1.0.0", "description": "Plant Village Orange <category> <split>", "url": ""},
  "images": [{"id": 1, "file_name": "oranges/images/image (1000).JPG", "width": 256, "height": 256}],
  "categories": [{"id": 1, "name": "orange", "supercategory": "plant"}],
  "annotations": [{"id": 10, "image_id": 1, "category_id": 1, "bbox": [x, y, w, h], "area": 1234, "iscrowd": 0}]
}
```

- Label maps: each category folder includes a `labelmap.json` for original IDs. In combined mode, categories are assigned as: `orange=1`, `background=2`.

## Stats and splits

### Image counts
- **Oranges**: 11,014 images (with Huanglongbing disease annotations)
- **Backgrounds**: 2,286 images (background/negative samples)

### Splits
- **Oranges**:
  - Train: 674 images
  - Validation: 173 images
  - Test: 1,166 images
  - Total: 11,014 images (includes augmented data)
- **Backgrounds**:
  - All images available (2,286 images)
  - Note: Background category may not have explicit train/val/test splits in the original dataset

Splits provided via `sets/*.txt`. You may define your own splits by editing those files.

## Quick start

Python (COCO):
```python
from pycocotools.coco import COCO
coco = COCO("annotations/oranges_instances_train.json")
img_ids = coco.getImgIds()
img = coco.loadImgs(img_ids[0])[0]
ann_ids = coco.getAnnIds(imgIds=img['id'])
anns = coco.loadAnns(ann_ids)
```

Convert CSV to COCO JSON:
```bash
python scripts/convert_to_coco.py --root . --out annotations --categories oranges backgrounds --splits train val test --combined
```

Dependencies:
```bash
python -m pip install pillow
```
Optional for the COCO API example:
```bash
python -m pip install pycocotools
```

## Evaluation and baselines
- Metric: mAP@[.50:.95] for detection tasks.
- Classification metrics: accuracy, precision, recall, F1-score for disease classification.

## Datasheet (data card)

### Motivation
This dataset was created to support research in citrus disease detection, specifically focusing on Huanglongbing (Citrus greening), one of the most devastating citrus diseases worldwide.

### Composition
- **Oranges category**: Images of orange leaves showing symptoms of Huanglongbing disease, with bounding box annotations for disease regions.
- **Backgrounds category**: Images without leaves or with non-diseased backgrounds, used as negative samples.

### Collection process
- Images were collected from field conditions and laboratory settings.
- Original images were processed and augmented to create multiple variants.
- Annotations were created to mark disease-affected regions in orange leaf images.

### Preprocessing
- Images were resized to 256×256 pixels.
- Data augmentation was applied (rotation, flipping, etc.) to increase dataset diversity.
- Original filenames were mapped to standardized naming conventions.

### Distribution
- Dataset is distributed in standardized format following the ACFR Multifruit 2016 structure guidelines.
- Original data structure is preserved in source directories for reference.

### Maintenance
- Dataset structure follows standardized format for easy integration with detection frameworks.
- Conversion scripts are provided for COCO format compatibility.

## Known issues and caveats
- **File naming**: Original images were renamed to standardized format (e.g., `image (1000).JPG`). Original filenames are preserved in JSON metadata.
- **Coordinate system**: Bounding box coordinates use top-left origin (x, y) with width and height.
- **Image format**: Orange category uses `.JPG` extension (uppercase), while backgrounds use `.jpg` (lowercase). Both are supported by the conversion scripts.
- **Augmentation**: The dataset includes both original and augmented images. The `without_augmentation` subset was used for standardization.
- **Split files**: Split files were generated based on original filenames and mapped to standardized names. Some images may not have explicit split assignments.

## License
This dataset is released under the Creative Commons Attribution 4.0 International License (CC BY 4.0). See `LICENSE` file for details.

Check the original dataset terms and cite appropriately.

## Citation
If you use this dataset, please cite:

```bibtex
@dataset{plant_village_orange,
  title={Plant Village Orange Dataset},
  author={Plant Village},
  year={2025},
  license={CC BY 4.0},
  url={}
}
```

## Changelog
- **V1.0.0** (2025-12-14): Initial standardized structure and COCO conversion utility
  - Reorganized dataset following ACFR Multifruit 2016 structure guidelines
  - Created standard directory structure with oranges/ and backgrounds/ categories
  - Generated CSV and JSON annotation files
  - Created COCO format conversion scripts
  - Fixed split file mappings

## Contact
- **Maintainers**: Dataset maintainers
- **Original authors**: Plant Village
- **Source**: Plant Village Orange dataset
