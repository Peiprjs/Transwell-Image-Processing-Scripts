import io
import os

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from data_indexer import main as index_images

IMAGE_MARKER_ORDER = ["Composite", "Occludin", "ZO-1"]


st.set_page_config(
    page_title="Microscopy Slide Comparison Viewer",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
    .image-caption {
        font-size: 0.9em;
        color: #555;
        text-align: center;
        margin-top: 8px;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_image_data():
    return index_images()


def add_label(img, letter):
    """Add a letter label in a dark square at the top-left corner of an image."""
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)
    square_size = 50
    draw.rectangle([0, 0, square_size, square_size], fill=(30, 30, 30))
    font = None

    for font_name in ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "FreeSans.ttf", "LiberationSans-Regular.ttf"]:
        try:
            font = ImageFont.truetype(font_name, 36)
            break
        except Exception:
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


def compose_grid(images_by_position, num_rows, num_cols, separator_width, use_labels):
    """
    Compose a grid image from a dict of {(row, col): PIL.Image} entries.

    Parameters
    ----------
    images_by_position : dict[(int, int), PIL.Image]
        Mapping of (row, col) -> image.
    num_rows, num_cols : int
        Grid dimensions.
    separator_width : int
        White gap between cells in pixels.
    use_labels : bool
        Whether to stamp alphabetical labels (a, b, c, ...) on each image.

    Returns
    -------
    PIL.Image
        The composited grid image.
    """
    if not images_by_position:
        return None

    if use_labels:
        ordered_positions = sorted(images_by_position.keys(), key=lambda rc: (rc[0], rc[1]))
        labelled = {}
        for idx, pos in enumerate(ordered_positions):
            letter = chr(ord("a") + idx) if idx < 26 else str(idx + 1)
            labelled[pos] = add_label(images_by_position[pos].copy(), letter)
        images_by_position = labelled

    col_widths = {c: 0 for c in range(num_cols)}
    row_heights = {r: 0 for r in range(num_rows)}

    for (r, c), img in images_by_position.items():
        if img.width > col_widths[c]:
            col_widths[c] = img.width
        if img.height > row_heights[r]:
            row_heights[r] = img.height

    nonzero_widths = [w for w in col_widths.values() if w > 0]
    nonzero_heights = [h for h in row_heights.values() if h > 0]
    default_w = int(sum(nonzero_widths) / len(nonzero_widths)) if nonzero_widths else 200
    default_h = int(sum(nonzero_heights) / len(nonzero_heights)) if nonzero_heights else 200

    for c in range(num_cols):
        if col_widths[c] == 0:
            col_widths[c] = default_w
    for r in range(num_rows):
        if row_heights[r] == 0:
            row_heights[r] = default_h

    total_width = sum(col_widths.values()) + separator_width * max(0, num_cols - 1)
    total_height = sum(row_heights.values()) + separator_width * max(0, num_rows - 1)
    composite = Image.new("RGB", (total_width, total_height), "white")

    for (r, c), img in images_by_position.items():
        x = sum(col_widths[i] + separator_width for i in range(c))
        y = sum(row_heights[i] + separator_width for i in range(r))
        composite.paste(img.convert("RGB"), (x, y))

    return composite


def render_gallery(filtered_df, display_mode):
    """Render the image gallery in either Grid or Carousel mode."""
    if len(filtered_df) == 0:
        st.warning("No images match the selected filters. Please adjust your filter selections.")
        return

    if display_mode == "Grid":
        cols_per_row = 3
        for idx in range(0, len(filtered_df), cols_per_row):
            cols = st.columns(cols_per_row)
            for col_idx, col in enumerate(cols):
                image_idx = idx + col_idx
                if image_idx >= len(filtered_df):
                    col.empty()
                    continue

                row = filtered_df.iloc[image_idx]
                image_path = row["image_path"]

                with col:
                    try:
                        if os.path.exists(image_path):
                            image = Image.open(image_path)
                            st.image(image, use_container_width=True)

                            caption_html = f"""
                            <div class="image-caption">
                                <strong>Slide:</strong> {row['slide_id']}<br/>
                                <strong>Name:</strong> {row['slide_name']}<br/>
                                <strong>Type:</strong> {row['slide_type']} | <strong>Condition:</strong> {row['condition']}<br/>
                                <strong>Marker:</strong> {row['image_marker']}<br/>
                                <strong>Time:</strong> {row['time_point']} | <strong>Conc:</strong> {row['concentration']}<br/>
                                <em style="color: #888;">{image_path}</em>
                            </div>
                            """
                            st.markdown(caption_html, unsafe_allow_html=True)
                        else:
                            st.error(f"File not found: {image_path}")
                    except Exception as e:
                        st.error(f"Error loading image: {str(e)}")
    else:
        image_list = filtered_df["image_path"].tolist()
        meta_list = [
            (
                f"{r['slide_id']} - {r['slide_name']} | {r['condition']} | "
                f"{r['image_marker']} | {r['time_point']} | {r['concentration']}"
            )
            for _, r in filtered_df.iterrows()
        ]

        if "carousel_index" not in st.session_state:
            st.session_state.carousel_index = 0

        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("Previous", key="carousel_prev"):
                st.session_state.carousel_index = (st.session_state.carousel_index - 1) % len(image_list)
        with c2:
            st.markdown(f"**Image {st.session_state.carousel_index + 1} of {len(image_list)}**")
        with c3:
            if st.button("Next", key="carousel_next"):
                st.session_state.carousel_index = (st.session_state.carousel_index + 1) % len(image_list)

        cur_idx = st.session_state.carousel_index
        cur_path = image_list[cur_idx]
        cur_meta = meta_list[cur_idx]

        try:
            if os.path.exists(cur_path):
                img = Image.open(cur_path)
                st.image(img, use_container_width=True)
                caption_html = f"""
                <div class="image-caption">
                    {cur_meta}<br/>
                    <em style="color: #888;">{cur_path}</em>
                </div>
                """
                st.markdown(caption_html, unsafe_allow_html=True)
            else:
                st.error(f"File not found: {cur_path}")
        except Exception as e:
            st.error(f"Error loading image: {str(e)}")


