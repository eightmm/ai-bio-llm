"""
LLM-based DB List Extractor

This module uses an LLM to extract data references from problem text.
"""

import json
import logging
import os
from typing import Dict, List
from openai import OpenAI

logger = logging.getLogger(__name__)


class DBListExtractor:
    """Extract database/file references from problem text using LLM"""

    def __init__(self):
        """Initialize the extractor with OpenRouter API configuration"""
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.model = os.getenv('DEFAULT_MODEL', 'anthropic/claude-3.5-sonnet')

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def extract_db_list(self, brain_output: Dict) -> List[str]:
        """
        Extract database/file references from brain module output using LLM.

        Args:
            brain_output: Dictionary containing 'original_problem_text', 'DB_list', etc.

        Returns:
            List of data reference strings (e.g., ["Q5", "exhaustion_signature", "Q5.exhaustion_signature"])
        """
        try:
            # Get problem text and existing DB_list
            problem_text = brain_output.get('original_problem_text', '')
            existing_db_list = brain_output.get('DB_list', '')

            if not problem_text:
                logger.warning("No original_problem_text found in brain_output")
                return []

            # Create prompt for LLM
            prompt = self._create_extraction_prompt(problem_text, existing_db_list)

            # Call LLM
            logger.info(f"Calling LLM ({self.model}) to extract DB references...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a bioinformatics data analyst assistant. Extract data file and folder references from research problem descriptions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500
            )

            # Parse response
            extracted_text = response.choices[0].message.content.strip()
            logger.info(f"LLM response: {extracted_text}")

            # Parse the extracted references
            db_refs = self._parse_llm_response(extracted_text)

            logger.info(f"Extracted {len(db_refs)} data references using LLM: {db_refs}")
            return db_refs

        except Exception as e:
            logger.error(f"Error during LLM-based extraction: {e}")
            return []

    def _create_extraction_prompt(self, problem_text: str, existing_db_list: str) -> str:
        """Create prompt for LLM to extract data references"""
        prompt = f"""Analyze the following research problem description and extract ALL data-related references.

**Problem Description:**
{problem_text}

**Existing DB_list:**
{existing_db_list}

**Task:**
Extract all data file names, folder names, and data identifiers mentioned in the problem. Include:
1. Question/section identifiers (e.g., Q1, Q2, Q5)
2. File names with extensions (e.g., active-control.pod5, active-cre.bam)
3. Data folder or dataset names (e.g., exhaustion_signature, polyA_data)
4. Combinations of identifiers (e.g., Q5.exhaustion_signature)

**Output Format:**
Return ONLY a comma-separated list of identifiers, nothing else.
Example: Q5, exhaustion_signature, Q5.exhaustion_signature, active-control.pod5, active-cre.bam

**Your response (comma-separated list only):**"""

        return prompt

    def _parse_llm_response(self, response_text: str) -> List[str]:
        """
        Parse LLM response to extract list of references.

        Args:
            response_text: Raw text from LLM

        Returns:
            List of cleaned reference strings
        """
        # Remove common prefixes/explanations
        response_text = response_text.strip()

        # If response contains multiple lines, use the last non-empty line
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        if lines:
            response_text = lines[-1]

        # Split by comma and clean each reference
        refs = []
        for ref in response_text.split(','):
            ref = ref.strip()
            # Remove quotes and extra whitespace
            ref = ref.strip('"\'` ')
            if ref:
                refs.append(ref)

        return refs
