# Job Description-Based Resume Optimizer - Agentic Workflow (using CrewAI)

The Job Description-Based Resume Optimizer is an innovative project designed to help job seekers tailor their resumes to specific job descriptions using advanced AI techniques. 

By leveraging a agentic workflows comprising multi-agent system, powered by CrewAI, this project ensures that resumes are optimized for Applicant Tracking Systems (ATS) and aligned with job requirements, enhancing the chances of landing an interview.

## Features

- **Detailed Analysis:** Provides a thorough analysis of both the resume and the job description to identify strengths, weaknesses, and areas for improvement.
- **ATS Optimization:** Ensures that resumes are optimized for Applicant Tracking Systems by incorporating relevant keywords and phrases.

## CrewAI Flow for Resume Optimization

This is what the overall workflow looks like:

![](./assets/resume-optimizer-crewai-flow.png)


This workflow involves CrewAI agents in 2 steps:

- **Resume Analysis:** Using `resume_analyzer` agent
- **Optimize Resume:** Using `job_description_analyzer` & `alignment_specialist` agents

The detailed implementation can currently be found in the [`analysis.ipynb` Notebook](./analysis.ipynb)

## GUI Tool

Coming Soon...

