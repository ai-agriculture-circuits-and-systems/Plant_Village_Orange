#!/usr/bin/env python3
"""Convert Plant Village Orange annotations to COCO JSON.

This script converts per-image CSV annotations in the Plant Village Orange
dataset into COCO-style JSON files, per category and/or combined across categories.

Usage examples:
    python scripts/convert_to_coco.py --root . --out annotations --categories oranges \
        --splits train val test

    python scripts/convert_to_coco.py --root . --out annotations --categories oranges backgrounds \
        --splits train val --combined
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image


@dataclass(frozen=True)
class CsvBox:
    """Normalized representation of a single annotation box.

    Always stored as COCO bbox [x, y, width, height] in pixel units.
    """

    x: float
    y: float
    width: float
    height: float


def _lower_keys(mapping: Dict[str, str]) -> Dict[str, str]:
    """Return a case-insensitive mapping by lowering keys."""
    return {k.lower(): v for k, v in mapping.items()}


def _read_split_list(split_file: Path) -> List[str]:
    """Read image base names (without extension) from a split file."""
    if not split_file.exists():
        return []
    lines = [line.strip() for line in split_file.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line]


def _image_size(image_path: Path) -> Tuple[int, int]:
    """Return (width, height) for an image path using PIL."""
    with Image.open(image_path) as img:
        return img.width, img.height


def _parse_csv_boxes(csv_path: Path) -> List[CsvBox]:
    """Parse a single per-image CSV file and return COCO-style bboxes.

    The parser is resilient to header variants by using case-insensitive
    lookups. Supported schemas:
      - Rectangle: x, y, width, height
    """
    if not csv_path.exists():
        return []

    boxes: List[CsvBox] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return boxes
        header = _lower_keys({k: k for k in reader.fieldnames})
        
        def get(row: Dict[str, str], *keys: str) -> Optional[float]:
            for key in keys:
                if key in row and row[key] not in (None, ""):
                    try:
                        return float(row[key])
                    except ValueError:
                        continue
            return None

        for raw_row in reader:
            row = {k.lower(): v for k, v in raw_row.items()}
            x = get(row, "x", "xc", "x_center")
            y = get(row, "y", "yc", "y_center")
            w = get(row, "w", "width", "dx")
            h = get(row, "h", "height", "dy")

            if x is None or y is None:
                continue
            if w is not None and h is not None:
                boxes.append(CsvBox(x=x, y=y, width=w, height=h))
            else:
                continue

    return boxes


def _collect_annotations_for_split(
    category_root: Path,
    split: str,
    category_name: str,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]:
    """Collect COCO dictionaries for images, annotations, and categories."""
    images_dir = category_root / "images"
    annotations_dir = category_root / "csv"
    sets_dir = category_root / "sets"

    split_file = sets_dir / f"{split}.txt"
    image_stems = set(_read_split_list(split_file))
    if not image_stems:
        # If no split list is provided, fall back to all images
        image_stems = {p.stem for p in images_dir.glob("*.jpg")}
        image_stems.update({p.stem for p in images_dir.glob("*.JPG")})
        image_stems.update({p.stem for p in images_dir.glob("*.png")})

    images: List[Dict[str, object]] = []
    anns: List[Dict[str, object]] = []
    
    # Get category name (singular form)
    category_singular = category_name[:-1] if category_name.endswith("s") else category_name
    categories: List[Dict[str, object]] = [
        {"id": 1, "name": category_singular, "supercategory": "plant"}
    ]

    image_id_counter = 1
    ann_id_counter = 1
    for stem in sorted(image_stems):
        # Try different image extensions
        img_path = images_dir / f"{stem}.jpg"
        if not img_path.exists():
            img_path = images_dir / f"{stem}.JPG"
        if not img_path.exists():
            img_path = images_dir / f"{stem}.png"
        if not img_path.exists():
            continue
            
        width, height = _image_size(img_path)
        images.append(
            {
                "id": image_id_counter,
                "file_name": str(img_path.relative_to(category_root.parent)),
                "width": width,
                "height": height,
            }
        )

        csv_path = annotations_dir / f"{stem}.csv"
        for box in _parse_csv_boxes(csv_path):
            anns.append(
                {
                    "id": ann_id_counter,
                    "image_id": image_id_counter,
                    "category_id": 1,
                    "bbox": [box.x, box.y, box.width, box.height],
                    "area": box.width * box.height,
                    "iscrowd": 0,
                }
            )
            ann_id_counter += 1

        image_id_counter += 1

    return images, anns, categories


def _merge_coco_splits(
    per_category: List[Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]],
    category_names: Sequence[str],
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]:
    """Merge multiple single-category COCO lists into a multi-category dataset."""
    images: List[Dict[str, object]] = []
    anns: List[Dict[str, object]] = []
    categories: List[Dict[str, object]] = []

    # Map each category to category id
    category_to_cat: Dict[str, int] = {}
    for idx, category in enumerate(category_names, start=1):
        category_singular = category[:-1] if category.endswith("s") else category
        categories.append(
            {"id": idx, "name": category_singular, "supercategory": "plant"}
        )
        category_to_cat[category] = idx

    # Remap ids to keep uniqueness across categories
    next_image_id = 1
    next_ann_id = 1
    for (img_list, ann_list, _cats), category in zip(per_category, category_names):
        # Create mapping from old image id to new merged id
        id_map: Dict[int, int] = {}
        for img in img_list:
            old_id = int(img["id"])
            new_img = dict(img)
            new_img["id"] = next_image_id
            images.append(new_img)
            id_map[old_id] = next_image_id
            next_image_id += 1

        for ann in ann_list:
            new_ann = dict(ann)
            new_ann["id"] = next_ann_id
            new_ann["image_id"] = id_map[int(ann["image_id"])]
            new_ann["category_id"] = category_to_cat[category]
            anns.append(new_ann)
            next_ann_id += 1

    return images, anns, categories


def _build_coco_dict(
    images: List[Dict[str, object]],
    anns: List[Dict[str, object]],
    categories: List[Dict[str, object]],
    description: str,
) -> Dict[str, object]:
    """Build a complete COCO dict from components."""
    return {
        "info": {
            "year": 2025,
            "version": "1.0.0",
            "description": description,
            "url": "",
        },
        "images": images,
        "annotations": anns,
        "categories": categories,
        "licenses": [],
    }


def convert(
    root: Path,
    out_dir: Path,
    categories: Sequence[str],
    splits: Sequence[str],
    combined: bool,
) -> None:
    """Convert selected categories and splits to COCO JSON files."""
    out_dir.mkdir(parents=True, exist_ok=True)

    for split in splits:
        # Per-category conversion
        per_category_results: List[Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]] = []
        for category in categories:
            category_root = root / category
            if not category_root.exists():
                print(f"Warning: Category directory {category_root} does not exist, skipping.")
                continue
            images, anns, categories_list = _collect_annotations_for_split(category_root, split, category)
            desc = f"Plant Village Orange {category} {split} split"
            coco = _build_coco_dict(images, anns, categories_list, desc)
            out_path = out_dir / f"{category}_instances_{split}.json"
            out_path.write_text(json.dumps(coco, indent=2), encoding="utf-8")
            print(f"Generated {out_path}: {len(images)} images, {len(anns)} annotations")
            per_category_results.append((images, anns, categories_list))

        if combined and len(per_category_results) > 1:
            images, anns, categories_list = _merge_coco_splits(per_category_results, categories)
            desc = f"Plant Village Orange combined {split} split ({', '.join(categories)})"
            coco = _build_coco_dict(images, anns, categories_list, desc)
            out_path = out_dir / f"combined_instances_{split}.json"
            out_path.write_text(json.dumps(coco, indent=2), encoding="utf-8")
            print(f"Generated {out_path}: {len(images)} images, {len(anns)} annotations")


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Dataset root containing category subfolders (default: dataset root)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "annotations",
        help="Output directory for COCO JSON files (default: <root>/annotations)",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        type=str,
        default=["oranges", "backgrounds"],
        help="Categories to include (default: oranges backgrounds)",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        type=str,
        default=["train", "val", "test"],
        help="Dataset splits to generate (default: train val test)",
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        help="Also produce a combined multi-class JSON per split",
    )

    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point for the converter CLI."""
    args = _parse_args(argv)
    convert(
        root=Path(args.root),
        out_dir=Path(args.out),
        categories=args.categories,
        splits=args.splits,
        combined=bool(args.combined),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
