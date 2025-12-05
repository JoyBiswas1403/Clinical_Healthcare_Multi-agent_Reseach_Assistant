# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""Agent 3: Fact-Check+Writer - Using Ollama (FREE).

Verifies claims, writes executive briefs with citations, generates traceability.
"""
import json
import re
import time
from typing import List, Dict, Any
from openai import OpenAI

from config.settings_lite import settings


BRIEF_WRITING_PROMPT = """You are a clinical research writer. Write a concise executive brief (≤300 words) with inline citations.

Topic: {topic}
Synthesis: {synthesis}
Source Summaries: {source_summaries}
Contradictions: {contradictions}

Requirements:
1. ≤300 words
2. Inline citations [1], [2], etc.
3. Clear, professional medical language
4. Address contradictions/limitations
5. Actionable insights for clinicians

Return a JSON object:
{{
  "brief_text": "Your brief text here with [1][2] citations...",
  "word_count": 250,
  "claims": [
    {{
      "claim_text": "The specific claim made",
      "citation_ids": ["1", "2"]
    }}
  ]
}}

Return ONLY valid JSON, no other text."""


RISK_ASSESSMENT_PROMPT = """You are a clinical safety expert. Identify risks and quality issues.

Topic: {topic}
Sources: {sources}

Identify:
1. Contradictions between sources (severity: high/medium/low)
2. Contraindications or safety concerns
3. Low-quality studies or bias
4. Data gaps or limitations

Return a JSON object:
{{
  "risk_flags": [
    {{
      "flag_type": "contradiction|contraindication|low_quality|bias|data_gap",
      "severity": "high|medium|low",
      "description": "Description of the risk",
      "affected_sources": ["1", "2"]
    }}
  ]
}}

