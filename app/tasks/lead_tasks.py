from enum import Enum
from typing import Dict, List, Optional, TypedDict, Annotated
from app.database.base import get_db
from app.services.company_service import update_company_with_enrichment, update_enrichment_job
from app.services.lead_service import update_lead_with_enrichment
from app.utils.ai_lead_scoring import AIScoringEngine
from app.utils.bright_data_helper import get_snapshot, poll_progress, trigger_scrape, trigger_scrape_glassdoor_comments
from app.utils.prompts import get_company_insights_messages, get_company_linkedin_url_messages, get_company_summary_messages, get_glassdoor_analysis_messages, get_glassdoor_url_messages, get_linkedin_company_analysis_messages, get_linkedin_profile_analysis_messages, get_linkedin_url_messages
from app.utils.web_search import scrape_with_web_unlocker, serp_search
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from ..celery_config import celery_app
from sqlalchemy import text
import logging
from langchain.chat_models import init_chat_model
import json
from ..database.base import get_db

logger = logging.getLogger(__name__)

llm = init_chat_model("gpt-4o-mini")

# --- Data Models ---

class State(TypedDict):
    messages: Annotated[list, add_messages]
    lead_details: dict
    name: str
    company_name: str
    designation: str
    email: str  
    google_results: Optional[str]
    linkedin_url: Optional[str]
    linkedin_details_raw: Optional[dict]
    linkedin_details: Optional[dict]
    lead_score: Optional[dict]
    company_search_results: Optional[str]  
    company_linkedin_url: Optional[str]
    company_linkedin_details: Optional[dict]
    company_linkedin_analysis: Optional[dict]
    glassdoor_url: Optional[str]
    glassdoor_details: Optional[dict]
    glassdoor_analysis: Optional[dict]
    company_insights: Optional[dict]
    lead_stage: Optional[str]
    stage_metadata: Optional[dict]
    content: Optional[dict]

class Experience(BaseModel):
    role: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)

class Education(BaseModel):
    degree: str
    school: str
    year: Optional[str] = None

class OtherLink(BaseModel):
    type: str
    url: str

class LinkedInProfileResult(BaseModel):
    name: str
    linkedin_url: Optional[str] = None
    headline: Optional[str] = None
    current_role: Optional[str] = None
    current_company: Optional[str] = None
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    summary: Optional[str] = None

class CompanyProfile(BaseModel):
    name: str
    website: Optional[str]
    industry: Optional[str]
    size: Optional[str]
    founded: Optional[int]
    locations: List[str] = Field(default_factory=list)

class GlassdoorAnalysisModel(BaseModel):
    overall_rating: float
    sentiment_positive: float
    sentiment_negative: float
    key_strengths: List[str]
    key_issues: List[str]
    summary: str

class RecentNews(BaseModel):
    title: str
    summary: str
    relevance: str
    potential_opportunity: str


class ConversationStarter(BaseModel):
    topic: str
    relevance: str
    talking_point: str


class CompanyInsightsModel(BaseModel):
    recent_news: List[RecentNews] = Field(default_factory=list)
    leadership_changes: List[str] = Field(default_factory=list)
    funding_events: List[str] = Field(default_factory=list)
    strategic_initiatives: List[str] = Field(default_factory=list)
    industry_trends: List[str] = Field(default_factory=list)
    conversation_starters: List[ConversationStarter] = Field(default_factory=list)

class LeadEngagement(BaseModel):
    emails_opened: int = 0
    links_clicked: int = 0
    content_downloaded: int = 0
    website_visits: int = 0
    meeting_booked: bool = False
    last_engagement_days: int = 30

class LeadStage(str, Enum):
    COLD = "Cold"
    AWARE = "Awareness"
    CONSIDERING = "Considering"
    ENGAGED = "Engaged"
    OPPORTUNITY = "Opportunity"
    CUSTOMER = "Customer"

