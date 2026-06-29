import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def add_label(img, letter):
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)
    square_size = 50
    draw.rectangle([0, 0, square_size, square_size], fill=(30, 30, 30))
    font = None
    for font_name in ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "FreeSans.ttf", "LiberationSans-Regular.ttf"]:
        try:
            font = ImageFont.truetype(font_name, 36)
            break
        except:
            pass
    if font is None:
        font = ImageFont.load_default()
        
    try:
        bbox = draw.textbbox((0, 0), letter, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (square_size - text_w) / 2 - bbox[0]
        y = (square_size - text_h) / 2 - bbox[1]
    except AttributeError:
        x, y = 15, 5
        
    draw.text((x, y), letter, fill="white", font=font)
    return img

def create_2x2_composites(base_directory, separator_width=20):
    base_path = Path(base_directory)

    numbers = [str(i) for i in range(1, 7)]
    letters = ['C', 'L', 'R']

    for num in numbers:
        for letter in letters:
            work_dir = base_path / num / letter
            pre_dir = work_dir / "Pre"
            post_dir = work_dir / "Wash8"
            dapi_dir = work_dir / "DAPI"
            ab_dir = work_dir / "AB"

            if not work_dir.exists():
                continue

            if not all(d.exists() for d in [pre_dir, post_dir, dapi_dir, ab_dir]):
                print(f"Skipping {work_dir}: Missing one or more required subfolders.")
                for d in [pre_dir, post_dir, dapi_dir, ab_dir]:
                    if not d.exists():
                        print(f"  -> Missing: {d.name}")
                continue

            png_files = list(pre_dir.glob("*.[pP][nN][gG]"))

            print(f"Checking {pre_dir}... Found {len(png_files)} PNG files.")

            for pre_img_path in png_files:
                img_name = pre_img_path.name

                post_img_path = post_dir / img_name
                dapi_img_path = dapi_dir / img_name
                ab_img_path = ab_dir / img_name

                if all(p.exists() for p in [post_img_path, dapi_img_path, ab_img_path]):
                    try:
                        pre_img = add_label(Image.open(pre_img_path), 'a')
                        post_img = add_label(Image.open(post_img_path), 'b')
                        dapi_img = add_label(Image.open(dapi_img_path), 'c')
                        ab_img = add_label(Image.open(ab_img_path), 'd')

                        col1_width = max(pre_img.width, dapi_img.width)
                        col2_width = max(post_img.width, ab_img.width)
                        row1_height = max(pre_img.height, post_img.height)
                        row2_height = max(dapi_img.height, ab_img.height)

                        total_width = col1_width + col2_width + separator_width
                        total_height = row1_height + row2_height + separator_width

                        composite = Image.new('RGB', (total_width, total_height), 'white')

                        composite.paste(pre_img, (0, 0))
                        composite.paste(post_img, (col1_width + separator_width, 0))
                        composite.paste(dapi_img, (0, row1_height + separator_width))
                        composite.paste(ab_img, (col1_width + separator_width, row1_height + separator_width))

                        output_filename = f"{num}{letter}_Merged.png"

                        output_path = work_dir / output_filename
                        composite.save(output_path)

                        print(f"  [SUCCESS] Created: {output_path}")

                    except Exception as e:
                        print(f"  [ERROR] Processing {img_name} in {work_dir}: {e}")
                else:
                    print(f"  [WARNING] Missing matching images in peer folders for {img_name}")

TARGET_DIRECTORY = "."
SEPARATOR_THICKNESS = 15

if __name__ == "__main__":
    print("Starting image processing...")
    create_2x2_composites(TARGET_DIRECTORY, SEPARATOR_THICKNESS)
    print("Processing complete.")
