"""
Layer 2 Investment Analyst - Content Analysis & Extraction Service
Analyzes scraped web content to extract relevant insights with confidence scoring
"""

import os
import asyncio
from typing import List, Dict, Optional
from openai import OpenAI
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Layer 2 System Prompt - Investment Analyst Content Extraction
SYSTEM_PROMPT_LAYER2 = """You are a senior investment analyst with over 5 years of experience in venture capital and private equity research. Your expertise lies in analyzing market research, competitive intelligence, and company data to provide actionable insights for investment decisions.

**YOUR TASK:**
You will receive scraped content from multiple web sources related to a specific research objective and sub-objective. Your job is to:

1. **Carefully read and analyze** all the provided web content
2. **Extract the most relevant and valuable information** that directly addresses the objective and sub-objective
3. **Synthesize insights** from multiple sources when they provide complementary information
4. **Assess confidence** in each extracted piece based on:
   - Source credibility (e.g., Gartner, Forrester = high; unknown blog = low)
   - Data recency (recent data = higher confidence)
   - Specificity and detail level (specific numbers/facts = higher confidence)
   - Consistency across multiple sources (corroborated = higher confidence)

**OUTPUT REQUIREMENTS:**
- Extract **5-15 distinct information pieces** (not more, not less)
- Each piece should be **relevant, specific, and actionable** for investment analysis
- Each piece must be **max 2000 characters** (concise but detailed)
- Include specific numbers, dates, company names, market figures when available
- Assign a **confidence score (0-100)** to each piece
- Cite the **source URL** for each piece

**CONFIDENCE SCORING GUIDE:**
- 90-100: High-credibility source (Gartner, Forrester, McKinsey, SEC filings) with recent, specific data
- 70-89: Reputable source (TechCrunch, Bloomberg, WSJ) with good detail and recency
- 50-69: Moderate source (industry blogs, company websites) or older data from good sources
- 30-49: Lower-credibility source or very general information
- 10-29: Questionable source or outdated/vague information

**EXAMPLE OUTPUT (for sub-objective "TAM/SAM/SOM for legal tech AI market"):**
```json
{
  "information_pieces": [
    {
      "content": "According to Gartner's 2024 Legal Technology Market Analysis, the global legal tech market is valued at $29.4 billion in 2024 and is projected to grow at a CAGR of 14.2% to reach $57.3 billion by 2029. The AI-powered legal automation segment specifically accounts for $8.7 billion (29.6% of total market) and is growing at 22.3% CAGR. North America represents 48% of the market ($14.1B), followed by Europe (28%, $8.2B) and Asia-Pacific (18%, $5.3B).",
      "confidence_score": 95,
      "source_url": "https://www.gartner.com/en/documents/legal-tech-market-analysis-2024"
    },
    {
      "content": "Thomson Reuters' 2024 State of Legal Tech report surveyed 2,300 law firms and found that 67% of large firms (500+ attorneys) have adopted AI-powered contract review tools, up from 34% in 2022. The report identifies contract analysis, legal research, and document automation as the three highest-adoption areas. Average deal size for enterprise legal tech solutions ranges from $150K-$800K annually, with 3-5 year contracts being standard.",
      "confidence_score": 92,
      "source_url": "https://www.thomsonreuters.com/en/reports/legal-tech-market-2024.html"
    },
    {
      "content": "CB Insights Legal Tech Market Map (Q2 2024) identifies 347 active legal tech startups globally, with $2.1 billion in venture funding deployed in 2023. The report segments the market into 12 categories, with AI-powered research & analytics receiving the most funding ($680M, 32% of total). Notable trends include consolidation among mid-market players and increasing enterprise adoption of multi-product platforms rather than point solutions.",
      "confidence_score": 88,
      "source_url": "https://www.cbinsights.com/research/legal-tech-market-landscape/"
    }
  ]
}
```

**IMPORTANT:**
- Focus on INVESTMENT-RELEVANT information (market size, growth rates, competitive dynamics, customer adoption, pricing, TAM/SAM/SOM)
- Avoid generic descriptions - prioritize specific data points, figures, and insights
- If sources contradict each other, mention both perspectives with confidence scores reflecting the conflict
- Skip information that is too vague, promotional, or off-topic
- Each information piece should stand alone and be immediately useful to an investor"""


