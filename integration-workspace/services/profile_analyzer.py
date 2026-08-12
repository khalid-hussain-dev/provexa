import pdfplumber
import docx
from github import Github
from typing import Dict, List, Optional
import re
from config import settings


class ProfileAnalyzer:
    def __init__(self):
        self.github_token = settings.GITHUB_TOKEN
        
    def extract_resume_text(self, file_path: str) -> str:
        """Extract text from resume file (PDF or DOCX)"""
        if file_path.endswith('.pdf'):
            return self._extract_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            return self._extract_from_docx(file_path)
        else:
            return file_path  # Assume it's already text
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return ""
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            print(f"Error extracting DOCX: {e}")
            return ""
    
    def analyze_github_profile(self, github_url: str) -> Dict:
        """Analyze GitHub profile to extract skills and experience"""
        if not self.github_token:
            return {"error": "GitHub token not provided"}
        
        try:
            # Extract username from URL
            username = github_url.rstrip('/').split('/')[-1]
            g = Github(self.github_token)
            user = g.get_user(username)
            
            repos = list(user.get_repos())
            
            # Extract languages used
            languages = {}
            for repo in repos:
                try:
                    repo_languages = repo.get_languages()
                    for lang, bytes_count in repo_languages.items():
                        try:
                            b_val = int(bytes_count)
                        except (ValueError, TypeError):
                            b_val = 0
                        languages[lang] = int(languages.get(lang, 0)) + b_val
                except Exception:
                    continue
            
            # Get total stars and forks
            total_stars = sum(repo.stargazers_count for repo in repos)
            total_forks = sum(repo.forks_count for repo in repos)
            
            return {
                "username": user.login,
                "bio": user.bio,
                "public_repos": user.public_repos,
                "followers": user.followers,
                "following": user.following,
                "total_stars": total_stars,
                "total_forks": total_forks,
                "languages": dict(sorted(languages.items(), key=lambda x: x[1], reverse=True)),
                "recent_repos": [
                    {
                        "name": repo.name,
                        "description": repo.description,
                        "language": repo.language,
                        "stars": repo.stargazers_count,
                        "forks": repo.forks_count
                    }
                    for repo in repos[:10]
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_web_profile(self, url: str) -> Dict:
        """Analyze a web profile (LinkedIn or Personal Website/Portfolio) by extracting metadata/text."""
        if not url:
            return {}
        try:
            import httpx
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            with httpx.Client(timeout=8.0, follow_redirects=True, headers=headers) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    text = resp.text[:4000]
                    # Strip basic HTML tags
                    clean_text = re.sub(r'<[^>]+>', ' ', text)
                    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                    skills = self.extract_skills_from_text(clean_text)
                    return {
                        "url": url,
                        "extracted_text_snippet": clean_text[:500],
                        "inferred_skills": skills
                    }
        except Exception as e:
            pass
        return {"url": url, "inferred_skills": []}

    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract technical skills from resume text"""
        # Common programming languages and technologies
        tech_keywords = [
            'python', 'javascript', 'java', 'c++', 'c#', 'ruby', 'go', 'rust', 'swift',
            'react', 'angular', 'vue', 'nodejs', 'django', 'flask', 'spring', 'express',
            'sql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform', 'ansible',
            'git', 'ci/cd', 'jenkins', 'github', 'gitlab', 'jira',
            'machine learning', 'deep learning', 'nlp', 'data science', 'tensorflow',
            'pytorch', 'pandas', 'numpy', 'spark', 'hadoop', 'kafka',
            'microservices', 'rest api', 'graphql', 'grpc', 'websocket',
            'agile', 'scrum', 'devops', 'testing', 'tdd', 'bdd'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for keyword in tech_keywords:
            if keyword in text_lower:
                found_skills.append(keyword)
        
        return list(set(found_skills))
    
    def create_profile_summary(self, candidate_data: Dict) -> str:
        """Create a comprehensive profile summary for CrewAI"""
        summary_parts = []
        
        summary_parts.append(f"Candidate Name: {candidate_data.get('name', 'Unknown')}")
        summary_parts.append(f"Target Role: {candidate_data.get('target_role', 'Unknown')}")
        summary_parts.append(f"Experience: {candidate_data.get('experience_years', 0)} years")
        
        if candidate_data.get('resume_text'):
            summary_parts.append(f"\nResume Content:\n{candidate_data['resume_text']}")
        
        if candidate_data.get('github_analysis'):
            github = candidate_data['github_analysis']
            summary_parts.append(f"\nGitHub Profile:")
            summary_parts.append(f"- Username: {github.get('username', 'N/A')}")
            summary_parts.append(f"- Public Repos: {github.get('public_repos', 0)}")
            summary_parts.append(f"- Total Stars: {github.get('total_stars', 0)}")
            summary_parts.append(f"- Languages: {', '.join(list(github.get('languages', {}).keys())[:5])}")
        
        if candidate_data.get('linkedin_url'):
            summary_parts.append(f"\nLinkedIn URL: {candidate_data['linkedin_url']}")
        
        if candidate_data.get('portfolio_url'):
            summary_parts.append(f"\nPersonal Portfolio URL: {candidate_data['portfolio_url']}")

        if candidate_data.get('web_profile_analysis'):
            web_data = candidate_data['web_profile_analysis']
            if web_data.get('inferred_skills'):
                summary_parts.append(f"- Skills found on web profile: {', '.join(web_data['inferred_skills'])}")

        if candidate_data.get('skills'):
            summary_parts.append(f"\nIdentified Skills: {', '.join(candidate_data['skills'])}")
        
        if candidate_data.get('additional_info'):
            summary_parts.append(f"\nAdditional Information:\n{candidate_data['additional_info']}")
        
        return "\n".join(summary_parts)

