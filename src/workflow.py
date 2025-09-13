from src.services.file_parser import FileParser
from src.graph.builder import create_workflow


class ResumeProcessingWorkflow:
    """Orchestrates the complete resume processing workflow."""

    def __init__(self):
        self.workflow = create_workflow()

    def process_resume(self, file_path):
        """
        Process a resume file through the complete workflow.

        Args:
            file_path: Path to the resume file

        Returns:
            The final state of the workflow
        """
        # Initialize state
        initial_state = {
            "input_file_path": file_path,
            "file_content": None,
            "file_links": None,
            "validation_result": None,
            "extraction_result": None,
            "error": None,
            "status": "initialized"
        }

        try:
            # Parse file
            initial_state["status"] = "parsing"
            parser = FileParser()
            parser.load(file_path)

            initial_state["file_content"] = parser.text
            initial_state["file_links"] = parser.links
            initial_state["status"] = "parsed"

            # Execute workflow
            final_state = self.workflow.invoke(initial_state)
            final_state["status"] = "completed"
            return final_state

        except Exception as e:
            initial_state["error"] = f"File processing failed: {str(e)}"
            initial_state["status"] = "failed"
            return initial_state