class LinkedInURLResult(BaseModel):
    linkedin_url: str | None = Field(
        description="Most relevant LinkedIn profile URL for the target individual, or None if not found"
    )

class GlassdoorURLResult(BaseModel):
    glassdoor_url: str | None = Field(
        description="Most relevant Glassdoor company URL, or None if not found"
    )

class CompanySummaryResult(BaseModel):
    summary: str

# --- Node Functions ---

def serp_search_google(state: State) -> dict:
    """Search Google for lead information."""
    logger.info("[SERP_SEARCH_GOOGLE] Starting Google search...")
    try:
        # Check if google_results already exists in state
        existing_results = state.get("google_results")
        if existing_results is not None:
            logger.info("[SERP_SEARCH_GOOGLE] Google results already exist, skipping search.")
            return {"google_results": existing_results}
        
        logger.info("Searching Google...")
        search_query = state.get("name") + " " + state.get("company_name")
        google_results = serp_search(search_query, engine="google")
        return {"google_results": google_results} 
    except Exception as e:
        logger.error(f"[SERP_SEARCH_GOOGLE] Error: {str(e)}")
        raise

def find_linkedin_url(state: State) -> dict:
    """Find LinkedIn URL from search results."""
    logger.info("[FIND_LINKEDIN_URL] Starting LinkedIn URL search...")
    try:
        # Check if linkedin_url already exists in state
        existing_url = state.get("linkedin_url")
        if existing_url is not None:
            logger.info("[FIND_LINKEDIN_URL] LinkedIn URL already exists, skipping search.")
            return {"linkedin_url": existing_url}
        
        print("Finding LinkedIn URL...")
        google_results = state.get("google_results", "")

        lead_details = {
            "name": state.get("name", ""),
            "company_name": state.get("company_name", ""),
        }
        
        # Get messages
        messages = get_linkedin_url_messages(lead_details, google_results)
        

        # Use structured output
        structured_llm = llm.with_structured_output(LinkedInURLResult)

        try:
            analysis = structured_llm.invoke(messages)
            linkedin_url = analysis.linkedin_url
            if linkedin_url:
                print(f"✅ Found LinkedIn URL: {linkedin_url}")
            else:
                print("⚠️ No LinkedIn URL found in results.")
        except Exception as e:
            print(f"❌ Error while analyzing LinkedIn URL: {e}")
            linkedin_url = None

        return {"linkedin_url": linkedin_url}
    except Exception as e:
        logger.error(f"[FIND_LINKEDIN_URL] Error: {str(e)}")
        raise

def scrape_linkedin(state: State) -> dict:
    """Scrape LinkedIn profile data."""
    logger.info("[SCRAPE_LINKEDIN] Starting LinkedIn profile scraping...")
    try:
        # Check if linkedin_details_raw already exists in state
        existing_raw = state.get("linkedin_details_raw")
        if existing_raw is not None:
            logger.info("[SCRAPE_LINKEDIN] LinkedIn details already exist, skipping scrape.")
            return {"linkedin_details_raw": existing_raw}
        
        dataset_id = "gd_l1viktl72bvl7bjuj0"
        urls = [state.get("linkedin_url")]
        trigger_res = trigger_scrape(dataset_id, urls)
        snapshot_id = trigger_res.get("snapshot_id")

        if not snapshot_id:
            raise ValueError(f"Snapshot ID not found in response: {trigger_res}")

        print(f"Triggered scrape. Snapshot ID: {snapshot_id}. Polling for results...")

        if poll_progress(snapshot_id):
            print("Scrape completed. Fetching results...")
            linkedin_details_raw = get_snapshot(snapshot_id)

            return {"linkedin_details_raw": linkedin_details_raw}
        else:
            raise TimeoutError("Scrape job timed out before completion.")
    except Exception as e:
        logger.error(f"[SCRAPE_LINKEDIN] Error: {str(e)}")
        raise

