# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""Agent 1: Query+Filter - Using Ollama (FREE).

Expands clinical queries into optimized searches with MeSH terms.
"""
import json
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI

from config.settings_lite import settings


QUERY_EXPANSION_PROMPT = """You are a clinical research query expert. Given a research topic, expand it into:
1. 3-5 optimized search queries for academic databases
2. Key MeSH terms and synonyms
3. Exclusion criteria (irrelevant topics to filter out)
4. Source type priorities (RCT, meta-analysis, clinical guidelines, etc.)

Topic: {topic}

Return a JSON object with:
{{
  "expanded_queries": ["query1", "query2", ...],
  "mesh_terms": ["term1", "term2", ...],
  "synonyms": {{"concept": ["syn1", "syn2"]}},
  "exclusion_criteria": ["criterion1", "criterion2", ...],
  "source_priorities": ["type1", "type2", ...]
}}

Return ONLY valid JSON, no other text."""


class QueryFilterAgentLite:
    """Query expansion agent using Ollama (FREE, local)."""
    
    def __init__(self):
        # Connect to Ollama's OpenAI-compatible API
        self.client = OpenAI(
            base_url=settings.ollama_base_url,
            api_key="ollama"  # Ollama doesn't need a real key
        )
        self.model = settings.ollama_model
        self.temperature = settings.query_filter_temperature
    
    def expand_query(self, topic: str) -> Dict[str, Any]:
        """Expand a research topic into optimized search queries."""
        prompt = QUERY_EXPANSION_PROMPT.format(topic=topic)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a clinical research query expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            # Sometimes models wrap JSON in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            # Return a reasonable default if JSON parsing fails
            return {
                "expanded_queries": [topic],
                "mesh_terms": [],
                "synonyms": {},
                "exclusion_criteria": [],
                "source_priorities": ["meta_analysis", "rct", "clinical_guideline"],
                "parse_error": str(e)
            }
        except Exception as e:
            return {
                "expanded_queries": [topic],
                "mesh_terms": [],
                "synonyms": {},
                "exclusion_criteria": [],
                "source_priorities": [],
                "error": str(e)
            }
    
    def run(
        self,
        topic: str,
        max_sources: int = 15,
        quality_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Execute the full query+filter pipeline."""
        start_time = time.time()
        errors = []
        metrics = {}
        
        try:
            # Expand query
            expansion = self.expand_query(topic)
            metrics["expanded_queries_count"] = len(expansion.get("expanded_queries", []))
            metrics["mesh_terms_count"] = len(expansion.get("mesh_terms", []))
            
            output_data = {
                "expansion": expansion,
                "topic": topic,
                "max_sources": max_sources,
                "quality_threshold": quality_threshold
            }
            
        except Exception as e:
            errors.append(str(e))
            output_data = {"error": str(e), "topic": topic}
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return {
            "agent_name": "QueryFilterAgentLite",
            "output_data": output_data,
            "metrics": metrics,
            "errors": errors,
            "execution_time_ms": execution_time_ms
        }


# Quick test
if __name__ == "__main__":
    print("Testing QueryFilterAgentLite with Ollama...")
    print("Make sure Ollama is running: ollama serve")
    print()
    
    agent = QueryFilterAgentLite()
    result = agent.run("diabetes management in elderly patients")
    
    print("Result:")
    print(json.dumps(result, indent=2))
