from crewai.tools import BaseTool


class ResumeMarkdownFileReadTool(BaseTool):
        name: str = "resume_markdown_file_read_tool"
        description: str = "Reads the contents of a resume stored in a markdown file, using the path provided (in UTF-8 format)."
        def _run(self, resume_file_path: str) -> str:
            with open(resume_file_path, 'r', encoding="utf-8") as f:
                resume_content = f.read()
            return resume_content