def analyze_linkedin(state: State) -> dict:
    """Analyze scraped LinkedIn data."""
    logger.info("[ANALYZE_LINKEDIN] Starting LinkedIn data analysis...")
    try:
        # Check if linkedin_details already exists in state
        existing_details = state.get("linkedin_details")

        if existing_details is not None:
            logger.info("[ANALYZE_LINKEDIN] LinkedIn details already exist, skipping analysis.")
            return {"linkedin_details": existing_details}
        
        linkedin_details_raw = state.get("linkedin_details_raw", {})

        lead_details = {
            "name": state.get("name", ""),
            "company_name": state.get("company_name", ""),
        }

        # Get messages
        messages = get_linkedin_profile_analysis_messages(lead_details, linkedin_details_raw)

        # Use structured output
        structured_llm = llm.with_structured_output(LinkedInProfileResult)

        analysis = structured_llm.invoke(messages)

        print("✅ LinkedIn profile analyzed successfully")
        return {"linkedin_details": analysis.model_dump()}
    except Exception as e:
        logger.error(f"[ANALYZE_LINKEDIN] Error: {str(e)}")
        raise

def find_company_search_results(state: State) -> dict:
    """Search for company information."""
    logger.info("[FIND_COMPANY_SEARCH_RESULTS] Starting company search...")
    try:
        # Check if company_search_results already exists in state
        existing_results = state.get("company_search_results")
        if existing_results is not None:
            logger.info("[FIND_COMPANY_SEARCH_RESULTS] Company search results already exist, skipping search.")
            return {"company_search_results": existing_results}
        
        search_query = state.get("company_name")

        google_results = serp_search(search_query, engine="google")

        website_url = google_results.get("organic", [{}])[0].get("link", "")

        webiste_content = scrape_with_web_unlocker(website_url)

        summary_message = get_company_summary_messages(state.get("company_name"), website_url, webiste_content)

        structured_llm = llm.with_structured_output(CompanySummaryResult)

        company_summary = structured_llm.invoke(summary_message)

        return {"company_search_results": company_summary.model_dump()}
    except Exception as e:
        logger.error(f"[FIND_COMPANY_SEARCH_RESULTS] Error: {str(e)}")
        raise

def find_company_linkedin_url(state: State) -> dict:
    """Find company's LinkedIn URL."""
    logger.info("[FIND_COMPANY_LINKEDIN_URL] Starting company LinkedIn URL search...")
    try:
        # Check if company_linkedin_url already exists in state
        existing_url = state.get("company_linkedin_url")
        if existing_url is not None:
            logger.info("[FIND_COMPANY_LINKEDIN_URL] Company LinkedIn URL already exists, skipping search.")
            return {"company_linkedin_url": existing_url}
        
        search_query = f"site:linkedin.com/company/ {state.get('company_name')}"

        google_results = serp_search(search_query, engine="google")
    
        company_details = {
            "company": state.get("company_name"),
            "location": state.get("lead_details", {}).get("location", "")
        }

        messages = get_company_linkedin_url_messages(company_details, google_results)

        # Use structured output
        structured_llm = llm.with_structured_output(LinkedInURLResult)

        analysis = structured_llm.invoke(messages)
        company_linkedin_url = analysis.linkedin_url

        if company_linkedin_url:
            print(f"✅ Found Company LinkedIn URL: {company_linkedin_url}")
        else:
            print("⚠️ No company LinkedIn URL found in results.")
            company_linkedin_url = None
        
        return {"company_linkedin_url": company_linkedin_url}
    except Exception as e:
        logger.error(f"[FIND_COMPANY_LINKEDIN_URL] Error: {str(e)}")
        raise

