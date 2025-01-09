import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from resume_optimizer_crew.types import JobDescriptionAnalysis, OptimizedResume, ResumeAnalyis
from resume_optimizer_crew.tools.resume_optimization_tools import ResumeMarkdownFileReadTool

load_dotenv()

azure_llm = LLM(
	model=os.getenv("AZURE_MODEL"),
	base_url=os.getenv("AZURE_API_BASE"),
	api_key=os.getenv("AZURE_API_KEY"),
	api_version=os.getenv("AZURE_API_VERSION")
)


###############################################
# Agent crew to analyze the standalone resume #
###############################################
@CrewBase
class ResumeAnalyzerCrew():
	"""Resume Analyzer crew"""
	agents_config = 'config/agents_resume_analysis.yaml'
	tasks_config = 'config/tasks_resume_analysis.yaml'

	@agent
	def resume_analyzer(self) -> Agent:
		return Agent(
			config=self.agents_config['resume_analyzer'],
			tools=[ResumeMarkdownFileReadTool()],
			llm=azure_llm,
			verbose=False
		)

	@task
	def analyze_resume(self) -> Task:
		return Task(
			config=self.tasks_config["analyze_resume"],
			output_pydantic=ResumeAnalyis
		)

	@crew
	def crew(self) -> Crew:
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			verbose=False,
		)

##################################################################
# Agent crew to optimize the resume based on the job description #
##################################################################
@CrewBase
class ResumeOptimizerCrew():
	"""Resume Optimizer crew"""
	agents_config = 'config/agents_resume_optimization.yaml'
	tasks_config = 'config/tasks_resume_optimization.yaml'

	@agent
	def job_description_analyzer(self) -> Agent:
		return Agent(
			config=self.agents_config['job_description_analyzer'],
			llm=azure_llm,
			verbose=False
		)

	@agent
	def alignment_specialist(self) -> Agent:
		return Agent(
			config=self.agents_config['alignment_specialist'],
			tools=[ResumeMarkdownFileReadTool()],
			llm=azure_llm,
			verbose=False
		)

	@task
	def analyze_job_description(self) -> Task:
		return Task(
			config=self.tasks_config["analyze_job_description"],
			output_pydantic=JobDescriptionAnalysis
		)

	@task
	def fine_tune_resume(self) -> Task:
		return Task(
			config=self.tasks_config["fine_tune_resume"],
			output_pydantic=OptimizedResume
		)

	@crew
	def crew(self) -> Crew:
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			verbose=False,
		)
