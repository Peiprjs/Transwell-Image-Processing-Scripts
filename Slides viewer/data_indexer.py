import os
import re
from pathlib import Path
import pandas as pd


def parse_slides_file(slides_file_path):
    slides_data = {}
    
    with open(slides_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            


            match = re.match(r'(\d+[LRC])\s*-\s*(T\d+)\s+([A-Z]/[A-Z])\s+(\d+)%', line)
            if match:
                slide_id = match.group(1)
                time_point = match.group(2)
                slide_type = match.group(3)
                concentration = match.group(4) + '%'
                
                slides_data[slide_id] = {
                    'name': line,
                    'time_point': time_point,
                    'slide_type': slide_type,
                    'concentration': concentration
                }
    
    return slides_data


def extract_condition_from_path(image_path):
    path_parts = image_path.split(os.sep)
    


    for i, part in enumerate(path_parts):
        if part in ['Pre', 'Wash4', 'Wash8', 'DAPI', 'AB', 'Post']:
            return part
    
    return None


def extract_slide_position_from_path(image_path):
    path_parts = image_path.split(os.sep)
    

    for i, part in enumerate(path_parts):
        if part in ['L', 'C', 'R']:

            if i + 1 < len(path_parts) and path_parts[i + 1] in ['Pre', 'Wash4', 'Wash8', 'DAPI', 'AB', 'Post']:
                return part
    
    return None


def extract_batch_number_from_path(image_path):
    path_parts = image_path.split(os.sep)
    

    for part in path_parts:
        if part.isdigit() and part in ['1', '2', '3', '4', '5', '6']:
            return part
    
    return None


def index_images(batch_dir, slides_data):
    images = []
    

    for root, dirs, files in os.walk(batch_dir):
        if 'Merged_Composite.png' in files:
            image_path = os.path.join(root, 'Merged_Composite.png')
            

            batch_num = extract_batch_number_from_path(image_path)
            position = extract_slide_position_from_path(image_path)
            condition = extract_condition_from_path(image_path)
            
            if batch_num and position and condition:

                slide_id = batch_num + position
                

                if slide_id in slides_data:
                    slide_info = slides_data[slide_id]
                    images.append({
                        'slide_id': slide_id,
                        'slide_name': slide_info['name'],
                        'time_point': slide_info['time_point'],
                        'slide_type': slide_info['slide_type'],
                        'concentration': slide_info['concentration'],
                        'condition': condition,
                        'image_path': os.path.abspath(image_path)
                    })
    
    return images


def main(batch_dir=None):
    if batch_dir is None:
        batch_dir = os.path.dirname(os.path.abspath(__file__))
    
    batch_dir = os.path.abspath(batch_dir)
    

    slides_file = os.path.join(batch_dir, 'Slides')
    if not os.path.exists(slides_file):
        raise FileNotFoundError(f"Slides file not found at {slides_file}")
    
    slides_data = parse_slides_file(slides_file)
    

    images = index_images(batch_dir, slides_data)
    

    df = pd.DataFrame(images)
    

    condition_order = ['Pre', 'Wash4', 'Wash8', 'DAPI', 'AB', 'Post']
    df['condition_order'] = df['condition'].map({c: i for i, c in enumerate(condition_order)})
    df = df.sort_values(['slide_id', 'condition_order']).drop('condition_order', axis=1).reset_index(drop=True)
    
    return df


if __name__ == '__main__':
    df = main()
    print(f"Indexed {len(df)} images")
    print("\nDataFrame Info:")
    print(df.info())
    print("\nFirst 10 rows:")
    print(df.head(10))
    print("\nUnique slides:")
    print(df['slide_id'].unique())
    print("\nImages per condition:")
    print(df['condition'].value_counts().sort_index())
