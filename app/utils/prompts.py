from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
import json
from pydantic import BaseModel, Field


def get_content_generation_system_prompt() -> str:
    """System prompt for generating personalized outreach content."""
    return """You are an expert content generator for sales outreach. Your task is to create highly personalized 
    and compelling email content based on the lead's profile, company details, and engagement stage.
    
    You will receive:
    1. Lead's personal and professional details
    2. Company information and insights
    3. Engagement metrics and lead stage
    4. Glassdoor analysis (if available)
    5. Recent company news and updates
    
    Your output should be a JSON object with:
    - subject: A compelling email subject line (max 60 chars)
    - greeting: Personalized greeting
    - body: Main email content (3-5 paragraphs)
    - call_to_action: Clear next step
    - personalization_elements: List of elements used for personalization
    - tone: The tone used (e.g., professional, conversational, enthusiastic)
    - length: Estimated word count
    """


def get_content_generation_messages(context: Dict) -> List[Dict]:
    """Prepare messages for content generation."""
    system_prompt = get_content_generation_system_prompt()
    
    user_prompt = f"""Please generate a personalized outreach email using the following context:
    
    Lead Information:
    - Name: {context['lead'].get('name', '')}
    - Role: {context['lead'].get('title', 'N/A')}
    - Company: {context['lead'].get('company', 'N/A')}
    - Industry: {context['lead'].get('industry', 'N/A')}
    - Linkedin_Details: {context['lead_details'].get('linkedin', {})}
    
    Company Insights:
    {json.dumps(context['company'].get('insights', {}), indent=2)[:1000]}...
    
    Engagement:
    - Stage: {context['engagement']['stage']}
    - Score: {context['engagement']['score']}/100
    - Last Engagement: {context['engagement']['metrics'].get('last_engagement_days', 'N/A')} days ago
    
    Available Insights:
    {context.get("insights", {}).get("industry_insights", [])}...


    Available Product Advantages:
    {context.get("insights", {}).get("product_advantages", [])}...


    Identified Issues:
    {json.dumps(context['company'].get('glassdoor', {}), indent=2)[:1000]}...
    
    Guidelines:
    1. Keep it concise (150-250 words)
    2. Focus on value proposition
    3. Use a {_get_tone_for_stage(context['engagement']['stage'])} tone
    4. Use the stage metadata to understand the lead's engagement level: {context['engagement']['stage_metadata']}
    4. Include 1-2 personalization elements
    5. End with a clear call-to-action
    6. Use this link if CTA is required: https://app.greatmanagerinstitute.com/manager/b2c-form
    """
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


def _get_tone_for_stage(stage: str) -> str:
    """Get appropriate tone based on lead stage."""
    tones = {
        "Cold": "professional and inquisitive",
        "Aware": "informative and helpful",
        "Considering": "consultative and solution-oriented",
        "Engaged": "collaborative and forward-looking",
        "Opportunity": "decisive and action-oriented"
    }
    return tones.get(stage, "professional")



