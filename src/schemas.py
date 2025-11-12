"""
Pydantic models for structured JSON output from OpenAI API.
"""
from pydantic import BaseModel, Field
from typing import List


class LinkRecommendation(BaseModel):
    """Schema for research link recommendations."""

    general_objective: str = Field(
        description="The general investment analysis objective (e.g., Market & Competition)"
    )
    sub_objective: str = Field(
        description="The specific sub-objective being researched"
    )
    links: List[str] = Field(
        description="List of 20 URLs recommended as research sources",
        min_items=20,
        max_items=20
    )


class CompanyResearchOutput(BaseModel):
    """Complete research output for a company analysis."""

    company_name: str = Field(description="Name of the company being analyzed")
    general_objective: str = Field(description="The general investment analysis objective")
    research_results: List[LinkRecommendation] = Field(
        description="List of research link recommendations for each sub-objective"
    )


# Layer 2 Models - Content Analysis & Extraction

class InformationPiece(BaseModel):
    """Individual piece of extracted information from web content."""

    content: str = Field(
        description="Extracted information content (max 2000 characters)",
        max_length=2000
    )
    confidence_score: int = Field(
        description="Confidence score 0-100 based on source credibility and data quality",
        ge=0,
        le=100
    )
    source_url: str = Field(description="The URL source of this information")


class SubObjectiveAnalysis(BaseModel):
    """Analysis results for a single sub-objective."""

    general_objective: str = Field(description="The general investment analysis objective")
    sub_objective: str = Field(description="The specific sub-objective analyzed")
    information_pieces: List[InformationPiece] = Field(
        description="Extracted information pieces with confidence scores",
        min_items=0
    )
    scraped_sources_count: int = Field(
        description="Number of web sources successfully scraped",
        ge=0
    )


class Layer2Output(BaseModel):
    """Complete Layer 2 analysis output."""

    company_name: str = Field(description="Name of the company being analyzed")
    general_objective: str = Field(description="The general investment analysis objective")
    total_sub_objectives: int = Field(description="Total number of sub-objectives processed")
    successful: int = Field(description="Number of successfully analyzed sub-objectives")
    failed: int = Field(description="Number of failed sub-objectives")
    failed_sub_objectives: List[str] = Field(
        description="List of sub-objectives that failed analysis"
    )
    analysis_results: List[SubObjectiveAnalysis] = Field(
        description="Detailed analysis results for each sub-objective"
    )
