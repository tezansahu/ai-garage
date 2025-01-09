from pydantic import BaseModel

###################################################
# Pydantic models for the Output of AGentic Tasks #
###################################################
class ResumeAnalyis(BaseModel):
    strengths: list[str]
    areas_of_improvement: list[str]
    recommendations: list[str]
    score: int

class JobDescriptionAnalysis(BaseModel):
    objectives_and_expectations: list[str]
    core_competencies: list[str]
    ats_friendly_keywords: list[str]

class OptimizedResume(BaseModel):
    resume_content: str
    optimization_rationale: str