#!/usr/bin/env python3
"""
修复划分文件，将原始文件名映射到实际图像文件名
"""

import json
from pathlib import Path
from collections import defaultdict

def build_filename_mapping(json_dir):
    """从JSON文件中构建原始文件名到实际文件名的映射"""
    mapping = {}
    json_path = Path(json_dir)
    
    for json_file in json_path.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'images' in data and len(data['images']) > 0:
                    img_info = data['images'][0]
                    # 获取原始文件名（不含扩展名）
                    original = img_info.get('pvc_filename', '')
                    if not original:
                        original = img_info.get('original_filename', '')
                    if original:
                        original_stem = Path(original).stem
                        actual_stem = json_file.stem
                        # 存储多个可能的映射键
                        mapping[original_stem] = actual_stem
                        mapping[original] = actual_stem  # 包含扩展名
                        # 也存储小写版本
                        mapping[original_stem.lower()] = actual_stem
                        mapping[original.lower()] = actual_stem
        except Exception as e:
            print(f"Warning: Failed to process {json_file}: {e}")
    
    return mapping

def fix_splits(category_dir, all_dir):
    """修复划分文件"""
    category_path = Path(category_dir)
    all_path = Path(all_dir)
    
    # 构建文件名映射
    json_dir = category_path / 'json'
    mapping = build_filename_mapping(json_dir)
    print(f"构建了 {len(mapping)} 个文件名映射")
    
    # 反向映射：从实际文件名到原始文件名
    reverse_mapping = {v: k for k, v in mapping.items()}
    
    # 处理每个划分文件
    for split_file in ['train.txt', 'val.txt', 'test.txt']:
        split_path = all_path / split_file
        if not split_path.exists():
            continue
        
        print(f"\n处理 {split_file}...")
        
        # 读取原始划分文件
        with open(split_path, 'r', encoding='utf-8') as f:
            original_lines = [line.strip() for line in f if line.strip()]
        
        # 映射到实际文件名
        mapped_lines = []
        unmapped = []
        for line in original_lines:
            # 移除扩展名（如果存在）
            line_stem = Path(line).stem
            line_lower = line.lower()
            line_stem_lower = line_stem.lower()
            
            # 尝试多种匹配方式
            found = False
            for key in [line, line_stem, line_lower, line_stem_lower]:
                if key in mapping:
                    mapped_lines.append(mapping[key])
                    found = True
                    break
            
            if not found:
                # 尝试部分匹配（处理可能的变体）
                for orig, actual in mapping.items():
                    orig_stem = Path(orig).stem if '.' in orig else orig
                    if orig_stem == line_stem or orig_stem == line_stem_lower:
                        mapped_lines.append(actual)
                        found = True
                        break
            
            if not found:
                unmapped.append(line)
        
        if unmapped:
            print(f"  警告: {len(unmapped)} 个文件名未找到映射（前10个）")
            for line in unmapped[:10]:
                print(f"    {line}")
        
        # 写入新的划分文件
        sets_dir = category_path / 'sets'
        sets_dir.mkdir(parents=True, exist_ok=True)
        target_split = sets_dir / split_file
        
        with open(target_split, 'w', encoding='utf-8') as f:
            for line in sorted(set(mapped_lines)):  # 去重并排序
                f.write(f"{line}\n")
        
        print(f"  写入 {len(set(mapped_lines))} 个图像到 {target_split}")

def main():
    root_dir = Path(__file__).parent.parent
    
    # 修复 oranges 类别
    oranges_dir = root_dir / "oranges"
    all_dir = root_dir / "all"
    if oranges_dir.exists() and all_dir.exists():
        print("修复 oranges 类别的划分文件...")
        fix_splits(oranges_dir, all_dir)
    
    # backgrounds 类别可能不需要修复（如果划分文件已经是正确的）
    # 但我们可以检查一下
    backgrounds_dir = root_dir / "backgrounds"
    if backgrounds_dir.exists():
        print("\n检查 backgrounds 类别的划分文件...")
        sets_dir = backgrounds_dir / 'sets'
        images_dir = backgrounds_dir / 'images'
        
        # 如果没有划分文件，从 all.txt 创建
        if not (sets_dir / 'train.txt').exists():
            # 创建简单的划分（如果需要）
            pass

if __name__ == '__main__':
    main()
