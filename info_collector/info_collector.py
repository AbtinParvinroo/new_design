from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json

class InfoCollector:
    def __init__(self):
        model_name = "nimendraai/NuExtract-tiny-Resume-Data-Extractor"
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=torch.bfloat16, trust_remote_code=True
        ).eval().cuda()

        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.TEMPLATE = json.dumps(
            {
            "personal_information": {
                "name": None,
                "email": None,
                "phone": None,
                "website": None,
                "location": None
            },
            "experience": [
                {
                "type": "work",
                "company": None,
                "title": None,
                "duration_months": None,
                "description": None,
                "responsibilities": [],
                "achievements": [],
                "technologies": []
                }
            ],
            "education": [
                {
                "institution": None,
                "degree": None,
                "field": None,
                "duration_months": None,
                "achievements": []
                }
            ],
            "projects": [
                {
                "name": None,
                "description": None,
                "duration_months": None,
                "technologies": [],
                "achievements": []
                }
            ],
            "skills": [
                {
                "name": None,
                }
            ],
            "certificates": [
                {
                "name": None,
                "issuer": None,
                "date": None,
                "description": None
                }
            ]
            }, indent=4)

    def extract_first_json(self, text):
        depth, start = 0, None
        for i, ch in enumerate(text):
            if ch == "{":
                if start is None: start = i
                depth += 1

            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start:i+1]

        return text

    def extract(self, resume_text: str) -> dict:
        prompt = (
            f"""
            You are a structured resume information extraction system.
            Your task is to extract factual information from the provided resume text and return exactly one valid JSON object following the provided extraction template.
            Your task is EXTRACTION ONLY.
            Do not evaluate the candidate.
            Do not score the candidate.
            Do not classify the candidate.
            Do not rank the candidate.
            Do not calculate career metrics.
            Do not generate recommendations.
            Do not infer unsupported information.
            Do not invent missing information.
            The resume text is the only source of truth.
            GENERAL RULES:
            1. Return exactly one JSON object.
            2. Return valid JSON only.
            3. Do not return Markdown.
            4. Do not return explanations.
            5. Do not return text before or after the JSON object.
            6. Follow the provided template exactly.
            7. Preserve factual information from the resume.
            8. If a scalar value cannot be determined reliably, return null.
            9. If a list has no items, return an empty list.
            10. Never fabricate information.
            11. Do not duplicate information unless it is explicitly presented in multiple contexts.
            12. Preserve names, company names, job titles, institutions, technologies, skills, and certifications as they appear in the source whenever possible.
            PERSONAL INFORMATION:
            Extract the following information when explicitly available:
            - name
            - email
            - phone
            - website
            - location
            Do not infer location from:
            - phone country code
            - email domain
            - company location
            - university location
            EXPERIENCE:
            Extract professional employment and internships.
            Each experience must contain:
            - type
            - company
            - title
            - duration_months
            - description
            - responsibilities
            - achievements
            - technologies
            TYPE:
            Use only:
            - "work"
            - "internship"
            Use "internship" only when the resume explicitly identifies the position as an internship.
            Use "work" for regular professional employment.
            Do not invent an employment type when the source is ambiguous.
            TITLE:
            Extract the original job title from the resume.
            Do not replace the title with a standardized title.
            Do not create a canonical job title.
            Do not assign a category.
            Do not assign a seniority level.
            Do not modify the title based on assumptions.
            Examples:
            "Senior Data Engineer" → "Senior Data Engineer"
            "Sr. Software Engineer" → "Sr. Software Engineer"
            "Data Engineering Intern" → "Data Engineering Intern"
            The original title will be normalized later by a deterministic mapping system.
            COMPANY:
            Extract the employer or organization associated with the experience.
            Preserve the company name as written in the resume.
            Do not infer the company when it is not explicitly identified.
            DURATION:
            Extract the duration of the experience in months.
            Examples:
            "2 years" → 24
            "2 years and 6 months" → 30
            "18 months" → 18
            "6 months" → 6
            If a clear start and end period is provided, calculate the duration in months.
            If the duration cannot be determined reliably, return null.
            Do not guess duration.
            Do not estimate duration from unrelated information.
            Do not use the current date to calculate an unspecified duration.
            If the resume explicitly states "Present" or "Current" and a reliable start date is available, calculate the duration only when the duration can be determined from the available information.
            DESCRIPTION:
            Extract the general description of the role when explicitly provided.
            Do not generate a description from the job title.
            RESPONSIBILITIES:
            Extract explicit responsibilities as separate list items.
            Do not convert responsibilities into achievements.
            Do not create responsibilities that are not supported by the resume.
            ACHIEVEMENTS:
            Extract explicit accomplishments, measurable results, awards, improvements, or outcomes.
            Do not transform ordinary responsibilities into achievements.
            Do not invent metrics or results.
            TECHNOLOGIES:
            Extract technologies, programming languages, frameworks, libraries, platforms, databases, tools, and technical systems explicitly associated with the experience.
            Do not infer technologies that are not mentioned.
            EDUCATION:
            Extract formal education.
            Each education item must contain:
            - institution
            - degree
            - field
            - duration_months
            - achievements
            Extract only information supported by the resume.
            Do not infer a degree type or field when it is not explicitly supported.
            If a clear education period is provided, calculate duration in months.
            If duration cannot be determined reliably, return null.
            PROJECTS:
            Extract explicitly identified projects.
            Each project must contain:
            - name
            - description
            - duration_months
            - technologies
            - achievements
            Only extract items that are actually presented as projects.
            Do not convert ordinary job responsibilities into projects.
            Do not invent project names.
            SKILLS:
            Extract explicitly stated skills.
            Each skill must contain only:
            - name
            Do not classify skills into categories.
            Do not infer skill proficiency.
            Do not assign skill levels.
            Do not generate skills from technologies unless the resume explicitly presents them as skills or clearly identifies them as part of the candidate's skill set.
            CERTIFICATES:
            Extract explicitly mentioned certifications.
            Each certificate must contain:
            - name
            - issuer
            - date
            - description
            Do not treat academic degrees as certificates.
            Do not invent certificate dates or issuers.
            NORMALIZATION:
            Perform only minimal normalization required for clean extraction.
            Do not perform semantic classification.
            Do not replace a job title with another job title.
            Do not map aliases to canonical job titles.
            Do not assign categories.
            Do not assign seniority levels.
            Do not infer career roles.
            The downstream system will perform deterministic normalization using an external JSON mapping.
            SOURCE OF TRUTH:
            When information is ambiguous:
            1. Prefer explicit information.
            2. Preserve the original wording when possible.
            3. Use null when reliable extraction is impossible.
            4. Never guess.
            IMPORTANT SEPARATION OF RESPONSIBILITIES:
            The language model performs:
            - factual extraction
            - limited normalization
            - duration extraction/calculation
            - structural organization
            The downstream deterministic system performs:
            - canonical job-title mapping
            - job category mapping
            - seniority/level mapping
            - role normalization
            - metric calculation
            - career scoring
            - career interpretation
            Never perform these downstream operations yourself.
            OUTPUT TEMPLATE:
            {
            "personal_information": {
            "name": null,
            "email": null,
            "phone": null,
            "website": null,
            "location": null
            },
            "experience": [
            {
            "type": "work",
            "company": null,
            "title": null,
            "duration_months": null,
            "description": null,
            "responsibilities": [],
            "achievements": [],
            "technologies": []
            }
            ],
            "education": [
            {
            "institution": null,
            "degree": null,
            "field": null,
            "duration_months": null,
            "achievements": []
            }
            ],
            "projects": [
            {
            "name": null,
            "description": null,
            "duration_months": null,
            "technologies": [],
            "achievements": []
            }
            ],
            "skills": [
            {
            "name": null
            }
            ],
            "certificates": [
            {
            "name": null,
            "issuer": null,
            "date": null,
            "description": null
            }
            ]
            }
            Now extract the information from the provided resume text.
            Return only the JSON object.
            {resume_text}
            """
        )

        inputs = self.tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=2048
        ).to(self.model.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs, max_new_tokens=512, do_sample=False
            )

        decoded = self.tokenizer.decode(out[0], skip_special_tokens=True)
        raw = decoded.split("<|output|>")[-1].strip()
        return json.loads(self.extract_first_json(raw))