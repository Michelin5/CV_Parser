from typing import TypedDict, List, Optional, Dict, Any, Literal

class EducationEntry(TypedDict):
    degree: Optional[str]
    field: Optional[str]
    institution: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    grade: Optional[str]

class EmploymentDetail(TypedDict):
    title: Optional[str]
    company: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    location: Optional[str]
    description: Optional[str]

class Project(TypedDict):
    title: Optional[str]
    description: Optional[str]
    technologies: Optional[List[str]]
    period: Optional[str]

class Publication(TypedDict):
    title: Optional[str]
    venue: Optional[str]
    year: Optional[str]
    authors: Optional[List[str]]
    link: Optional[str]

class TechnicalSkill(TypedDict):
    category: Optional[str]
    skills: List[str]

class ProgrammingLanguage(TypedDict):
    language: str
    proficiency: Optional[str]

class LanguageSkill(TypedDict):
    language: str
    proficiency: Optional[str]

class ResumeValidationResult(TypedDict):
    is_resume: bool
    primary_format: Literal["resume", "cv", "other"]
    confidence: float
    explain: str
    evidence: List[Dict[str, str]]
    suggested_action: Literal["proceed", "ask_for_more", "reject"]
    excerpt: str

class ExtractedResumeData(TypedDict):
    full_name: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    education: Optional[List[EducationEntry]]
    employment_details: Optional[List[EmploymentDetail]]
    projects: Optional[List[Project]]
    publications: Optional[List[Publication]]
    technical_skills: Optional[List[TechnicalSkill]]
    programming_languages: Optional[List[ProgrammingLanguage]]
    soft_skills: Optional[List[str]]
    languages: Optional[List[LanguageSkill]]
    additional_information: Optional[str]

class AgentState(TypedDict):
    input_file_path: Optional[str]
    file_content: Optional[str]
    file_links: Optional[List[str]]
    validation_result: Optional[ResumeValidationResult]
    extraction_result: Optional[ExtractedResumeData]
    summary: Optional[str]
    error: Optional[str]
    status: Literal["initialized", "parsing", "validating", "extracting", "completed", "failed"]