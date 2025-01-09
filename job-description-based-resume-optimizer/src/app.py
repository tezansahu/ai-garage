import streamlit as st
from resume_optimization_flow import ResumeOptimizationFlow
from utils import save_uploaded_resume_temp, read_file

st.set_page_config(
    page_icon="📄",
    page_title="Job Description Based Resume Optimizer", 
    layout="wide"
)

if "flow_successful" not in st.session_state:
    st.session_state.flow_successful = False
if "resume_md_original" not in st.session_state:
    st.session_state.resume_md_original = None
if "resume_md_optimized" not in st.session_state:
    st.session_state.resume_md_optimized = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "optimization_rationale" not in st.session_state:
    st.session_state.optimization_rationale = None


st.title("Job Description Based Resume Optimizer")

flow = ResumeOptimizationFlow()

job_description = st.text_area("Job Description", placeholder="Paste the job description here", height=300)
uploaded_file = st.file_uploader("Upload your Resume", type=["pdf", "docx"])

if st.button("Optimize Resume", icon="✨", type="primary", use_container_width=True):
    # st.session_state.flow_successful = False
    if not job_description:
        st.error("Please paste the job description.")
    if not uploaded_file:
        st.error("Please upload a resume.")
    if uploaded_file is not None and job_description:
        with st.spinner("Optimizing resume..."):
            resume_path = save_uploaded_resume_temp(uploaded_file)
            st.toast("Resume optimizer flow initialized")
            flow.state.resume_path = resume_path
            flow.state.job_description = job_description
            try:
                flow.kickoff()
                st.toast("Resume optimized successfully")
                st.session_state.flow_successful = True
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.session_state.flow_successful = False
        
if st.session_state.flow_successful:
    st.session_state.resume_md_original = read_file(flow.state.resume_markdown_path)
    st.session_state.resume_md_optimized = flow.state.resume_optimization_result.resume_content
    st.session_state.analysis_results = flow.state.resume_analysis_result
    st.session_state.optimization_rationale = flow.state.resume_optimization_result.optimization_rationale
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original Resume")
        with st.container(border=True, height=800):
            st.write(st.session_state.resume_md_original)
        
        with st.container(border=True):
            st.subheader("Resume Analysis")
            st.write(f"**Overall Resume Score:** {st.session_state.analysis_results.score}")
            with st.expander("Strengths"):
                for strength in st.session_state.analysis_results.strengths:
                    st.write(f"- {strength}")
            with st.expander("Areas of Improvement"):
                for area in st.session_state.analysis_results.areas_of_improvement:
                    st.write(f"- {area}")
            with st.expander("Recommendations"):
                for recommendation in st.session_state.analysis_results.recommendations:
                    st.write(f"- {recommendation}")
    
    with col2:
        st.subheader("Optimized Resume")
        with st.container(border=True, height=800):
            st.write(st.session_state.resume_md_optimized)

        st.download_button(
            label="Download Optimized Resume",
            data=st.session_state.resume_md_optimized,
            file_name="optimized_resume.md",
            mime="text/markdown",
            use_container_width=True
        )

        with st.expander("Optimization Rationale"):
            st.info(st.session_state.optimization_rationale)       