def scrape_company_linkedin(state: State) -> dict:
    """Scrape company LinkedIn data."""
    logger.info("[SCRAPE_COMPANY_LINKEDIN] Starting company LinkedIn data scraping...")
    try:
        # Check if company_linkedin_url already exists in state
        existing_url = state.get("company_linkedin_details")
        if existing_url is not None:
            logger.info("[SCRAPE_COMPANY_LINKEDIN] Company LinkedIn URL already exists, skipping scrape.")
            return {"company_linkedin_details": existing_url}
        
        dataset_id = "gd_l1vikfnt1wgvvqz95w"
        urls = [state.get("company_linkedin_url")]

        trigger_res = trigger_scrape(dataset_id, urls)

        snapshot_id = trigger_res.get("snapshot_id")

        if not snapshot_id:
            raise ValueError(f"Snapshot ID not found in response: {trigger_res}")

        print(f"Triggered scrape. Snapshot ID: {snapshot_id}. Polling for results...")

        if poll_progress(snapshot_id):
            print("Scrape completed. Fetching results...")
            linkedin_details_raw = get_snapshot(snapshot_id)

            return {"company_linkedin_details": linkedin_details_raw}
        else:
            raise TimeoutError("Scrape job timed out before completion.")
    except Exception as e:
        logger.error(f"[SCRAPE_COMPANY_LINKEDIN] Error: {str(e)}")
        raise

def analyze_company_linkedin(state: State) -> dict:
    """Analyze company LinkedIn data."""
    logger.info("[ANALYZE_COMPANY_LINKEDIN] Starting company LinkedIn data analysis...")
    try:
        # Check if company_linkedin_url already exists in state
        existing_url = state.get("company_linkedin_analysis")
        if existing_url is not None:
            logger.info("[ANALYZE_COMPANY_LINKEDIN] Company LinkedIn URL already exists, skipping scrape.")
            return {"company_linkedin_analysis": existing_url}
        
        company_linkedin_details = state.get("company_linkedin_details", {})

        # Get messages
        messages = get_linkedin_company_analysis_messages(company_linkedin_details)

        # Use structured output
        structured_llm = llm.with_structured_output(CompanyProfile)

        analysis = structured_llm.invoke(messages)

        print("✅Company LinkedIn profile analyzed successfully")

        return {"company_linkedin_analysis": analysis.model_dump()}
    except Exception as e:
        logger.error(f"[ANALYZE_COMPANY_LINKEDIN] Error: {str(e)}")
        raise

def score_lead(state: State) -> dict:
    """Score lead based on profile and company data."""
    logger.info("[SCORE_LEAD] Starting lead scoring...")
    try:
        # Implementation will go herehere
        existing_url = state.get("lead_score")
        if existing_url is not None:
            logger.info("[SCORE_LEAD] Lead score already exists, skipping search.")
            return {"lead_score": existing_url}

        linkedin_details = state.get("linkedin_details", {})
        company_linkedin_details = state.get("company_linkedin_details", {})

        scoring_engine = AIScoringEngine()
        core = scoring_engine.score_lead(linkedin_details, company_linkedin_details)

        return {"lead_score": core}
    except Exception as e:
        logger.error(f"[SCORE_LEAD] Error: {str(e)}")
        raise

def find_glassdoor_url(state: State) -> dict:
    """Find company's Glassdoor URL."""
    logger.info("[FIND_GLASSDOOR_URL] Starting Glassdoor URL search...")
    try:
        # Check if glassdoor_url already exists in state
        existing_url = state.get("glassdoor_url")
        if existing_url is not None:
            logger.info("[FIND_GLASSDOOR_URL] Glassdoor URL already exists, skipping search.")
            return {"glassdoor_url": existing_url}
        
        company_name = state.get("company_name")
    
        if not company_name:
            print("❌ No company name provided for Glassdoor search")
            return {"glassdoor_url": None}
        
        # Search for company on Glassdoor
        search_query = f"{company_name} site:glassdoor.com India"
        search_results = serp_search(search_query, engine="google")
        
        if not search_results or "organic" not in search_results or not search_results["organic"]:
            print(f"❌ No search results found for {company_name} on Glassdoor")
            return {"glassdoor_url": None}
        
        # Prepare company details for the prompt
        company_details = {
            "company": company_name,
            "location": state.get("lead_details", {}).get("location", "")
        }
        
        # Get messages for the LLM
        messages = get_glassdoor_url_messages(company_details, str(search_results))
        
        # Use structured output to get the Glassdoor URL
        structured_llm = llm.with_structured_output(GlassdoorURLResult)
        
        result = structured_llm.invoke(messages)
        glassdoor_url = result.glassdoor_url
            
        if glassdoor_url:
            # Ensure the URL is complete (add https:// if missing)
            if not glassdoor_url.startswith(('http://', 'https://')):
                glassdoor_url = f"https://{glassdoor_url}"
            print(f"✅ Found Glassdoor URL: {glassdoor_url}")
        else:
            print("❌ No Glassdoor URL found in search results")
                
        return {"glassdoor_url": glassdoor_url}
    except Exception as e:
        logger.error(f"[FIND_GLASSDOOR_URL] Error: {str(e)}")
        raise