class InvestmentAnalystLayer2:
    """
    Layer 2 Investment Analyst Service - Extracts insights from scraped web content
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Layer 2 analyst service

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # Use GPT-4o for better analysis quality

    def analyze_sub_objective(
        self,
        general_objective: str,
        sub_objective: str,
        scraped_contents: List[Dict[str, str]],
        max_retries: int = 3
    ) -> Optional[Dict]:
        """
        Analyze scraped content for a single sub-objective

        Args:
            general_objective: The general research objective
            sub_objective: The specific sub-objective
            scraped_contents: List of scraped content dicts with 'url' and 'content'
            max_retries: Maximum number of retry attempts

        Returns:
            Dict with extracted information pieces, or None if failed
        """
        if not scraped_contents:
            logger.warning(f"No scraped content available for sub-objective: {sub_objective}")
            return None

        # Build the user prompt with all scraped content
        user_prompt = self._build_user_prompt(general_objective, sub_objective, scraped_contents)

        # Define the JSON schema for response validation
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "information_extraction",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "information_pieces": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "content": {"type": "string"},
                                    "confidence_score": {"type": "integer"},
                                    "source_url": {"type": "string"}
                                },
                                "required": ["content", "confidence_score", "source_url"],
                                "additionalProperties": False
                            },
                            "minItems": 5,
                            "maxItems": 15
                        }
                    },
                    "required": ["information_pieces"],
                    "additionalProperties": False
                }
            }
        }

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                logger.info(f"Analyzing sub-objective: {sub_objective} (attempt {attempt + 1}/{max_retries})")

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_LAYER2},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format=response_format,
                    temperature=0.5,  # Balance between creativity and consistency
                    max_tokens=4000
                )

                # Parse the response
                result = eval(response.choices[0].message.content)

                # Validate and truncate content to 2000 chars
                for piece in result["information_pieces"]:
                    if len(piece["content"]) > 2000:
                        piece["content"] = piece["content"][:1997] + "..."

                logger.info(f"Successfully analyzed sub-objective: {sub_objective} "
                           f"({len(result['information_pieces'])} pieces extracted)")

                return result

            except Exception as e:
                logger.error(f"Error analyzing sub-objective (attempt {attempt + 1}): {str(e)}")

                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to analyze sub-objective after {max_retries} attempts: {sub_objective}")
                    return None

        return None

    def _build_user_prompt(
        self,
        general_objective: str,
        sub_objective: str,
        scraped_contents: List[Dict[str, str]]
    ) -> str:
        """
        Build the user prompt with all scraped content

        Args:
            general_objective: The general research objective
            sub_objective: The specific sub-objective
            scraped_contents: List of scraped content dicts

        Returns:
            Formatted user prompt string
        """
        # Limit total content to avoid token limits (approx 80K chars = 20K tokens)
        max_total_chars = 80000
        truncated_contents = []
        current_chars = 0

        for item in scraped_contents:
            content = item["content"]
            url = item["url"]

            if current_chars + len(content) > max_total_chars:
                # Truncate this content to fit
                remaining = max_total_chars - current_chars
                if remaining > 1000:  # Only include if at least 1000 chars available
                    content = content[:remaining]
                    truncated_contents.append({"url": url, "content": content})
                break
            else:
                truncated_contents.append({"url": url, "content": content})
                current_chars += len(content)

        # Build the prompt
        prompt = f"""**RESEARCH OBJECTIVE:**
General Objective: {general_objective}
Sub-Objective: {sub_objective}

**TASK:**
Analyze the following web content from {len(truncated_contents)} sources and extract the most relevant, valuable insights that address the research objective. Focus on investment-relevant information: market sizing, growth trends, competitive dynamics, customer adoption, pricing, and strategic opportunities.

Extract 5-15 distinct information pieces, each with:
- Specific, actionable content (max 2000 characters)
- Confidence score (0-100) based on source credibility, recency, and specificity
- Source URL

**SCRAPED WEB CONTENT:**

"""

        # Add each scraped content with URL
        for i, item in enumerate(truncated_contents, 1):
            prompt += f"\n{'='*80}\n"
            prompt += f"SOURCE {i}: {item['url']}\n"
            prompt += f"{'='*80}\n"
            prompt += f"{item['content']}\n\n"

        prompt += f"\n{'='*80}\n"
        prompt += "**NOW EXTRACT THE INFORMATION PIECES IN JSON FORMAT AS SPECIFIED.**"

        return prompt

    def analyze_batch(
        self,
        company_name: str,
        general_objective: str,
        sub_objectives_with_content: List[Dict]
    ) -> Dict:
        """
        Analyze multiple sub-objectives in batch

        Args:
            company_name: Name of the company being researched
            general_objective: The general research objective
            sub_objectives_with_content: List of dicts with 'sub_objective' and 'scraped_contents'

        Returns:
            Complete Layer 2 analysis results
        """
        results = []
        successful = 0
        failed = 0
        failed_sub_objectives = []

        for item in sub_objectives_with_content:
            sub_objective = item["sub_objective"]
            scraped_contents = item["scraped_contents"]

            logger.info(f"Processing sub-objective: {sub_objective} "
                       f"({len(scraped_contents)} scraped pages)")

            analysis = self.analyze_sub_objective(
                general_objective=general_objective,
                sub_objective=sub_objective,
                scraped_contents=scraped_contents
            )

            if analysis:
                results.append({
                    "general_objective": general_objective,
                    "sub_objective": sub_objective,
                    "information_pieces": analysis["information_pieces"],
                    "scraped_sources_count": len(scraped_contents)
                })
                successful += 1
            else:
                failed += 1
                failed_sub_objectives.append(sub_objective)

        return {
            "company_name": company_name,
            "general_objective": general_objective,
            "total_sub_objectives": len(sub_objectives_with_content),
            "successful": successful,
            "failed": failed,
            "failed_sub_objectives": failed_sub_objectives,
            "analysis_results": results
        }