class PromptTemplates:
    """Container for all prompt templates used in the research assistant."""


    @staticmethod
    def linkedin_url_finder_system() -> str:
        """System prompt for identifying the correct LinkedIn profile URL from Google results."""
        return """You are an expert at entity resolution and professional data research. 
            Your task is to identify the most relevant LinkedIn profile URL for a given person from the provided Google search results.


            Focus on:
            - Links that are from linkedin.com (including in.linkedin.com, www.linkedin.com, etc.)
            - Matches where the name and company align with the target person
            - Higher-ranked results are usually more reliable
            - Ignore aggregator sites (RocketReach, SignalHire, Crunchbase, etc.) unless no LinkedIn link exists
            - If multiple LinkedIn profiles are found, prefer the one that explicitly mentions the correct company


            Return only the most relevant LinkedIn profile URL as your final answer."""


    @staticmethod
    def linkedin_url_finder_user(lead_details: dict, google_results: str) -> str:
        """User prompt for LinkedIn URL finding."""
        return f"""Target: {lead_details['name']} at {lead_details['company_name']}  


            Google Search Results: {google_results}


            Please extract the most relevant LinkedIn profile URL for the target individual based on these search results."""


    @staticmethod
    def linkedin_profile_analysis_system() -> str:
        """System prompt for analyzing scraped LinkedIn profile data."""
        return """You are an expert LinkedIn analyst and data normalizer. 
        Your job is to take raw scraped LinkedIn profile data and return a structured JSON 
        containing maximum useful details.


        Rules:
        - Use only facts from the input (no hallucinations).
        - If a field cannot be inferred, leave it empty or as an empty list.
        - Ensure response is valid JSON and matches schema.
        - Provide both structured data and a human-readable summary.
        """


    @staticmethod
    def linkedin_profile_analysis_user(lead_details: dict, linkedin_scrape: dict) -> str:
        """User prompt for LinkedIn profile analysis."""
        return f"""Target: {lead_details.get('name')} at {lead_details.get('company_name')}  


        Scraped LinkedIn Data:
        {linkedin_scrape}


        Please normalize this into the defined schema.
        """


    @staticmethod
    def company_summary_system() -> str:
        """System prompt for summarizing company website data."""
        return """You are an expert company analyst.
        Your job is to analyze the content from a company's website 
        and return a concise summary (3–5 sentences max) of what the company does.


        Rules:
        - Use only information from the website content provided (no hallucinations).
        - Keep the tone professional and neutral.
        - Focus on the company's core products/services, industry, and target customers.
        - If information is missing, omit it (do not guess).
        """


    @staticmethod
    def company_summary_user(company_name: str, website_url: str, website_content: str) -> str:
        """User prompt for company summary using website data."""
        return f"""Company: {company_name}  
        Website: {website_url}  


        Website Content:
        {website_content}


        Please provide a short summary of what this company does.
        """
    # In prompts.py, add these new functions:


    @staticmethod
    def company_linkedin_url_finder_system() -> str:
        """System prompt for identifying the correct company LinkedIn URL from search results."""
        return """You are an expert at finding company LinkedIn profiles. 
            Your task is to identify the most relevant LinkedIn company page URL from the provided search results.


            Focus on:
            - Links that are from linkedin.com/company/ (including www.linkedin.com/company/, etc.)
            - Matches where the company name aligns with the target company
            - Higher-ranked results are usually more reliable
            - Ignore individual profiles (look for /company/ in the URL)
            - If multiple company pages are found, prefer the one that is verified or has more followers


            Return only the most relevant LinkedIn company URL as your final answer."""


    @staticmethod
    def company_linkedin_url_finder_user(company_details: dict, search_results: str) -> str:
        """User prompt for company LinkedIn URL finding."""
        return f"""Target Company: {company_details.get('company', 'Unknown')}
            Location: {company_details.get('location', 'Not specified')}


            Search Results:
            {search_results}


            Please extract the most relevant LinkedIn company page URL from these search results.
            Only return the URL, nothing else."""


    @staticmethod
    def linkedin_company_analysis_system() -> str:
        """System prompt for analyzing scraped LinkedIn company profile data."""
        return """You are an expert LinkedIn analyst and data normalizer.
        Your job is to take raw scraped LinkedIn company profile data and return a structured JSON
        that strictly matches the provided schema.


        Rules:
        - Use only facts from the input (no hallucinations).
        - If a field is missing, leave it null or an empty list.
        - Ensure response is valid JSON and matches the schema exactly.
        - Normalize 'specialties' into a clean list of strings.
        - Industries must always be returned as a list.
        - Only include factual LinkedIn details (do not invent values)."""


    @staticmethod
    def linkedin_company_analysis_user(scraped_data: dict) -> str:
        """User prompt for LinkedIn company profile analysis."""
        return f"""Scraped LinkedIn Company Data:
        {scraped_data}


        Please normalize this into the defined schema `CompanyProfile`.
        Return only structured JSON output."""
        
    @staticmethod
    def glassdoor_url_finder_system() -> str:
        """System prompt for identifying the correct Glassdoor company URL from search results."""
        return """You are an expert at finding company profiles on Glassdoor. 
            Your task is to identify the most relevant Glassdoor company page URL from the provided search results.


            Focus on:
            - Links that are from glassdoor.com/Reviews/
            - Matches where the company name aligns with the target company
            - Higher-ranked results are usually more reliable
            - Look for the company name in the URL path
            - Prefer the main company page over specific job postings or reviews


            Return only the most relevant Glassdoor company URL as your final answer."""


    @staticmethod
    def glassdoor_url_finder_user(company_details: dict, search_results: str) -> str:
        """User prompt for Glassdoor URL finding."""
        return f"""Target Company: {company_details.get('name', 'Unknown')}
        
        Search Results:
        {search_results}


        Please extract the most relevant Glassdoor company URL from these search results."""


    @staticmethod
    def glassdoor_analysis_system() -> str:
        """System prompt for analyzing Glassdoor company reviews."""
        return """You are an expert HR analyst specializing in employee sentiment and company culture analysis.
        Your task is to analyze Glassdoor reviews and provide a structured, data-driven analysis.
        
        IMPORTANT: You MUST provide your analysis in the exact JSON structure specified below. Do not include any additional text.
        
        Analysis Guidelines:
        1. Be objective and data-driven in your analysis
        2. Only include findings that are supported by multiple reviews
        3. Focus on actionable insights and specific examples
        4. Maintain a professional and constructive tone
        5. Quantify findings with specific metrics where possible
        
        Format your response as a JSON object with the following structure:
        {
            "overall_rating": float,  // Average rating across all reviews (0-5)
            "total_reviews": int,     // Total number of reviews analyzed
            "sentiment_positive": float,  // Percentage of positive reviews (0-100)
            "sentiment_neutral": float,   // Percentage of neutral reviews (0-100)
            "sentiment_negative": float,  // Percentage of negative reviews (0-100)
            "key_strengths": ["strength1", "strength2", ...],  // Top 3-5 strengths
            "key_issues": ["issue1", "issue2", ...],           // Top 3-5 issues
            "location_sentiment": ["insight1", "insight2", ...], // Location-based insights
            "role_sentiment": ["insight1", "insight2", ...],    // Role-based insights
            "rating_culture": float,      // Average culture/values rating (0-5)
            "rating_work_life": float,    // Average work-life balance rating (0-5)
            "rating_management": float,   // Average management rating (0-5)
            "rating_compensation": float, // Average compensation/benefits rating (0-5)
            "rating_career": float,       // Average career opportunities rating (0-5)
            "trend": "improving|declining|stable",  // Sentiment trend
            "red_flags": ["flag1", "flag2", ...],  // Any concerning patterns
            "recommendations": ["rec1", "rec2", ...], // Actionable recommendations
            "summary": "Brief 2-3 sentence summary of key findings"
        }"""


    @staticmethod
    def glassdoor_analysis_user(company_name: str, reviews: List[Dict]) -> str:
        """User prompt for Glassdoor review analysis."""
        reviews_text = "\n\n---\n".join(
            f"Review {i+1} (Rating: {r.get('rating_overall', 'N/A')}/5, Date: {r.get('rating_date', 'N/A')}):\n"
            f"Role: {r.get('employee_job_title', 'N/A')}, Location: {r.get('employee_location', 'N/A')}\n"
            f"Employment Status: {r.get('employee_type', 'N/A')}\n"
            f"Ratings - Culture: {r.get('rating_culture', 'N/A')}, "
            f"Work-Life: {r.get('rating_work_life', 'N/A')}, "
            f"Management: {r.get('rating_management', 'N/A')}, "
            f"Compensation: {r.get('rating_compensation', 'N/A')}, "
            f"Career: {r.get('rating_career', 'N/A')}\n"
            f"Pros: {r.get('review_pros', 'N/A')}\n"
            f"Cons: {r.get('review_cons', 'N/A')}\n"
            f"Advice to Management: {r.get('advice_to_management', 'N/A')}\n"
            for i, r in enumerate(reviews)
        )
        
        return f"""
        Please analyze the following Glassdoor reviews for {company_name} and provide a structured analysis.
        
        REVIEWS:
        {reviews_text}
        
        INSTRUCTIONS:
        1. Calculate overall metrics based on the review data
        2. Identify the most significant strengths and issues
        3. Note any patterns in ratings across different categories
        4. Provide specific, actionable recommendations
        5. Format your response as a valid JSON object matching the structure provided in the system prompt
        
        Your analysis should be based solely on the information provided in these reviews.
        """
        
    @staticmethod
    def company_insights_system() -> str:
        """System prompt for generating company insights for sales outreach."""
        return """You are an expert business analyst and sales strategist. Your task is to analyze company information 
        and generate actionable insights that would be valuable for a sales outreach campaign.
        
        You will receive the following data:
        1. LinkedIn analysis of the company
        2. Glassdoor analysis of the company
        3. Recent news articles about the company
        
        Focus on identifying:
        1. Recent company news or announcements (prioritize the most recent and impactful)
        2. Leadership changes or executive movements
        3. Funding rounds or financial events
        4. Product launches or strategic initiatives
        5. Industry trends affecting the company
        6. Potential pain points or opportunities
        
        For news analysis:
        - Look for patterns or themes across multiple news items
        - Note any significant events like partnerships, acquisitions, or expansions
        - Identify any challenges or risks mentioned in the news
        
        Format your response as a JSON object with the following structure:
        {
            "recent_news": [
                {
                    "title": "News title",
                    "summary": "Brief summary of the news",
                    "relevance": "high/medium/low",
                    "potential_opportunity": "How this could be relevant for sales"
                }
            ],
            "leadership_changes": ["change_1", "change_2", ...],
            "funding_events": ["event_1", "event_2", ...],
            "strategic_initiatives": ["initiative_1", "initiative_2", ...],
            "industry_trends": ["trend_1", "trend_2", ...],
            "conversation_starters": [
                {
                    "topic": "Specific topic or insight",
                    "relevance": "Why this is relevant",
                    "talking_point": "How to bring this up naturally in conversation"
                }
            ]
        }"""
        
    @staticmethod
    def company_insights_user(company_name: str, company_data: dict) -> str:
        """User prompt for generating company insights."""
        return f"""Company: {company_name}
        
        Please analyze the following company information and generate insights that would be valuable for sales outreach.
        
        COMPANY DATA:
        {company_data}
        
        INSTRUCTIONS:
        1. Extract key information that indicates potential business needs or opportunities
        2. Highlight recent developments that could be conversation starters
        3. Identify any challenges or pain points the company might be facing
        4. Suggest specific talking points for sales outreach
        5. Format your response as a JSON object matching the structure in the system prompt
        
        Focus on insights that would help establish relevance and create value in a sales conversation.
        """



