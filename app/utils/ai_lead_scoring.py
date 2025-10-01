import os
from typing import Dict, Any
from dataclasses import asdict, dataclass
import logging
from openai import OpenAI
from dotenv import load_dotenv
import json


# Load environment variables
load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of lead scoring components"""
    role_fit: int = 0
    industry_alignment: int = 0
    company_size: int = 0
    geographic_fit: int = 0
    psychographic_fit: int = 0
    motivation_alignment: int = 0
    micro_audience_bonus: int = 0
    red_flags_penalty: int = 0
    total_score: int = 0
    grade: str = "F"
    recommended_campaign: str = ""
    priority: str = "Low"
    reasoning: str = ""  # AI-generated explanation for the score


class AIScoringEngine:
    """AI-powered lead scoring engine using OpenAI's GPT models"""


    def __init__(self, model: str = "gpt-4-turbo"):
        """Initialize the AI scoring engine"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.system_prompt = """
You are an expert in lead scoring and ideal customer profiling for the Great Manager Recognition program.
Your task is to analyze the provided lead/company data and score them based on the ICP fit.


Scoring Guidelines (0–100 scale):


1. Role & Seniority Fit (0–25 points):
   - Target = Mid-level people managers (team leads, project managers, dept heads, mid-level executives).
   - Typical = 5–15 years of management experience.
   - Lower = Very junior ICs or senior CXOs (different fit).


2. Industry Alignment (0–15 points):
   - Strong = IT/ITES, BFSI, Consulting, Manufacturing, Healthcare, Retail, Startups.
   - Medium = Adjacent industries with leadership culture.
   - Low = Non-aligned sectors.


3. Company Size Fit (0–10 points):
   - High = 200–5,000 employees (sweet spot: 1,000–2,500 with 50–200 managers).
   - Medium = 50–200 employees.
   - Low = <50 employees unless self-funded.


4. Geographic Fit (0–10 points):
   - Strong = Urban India metros (Mumbai, Bangalore, Delhi, Chennai, Hyderabad, Pune).
   - Medium = Tier-2 Indian cities.
   - Lower = Outside India unless MNC with Indian ops.


5. Psychographic Fit (0–15 points):
   - Growth-oriented, ambitious, values recognition, prestige, and data-driven validation.
   - Motivated by credibility, ROI, peer endorsement, career branding.


6. Motivation & Pain Alignment (0–10 points):
   - High = Clear pain (feels undervalued, lacks benchmarks, no feedback, fears stagnation).
   - High = Aspiration (recognition, prestige, national credibility).
   - Low = No alignment with these needs.


7. Micro-Niche Bonus (0–5 points):
   Award if they belong to:
   - Tech/startup managers (branding + analytics-driven).
   - BFSI/Consulting (formal recognition + benchmarking).
   - Manufacturing/Retail/Pharma frontline leaders.
   - New managers (1–3 years, validation seekers).
   - Mid-career managers (5–15 years, career acceleration).


8. Red Flags Penalty (0–10 points):
   Deduct for:
   - Extremely small orgs with no budgets.
   - Anti-recognition/anti-management culture.
   - Already tied to competing recognition programs.
   - Not managing teams.


Output JSON Fields:
- role_fit: int
- industry_alignment: int
- company_size: int
- geographic_fit: int
- psychographic_fit: int
- motivation_alignment: int
- micro_audience_bonus: int
- red_flags_penalty: int
- total_score: int (0–100 after penalties)
- grade: str (A=85+, B=70–84, C=55–69, D=40–54, F<40)
- recommended_campaign: str (best campaign/CTA for ICP persona)
- priority: str (High=Grade A/B, Medium=C, Low=D/F)
- reasoning: str (short explanation referencing ICP criteria and persona signals)
"""


    def _call_ai(self, prompt: str) -> Dict[str, Any]:
        """Make API call to OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise


    def score_lead(self, profile_data: Dict[str, Any], company_data: Dict[str, Any]) -> ScoreBreakdown:
        """
        Score a lead using AI
        """
        prompt = f"""
        Please analyze and score this lead based on the provided information.


        LEAD PROFILE:
        {str(profile_data)}


        COMPANY INFORMATION:
        {str(company_data)}


        Please provide the scoring in the requested JSON format.
        """


        try:
            response = self._call_ai(prompt)
            score_data = json.loads(response)  # safer than eval
            score = ScoreBreakdown(**score_data)
            return asdict(score)
        except Exception as e:
            logger.error(f"Error in AI scoring: {str(e)}")
            return ScoreBreakdown(
                total_score=0,
                grade="F",
                recommended_campaign="General Outreach",
                priority="Low",
                reasoning=f"Error in scoring: {str(e)}"
            )