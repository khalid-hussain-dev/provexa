"""
Simple test script to verify the project setup
Run this to check if all dependencies are installed correctly
"""

import sys

# Configure UTF-8 encoding for Windows terminals to avoid UnicodeEncodeError
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")



def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import crewai
        print("✓ crewai imported successfully")
    except ImportError as e:
        print(f"✗ crewai import failed: {e}")
        return False
    
    try:
        import langchain_openai
        print("✓ langchain_openai imported successfully")
    except ImportError as e:
        print(f"✗ langchain_openai import failed: {e}")
        return False
    
    try:
        import fastapi
        print("✓ fastapi imported successfully")
    except ImportError as e:
        print(f"✗ fastapi import failed: {e}")
        return False
    
    try:
        import pydantic
        print("✓ pydantic imported successfully")
    except ImportError as e:
        print(f"✗ pydantic import failed: {e}")
        return False
    
    try:
        import pdfplumber
        print("✓ pdfplumber imported successfully")
    except ImportError as e:
        print(f"✗ pdfplumber import failed: {e}")
        return False
    
    try:
        import github
        print("✓ github imported successfully")
    except ImportError as e:
        print(f"✗ github import failed: {e}")
        return False
    
    return True


def test_project_modules():
    """Test if project modules can be imported"""
    print("\nTesting project modules...")
    
    try:
        from models import CandidateProfile, InterviewResult
        print("✓ models imported successfully")
    except ImportError as e:
        print(f"✗ models import failed: {e}")
        return False
    
    try:
        from config import settings
        print("✓ config imported successfully")
    except ImportError as e:
        print(f"✗ config import failed: {e}")
        return False
    
    try:
        from agents import InterviewAgents
        print("✓ agents imported successfully")
    except ImportError as e:
        print(f"✗ agents import failed: {e}")
        return False
    
    try:
        from profile_analyzer import ProfileAnalyzer
        print("✓ profile_analyzer imported successfully")
    except ImportError as e:
        print(f"✗ profile_analyzer import failed: {e}")
        return False
    
    try:
        from interview_system import InterviewSystem
        print("✓ interview_system imported successfully")
    except ImportError as e:
        print(f"✗ interview_system import failed: {e}")
        return False
    
    try:
        from job_service import JobRecommendationService
        print("✓ job_service imported successfully")
    except ImportError as e:
        print(f"✗ job_service import failed: {e}")
        return False
    
    try:
        from main import app
        print("✓ main app imported successfully")
    except ImportError as e:
        print(f"✗ main import failed: {e}")
        return False
    
    return True


def test_models():
    """Test if Pydantic models work correctly"""
    print("\nTesting Pydantic models...")
    
    try:
        from models import CandidateProfile, SkillAssessment, InterviewResult
        
        # Test CandidateProfile
        profile = CandidateProfile(
            name="Test User",
            email="test@example.com",
            target_role="Backend Engineer",
            experience_years=2.5,
            skills=["Python", "Django"]
        )
        print(f"✓ CandidateProfile created: {profile.name}")
        
        # Test SkillAssessment
        skill = SkillAssessment(
            skill_name="Python",
            percentage=75.0,
            strength_level="advanced",
            evidence=["Good understanding of OOP", "Experience with frameworks"]
        )
        print(f"✓ SkillAssessment created: {skill.skill_name} - {skill.percentage}%")
        
        return True
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("AI Interview & Assessment System - Setup Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Test imports
    results.append(("Dependencies", test_imports()))
    
    # Test project modules
    results.append(("Project Modules", test_project_modules()))
    
    # Test models
    results.append(("Pydantic Models", test_models()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All tests passed! The project is ready to use.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env")
        print("2. Add your OPENAI_API_KEY to .env")
        print("3. Run: python main.py")
        print("4. Visit http://localhost:8000/docs for API documentation")
    else:
        print("\n✗ Some tests failed. Please install missing dependencies:")
        print("   pip install -r requirements.txt")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
