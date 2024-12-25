import json
import streamlit as st
from llm import AzureOpenAI
from prompts import *
from utils import *

def init_session():
    if "response" not in st.session_state:
        st.session_state.response = None
    if "plantuml_svg" not in st.session_state:
        st.session_state['plantuml_svg'] = None
    if "plantuml_png" not in st.session_state:
        st.session_state['plantuml_png'] = None


def cleanup():
    st.session_state.clear()
    init_session()

init_session()
llm_client = AzureOpenAI()

st.header("AI-Powered Diagram Generator")
st.markdown("Using **GPT-4o (Azure OpenAI)** & **PlantUML**")

with st.container(border=True):
    st.markdown("##### Select Diagram Generation Mode")
    mode = st.pills("Select Diagram Generation Mode", ["From Text", "From Sketch"], default="From Text",  label_visibility="collapsed")

if mode == "From Text":
    cleanup()
    st.markdown("### Generate Diagram from Ideas & Textual Descriptions")
    selected_sample_text = st.selectbox("Select Sample Text", options=[sample_text["display_text"] for sample_text in get_sample_texts()], index=None)
    st.text_area("Idea / Specification", placeholder="What do you wish to visualize?", height=200, key="text", value=get_sample_texts(selected_sample_text) if selected_sample_text else None)
    if st.button("Generate Diagram", icon="✨", type="primary", use_container_width=True):
        if not st.session_state.text:
            st.error("Please enter an idea or select a sample text.")
        else:
            cleanup()
            messages = TEXT_TO_DIAGRAM.copy()
            messages.append({"role": "user", "content": st.session_state.text})
            with st.spinner("Hold tight! Your awesome diagram is brewing... ☕✨"):
                st.session_state.response = llm_client.send_message(messages)
                print(st.session_state.response)

if mode == "From Sketch":
    cleanup()
    st.markdown("### Convert Hand-Drawn Sketches to Professional Diagrams")
    sketch_path=None
    selected_sample_sketch = st.selectbox("Select Sample Sketch", options=get_sample_sketches(), index=None)
    if selected_sample_sketch:
        sketch_path = os.path.join("samples", selected_sample_sketch)
        st.image(sketch_path, caption="Selected Sketch", use_container_width=True)
    else:
        uploaded_sketch = st.file_uploader("Upload sketch", type=["png", "jpg", "jpeg"])
        if uploaded_sketch:
            sketch_path = f"tmp_{uploaded_sketch.name}"
            with open(sketch_path, "wb") as f:
                f.write(uploaded_sketch.getbuffer())
            st.image(sketch_path, caption="Uploaded Sketch", use_container_width=True)

    if st.button("Convert to Diagram", icon="✨", type="primary", use_container_width=True):
        if not sketch_path:
            st.error("Please upload a sketch or select a sample sketch.")
        else:
            cleanup()
            messages = SKETCH_TO_DIAGRAM.copy()
            messages.append({"role": "user", "content": [{"type": "image_url", "image_url": {"url": local_image_to_data_url(sketch_path)}}]})
            with st.spinner("Hold tight! Your awesome diagram is brewing... ☕✨"):
                st.session_state.response = llm_client.send_message(messages)
                if not selected_sample_sketch:
                    os.remove(sketch_path)
    
try:
    if st.session_state.response:
        response_json = json.loads(st.session_state.response)
        explanation =response_json["explanation"]
        plantuml_syntax =response_json["plantuml_syntax"]

        if not st.session_state.plantuml_svg or not st.session_state.plantuml_png:
            with st.spinner("Almost there! Rendering the diagram... 🎨"):
                st.session_state.plantuml_svg = plantuml_to_base64(plantuml_syntax, "svg")
                st.session_state.plantuml_png = plantuml_to_base64(plantuml_syntax, "png")
        
        if st.session_state.plantuml_svg and st.session_state.plantuml_png:
            with st.container():
                plantuml_html = f"<a href='data:image/svg+xml;base64,{st.session_state.plantuml_svg[1]}'><img src='data:image/svg+xml;base64,{st.session_state.plantuml_svg[1]}'/></a><br />"
                st.write(plantuml_html, unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("Download as SVG", icon="💾", data=st.session_state.plantuml_svg[0], mime="image/svg+xml", use_container_width=True)
            with col2:
                st.download_button("Download as PNG", icon="💾", data=st.session_state.plantuml_png[0], mime="image/png", use_container_width=True)

            with st.expander("🔍 View Explanation"):
                st.write(explanation)
            with st.expander("💻 PlantUML Syntax"):
                st.code(plantuml_syntax, language="plantuml")
except Exception as e:
    st.error(f"Oops! Something went wrong. Please try again.\nError: {e}")
