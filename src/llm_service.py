"""
LLM service for generating investment research link recommendations.
"""
import os
import json
import time
from typing import Optional, Dict, Any
from openai import OpenAI
from .schemas import LinkRecommendation


class InvestmentAnalystLLM:
    """Service for generating research links using OpenAI's GPT-4o-mini."""

    SYSTEM_PROMPT = """You are a senior investment analyst with 5+ years of experience in top-tier VC investment analytics and due diligence.

Your role is to provide SPECIFIC, HIGH-QUALITY research sources (URLs) that can be used for professional investment analysis presentations comparing companies in various sectors.

You understand that thorough investment analysis requires:
- Industry reports and market research from reputable sources (Gartner, Forrester, CB Insights, PitchBook)
- Financial data and company filings (Crunchbase, SEC filings, company investor relations pages)
- News articles from business publications (TechCrunch, The Information, Bloomberg, WSJ)
- Industry-specific publications and trade journals
- Academic research and white papers
- Competitive analysis reports
- Expert commentary and thought leadership pieces

IMPORTANT: You must provide EXACTLY 20 specific, diverse, and relevant URLs for each research query.

EXAMPLE:

Input:
- Company: "Harvey AI"
- General Objective: "Market & Competition"
- Sub-Objective: "TAM/SAM/SOM for legal tech AI specifically"

Expected Output:
{
  "general_objective": "Market & Competition",
  "sub_objective": "TAM/SAM/SOM for legal tech AI specifically",
  "links": [
    "https://www.gartner.com/en/documents/legal-technology-market-analysis-2024",
    "https://www.mckinsey.com/industries/legal/our-insights/legal-tech-market-sizing",
    "https://www.thomsonreuters.com/en/reports/legal-tech-market-2024.html",
    "https://www.grandviewresearch.com/industry-analysis/legal-tech-market",
    "https://www.statista.com/statistics/legal-technology-market-size/",
    "https://www.marketsandmarkets.com/Market-Reports/legal-tech-market.html",
    "https://pitchbook.com/news/reports/legal-tech-market-map-2024",
    "https://www.cbinsights.com/research/legal-tech-market-landscape/",
    "https://www.forrester.com/report/legal-technology-market-forecast/",
    "https://www.idc.com/getdoc.jsp?containerId=legal-tech-tam",
    "https://www.bloomberg.com/news/articles/legal-tech-industry-size-projections",
    "https://www.pwc.com/legal-tech-market-analysis-2024",
    "https://www2.deloitte.com/insights/legal-tech-opportunities.html",
    "https://www.accenture.com/legal-technology-market-trends",
    "https://www.bain.com/insights/legal-services-technology-disruption/",
    "https://www.bcg.com/publications/legal-tech-market-opportunity",
    "https://www.legalexecutiveinstitute.com/market-sizing-legal-tech/",
    "https://www.artificiallawyer.com/legal-ai-market-analysis-2024/",
    "https://www.law.com/legaltechnews/market-size-legal-ai/",
    "https://www.abajournal.com/magazine/article/legal-tech-market-research"
  ]
}

Your recommendations should:
1. Cover diverse source types (research firms, news, academic, industry publications)
2. Include both established sources and specialized industry publications
3. Prioritize sources likely to have the specific data requested
4. Include URLs that would be realistic for the given query
5. Ensure all 20 links are distinct and non-repetitive"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM service.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env variable.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key to constructor."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"

    def generate_research_links(
        self,
        company_name: str,
        general_objective: str,
        sub_objective: str,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> Optional[LinkRecommendation]:
        """
        Generate research link recommendations for a specific sub-objective.

        Args:
            company_name: Name of the company being analyzed
            general_objective: The general investment analysis objective
            sub_objective: The specific sub-objective to research
            max_retries: Maximum number of retry attempts on failure
            retry_delay: Delay in seconds between retries (with exponential backoff)

        Returns:
            LinkRecommendation object with the results, or None if all retries fail
        """
        user_prompt = f"""Generate research link recommendations for the following investment analysis:

Company: {company_name}
General Objective: {general_objective}
Sub-Objective: {sub_objective}

Provide EXACTLY 20 high-quality, specific URLs that would be valuable research sources for analyzing this sub-objective in the context of {company_name}.

Focus on sources that would help understand:
- Market data and sizing
- Competitive landscape
- Industry trends and insights
- Company-specific information
- Expert analysis and commentary

Ensure the links are diverse (different types of sources) and highly relevant to the specific sub-objective."""

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "link_recommendation",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "general_objective": {
                                        "type": "string",
                                        "description": "The general investment analysis objective",
                                    },
                                    "sub_objective": {
                                        "type": "string",
                                        "description": "The specific sub-objective being researched",
                                    },
                                    "links": {
                                        "type": "array",
                                        "description": "List of 20 URLs recommended as research sources",
                                        "items": {"type": "string"},
                                        "minItems": 20,
                                        "maxItems": 20,
                                    },
                                },
                                "required": [
                                    "general_objective",
                                    "sub_objective",
                                    "links",
                                ],
                                "additionalProperties": False,
                            },
                        },
                    },
                    temperature=0.7,
                )

                # Parse and validate response
                content = response.choices[0].message.content
                data = json.loads(content)
                result = LinkRecommendation(**data)

                return result

            except Exception as e:
                error_msg = f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}"
                print(f"⚠️  {error_msg}")

                if attempt < max_retries - 1:
                    # Exponential backoff
                    sleep_time = retry_delay * (2**attempt)
                    print(f"   Retrying in {sleep_time:.1f} seconds...")
                    time.sleep(sleep_time)
                else:
                    print(f"❌ All retries exhausted for sub-objective: {sub_objective}")
                    return None

        return None

    def generate_batch_research(
        self,
        company_name: str,
        general_objective: str,
        sub_objectives: list[str],
    ) -> Dict[str, Any]:
        """
        Generate research links for multiple sub-objectives.

        Args:
            company_name: Name of the company being analyzed
            general_objective: The general investment analysis objective
            sub_objectives: List of sub-objectives to research

        Returns:
            Dictionary containing all results and metadata
        """
        results = []
        failed_objectives = []

        print(f"\n🔍 Generating research links for {company_name}")
        print(f"📊 General Objective: {general_objective}\n")

        for i, sub_obj in enumerate(sub_objectives, 1):
            print(f"[{i}/{len(sub_objectives)}] Processing: {sub_obj}")

            result = self.generate_research_links(
                company_name=company_name,
                general_objective=general_objective,
                sub_objective=sub_obj,
            )

            if result:
                results.append(result.model_dump())
                print(f"✅ Successfully generated {len(result.links)} links\n")
            else:
                failed_objectives.append(sub_obj)
                print(f"❌ Failed to generate links\n")

        return {
            "company_name": company_name,
            "general_objective": general_objective,
            "total_sub_objectives": len(sub_objectives),
            "successful": len(results),
            "failed": len(failed_objectives),
            "failed_objectives": failed_objectives,
            "research_results": results,
        }
