import streamlit as st
import pandas as pd
from pathlib import Path
from PIL import Image
import os
from data_indexer import main as index_images



st.set_page_config(
    page_title="Microscopy Slide Comparison Viewer",
    page_icon="[microscope]",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-card {
        background-color:
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
    .image-caption {
        font-size: 0.9em;
        color:
        text-align: center;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_image_data():
    return index_images()


def main():
    st.title("Microscopy Slide Comparison Viewer")
    st.markdown(
        "Interactive viewer for comparing microscopy slides across different batches, "
        "conditions, slide types (F/L, G/L, L/L, S/L), time points (T0, T120), and concentrations."
    )
    st.divider()

    with st.spinner("Loading slide data..."):
        df = load_image_data()

    if df.empty:
        st.error("No images found in the batch directory.")
        return

    unique_slides = sorted(df['slide_id'].unique().tolist())
    unique_conditions = sorted(df['condition'].unique().tolist())
    unique_slide_types = sorted(df['slide_type'].unique().tolist())
    unique_time_points = sorted(df['time_point'].unique().tolist())
    unique_concentrations = sorted(df['concentration'].unique().tolist())

    st.sidebar.header("Filters")

    selected_slide_types = st.sidebar.multiselect(
        "Slide Type",
        options=unique_slide_types,
        default=unique_slide_types,
        help="Select slide types: F/L, G/L, L/L, S/L"
    )


    selected_conditions = st.sidebar.multiselect(
        "Slide Condition",
        options=unique_conditions,
        default=unique_conditions,
        help="Select imaging conditions: Pre, Wash4, Wash8, DAPI, AB, Post"
    )


    selected_time_points = st.sidebar.multiselect(
        "Time Point (Optional)",
        options=unique_time_points,
        default=unique_time_points,
        help="Select time points: T0, T120"
    )


    selected_concentrations = st.sidebar.multiselect(
        "Concentration (Optional)",
        options=unique_concentrations,
        default=unique_concentrations,
        help="Select concentrations: 100%, 33%"
    )


    selected_slides = st.sidebar.multiselect(
        "Slide ID (Optional)",
        options=unique_slides,
        default=unique_slides,
        help="Select specific slides (e.g., 1L, 2R, 3C)"
    )


    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Reset Filters", use_container_width=True):
            st.rerun()
    with col2:
        pass


    st.sidebar.divider()
    st.sidebar.markdown("
    st.sidebar.markdown(f"**Slide Types:** {', '.join(selected_slide_types) if selected_slide_types else 'None'}")
    st.sidebar.markdown(f"**Conditions:** {', '.join(selected_conditions) if selected_conditions else 'None'}")
    st.sidebar.markdown(f"**Time Points:** {', '.join(selected_time_points) if selected_time_points else 'None'}")
    st.sidebar.markdown(f"**Concentrations:** {', '.join(selected_concentrations) if selected_concentrations else 'None'}")


    with st.spinner("Filtering images..."):
        filtered_df = df.copy()
        
        if selected_slide_types:
            filtered_df = filtered_df[filtered_df['slide_type'].isin(selected_slide_types)]
        if selected_conditions:
            filtered_df = filtered_df[filtered_df['condition'].isin(selected_conditions)]
        if selected_time_points:
            filtered_df = filtered_df[filtered_df['time_point'].isin(selected_time_points)]
        if selected_concentrations:
            filtered_df = filtered_df[filtered_df['concentration'].isin(selected_concentrations)]
        if selected_slides:
            filtered_df = filtered_df[filtered_df['slide_id'].isin(selected_slides)]


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


    st.header("Image Gallery")


    display_mode = st.sidebar.radio("Display Mode", ("Grid", "Carousel"), index=0)

    if len(filtered_df) == 0:
        st.warning(
            "No images match the selected filters. "
            "Please adjust your filter selections."
        )
    else:
        if display_mode == "Grid":

            cols_per_row = 3
            

            for idx in range(0, len(filtered_df), cols_per_row):
                cols = st.columns(cols_per_row)
                
                for col_idx, col in enumerate(cols):
                    image_idx = idx + col_idx
                    
                    if image_idx < len(filtered_df):
                        row = filtered_df.iloc[image_idx]
                        image_path = row['image_path']
                        
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
                                        <strong>Time:</strong> {row['time_point']} | <strong>Conc:</strong> {row['concentration']}<br/>
                                        <em style="color:
                                    </div>
                                    """
                                    st.markdown(caption_html, unsafe_allow_html=True)
                                else:
                                    st.error(f"File not found: {image_path}")
                            
                            except Exception as e:
                                st.error(f"Error loading image: {str(e)}")
                    
                    else:

                        col.empty()
        else:

            image_list = filtered_df['image_path'].tolist()
            meta_list = [f"{r['slide_id']} — {r['slide_name']} | {r['condition']} | {r['time_point']} | {r['concentration']}" for _, r in filtered_df.iterrows()]

            if 'carousel_index' not in st.session_state:
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
                        <em style="color:
                    </div>
                    """
                    st.markdown(caption_html, unsafe_allow_html=True)
                else:
                    st.error(f"File not found: {cur_path}")
            except Exception as e:
                st.error(f"Error loading image: {str(e)}")


    st.divider()
    st.markdown("
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
