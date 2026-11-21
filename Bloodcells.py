import random
from pathlib import Path
import kagglehub
from PIL import Image
import streamlit as st

# Page setup
st.set_page_config(
    page_title="Blood Cell Recognition Quiz",
    page_icon="🩸",
    layout="centered",
)

# Clean display names for the 8 classes in unclesamulus/blood-cells-image-dataset
DISPLAY_NAMES = {
    "basophil": "Basophil",
    "eosinophil": "Eosinophil",
    "erythroblast": "Erythroblast",
    "ig": "Immature Granulocyte (IG)",
    "lymphocyte": "Lymphocyte",
    "monocyte": "Monocyte",
    "neutrophil": "Neutrophil",
    "platelet": "Platelet",
}

def format_label(raw_name: str) -> str:
    return DISPLAY_NAMES.get(raw_name.lower(), raw_name.replace("_", " ").title())

# 1. Download / locate cached Kaggle dataset and index all images
@st.cache_data(show_spinner="Loading Kaggle blood cells dataset...")
def load_dataset():
    dataset_path = Path(
        kagglehub.dataset_download("unclesamulus/blood-cells-image-dataset")
    )
    image_paths = [
        p for p in dataset_path.rglob("*")
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]
    classes = sorted({p.parent.name for p in image_paths})
    return str(dataset_path), image_paths, classes

dataset_dir, image_paths, all_classes = load_dataset()

if not image_paths:
    st.error(f"No images found in {dataset_dir}. Check your Kaggle download.")
    st.stop()

# 2. Quiz state helper functions
def pick_new_image(allowed_classes):
    filtered = [p for p in image_paths if p.parent.name in allowed_classes]
    st.session_state.current_img = random.choice(filtered)
    st.session_state.answered = False
    st.session_state.selected = None

def submit_answer(choice):
    st.session_state.answered = True
    st.session_state.selected = choice
    st.session_state.total += 1
    true_label = st.session_state.current_img.parent.name
    if choice == true_label:
        st.session_state.score += 1
    else:
        st.session_state.missed.append(
            (str(st.session_state.current_img), true_label, choice)
        )

def reset_quiz(allowed_classes):
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.missed = []
    pick_new_image(allowed_classes)

# 3. Sidebar controls
with st.sidebar:
    st.header("Practice Settings")
    selected_classes = st.multiselect(
        "Cell types to drill:",
        options=all_classes,
        default=all_classes,
        format_func=format_label,
    )

    if not selected_classes:
        st.warning("Select at least one cell type to practice.")
        st.stop()

    st.caption(f"Dataset loaded: {len(image_paths):,} images")

    if st.button("Reset Score & History", use_container_width=True):
        reset_quiz(selected_classes)

# 4. Initialize session state on first load
if "score" not in st.session_state:
    st.session_state.score = 0
    st.session_state.total = 0
    st.session_state.missed = []
    pick_new_image(selected_classes)

# Ensure current image matches active sidebar filter
if st.session_state.current_img.parent.name not in selected_classes:
    pick_new_image(selected_classes)

# 5. Title & live scoreboard
st.title("🩸 Blood Cell Practical Prep")

accuracy = (
    (st.session_state.score / st.session_state.total) * 100
    if st.session_state.total > 0
    else 0.0
)
c1, c2, c3 = st.columns(3)
c1.metric("Correct", st.session_state.score)
c2.metric("Attempted", st.session_state.total)
c3.metric("Accuracy", f"{accuracy:.1f}%")

st.divider()

# 6. Show current blood cell image
img = Image.open(st.session_state.current_img)
left, center, right = st.columns([1, 2, 1])
with center:
    st.image(img, width=320)

# 7. Multiple-choice buttons
st.subheader("Identify this cell:")
true_label = st.session_state.current_img.parent.name

cols = st.columns(2)
for idx, cell_class in enumerate(selected_classes):
    with cols[idx % 2]:
        st.button(
            format_label(cell_class),
            key=f"choice_{cell_class}",
            on_click=submit_answer,
            args=(cell_class,),
            disabled=st.session_state.answered,
            use_container_width=True,
        )

# 8. Feedback & Next button
if st.session_state.answered:
    if st.session_state.selected == true_label:
        st.success(f"Correct! This is a **{format_label(true_label)}**.")
    else:
        st.error(
            f"Incorrect. You selected **{format_label(st.session_state.selected)}**, "
            f"but this is a **{format_label(true_label)}**."
        )

    st.button(
        "Next Cell ➡️",
        type="primary",
        on_click=pick_new_image,
        args=(selected_classes,),
        use_container_width=True,
    )

# 9. Review missed cells at the bottom
if st.session_state.missed:
    st.divider()
    with st.expander(f"Review Missed Cells ({len(st.session_state.missed)})"):
        for img_path, actual, guessed in reversed(st.session_state.missed[-10:]):
            r1, r2 = st.columns([1, 3])
            with r1:
                st.image(Image.open(img_path), width=90)
            with r2:
                st.markdown(f"**Actual:** {format_label(actual)}")
                st.markdown(f"**Your guess:** {format_label(guessed)}")