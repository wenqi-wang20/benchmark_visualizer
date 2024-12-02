import streamlit as st
from PIL import Image
import pandas as pd
import json
import os
import pygit2

# designe the data json format
# [{
    # "dataset_name": "Dataset 1",
    # "url": "https://www.kaggle.com/ashishsaxena2209/animal-image-datasetdog-cat-and-panda",
    # "description": "This dataset contains images of animals.",
    # "examples": [
        # { 
        #   "spatial_type": "relationship",
        #   "origin": "",
        #   "images": [img_url1, img_url2, ...], 
        #   "Question/Annotation": "This is a cat.",
        #   "Answer":  ""
        # },
    #   ... ]
# },
# ...]
    

# Load the dataset JSON file
def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    return []

# Save the dataset JSON file
def save_data(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
        
# Ensure images directory exists
def ensure_images_dir():
    if not os.path.exists("images"):
        os.makedirs("images")

# Save uploaded image
def save_uploaded_image(uploaded_file, name):
    # ensure_images_dir()
    os.makedirs(os.path.dirname(name), exist_ok=True)
    file_path = name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


# File path to the dataset JSON
DATA_FILE = "data.json"
data = load_data(DATA_FILE)

# Initialize session state for selected dataset
if "selected_dataset" not in st.session_state:
    st.session_state.selected_dataset = ""
if "selected_spatial_type" not in st.session_state:
    st.session_state.selected_spatial_type = "All"

# Streamlit app
st.title("Spatial Related Dataset Viewer and Editor")

# Sidebar for selecting a dataset
st.sidebar.title("Datasets")
dataset_names = [d["dataset_name"] for d in data]
selected_dataset = st.sidebar.selectbox("Select a dataset", 
                                        options=["Add New Dataset"] + dataset_names,)
                                        # index=dataset_names.index(st.session_state.selected_dataset) if st.session_state.selected_dataset in dataset_names else 0)
# Update session state only when the selection changes
print(selected_dataset, st.session_state.selected_dataset)
if selected_dataset != st.session_state.selected_dataset:
    st.session_state.selected_dataset = selected_dataset
    # selected_dataset = st.session_state.selected_dataset
    

# Display spatial types overview
st.sidebar.title("Spatial Types Overview")
spatial_type_counts = {}
for dataset in data:
    for example in dataset["examples"]:
        spatial_type = example["spatial_type"]
        if spatial_type == "":
            # spatial_type = "Unknown"
            continue
        if spatial_type in spatial_type_counts:
            spatial_type_counts[spatial_type] += 1
        else:
            spatial_type_counts[spatial_type] = 1
            
# Sidebar for selecting a dataset
# Sidebar for displaying all spatial types across datasets
st.sidebar.title("Examples by Spatial Type")
selected_spatial_type_overview = st.sidebar.selectbox(
    "Select Spatial Type to View Examples",
    options=["All"] + list(spatial_type_counts.keys())
)

# Create a dataframe for better visualization
spatial_type_df = pd.DataFrame(list(spatial_type_counts.items()), columns=["Spatial Type", "Count"])
spatial_type_df = spatial_type_df.sort_values(by="Count", ascending=False)

# Display spatial type counts as a table with styles
# Display spatial type counts as a table in the sidebar
st.sidebar.dataframe(
    spatial_type_df.style.set_properties(**{
        'text-align': 'left',
        'font-weight': 'bold'
    }).set_table_styles([
        dict(selector="th", props=[("font-size", "14px"), ("text-align", "center")]),
        dict(selector="td", props=[("padding", "10px")])
    ])
)

# If "Add New Dataset" is selected
if selected_spatial_type_overview != "All":
    examples_by_spatial_type = []
    for dataset in data:
        for example in dataset["examples"]:
            if example["spatial_type"] == selected_spatial_type_overview:
                examples_by_spatial_type.append({
                    "Dataset Name": dataset["dataset_name"],
                    "Question/Annotation": example["Question/Annotation"],
                    "Answer": example["Answer"],
                    "Images": example["images"]
                })

    st.subheader(f"Examples for Spatial Type: {selected_spatial_type_overview}")
    st.write("---")
    for ex in examples_by_spatial_type:
        st.write(f"**Dataset:** {ex['Dataset Name']}")
        st.write(f"**Question/Annotation:** {ex['Question/Annotation']}")
        st.write(f"**Answer:**  {ex['Answer']}")
        if ex["Images"]:
            for img_path in ex["Images"]:
                st.image(img_path, use_container_width=True)
        st.write("---")
elif selected_dataset == "Add New Dataset":
    st.subheader("Add New Dataset")
    dataset_name = st.text_input("Dataset Name")
    dataset_url = st.text_input("Dataset URL")
    dataset_description = st.text_area("Dataset Description")

    if st.button("Add Dataset"):
        if dataset_name:
            new_dataset = {
                "dataset_name": dataset_name,
                "url": dataset_url,
                "description": dataset_description,
                "examples": []
            }
            data.append(new_dataset)
            os.makedirs(f"sample_data/{dataset_name}", exist_ok=True)
            save_data(DATA_FILE, data)
            st.session_state.selected_dataset = dataset_name
            st.success(f"Dataset '{dataset_name}' added successfully!")
            st.rerun()
            st.query_params["selected"] = st.session_state.selected_dataset
        else:
            st.error("Dataset name is required.")
else:
    # Display selected dataset details
    selected_data = next(d for d in data if d["dataset_name"] == selected_dataset)

    st.subheader(f"{selected_dataset}")

    # Editable fields
    selected_data["dataset_name"] = st.text_input("Dataset Name", value=selected_data["dataset_name"])
    selected_data["url"] = st.text_input("Dataset URL", value=selected_data["url"])
    selected_data["description"] = st.text_area("Dataset Description", value=selected_data["description"])

    # Examples section
    st.subheader("Examples")
    for idx, example in enumerate(selected_data["examples"]):
        with st.expander(f"Example {idx + 1} - {example['spatial_type']}"):
            example["spatial_type"] = st.text_input("Spatial Type", value=example["spatial_type"], key=f"spatial_type_{idx}")
            example["origin"] = st.text_input("Origin", value=example["origin"], key=f"origin_{idx}")
            example["Question/Annotation"] = st.text_area("Question/Annotation", value=example["Question/Annotation"], key=f"question_{idx}")
            example["Answer"] = st.text_input("Answer", value=example["Answer"], key=f"answer_{idx}")

            # Editable image URLs
            st.write("Images")
            for img_idx, img_path in enumerate(example["images"]):
                col1, col2 = st.columns([3, 1])
                with col1:
                    if os.path.exists(img_path):
                        st.image(img_path, caption=f"Image {img_idx + 1}", use_container_width=True)
                    else:
                        st.warning(f"Image not found: {img_path}")

                with col2:
                    if st.button("Remove", key=f"remove_image_{idx}_{img_idx}"):
                        example["images"].pop(img_idx)
                        save_data(DATA_FILE, data)
                        st.success("Image removed successfully!")
                        st.rerun()
                        st.query_params["selected"] = st.session_state.selected_dataset
            
            # exisiting image number
            img_count = len(example["images"])
                                    
            # Add new image
            uploaded_file = st.file_uploader("Upload Image", key=f"upload_image_{idx}")
            if uploaded_file is not None and f"uploaded_{idx}" not in st.session_state:
                file_name = f"sample_data/{selected_data['dataset_name']}/{example['spatial_type'].replace(' ','_')}{img_count+1}.jpg"
                file_path = save_uploaded_image(uploaded_file, file_name)
                example["images"].append(file_path)
                save_data(DATA_FILE, data)
                st.success("Image uploaded successfully!")
                st.session_state[f"uploaded_{idx}"] = True
                st.rerun()
                st.query_params["selected"] = st.session_state.selected_dataset
                
            # Delete example
            if st.button("Delete Example", key=f"delete_example_{idx}"):
                selected_data["examples"].pop(idx)
                save_data(DATA_FILE, data)
                st.success("Example deleted successfully!")
                st.rerun()
                st.query_params["selected"] = st.session_state.selected_dataset
            
    # Add a new example
    if st.button("Add New Example"):
        selected_data["examples"].append({
            "spatial_type": "",
            "origin": "",
            "images": [],
            "Question/Annotation": "",
            "Answer": ""
        })
        save_data(DATA_FILE, data)
        st.success("New example added successfully!")
        st.rerun()
        st.query_params["selected"] = st.session_state.selected_dataset

    # Save changes
    if st.button("Save Changes"):
        save_data(DATA_FILE, data)
        st.success("Changes saved successfully!")
        st.rerun()
        st.query_params["selected"] = st.session_state.selected_dataset
