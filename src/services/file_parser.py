import os
import pdfplumber
from docx import Document


class FileParser:
    """Service for parsing different file types to extract text content."""

    def __init__(self):
        self.text = ""
        self.links = []

    def load(self, file_path: str) -> None:
        """
        Load and parse a file based on its extension.

        Args:
            file_path: Path to the file to parse

        Raises:
            ValueError: If file format is not supported
        """
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()

        if file_extension == '.pdf':
            self._parse_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            self._parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

    def _parse_pdf(self, file_path: str) -> None:
        """Parse PDF file to extract text and links."""
        text = ''
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        self.text = text.strip()

    def _parse_docx(self, file_path: str) -> None:
        """Parse DOCX file to extract text and links."""
        doc = Document(file_path)
        self.text = ""
        self.links = []

        for para in doc.paragraphs:
            self.text += para.text + "\n"

        # Extract hyperlinks
        for rel in doc.part.rels.values():
            if "Hyperlink" in rel.reltype:
                self.links.append(rel._target)