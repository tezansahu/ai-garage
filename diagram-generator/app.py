import json
import streamlit as st
from llm import AzureOpenAI
from prompts import *
from utils import *

def init_session():
    """
    Initialize the session state variables for the Streamlit application.

    This function checks if the session state variables 'response', 'plantuml_svg',
    and 'plantuml_png' exist in the Streamlit session state. If they do not exist,
    it initializes them to None.
    """
    if "prev_mode" not in st.session_state:
        st.session_state.prev_mode = "From Text"
    # if "text" not in st.session_state:
    #     st.session_state.text = None
    if "response" not in st.session_state:
        st.session_state.response = None
    if "plantuml_svg" not in st.session_state:
        st.session_state['plantuml_svg'] = None
    if "plantuml_png" not in st.session_state:
        st.session_state['plantuml_png'] = None


def cleanup():
    """
    Clears the current Streamlit session state and reinitializes the session.

    This function is typically used to reset the application state, ensuring
    that all session variables are cleared and the session is reinitialized
    to its default state.
    """
    st.session_state.response = None
    st.session_state['plantuml_svg'] = None
    st.session_state['plantuml_png'] = None


# Initialize session state variables at the start
init_session()
llm_client = AzureOpenAI()

# Streamlit UI setup
st.header("AI-Powered Diagram Generator")
st.markdown("Using **GPT-4o (Azure OpenAI)** & **PlantUML**")

with st.container(border=True):
    st.markdown("##### Select Diagram Generation Mode")
    mode = st.pills("Select Diagram Generation Mode", ["From Text", "From Sketch"], default="From Text",  label_visibility="collapsed")

# Handle inputs for diagram generation from text descriptions
if mode == "From Text":
    if st.session_state.prev_mode != "From Text":
        cleanup()
    st.session_state.prev_mode = "From Text"
    st.markdown("### Generate Diagram from Ideas & Textual Descriptions")
    selected_sample_text = st.selectbox("Select Sample Text", options=[sample_text["display_text"] for sample_text in get_sample_texts()], index=None)
    if selected_sample_text:
        text_area_value = get_sample_texts(selected_sample_text)
    else:
        text_area_value = None
    text_area_value = st.text_area("Idea / Specification", placeholder="What do you wish to visualize?", height=200, value=text_area_value)
    if st.button("Generate Diagram", icon="✨", type="primary", use_container_width=True):
        if not text_area_value:
            st.error("Please enter an idea or select a sample text.")
        else:
            cleanup()
            messages = TEXT_TO_DIAGRAM.copy()
            messages.append({"role": "user", "content": text_area_value})
            with st.spinner("Hold tight! Your awesome diagram is brewing... ☕✨"):
                st.session_state.response = llm_client.send_message(messages)

# Handle inputs for diagram generation from sketches
if mode == "From Sketch":
    if st.session_state.prev_mode != "From Sketch":
        cleanup()
    st.session_state.prev_mode = "From Sketch"
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

# Process and display the response    
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
                st.download_button("Download as SVG", icon="💾", data=st.session_state.plantuml_svg[0], mime="image/svg+xml", type="primary", use_container_width=True)
            with col2:
                st.download_button("Download as PNG", icon="💾", data=st.session_state.plantuml_png[0], mime="image/png", use_container_width=True)

            with st.expander("🔍 View Explanation"):
                st.write(explanation)
            with st.expander("💻 PlantUML Syntax"):
                st.code(plantuml_syntax, language="plantuml")

                
            with st.expander("🔄 Want to see your diagram in a different format?"):
                st.markdown("Convert PlantUML Syntax to Another Diagram Language")
                conversion_option = st.selectbox("Select Diagramming Language", options=["Mermaid", "GraphViz", "D2"], index=None)
                if st.button("Convert Diagram", icon="🔄", type="primary", use_container_width=True):
                    if not conversion_option:
                        st.error("Please select a diagramming language.")
                    else:
                        conversion_messages = PLANTUML_TO_OTHER.copy()
                        conversion_messages.append({"role": "user", "content": json.dumps({"plantuml_syntax": plantuml_syntax, "target_language": conversion_option})})
                        with st.spinner("Converting the diagram... 🔄✨"):
                            conversion_response = llm_client.send_message(conversion_messages)
                            try:
                                st.markdown(f"**Converted Diagram Syntax ({conversion_option})**")
                                st.code(conversion_response, language=conversion_option.lower())
                            except Exception as e:
                                st.error(f"Conversion failed. Please try again.\nError: {e}")
            
except Exception as e:
    st.error(f"Oops! Something went wrong. Please try again.\nError: {e}")
