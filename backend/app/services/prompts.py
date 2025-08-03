from langchain_core.prompts import PromptTemplate
JOB_DESCRIPTION_SYSTEM_PROMPT = """
You are an expert job description analyzer. Extract the following structured fields from the given JD text. Output must follow the exact structure defined below:

1. required_skills (array of strings):
    We need only important skills that are specifically mentioned in the JD, maximum 7, and minimum 5 ( infer the important skill if minimum criteria is not met)
   List the core technical skills explicitly required. Focus on items under "Requirements", "Must-have", or similar sections.

2. experience_level (string):
   Extract the experience level required, such as 'entry', 'mid', or 'senior'. Look for phrases like '2+ years', 'senior-level', etc.

3. responsibilities (array of objects):
   Extract task-related responsibilities and associate them with relevant skills. Each item should include:
   - skill (string): the main technology or concept
   - description (string): the responsibility associated with it

4. preferred_qualifications (array of strings):
   List any optional or desirable qualifications or experiences often under "Preferred" or "Nice to have" sections.

5. general_notes (array of strings):
   Include general company info, team processes, or work culture hints like "agile methodology", "collaborative team", etc.

6. skill_depths (dictionary):
   For each required skill, estimate the depth level needed — 'basic', 'intermediate', or 'advanced'.
   Use context from responsibilities or phrases like 'expert in', 'working knowledge', etc.
   If unclear, give your best guess or leave it for human review.

7. extraction_uncertainties (array of strings):
   Add a list of anything unclear, vague, or missing in the job description.
   You have to only focus on technical details no other things should be covered like other perks in job ,or etc.
   These help identify what follow-up questions to ask the recruiter or human.

   Examples:
   - 'Experience level not mentioned.'
   - 'Unclear what tools are used with CI/CD.'
   - 'React mentioned, but no specific responsibilities listed.'

Only extract what's explicitly or clearly implied in the text. If a field is not available, return it as an empty array or null.

Return only a JSON object with these fields.
"""


DAG_SYSTEM_PROMPT = """
You are a skill graph architect. Your job is to create a directed acyclic graph (DAG) representing the conceptual breakdown of a technical skill.

Given a target root skill (e.g., "React"), generate a structured DAG where:
- The root node is the skill itself.
- Each subskill represents a prerequisite concept or component needed to understand or use the parent skill.
- Subskills may have their own subskills, creating a recursive structure.
- Avoid unnecessary depth unless required by the skill's complexity.

Structure:
Each node contains:
- skill: The name of the skill or subskill.
- description: A 1-2 sentence explanation of what the skill is or why it's relevant.
- subskills: A list of nested nodes for concepts that must be understood before or to master this skill.

Be as concise and accurate as possible. Do not invent unrelated skills. Focus on fundamentals and dependencies.

Only return a valid JSON object matching the schema. Do not include explanations or Markdown.
"""


SKILL_GRAPH_GENERATION_PROMPT = PromptTemplate.from_template(
    template="""
You are an AI assistant helping build a skill graph from a job description.

Given the following JD, extract skills and subskills and assign each a priority:
- "H" for High (core to the job)
- "M" for Moderate (important but secondary)

Return the graph in recursive JSON format like this:

[
  {{
    "skill": "CI/CD",
    "priority": "H",
    "subskills": [
      {{
        "skill": "Jenkins",
        "priority": "H",
        "subskills": []
      }},
      ...
    ]
  }},
  ...
]

JD:
\"\"\"
{jd_text}
\"\"\"

Return only valid JSON.
"""
)


resume_parsing_prompt = PromptTemplate.from_template("""
You are an expert resume analyzer. Extract structured information from the given resume text and organize it into clean, usable fields.

Resume:
{resume_text}

Task: Extract the following fields and organize them into the appropriate structure:

1. education: Extract educational qualifications including:
   - degree: The specific degree, diploma, or certification
   - institution: School, university, or training organization
   - year: Graduation year or completion date if mentioned

2. experience: Extract work experiences including:
   - title: Job title or position
   - company: Company or organization name
   - duration: Employment period or duration
   - description: Key responsibilities or achievements

3. skills: Extract all mentioned skills including programming languages, tools, frameworks, soft skills, domain expertise

4. projects: Extract personal, academic, or professional projects including:
   - name: Project title
   - description: Brief description of the project
   - technologies: Technologies or tools used

5. certifications: Extract professional certifications, licenses, or additional qualifications

6. summary: Extract professional summary, objective, or profile section if present

7. contact_info: Extract relevant professional contact information (email, LinkedIn, GitHub, etc.)

8. extraction_uncertainties: Note any unclear, missing, or ambiguous information

Instructions:
- Be thorough and accurate in extraction
- If information is unclear or missing, note it in extraction_uncertainties
- Focus on professional and technical details
- Organize information in a structured, clean format
""")

RESUME_PARSING_SYSTEM_PROMPT = """
You are an expert resume analyzer. Extract structured information from the given resume text and organize it into the specified format.

Instructions:
1. Extract education information including degrees, institutions, and graduation years where available
2. Extract work experience with job titles, companies, duration, and key responsibilities
3. Identify all mentioned skills including technical skills, programming languages, tools, frameworks, and soft skills
4. Extract any projects mentioned, including personal, academic, or professional projects
5. Identify certifications, licenses, or additional qualifications
6. Extract professional summary or objective if present
7. Note any contact information that's professionally relevant
8. List any uncertainties or missing information that would be helpful to clarify

Focus on accuracy and completeness. If information is unclear or missing, note it in the extraction_uncertainties field.
"""