def scrape_glassdoor(state: State) -> dict:
    """Scrape Glassdoor company data."""
    logger.info("[SCRAPE_GLASSDOOR] Starting Glassdoor data scraping...")
    try:
        # Implementation will go here
        existing_details = state.get("glassdoor_details")
        if existing_details is not None:
            logger.info("[SCRAPE_GLASSDOOR] Glassdoor details already exist, skipping scraping.")
            return {"glassdoor_details": existing_details}
        glassdoor_url = state.get("glassdoor_url")
        
        if not glassdoor_url:
            print("❌ No Glassdoor URL provided for scraping")
            return {"glassdoor_details": None}
        
        dataset_id = "gd_l7j1po0921hbu0ri1z"
        trigger_res = trigger_scrape_glassdoor_comments(dataset_id, [glassdoor_url])
        
        snapshot_id = trigger_res.get("snapshot_id")
        
        if not snapshot_id:
            print(f"❌ Snapshot ID not found in response: {trigger_res}")
            return {"glassdoor_details": None}
        
        print(f"Triggered scrape. Snapshot ID: {snapshot_id}. Polling for results...")
        
        # Poll for results
        if poll_progress(snapshot_id):
            print("Scrape completed. Fetching results...")
            glassdoor_details = get_snapshot(snapshot_id)

            print(glassdoor_details,'glassdoor_details')
            
            if glassdoor_details:
                print("✅ Successfully scraped Glassdoor data")
                return {"glassdoor_details": glassdoor_details}
            else:
                print("❌ Failed to get Glassdoor data")
                return {"glassdoor_details": None}
        else:
            print("❌ Scrape job timed out or failed")
            return {"glassdoor_details": None}
    except Exception as e:
        logger.error(f"[SCRAPE_GLASSDOOR] Error: {str(e)}")
        raise

def analyze_glassdoor(state: State) -> dict:
    """Analyze Glassdoor company data."""
    logger.info("[ANALYZE_GLASSDOOR] Starting Glassdoor data analysis...")
    try:
        # Implementation will go here
        existing_url = state.get("glassdoor_analysis")
        if existing_url is not None:
            logger.info("[FIND_GLASSDOOR_URL] Glassdoor URL already exists, skipping search.")
            return {"glassdoor_analysis": existing_url}
        if not state.get("glassdoor_details"):
            print("❌ No Glassdoor data available to analyze")
            return {"glassdoor_analysis": None}
         
        # Get company name from state or use a default
        company_name = state.get("company_name")
        
        # Get reviews from state
        reviews = state["glassdoor_details"]
        if not isinstance(reviews, list):
            reviews = [reviews]

        if not reviews:
            print("❌ No reviews found in Glassdoor data")
            return {"glassdoor_analysis": None}
        
        print(f"Analyzing {len(reviews)} Glassdoor reviews for {company_name}...")
        
        # Get analysis messages using our prompt templates
        messages = get_glassdoor_analysis_messages(company_name, reviews)

        structured_llm = llm.with_structured_output(GlassdoorAnalysisModel)

        # Call the LLM to analyze the reviews
        response = structured_llm.invoke(messages)

        return {"glassdoor_analysis": response.model_dump()}
    except Exception as e:
        logger.error(f"[ANALYZE_GLASSDOOR] Error: {str(e)}")
        raise