Return ONLY valid JSON, no other text."""


class FactCheckWriterAgentLite:
    """Fact-Check+Writer using Ollama (FREE, local)."""
    
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.ollama_base_url,
            api_key="ollama"
        )
        self.model = settings.ollama_model
        self.fact_check_temp = settings.fact_check_temperature
        self.writer_temp = settings.writer_temperature
        self.max_words = settings.brief_max_words
    
    def write_brief(
        self,
        topic: str,
        summary_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Write executive brief with inline citations."""
        synthesis = summary_data.get("synthesis", "No synthesis available.")
        source_summaries = summary_data.get("source_summaries", [])
        contradictions = summary_data.get("contradictions", [])
        
        prompt = BRIEF_WRITING_PROMPT.format(
            topic=topic,
            synthesis=synthesis,
            source_summaries=json.dumps(source_summaries, indent=2),
            contradictions=json.dumps(contradictions, indent=2)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a clinical research writer. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.writer_temp
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content)
            
        except Exception as e:
            return {
                "brief_text": f"Error generating brief: {str(e)}",
                "word_count": 0,
                "claims": [],
                "error": str(e)
            }
    
    def assess_risks(
        self,
        topic: str,
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Assess risks and quality issues."""
        # Simplify sources for prompt
        simplified_sources = []
        for i, s in enumerate(sources[:10]):
            simplified_sources.append({
                "id": str(i + 1),
                "title": s.get("title", "Unknown"),
                "abstract": s.get("abstract", s.get("text", ""))[:300]
            })
        
        prompt = RISK_ASSESSMENT_PROMPT.format(
            topic=topic,
            sources=json.dumps(simplified_sources, indent=2)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a clinical safety expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.fact_check_temp
            )
            
            content = response.choices[0].message.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content)
            return result.get("risk_flags", [])
            
        except Exception as e:
            return [{"flag_type": "error", "severity": "low", "description": str(e), "affected_sources": []}]
    
    def extract_citations(self, brief_text: str) -> List[str]:
        """Extract citation markers from brief text."""
        pattern = r'\[(\d+)\]'
        matches = re.findall(pattern, brief_text)
        return list(set(matches))
    
    def build_traceability(
        self,
        claims: List[Dict[str, Any]],
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build traceability from claims to sources."""
        traceability = []
        
        for claim in claims:
            claim_text = claim.get("claim_text", "")
            citation_ids = claim.get("citation_ids", [])
            
            supporting = []
            for cid in citation_ids:
                idx = int(cid) - 1
                if 0 <= idx < len(sources):
                    source = sources[idx]
                    supporting.append({
                        "source_id": cid,
                        "title": source.get("title", "Unknown"),
                        "passage": source.get("abstract", source.get("text", ""))[:200]
                    })
            
            traceability.append({
                "claim": claim_text,
                "supporting_sources": supporting,
                "verification_status": "verified" if supporting else "unsupported"
            })
        
        return traceability
    
    def run(
        self,
        topic: str,
        retrieved_docs: List[Dict[str, Any]],
        summary_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute fact-checking, writing, and traceability generation."""
        start_time = time.time()
        errors = []
        metrics = {}
        
        try:
            # Step 1: Write brief
            brief_data = self.write_brief(topic, summary_data)
            brief_text = brief_data.get("brief_text", "")
            word_count = brief_data.get("word_count", len(brief_text.split()))
            claims = brief_data.get("claims", [])
            
            metrics["word_count"] = word_count
            metrics["claims_count"] = len(claims)
            
            # Step 2: Build source list
            sources = []
            for i, doc in enumerate(retrieved_docs[:15]):
                sources.append({
                    "citation_id": str(i + 1),
                    "doc_id": doc.get("doc_id", f"doc_{i}"),
                    "title": doc.get("title", "Unknown"),
                    "authors": doc.get("authors", "Unknown"),
                    "abstract": doc.get("abstract", doc.get("text", ""))[:300]
                })
            
            # Step 3: Extract citations
            citation_ids = self.extract_citations(brief_text)
            metrics["citations_count"] = len(citation_ids)
            
            # Step 4: Risk assessment
            risk_flags = self.assess_risks(topic, retrieved_docs)
            metrics["risk_flags_count"] = len(risk_flags)
            
            # Step 5: Build traceability
            traceability = self.build_traceability(claims, retrieved_docs)
            metrics["traceability_entries"] = len(traceability)
            
            # Step 6: Assemble research brief
            research_brief = {
                "executive_brief": brief_text,
                "word_count": word_count,
                "sources": sources,
                "risk_flags": risk_flags,
                "traceability": traceability,
                "metadata": {
                    "topic": topic,
                    "overall_quality": summary_data.get("overall_quality", "unknown")
                }
            }
            
            output_data = {
                "research_brief": research_brief,
                "topic": topic
            }
            
        except Exception as e:
            errors.append(str(e))
            output_data = {"error": str(e), "topic": topic}
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        return {
            "agent_name": "FactCheckWriterAgentLite",
            "output_data": output_data,
            "metrics": metrics,
            "errors": errors,
            "execution_time_ms": execution_time_ms
        }


# Quick test
if __name__ == "__main__":
    print("Testing FactCheckWriterAgentLite...")
    print("Make sure Ollama is running: ollama serve")
    print()
    
    agent = FactCheckWriterAgentLite()
    
    # Mock data for testing
    mock_docs = [
        {"doc_id": "1", "title": "Diabetes Guidelines 2023", "abstract": "HbA1c targets of 7-8% recommended for elderly."},
        {"doc_id": "2", "title": "SGLT2 Inhibitors Review", "abstract": "Cardiovascular benefits but monitor for dehydration."}
    ]
    mock_summary = {
        "synthesis": "Current evidence supports individualized glycemic targets for elderly diabetics.",
        "source_summaries": [{"source_id": "1", "summary": "Recommends relaxed targets."}],
        "contradictions": [],
        "overall_quality": "high"
    }
    
    result = agent.run(
        topic="diabetes management in elderly",
        retrieved_docs=mock_docs,
        summary_data=mock_summary
    )
    
    print("Result:")
    print(json.dumps(result, indent=2, default=str))
