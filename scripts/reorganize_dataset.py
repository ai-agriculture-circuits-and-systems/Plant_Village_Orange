#!/usr/bin/env python3
"""
重组 Plant Village Orange 数据集为标准结构
根据 acfr-multifruit-2016 数据集结构规范
"""

import os
import json
import shutil
from pathlib import Path
from collections import defaultdict

def read_json_file(json_path):
    """读取JSON标注文件"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def json_to_csv(json_data, csv_path):
    """将JSON标注转换为CSV格式"""
    annotations = json_data.get('annotations', [])
    if not annotations:
        # 创建空CSV文件
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("#item,x,y,width,height,label\n")
        return
    
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("#item,x,y,width,height,label\n")
        for idx, ann in enumerate(annotations):
            bbox = ann['bbox']  # [x, y, width, height]
            category_id = ann['category_id']
            # 将category_id映射到标准label (1 for object, 0 for background)
            label = 1 if category_id != 0 else 0
            f.write(f"{idx},{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},{label}\n")

def reorganize_category(source_dir, target_category_dir, category_name, image_ext='.JPG'):
    """重组单个类别的数据"""
    source_path = Path(source_dir)
    target_path = Path(target_category_dir)
    
    images_dir = target_path / 'images'
    json_dir = target_path / 'json'
    csv_dir = target_path / 'csv'
    
    images_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)
    
    # 处理 without_augmentation 目录
    without_aug_dir = source_path / 'without_augmentation'
    if without_aug_dir.exists():
        print(f"处理 {category_name} without_augmentation...")
        process_directory(without_aug_dir, images_dir, json_dir, csv_dir, image_ext)
    
    # 处理 with_augmentation 目录（可选，如果需要保留增强数据）
    # with_aug_dir = source_path / 'with_augmentation'
    # if with_aug_dir.exists():
    #     print(f"处理 {category_name} with_augmentation...")
    #     process_directory(with_aug_dir, images_dir, json_dir, csv_dir, image_ext)

def process_directory(source_dir, images_dir, json_dir, csv_dir, image_ext):
    """处理目录中的图像和标注文件"""
    source_path = Path(source_dir)
    
    # 查找所有图像文件
    image_files = list(source_path.glob(f"*{image_ext}"))
    image_files.extend(list(source_path.glob(f"*{image_ext.lower()}")))
    
    print(f"  找到 {len(image_files)} 个图像文件")
    
    for img_file in image_files:
        # 获取文件名（不含扩展名）
        stem = img_file.stem
        
        # 查找对应的JSON文件
        json_file = source_path / f"{stem}.json"
        if not json_file.exists():
            # 尝试不同的扩展名
            json_file = source_path / f"{img_file.name}.json"
        
        # 复制图像文件
        target_img = images_dir / img_file.name
        shutil.copy2(img_file, target_img)
        
        # 处理JSON文件
        if json_file.exists():
            # 复制JSON文件
            target_json = json_dir / f"{stem}.json"
            shutil.copy2(json_file, target_json)
            
            # 读取JSON并生成CSV
            try:
                json_data = read_json_file(json_file)
                csv_file = csv_dir / f"{stem}.csv"
                json_to_csv(json_data, csv_file)
            except Exception as e:
                print(f"  警告: 处理 {json_file} 时出错: {e}")
        else:
            # 如果没有JSON文件，创建空的CSV文件
            csv_file = csv_dir / f"{stem}.csv"
            with open(csv_file, 'w', encoding='utf-8') as f:
                f.write("#item,x,y,width,height,label\n")

def reorganize_splits(all_dir, category_dirs):
    """重组数据集划分文件"""
    all_path = Path(all_dir)
    
    for split_file in ['train.txt', 'val.txt', 'test.txt']:
        split_path = all_path / split_file
        if not split_path.exists():
            continue
        
        print(f"处理划分文件: {split_file}")
        
        # 读取划分文件
        with open(split_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        # 按类别分组
        category_lines = defaultdict(list)
        
        for line in lines:
            # 判断属于哪个类别
            # 根据文件名特征判断
            if 'CREC_HLB' in line or 'UF.Citrus_HLB' in line or 'image (' in line:
                # Orange类别
                # 提取文件名（不含扩展名）
                stem = Path(line).stem
                category_lines['oranges'].append(stem)
            else:
                # Background类别
                stem = Path(line).stem
                category_lines['backgrounds'].append(stem)
        
        # 为每个类别创建划分文件
        for category_name, category_dir in category_dirs.items():
            if category_name in category_lines:
                sets_dir = category_dir / 'sets'
                sets_dir.mkdir(parents=True, exist_ok=True)
                
                target_split = sets_dir / split_file
                with open(target_split, 'w', encoding='utf-8') as f:
                    for line in category_lines[category_name]:
                        f.write(f"{line}\n")
                
                print(f"  {category_name}: {len(category_lines[category_name])} 个图像")

def create_labelmap(category_dir, category_singular, category_plural):
    """创建labelmap.json文件"""
    labelmap = [
        {
            "object_id": 0,
            "label_id": 0,
            "keyboard_shortcut": "0",
            "object_name": "background"
        },
        {
            "object_id": 1,
            "label_id": 1,
            "keyboard_shortcut": "1",
            "object_name": category_singular
        }
    ]
    
    labelmap_path = Path(category_dir) / 'labelmap.json'
    with open(labelmap_path, 'w', encoding='utf-8') as f:
        json.dump(labelmap, f, indent=2, ensure_ascii=False)
    
    print(f"创建 labelmap.json: {labelmap_path}")

def main():
    root_dir = Path(__file__).parent.parent
    
    print("开始重组 Plant Village Orange 数据集...")
    print(f"根目录: {root_dir}")
    
    # 重组 Orange 类别
    source_orange = root_dir / "Orange___Haunglongbing_(Citrus_greening)"
    target_orange = root_dir / "oranges"
    if source_orange.exists():
        reorganize_category(source_orange, target_orange, "oranges", image_ext='.JPG')
        create_labelmap(target_orange, "orange", "oranges")
    
    # 重组 Background 类别
    source_bg = root_dir / "Background_without_leaves"
    target_bg = root_dir / "backgrounds"
    if source_bg.exists():
        reorganize_category(source_bg, target_bg, "backgrounds", image_ext='.jpg')
        create_labelmap(target_bg, "background", "backgrounds")
    
    # 重组划分文件
    all_dir = root_dir / "all"
    category_dirs = {
        'oranges': target_orange,
        'backgrounds': target_bg
    }
    if all_dir.exists():
        reorganize_splits(all_dir, category_dirs)
    
    # 创建 all.txt 文件
    for category_name, category_dir in category_dirs.items():
        if category_dir.exists():
            images_dir = category_dir / 'images'
            if images_dir.exists():
                image_files = list(images_dir.glob("*.JPG")) + list(images_dir.glob("*.jpg"))
                sets_dir = category_dir / 'sets'
                sets_dir.mkdir(parents=True, exist_ok=True)
                
                all_txt = sets_dir / 'all.txt'
                with open(all_txt, 'w', encoding='utf-8') as f:
                    for img_file in sorted(image_files):
                        f.write(f"{img_file.stem}\n")
                
                print(f"{category_name}: 创建 all.txt，包含 {len(image_files)} 个图像")
    
    print("\n数据集重组完成！")

if __name__ == '__main__':
    main()