def find_company_insights(state: State) -> dict:
    """Generate actionable insights from company data."""
    logger.info("[FIND_COMPANY_INSIGHTS] Starting company insights generation...")
    try:
        # Implementation will go here
        existing_url = state.get("company_insights")
        if existing_url is not None:
            logger.info("[FIND_COMPANY_INSIGHTS] Company insights already exists, skipping search.")
            return {"company_insights": existing_url}
        
        if not state.get("company_linkedin_details") and not state.get("glassdoor_analysis"):
            print("❌ No company data available for analysis")
            return {"company_insights": None}
    
        # Get company name from state or use a default
        company_name = state.get("company_name")

        query = f"{company_name} news"
        
        # Search for recent news about the company
        news_items = serp_search(query=query)
        
        # Prepare company data from available sources
        company_data = {
            "linkedin_analysis": state.get("company_linkedin_analysis"),
            "glassdoor_analysis": state.get("glassdoor_analysis"),
            "recent_news": news_items,
            "company_name": company_name
        }
        
        # Get analysis messages using our prompt templates
        messages = get_company_insights_messages(company_name, company_data)
        
        # Configure LLM with structured output
        structured_llm = llm.with_structured_output(CompanyInsightsModel)
        
        # Call the LLM to analyze the company data
        insights = structured_llm.invoke(messages)
        
        # Log the insights for debugging
        print("✅ Successfully generated company insights")
        if insights.conversation_starters:
            print("💡 Conversation starters:")
            for i, starter in enumerate(insights.conversation_starters[:3], 1):
                print(f"   {i}. {starter}")
        
        return {"company_insights": insights.model_dump()}
    except Exception as e:
        logger.error(f"[FIND_COMPANY_INSIGHTS] Error: {str(e)}")
        raise

# --- Graph Construction ---

def create_lead_enrichment_graph():
    """Create and configure the lead enrichment graph."""
    builder = StateGraph(State)
    
    # Add nodes
    builder.add_node("serp_search_google", serp_search_google)
    builder.add_node("find_linkedin_url", find_linkedin_url)
    builder.add_node("scrape_linkedin", scrape_linkedin)
    builder.add_node("analyze_linkedin", analyze_linkedin)    
    builder.add_node("score_lead", score_lead)
    builder.add_node("find_company_search_results", find_company_search_results)
    builder.add_node("find_company_linkedin_url", find_company_linkedin_url)
    builder.add_node("scrape_company_linkedin", scrape_company_linkedin)
    builder.add_node("analyze_company_linkedin", analyze_company_linkedin)
    builder.add_node("find_glassdoor_url", find_glassdoor_url)
    builder.add_node("scrape_glassdoor", scrape_glassdoor)
    builder.add_node("analyze_glassdoor", analyze_glassdoor)
    builder.add_node("find_company_insights", find_company_insights)

    print("Nodes added so far:", list(builder.nodes.keys()))

    
    # Define edges
    builder.add_edge(START, "serp_search_google")
    builder.add_edge("serp_search_google", "find_linkedin_url")
    builder.add_edge("find_linkedin_url", "scrape_linkedin")
    builder.add_edge("scrape_linkedin", "analyze_linkedin")
    builder.add_edge("analyze_linkedin", "find_company_search_results")
    builder.add_edge("find_company_search_results", "find_company_linkedin_url")
    builder.add_edge("find_company_linkedin_url", "scrape_company_linkedin")
    builder.add_edge("scrape_company_linkedin", "analyze_company_linkedin")
    builder.add_edge("analyze_company_linkedin", "score_lead")
    builder.add_edge("score_lead", "find_glassdoor_url")
    builder.add_edge("find_glassdoor_url", "scrape_glassdoor")
    builder.add_edge("scrape_glassdoor", "analyze_glassdoor")
    builder.add_edge("analyze_glassdoor", "find_company_insights")
    builder.add_edge("find_company_insights", END)
    
    return builder.compile()