def render_grid_composer(filtered_df):
    """Render the Image Grid Composer tab."""
    st.markdown(
        "Select images from the filtered gallery and arrange them in a custom grid. "
        "Choose how many rows and columns you need, then assign an image to each cell."
    )

    if len(filtered_df) == 0:
        st.warning("No images available. Adjust the sidebar filters to get images.")
        return

    image_options = {}
    for _, row in filtered_df.iterrows():
        label = (
            f"{row['slide_id']} | {row['condition']} | {row['image_marker']} | "
            f"{row['time_point']} | {row['concentration']}"
        )
        base_label = label
        counter = 2
        while label in image_options:
            label = f"{base_label} ({counter})"
            counter += 1
        image_options[label] = row["image_path"]

    option_labels = ["(empty)"] + sorted(image_options.keys())

    col_a, col_b = st.columns(2)
    with col_a:
        num_rows = st.number_input("Rows", min_value=1, max_value=10, value=2, step=1, key="grid_rows")
    with col_b:
        num_cols = st.number_input("Columns", min_value=1, max_value=10, value=2, step=1, key="grid_cols")

    opt_col1, opt_col2 = st.columns(2)
    with opt_col1:
        separator_width = st.slider("Separator width (px)", min_value=0, max_value=50, value=15, key="grid_sep")
    with opt_col2:
        use_labels = st.checkbox("Add letter labels (a, b, c, ...)", value=True, key="grid_labels")

    st.divider()
    st.subheader("Assign images to grid cells")

    for r in range(num_rows):
        cols = st.columns(num_cols)
        for c_idx, col in enumerate(cols):
            with col:
                st.selectbox(
                    f"Row {r + 1}, Col {c_idx + 1}",
                    options=option_labels,
                    index=0,
                    key=f"grid_cell_{r}_{c_idx}",
                )

    st.divider()
    output_name = st.text_input("Output filename", value="custom_grid.png", key="grid_output_name")

    if st.button("Generate Grid", type="primary", key="grid_generate"):
        images_by_position = {}
        for r in range(num_rows):
            for c in range(num_cols):
                selected = st.session_state.get(f"grid_cell_{r}_{c}", "(empty)")
                if selected != "(empty)" and selected in image_options:
                    img_path = image_options[selected]
                    if os.path.exists(img_path):
                        images_by_position[(r, c)] = Image.open(img_path)

        if not images_by_position:
            st.error("No images selected. Please assign at least one image to a grid cell.")
            return

        with st.spinner("Compositing grid..."):
            composite = compose_grid(images_by_position, num_rows, num_cols, separator_width, use_labels)

        if composite is not None:
            st.success(f"Grid composed: {composite.width} x {composite.height} px")
            st.image(composite, use_container_width=True)

            buf = io.BytesIO()
            composite.save(buf, format="PNG")
            buf.seek(0)

            st.download_button(
                label="Download Grid Image",
                data=buf,
                file_name=output_name if output_name.endswith(".png") else output_name + ".png",
                mime="image/png",
                key="grid_download",
            )


