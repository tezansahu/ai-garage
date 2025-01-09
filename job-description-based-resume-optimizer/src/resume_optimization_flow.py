import os
import json
from pathlib import Path

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel
from markitdown import MarkItDown

from resume_optimizer_crew.crew import ResumeAnalyzerCrew, ResumeOptimizerCrew
from resume_optimizer_crew.types import OptimizedResume, ResumeAnalyis

class ResumeOptimizationState(BaseModel):
    job_description: str = ""
    resume_path: Path = "sample_resume/"
    resume_markdown_path: Path = "sample_resume/"
    resume_analysis_result: ResumeAnalyis = None
    resume_optimization_result: OptimizedResume = None


class ResumeOptimizationFlow(Flow[ResumeOptimizationState]):
    def __init__(self):
        super().__init__()
        self.md_converter = MarkItDown()


    @start()
    def convert_resume_to_markdown(self):
        print("Converting resume to markdown")
        if os.path.exists(self.state.resume_path):
            result = self.md_converter.convert(self.state.resume_path)

            file_name = os.path.splitext(os.path.basename(self.state.resume_path))[0]
            
            os.makedirs(f"temp/{file_name}", exist_ok=True)

            self.state.resume_markdown_path = f"temp/{file_name}/resume_original.md"

            with open(self.state.resume_markdown_path, "w", encoding="utf-8") as f:
                f.write(result.text_content)
            print("Resume converted to markdown\n")
        else:
            print("Resume path does not exist")
    
    @listen(convert_resume_to_markdown)
    def resume_analysis(self):
        print("Analyzing resume")
        resume_analysis_result = ResumeAnalyzerCrew().crew().kickoff(
            inputs = {
                "resume_path": self.state.resume_markdown_path
            }
        )
        print("Resume analysis complete\n")
        self.state.resume_analysis_result = resume_analysis_result.pydantic

    @listen(resume_analysis)
    def save_resume_analysis(self):
        print("Saving resume analysis")
        file_name = os.path.splitext(os.path.basename(self.state.resume_path))[0]
        analysis_path = f"temp/{file_name}/resume_analysis.json"
        with open(analysis_path, "w") as f:
            json.dump(self.state.resume_analysis_result.model_dump(), f, indent=4)
        print(f"Resume analysis saved at {analysis_path}\n")

    @listen(resume_analysis)
    def optimize_resume(self):
        print("Optimizing resume")
        resume_optimization_result = ResumeOptimizerCrew().crew().kickoff(
            inputs = {
                "resume_path": self.state.resume_markdown_path,
                "job_description": self.state.job_description,
                "recommendations": "- " + "\n- ".join(self.state.resume_analysis_result.recommendations)
            }
        )
        print("Resume optimization complete\n")
        self.state.resume_optimization_result = resume_optimization_result.pydantic

    @listen(optimize_resume)
    def save_optimized_resume(self):
        print("Saving optimized resume")
        file_name = os.path.splitext(os.path.basename(self.state.resume_path))[0]
        optimized_resume_path = f"temp/{file_name}/resume_optimized.md"
        with open(optimized_resume_path, "w", encoding="utf-8") as f:
            f.write(self.state.resume_optimization_result.resume_content)
        print(f"Aligned resume saved at {optimized_resume_path}\n")


def kickoff(resume_path: Path, job_description: str):
    """
    Run the flow.
    """
    resume_optimization_flow = ResumeOptimizationFlow()
    resume_optimization_flow.state.resume_path = resume_path
    resume_optimization_flow.state.job_description = job_description

    resume_optimization_flow.kickoff()


def plot_flow():
    """
    Plot the flow.
    """
    resume_optimization_flow = ResumeOptimizationFlow()
    resume_optimization_flow.plot()