# AI Interview & Assessment System

An intelligent interview and skill assessment system powered by CrewAI that evaluates candidates based on their resume, GitHub profile, and interview responses. The system provides detailed skill assessments with percentage scores, identifies strengths and weaknesses, generates personalized course recommendations, and suggests suitable job opportunities.

## Features

- **Profile Analysis**: Analyzes resumes (PDF/DOCX) and GitHub profiles to extract skills and experience
- **AI-Powered Interviews**: Generates contextual interview questions based on candidate profile and target role
- **Skill Assessment**: Evaluates responses and provides percentage-based skill scores
- **Strengths & Weaknesses**: Identifies specific strengths and areas for improvement
- **Course Recommendations**: Generates personalized learning paths to address skill gaps
- **Job Recommendations**: Suggests relevant job opportunities based on assessment results
- **Career Path Suggestions**: Provides career progression recommendations

## Architecture

The system uses CrewAI with two specialized crews that work sequentially:

### ProfileAnalysisCrew
This crew is dedicated to analyzing candidate profiles and extracting comprehensive context:

1. **Resume Extractor**: Extracts technical information, skills, experience, and achievements from resume text
2. **GitHub Profile Analyst**: Analyzes GitHub profiles to extract technical skills, project experience, and code quality indicators
3. **Technical Domain Classifier**: Classifies the candidate's primary technical domain and identifies secondary domains
4. **Profile Synthesizer**: Synthesizes all profile information into a comprehensive candidate profile context

**Output**: Domain classification, extracted skills, technical strengths, potential weaknesses, and interview readiness assessment

### InterviewCrew
This crew focuses on conducting interviews and identifying strong/weak areas:

1. **Domain-Specific Technical Interviewer**: Generates targeted interview questions based on the candidate's domain and profile context
2. **Technical Response Evaluator**: Evaluates interview responses to determine skill proficiency
3. **Strength and Weakness Analyzer**: Analyzes interview performance to identify specific strong and weak areas with detailed explanations
4. **Skill Proficiency Assessor**: Provides detailed skill assessments with percentage scores based on interview performance

**Output**: Domain-specific interview questions, strong areas with evidence, weak areas with improvement suggestions, percentage-based skill assessments

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Project
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Unix
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
GITHUB_TOKEN=your_github_token_here
JOB_API_KEY=your_job_api_key_here
```

## Usage

### Start the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Analyze Profile
```http
POST /api/v1/profile/analyze
Content-Type: multipart/form-data

name: string
email: string
target_role: string
experience_years: float
github_url: string (optional)
additional_info: string (optional)
resume: file (optional)
skills: JSON array (optional)
```

#### 2. Generate Interview Questions
```http
POST /api/v1/interview/questions
Content-Type: multipart/form-data

name: string
email: string
target_role: string
experience_years: float
github_url: string (optional)
additional_info: string (optional)
resume: file (optional)
skills: JSON array (optional)
num_questions: integer (default: 10)
```

#### 3. Evaluate Interview Responses
```http
POST /api/v1/interview/evaluate
Content-Type: multipart/form-data

name: string
email: string
target_role: string
experience_years: float
github_url: string (optional)
additional_info: string (optional)
resume: file (optional)
skills: JSON array (optional)
responses: JSON array of interview responses
```

Response format:
```json
{
  "question": "string",
  "answer": "string",
  "confidence": 1-10
}
```

#### 4. Get Job Recommendations
```http
POST /api/v1/jobs/recommend
Content-Type: application/json

{
  "interview_result": { ... },
  "location": string (optional),
  "limit": integer (default: 5)
}
```

#### 5. Complete Assessment (End-to-End)
```http
POST /api/v1/assessment/complete
Content-Type: multipart/form-data

name: string
email: string
target_role: string
experience_years: float
github_url: string (optional)
additional_info: string (optional)
resume: file (optional)
skills: JSON array (optional)
responses: JSON array of interview responses
location: string (optional)
job_limit: integer (default: 5)
```

## Example Workflow

1. **Submit Candidate Profile**
   - Upload resume or provide GitHub URL
   - Specify target role (e.g., "Backend Engineer")
   - System analyzes profile and extracts skills

2. **Generate Interview Questions**
   - System generates 10 contextual questions
   - Questions vary by difficulty (easy, medium, hard)
   - Questions cover relevant technical areas

3. **Conduct Interview**
   - Candidate responds to questions
   - Each response includes confidence level (1-10)

4. **Get Assessment Results**
   - Overall score (0-100)
   - Skill assessments with percentages
   - Strengths and weaknesses
   - Course recommendations
   - Job suggestions

5. **Career Guidance**
   - Personalized learning paths
   - Career progression suggestions
   - Job matching based on skills

## Skill Assessment Levels

- **Expert** (90-100%): Mastery with deep understanding
- **Advanced** (75-89%): Strong proficiency with experience
- **Intermediate** (60-74%): Good working knowledge
- **Beginner** (40-59%): Basic understanding
- **Novice** (0-39%): Limited or no experience

## Project Structure

```
Project/
├── main.py                    # FastAPI application with API endpoints
├── profile_analysis_crew.py   # CrewAI crew for profile analysis (resume, GitHub, domain classification)
├── interview_crew.py          # CrewAI crew for interview generation and evaluation
├── interview_system.py        # Orchestrates the two crews and manages workflow
├── profile_analyzer.py       # Resume text extraction and GitHub API integration
├── job_service.py             # Job recommendation service
├── models.py                  # Pydantic data models
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── example_usage.py          # Example usage script
├── test_setup.py             # Setup verification script
├── README.md                 # This file
└── uploads/                  # Directory for uploaded resumes
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

### OpenAI API
Required for CrewAI agents. Get your API key from [OpenAI](https://platform.openai.com/api-keys).

### GitHub Token (Optional)
Required for GitHub profile analysis. Create a personal access token at [GitHub Settings](https://github.com/settings/tokens).

### Job API Key (Optional)
For real job recommendations. Currently supports mock recommendations without API key.

## Development

### Running Tests
```bash
pytest tests/
```

### Adding New Agents
Edit `agents.py` to add new CrewAI agents with specific roles and goals.

### Customizing Job Sources
Modify `job_service.py` to integrate with different job board APIs (Adzuna, Indeed, Reed, etc.).

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
