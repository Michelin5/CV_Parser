from llmclient import call_qwen
import json
from typing import Dict, Any, Optional


def agent0_validator(cv_text: str) -> Optional[Dict[str, Any]]:
    """
    Validates if the provided text is a resume/CV.

    Args:
        cv_text: Text to validate

    Returns:
        Validation result as dictionary or None if error
    """
    system_prompt = """
    You are an accuracy-focused classifier whose single task is: decide whether the provided text is a Resume / CV.

    Rules & behaviour:
    - Use ONLY the content provided. Do NOT invent facts or guess details not present.
    - Look for common resume/CV signals: candidate name/header, contact info (email, phone, LinkedIn/URL), sections titled Experience/Work History, Education, Skills, Publications, Projects, Certifications, Dates/years (e.g., 2018–2023), job titles, company/institution names, bullet lists describing responsibilities/results, and clear chronological entries.
    - Heuristics (use to compute confidence):
      • Strong signals: contact info + (Experience or Education) + explicit job titles or company names.
      • Medium signals: Skills, Projects, Certifications, multiple dated entries.
      • Weak signals: single paragraph mentioning work/education without structure.
      • Negative signals: short chat, job description, cover letter greeting, generic biography, web page unrelated to an individual CV.
    - If ambiguous, favour safe behaviour: set is_resume=false and suggested_action="ask_for_more".

    Output (MUST be valid JSON only — no extra text):
    {
      "is_resume": true|false,
      "primary_format": "resume"|"cv"|"other",
      "confidence": 0.00-1.00,           // float, calibrated from heuristics above
      "explain": "one-sentence summary justification (max 20 words)",
      "evidence": [                      // up to 6 short excerpts (<=120 chars) each with a 3-6 word reason
        {"text_excerpt":"...","reason":"contains email"},
        ...
      ],
      "suggested_action":"proceed"|"ask_for_more"|"reject",
      "excerpt": "single short (<=200 chars) representative snippet from input"
    }

    Formatting constraints:
    - Return JSON only (no code fences, no commentary).
    - Keep explain concise. Each evidence item must be verbatim substring from the input.
    - Confidence must reflect heuristics (e.g., 0.85 for strong match, <=0.5 for weak/ambiguous).
    - Do not output internal chain-of-thought or step-by-step reasoning.

    Quick examples:
    Input snippet: "John Doe\njohn@example.com\nExperience\nSoftware Engineer, Acme Corp 2019-2024\nSkills: Python, SQL"
    -> is_resume: true, high confidence, evidence includes email + Experience + dated job line.

    Input snippet: "Company privacy policy: We collect data to..."
    -> is_resume: false, low confidence, suggested_action: reject.

    Now inspect the user's message and produce the JSON described above.
    """

    response = call_qwen(user_prompt=cv_text, system_instruction=system_prompt)

    try:
        clean_response = response.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:-3].strip()
        elif clean_response.startswith('```'):
            clean_response = clean_response[3:-3].strip()

        return json.loads(clean_response)
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse LLM response as JSON",
            "raw_response": response
        }
    except Exception as e:
        return {
            "error": f"Validation failed: {str(e)}",
            "raw_response": response
        }


def agent1_extractor(cv_text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts structured data from a resume/CV.

    Args:
        cv_text: Text of the resume to extract from

    Returns:
        Extracted data as dictionary or None if error
    """
    system_prompt = """
    You are a specialist Resume/CV extraction agent. Input: a resume or CV as plain text (or OCR text). Output: a single machine-parsable JSON object and nothing else.

    OUTPUT RULES
    - Return ONLY valid JSON (no prose, no Markdown, no explanations).
    - The top-level object MUST contain these keys exactly and in any order:
      full_name, email, education, employment_details, projects, publications,
      technical_skills, programming_languages, languages, soft_skills, additional_information
    - If a section is not found, set its value to null (do NOT return empty strings/arrays for missing sections).
    - Do NOT add any extra keys.

    SCHEMA (types)
    {
      "full_name": string | null,
      "email": string | null,
      "education": [ { "degree": string | null, "field": string | null, "institution": string | null,
                       "start_date": "YYYY-MM" | "YYYY" | null, "end_date": "YYYY-MM" | "YYYY" | "present" | null,
                       "grade": string | null } , ... ] | null,
      "employment_details": [ { "title": string | null, "company": string | null,
                               "start_date": "YYYY-MM" | "YYYY" | null, "end_date": "YYYY-MM" | "YYYY" | "present" | null,
                               "location": string | null, "description": string | null } , ... ] | null,
      "projects": [ { "title": string | null, "description": string | null, "technologies": [string,...] | null, "period": string | null } , ... ] | null,
      "publications": [ { "title": string | null, "venue": string | null, "year": "YYYY" | null, "authors": [string,...] | null, "link": string | null } , ... ] | null,
      "technical_skills": [ { "category": string | null, "skills": [string,...] } , ... ] | null,
      "programming_languages": [ { "language": string, "proficiency": string | null } , ... ] | null,
      "languages": [ { "language": string, "proficiency": string | null } , ... ] | null,
      "soft_skills": [ string, ... ] | null,
      "additional_information": string | null
    }

    NORMALIZATION & BEHAVIOR
    - Dates: normalize to "YYYY-MM" when month known, otherwise "YYYY". Use "present" for ongoing roles.
    - Degrees: normalize common abbreviations when obvious (e.g., "BSc" -> "Bachelor of Science"); if uncertain, return the original short form.
    - Email: accept only valid email format; otherwise set email to null.
    - Deduplicate equivalent skills and standardize common category names (e.g., "Databases", "Cloud", "Frameworks"); if unsure, set category to null.
    - Condense multi-line descriptions to 1–2 concise sentences.
    - Do NOT hallucinate or invent details. If you cannot confidently extract a field, return null for that field or section.
    - If multiple plausible candidates exist (e.g., multiple names), choose the most likely as the value. If ambiguity prevents a safe choice, return null.

    EXAMPLE (minimal)
    {
      "full_name":"Jane Doe",
      "email":"jane@example.com",
      "education":null,
      "employment_details":null,
      "projects":null,
      "publications":null,
      "technical_skills":null,
      "programming_languages":null,
      "languages":null,
      "soft_skills":null,
      "additional_information":null
    }

    Process the provided resume text and return the JSON (no Markdown-formatting) exactly following these rules.
    """

    response = call_qwen(user_prompt=cv_text, system_instruction=system_prompt)

    try:
        clean_response = response.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:-3].strip()
        elif clean_response.startswith('```'):
            clean_response = clean_response[3:-3].strip()

        return json.loads(clean_response)
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse LLM response as JSON",
            "raw_response": response
        }
    except Exception as e:
        return {
            "error": f"Extraction failed: {str(e)}",
            "raw_response": response
        }