def main():
    st.title("Microscopy Slide Comparison Viewer")
    st.markdown(
        "Interactive viewer for comparing microscopy slides across different batches, "
        "conditions, markers (Composite, Occludin, ZO-1), slide types (F/L, G/L, L/L, S/L), "
        "time points (T0, T120), and concentrations."
    )
    st.divider()

    with st.spinner("Loading slide data..."):
        df = load_image_data()

    if df.empty:
        st.error("No images found in the batch directory.")
        return

    unique_slides = sorted(df["slide_id"].unique().tolist())
    unique_conditions = sorted(df["condition"].unique().tolist())
    unique_slide_types = sorted(df["slide_type"].unique().tolist())
    unique_time_points = sorted(df["time_point"].unique().tolist())
    unique_concentrations = sorted(df["concentration"].unique().tolist())
    unique_markers = sorted(
        df["image_marker"].unique().tolist(),
        key=lambda marker: IMAGE_MARKER_ORDER.index(marker) if marker in IMAGE_MARKER_ORDER else len(IMAGE_MARKER_ORDER),
    )

    st.sidebar.header("Filters")

    selected_slide_types = st.sidebar.multiselect(
        "Slide Type",
        options=unique_slide_types,
        default=unique_slide_types,
        help="Select slide types: F/L, G/L, L/L, S/L",
    )

    selected_conditions = st.sidebar.multiselect(
        "Slide Condition",
        options=unique_conditions,
        default=unique_conditions,
        help="Select imaging conditions: Pre, Wash4, Wash8, DAPI, AB, Post",
    )

    selected_markers = st.sidebar.multiselect(
        "Image Marker",
        options=unique_markers,
        default=unique_markers,
        help="Toggle which merged images to display.",
    )

    selected_time_points = st.sidebar.multiselect(
        "Time Point (Optional)",
        options=unique_time_points,
        default=unique_time_points,
        help="Select time points: T0, T120",
    )

    selected_concentrations = st.sidebar.multiselect(
        "Concentration (Optional)",
        options=unique_concentrations,
        default=unique_concentrations,
        help="Select concentrations: 100%, 33%",
    )

    selected_slides = st.sidebar.multiselect(
        "Slide ID (Optional)",
        options=unique_slides,
        default=unique_slides,
        help="Select specific slides (e.g., 1L, 2R, 3C)",
    )

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Reset Filters", use_container_width=True):
            st.rerun()
    with col2:
        pass

    st.sidebar.divider()
    st.sidebar.markdown("**Active Filters:**")
    st.sidebar.markdown(f"**Slide Types:** {', '.join(selected_slide_types) if selected_slide_types else 'None'}")
    st.sidebar.markdown(f"**Conditions:** {', '.join(selected_conditions) if selected_conditions else 'None'}")
    st.sidebar.markdown(f"**Markers:** {', '.join(selected_markers) if selected_markers else 'None'}")
    st.sidebar.markdown(f"**Time Points:** {', '.join(selected_time_points) if selected_time_points else 'None'}")
    st.sidebar.markdown(f"**Concentrations:** {', '.join(selected_concentrations) if selected_concentrations else 'None'}")

    with st.spinner("Filtering images..."):
        filtered_df = df.copy()

        if selected_slide_types:
            filtered_df = filtered_df[filtered_df["slide_type"].isin(selected_slide_types)]
        if selected_conditions:
            filtered_df = filtered_df[filtered_df["condition"].isin(selected_conditions)]
        if selected_markers:
            filtered_df = filtered_df[filtered_df["image_marker"].isin(selected_markers)]
        else:
            filtered_df = filtered_df.iloc[0:0]
        if selected_time_points:
            filtered_df = filtered_df[filtered_df["time_point"].isin(selected_time_points)]
        if selected_concentrations:
            filtered_df = filtered_df[filtered_df["concentration"].isin(selected_concentrations)]
        if selected_slides:
            filtered_df = filtered_df[filtered_df["slide_id"].isin(selected_slides)]

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric("Total Images", len(df))
    with col2:
        st.metric("Matching Images", len(filtered_df))
    with col3:
        if len(filtered_df) > 0:
            match_percentage = (len(filtered_df) / len(df)) * 100
            st.metric("Match %", f"{match_percentage:.1f}%")

    st.divider()
    tab_gallery, tab_composer = st.tabs(["Image Gallery", "Image Grid Composer"])

    with tab_gallery:
        st.header("Image Gallery")
        display_mode = st.sidebar.radio("Display Mode", ("Grid", "Carousel"), index=0)
        render_gallery(filtered_df, display_mode)

    with tab_composer:
        st.header("Image Grid Composer")
        render_grid_composer(filtered_df)

    st.divider()
    st.markdown("**Dataset Statistics**")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Slide Types", len(unique_slide_types))
    with col2:
        st.metric("Conditions", len(unique_conditions))
    with col3:
        st.metric("Time Points", len(unique_time_points))
    with col4:
        st.metric("Concentrations", len(unique_concentrations))
    with col5:
        st.metric("Total Images", len(df))


if __name__ == "__main__":
    main()