# --- Task Definition ---

@celery_app.task(name="enrich_lead_task")
def enrich_lead_task(lead_data: Dict[str, any]) -> Dict[str, any]:
    """
    Task to enrich lead information using a multi-step workflow.
    
    Args:
        lead_data: Dictionary containing lead details
            {
                "name": str,
                "email": str,
                "designation": str,
                "company": str
            }
            
    Returns:
        dict: The enriched lead data
    """
    try:
        logger.info(f"[ENRICH_LEAD] Processing lead: {lead_data}")
        
        # Initialize state
        # Handle lead_data if it's a list
        if isinstance(lead_data, list) and lead_data:
            lead = lead_data[0]
        else:
            lead = lead_data
        
        state: State = {
            "messages": [],
            "lead_details": lead,
            "name": lead.get('name'),
            "company_name": lead.get('company_name'),
            "designation": lead.get('designation'),
            "email": lead.get('email'),
            "google_results": lead.get('google_results'),
            "linkedin_url": lead.get('linkedin_url'),
            "linkedin_details_raw": lead.get('linkedin_details_raw'),
            "linkedin_details": lead.get('linkedin_details'),
            "lead_score": lead.get('lead_score'),
            "company_search_results": lead.get('company_search_results'),
            "lead_stage": lead.get('lead_stage'),
            "stage_metadata": lead.get('stage_metadata'),
            "company_linkedin_url": lead.get('company_linkedin_url'),
            "company_linkedin_details": lead.get('company_linkedin_details'),
            "company_linkedin_analysis": lead.get('company_linkedin_analysis'),
            "glassdoor_url": lead.get('glassdoor_url'),
            "glassdoor_details": lead.get('glassdoor_details'),
            "glassdoor_analysis": lead.get('glassdoor_analysis'),
            "company_insights": lead.get('company_insights'),
            "enrichment_status": lead.get('enrichment_status'),
            "content": None,
        }
        
        # Run the workflow
        graph = create_lead_enrichment_graph()
        final_state = graph.invoke(state)

        
        # Update database with enriched data
        db = next(get_db())
        try:
            # Handle JSON strings in final_state
            lead_details = final_state.get('lead_details')
            if isinstance(lead_details, str):
                lead_details = json.loads(lead_details)
            if not isinstance(lead_details, dict) or 'lead_id' not in lead_details:
                raise ValueError("Invalid lead_details: missing 'lead_id'")
            lead_id = lead_details['lead_id']
            
            company_id = lead_details.get('company_id')
            
            # Update lead
            update_lead_with_enrichment(db, lead_id, final_state)
            # Update company
            update_company_with_enrichment(db, company_id, final_state)
            # Update enrichment job
            update_enrichment_job(db, lead_id, 'completed', final_state)

            db.commit()
            logger.info("[ENRICH_LEAD] Database updated successfully")
        except Exception as e:
            logger.error(f"[ENRICH_LEAD] Error updating database: {str(e)}")
            db.rollback()
        finally:
            db.close()
        
        # Write final status to file
        # try:
        #     with open('/tmp/enrichment_status.json', 'w') as f:
        #         json.dump(final_state, f, default=str, indent=4)
        #     print("Final status written to /tmp/enrichment_status.json")
        # except Exception as e:
        #     print(f"Error writing status to file: {str(e)}")
        
        logger.info("[ENRICH_LEAD] Lead enrichment completed successfully")
        return final_state
        
    except Exception as e:
        error_msg = f"Error enriching lead {lead_data.get('email')}: {str(e)}"
        logger.error(f"[ENRICH_LEAD_ERROR] {error_msg}")
        raise