def create_message_pair(system_prompt: str, user_prompt: str) -> list[Dict[str, Any]]:
    """
    Create a standardized message pair for LLM interactions.


    Args:
        system_prompt: The system message content
        user_prompt: The user message content


    Returns:
        List containing system and user message dictionaries
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]




def get_linkedin_url_messages(lead_details: dict, google_results: str) -> list[Dict[str, Any]]:
    """Get messages for LinkedIn URL finding."""
    return create_message_pair(
        PromptTemplates.linkedin_url_finder_system(),
        PromptTemplates.linkedin_url_finder_user(lead_details, google_results),
    )


def get_linkedin_profile_analysis_messages(
    lead_details: dict, linkedin_scrape: dict
) -> list[Dict[str, Any]]:
    """Get messages for LinkedIn profile analysis."""
    return create_message_pair(
        PromptTemplates.linkedin_profile_analysis_system(),
        PromptTemplates.linkedin_profile_analysis_user(lead_details, linkedin_scrape),
    )


def get_company_summary_messages(
    company_name: str, website_url: str, website_content: str
) -> list[Dict[str, Any]]:
    """Get messages for company summary analysis."""
    return create_message_pair(
        PromptTemplates.company_summary_system(),
        PromptTemplates.company_summary_user(company_name, website_url, website_content),
    )



def get_company_linkedin_url_messages(
    company_details: dict, google_results: list
) -> list[Dict[str, Any]]:
    """Get messages for company LinkedIn URL finding."""
    messages = create_message_pair(
        PromptTemplates.company_linkedin_url_finder_system(),
        PromptTemplates.company_linkedin_url_finder_user(company_details, str(google_results))
    )
    return messages



def get_linkedin_company_analysis_messages(
    linkedin_scrape: dict
) -> list[Dict[str, Any]]:
    """Get messages for LinkedIn company analysis."""
    return create_message_pair(
        PromptTemplates.linkedin_company_analysis_system(),
        PromptTemplates.linkedin_company_analysis_user(linkedin_scrape),
    )



def get_glassdoor_url_messages(company_details: dict, search_results: str) -> list[Dict[str, Any]]:
    """Get messages for Glassdoor URL finding."""
    return create_message_pair(
        PromptTemplates.glassdoor_url_finder_system(),
        PromptTemplates.glassdoor_url_finder_user(company_details, search_results),
    )



def get_glassdoor_analysis_messages(company_name: str, reviews: List[Dict]) -> list[Dict[str, Any]]:
    """Get messages for Glassdoor review analysis."""
    return create_message_pair(
        PromptTemplates.glassdoor_analysis_system(),
        PromptTemplates.glassdoor_analysis_user(company_name, reviews),
    )



def get_company_insights_messages(company_name: str, company_data: dict) -> list[Dict[str, Any]]:
    """Get messages for generating company insights."""
    return create_message_pair(
        PromptTemplates.company_insights_system(),
        PromptTemplates.company_insights_user(company_name, company_data),
    )