import os
from pathlib import Path
from PIL import Image

def process_finals_directories(base_directory, separator_width=20):
    base_path = Path(base_directory)
    
    finals_dirs = list(base_path.rglob("Finals"))
    
    for finals_dir in finals_dirs:
        if not finals_dir.is_dir():
            continue
            
        pre_img_path = None
        post_img_path = None
        numbered_images = {}
        
        for p in finals_dir.glob("*.[pP][nN][gG]"):
            if "merged" in p.name.lower():
                continue
                
            name = p.stem.lower()
            if name == "pre":
                pre_img_path = p
            elif name == "post":
                post_img_path = p
            elif p.stem.isdigit():
                numbered_images[int(p.stem)] = p

        if not pre_img_path or not post_img_path:
            continue
            
        print(f"Processing {finals_dir}...")
            
        try:
            images = {}
            images['pre'] = Image.open(pre_img_path)
            images['post'] = Image.open(post_img_path)
            
            for num, p in numbered_images.items():
                images[num] = Image.open(p)
                
            total_images = len(numbered_images) + 2
            num_columns = 3 if total_images > 4 else 2

            layout = {}
            layout['pre'] = (0, 0)
            
            max_row = 0
            if not numbered_images:
                layout['post'] = (0, 1)
            else:
                for num in sorted(numbered_images.keys()):
                    row = num // num_columns
                    col = num % num_columns
                    layout[num] = (row, col)
                    if row > max_row:
                        max_row = row
                
                post_num = max(numbered_images.keys()) + 1
                post_row = post_num // num_columns
                post_col = post_num % num_columns
                layout['post'] = (post_row, post_col)
                if post_row > max_row:
                    max_row = post_row
            
            col_widths = {c: 0 for c in range(num_columns)}
            row_heights = {r: 0 for r in range(max_row + 1)}
            
            for key, (r, c) in layout.items():
                img = images[key]
                if img.width > col_widths[c]:
                    col_widths[c] = img.width
                if img.height > row_heights[r]:
                    row_heights[r] = img.height
                    
            max_col = max(c for key, (r, c) in layout.items())
            num_active_cols = max_col + 1
            
            total_width = sum(col_widths[c] for c in range(num_active_cols)) + separator_width * max(0, num_active_cols - 1)
            total_height = sum(row_heights.values()) + separator_width * max_row
            
            composite = Image.new('RGB', (total_width, total_height), 'white')
            
            for key, (r, c) in layout.items():
                img = images[key]
                x = sum(col_widths[i] + separator_width for i in range(c))
                y = sum(row_heights[i] + separator_width for i in range(r))
                composite.paste(img, (x, y))
                
            output_filename = f"{finals_dir.parent.name}.png"
            output_path = finals_dir / output_filename
            composite.save(output_path)
            
            print(f"  [SUCCESS] Created: {output_path}")
            
        except Exception as e:
            print(f"  [ERROR] Processing {finals_dir}: {e}")

TARGET_DIRECTORY = "."
SEPARATOR_THICKNESS = 15

if __name__ == "__main__":
    print("Starting image processing...")
    process_finals_directories(TARGET_DIRECTORY, SEPARATOR_THICKNESS)
    print("Processing complete.")
