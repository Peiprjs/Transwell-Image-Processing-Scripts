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
                
            layout = {}
            layout['pre'] = (0, 0)
            
            max_row = 0
            if not numbered_images:
                layout['post'] = (0, 1)
            else:
                for num in sorted(numbered_images.keys()):
                    row = num // 2
                    col = 1 if num % 2 != 0 else 0
                    layout[num] = (row, col)
                    if row > max_row:
                        max_row = row
                
                post_num = max(numbered_images.keys()) + 1
                post_row = post_num // 2
                post_col = 1 if post_num % 2 != 0 else 0
                layout['post'] = (post_row, post_col)
                if post_row > max_row:
                    max_row = post_row
            
            col_widths = {0: 0, 1: 0}
            row_heights = {r: 0 for r in range(max_row + 1)}
            
            for key, (r, c) in layout.items():
                img = images[key]
                if img.width > col_widths[c]:
                    col_widths[c] = img.width
                if img.height > row_heights[r]:
                    row_heights[r] = img.height
                    
            total_width = col_widths[0] + col_widths[1] + (separator_width if col_widths[1] > 0 else 0)
            total_height = sum(row_heights.values()) + separator_width * max_row
            
            composite = Image.new('RGB', (total_width, total_height), 'white')
            
            for key, (r, c) in layout.items():
                img = images[key]
                x = col_widths[0] + separator_width if c == 1 else 0
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
