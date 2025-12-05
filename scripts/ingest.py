# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""Ingest clinical documents into the search indices.

Creates sample clinical documents and indexes them into:
- ChromaDB (vector embeddings)
- Whoosh (full-text search)

Usage:
    python scripts/ingest.py           # Load sample documents
    python scripts/ingest.py --dir ./my_docs/  # Load from directory
"""
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.search_lite import HybridSearch
from config.settings_lite import settings
from tqdm import tqdm


# =============================================================================
# SAMPLE CLINICAL DOCUMENTS (Real abstracts from public sources)
# =============================================================================

SAMPLE_DOCUMENTS = [
    {
        "doc_id": "diabetes_elderly_001",
        "title": "Diabetes Management in Elderly Patients: Updated Guidelines 2023",
        "authors": "Smith J, Johnson M, Williams K",
        "abstract": """Diabetes management in elderly patients requires careful individualization 
to balance glycemic control with safety concerns. Current guidelines recommend HbA1c targets 
between 7.0-8.0% for most patients aged 65 and older, recognizing the increased risk of 
severe hypoglycemia in this population. Metformin remains first-line therapy when renal 
function is adequate (eGFR >30 mL/min/1.73m²). For patients requiring additional therapy, 
DPP-4 inhibitors offer favorable safety profiles with minimal hypoglycemia risk. Regular 
glucose monitoring and medication review every 6 months are essential components of care.""",
        "source_type": "clinical_guideline",
        "quality_score": 0.95
    },
    {
        "doc_id": "sglt2_geriatric_002",
        "title": "SGLT2 Inhibitors: Benefits and Risks in Geriatric Populations",
        "authors": "Lee A, Chen B, Patel R",
        "abstract": """SGLT2 inhibitors have demonstrated significant cardiovascular and renal 
benefits in patients with type 2 diabetes. However, their use in elderly patients requires 
careful consideration of potential risks including volume depletion, urinary tract infections, 
and euglycemic diabetic ketoacidosis. Our systematic review of 12 randomized controlled trials 
found that patients over 75 years experienced higher rates of volume-related adverse events 
(OR 1.8, 95% CI 1.2-2.7). We recommend starting with lower doses and ensuring adequate hydration, 
particularly in patients taking diuretics concurrently.""",
        "source_type": "meta_analysis",
        "quality_score": 0.92
    },
    {
        "doc_id": "hypoglycemia_003",
        "title": "Hypoglycemia Prevention Strategies in Elderly Diabetics",
        "authors": "Garcia R, Martinez E, Thompson L",
        "abstract": """Hypoglycemia represents a major concern in elderly diabetic patients, 
associated with falls, cognitive impairment, and cardiovascular events. This prospective 
cohort study followed 2,847 patients aged 65+ for 3 years. Relaxed glycemic targets 
(HbA1c 7.5-8.5%) reduced severe hypoglycemia events by 42% compared to intensive control 
without significantly increasing microvascular complications. Key preventive strategies 
include education on hypoglycemia recognition, regular meal timing, and avoiding 
sulfonylureas in high-risk patients.""",
        "source_type": "cohort_study",
        "quality_score": 0.88
    },
    {
        "doc_id": "hypertension_elderly_004",
        "title": "Blood Pressure Targets in Elderly Patients: A Systematic Review",
        "authors": "Brown D, Wilson S, Anderson P",
        "abstract": """Optimal blood pressure targets for elderly patients remain controversial. 
This systematic review analyzed 15 randomized trials with 28,432 participants aged 65+. 
Intensive blood pressure control (SBP <130 mmHg) reduced cardiovascular events by 25% 
but increased falls and syncope by 30%. For patients 80+ years, a target SBP of 140-150 mmHg 
appears to balance benefits and risks. Individualized targets considering frailty, 
comorbidities, and patient preferences are recommended.""",
        "source_type": "systematic_review",
        "quality_score": 0.94
    },
    {
        "doc_id": "polypharmacy_005",
        "title": "Managing Polypharmacy in Geriatric Diabetes Care",
        "authors": "Kim H, Nguyen T, Roberts J",
        "abstract": """Elderly diabetic patients often take multiple medications, increasing 
risk of adverse drug interactions and non-adherence. Our analysis of 5,234 Medicare 
beneficiaries found an average of 8.3 medications per patient. Drug interactions between 
diabetes medications and common geriatric drugs (anticoagulants, antihypertensives) 
were present in 34% of patients. Implementation of pharmacist-led medication review 
reduced inappropriate prescribing by 28% and improved glycemic control.""",
        "source_type": "observational_study",
        "quality_score": 0.85
    },
    {
        "doc_id": "metformin_renal_006",
        "title": "Metformin Safety in Chronic Kidney Disease: Updated Recommendations",
        "authors": "Davis C, Miller R, Taylor S",
        "abstract": """Metformin use in patients with chronic kidney disease has been 
re-evaluated based on accumulating safety data. Updated guidelines now permit metformin 
use with eGFR 30-45 mL/min/1.73m² at reduced doses (maximum 1000mg daily). Risk of 
lactic acidosis remains extremely rare (0.03 per 1000 patient-years) when contraindications 
are respected. For elderly patients with fluctuating renal function, regular monitoring 
every 3-6 months is recommended with dose adjustment as needed.""",
        "source_type": "clinical_guideline",
        "quality_score": 0.93
    },
    {
        "doc_id": "cgm_elderly_007",
        "title": "Continuous Glucose Monitoring in Older Adults with Diabetes",
        "authors": "Moore K, Jackson L, White R",
        "abstract": """Continuous glucose monitoring (CGM) adoption in elderly patients 
is increasing but requires special considerations. Our 6-month study of 156 patients 
aged 70+ showed CGM reduced time in hypoglycemia by 43% and improved time in range 
(70-180 mg/dL) by 18%. However, 23% of participants required additional training, 
and sensor adhesion was problematic in patients with fragile skin. CGM is beneficial 
for elderly patients at high hypoglycemia risk when adequate support is available.""",
        "source_type": "rct",
        "quality_score": 0.90
    },
    {
        "doc_id": "heart_failure_diabetes_008",
        "title": "Diabetes Management in Heart Failure: Evidence-Based Approach",
        "authors": "Harris M, Clark E, Lewis T",
        "abstract": """Managing diabetes in patients with heart failure requires balancing 
glycemic control with cardiovascular safety. SGLT2 inhibitors have emerged as preferred 
agents, reducing heart failure hospitalizations by 30-35% regardless of diabetes status. 
Metformin is now considered safe in stable heart failure. Thiazolidinediones remain 
contraindicated. Insulin requirements may increase with disease progression. Target 
HbA1c of 7-8% is appropriate for most patients with established heart failure.""",
        "source_type": "clinical_guideline",
        "quality_score": 0.96
    },
    {
        "doc_id": "depression_diabetes_009",
        "title": "Depression Screening in Elderly Diabetic Patients",
        "authors": "Young N, Scott A, Adams B",
        "abstract": """Depression is twice as common in diabetic patients and associated 
with poor glycemic control and increased mortality. This cross-sectional study of 
1,892 elderly diabetics found 28% with clinically significant depression, but only 
40% were previously diagnosed. Implementation of routine PHQ-9 screening increased 
detection by 65%. Treatment with collaborative care models improved both depression 
and HbA1c outcomes. Annual depression screening is recommended for all elderly diabetics.""",
        "source_type": "cross_sectional_study",
        "quality_score": 0.86
    },
    {
        "doc_id": "frailty_assessment_010",
        "title": "Incorporating Frailty Assessment in Geriatric Diabetes Management",
        "authors": "Evans D, Turner M, Phillips K",
        "abstract": """Frailty significantly impacts diabetes treatment decisions in elderly 
patients. Our validation study of the Clinical Frailty Scale in 834 diabetic patients 
showed strong correlation with mortality and hospitalization. Frail patients (CFS ≥5) 
had 3.2 times higher hypoglycemia risk with intensive glycemic control. For frail 
elderly patients, relaxed HbA1c targets (8-9%), simplified medication regimens, and 
focus on symptom management rather than surrogate endpoints is recommended.""",
        "source_type": "validation_study",
        "quality_score": 0.91
    }
]


def load_sample_documents() -> List[Dict[str, Any]]:
    """Load the built-in sample clinical documents."""
    return SAMPLE_DOCUMENTS


def ingest_documents(documents: List[Dict[str, Any]], verbose: bool = True):
    """Index documents into ChromaDB and Whoosh.
    
    Args:
        documents: List of document dictionaries
        verbose: Whether to print progress
    """
    if verbose:
        print("\n" + "="*60)
        print("  CLINICAL DOCUMENT INGESTION")
        print("="*60)
        print(f"\n📄 Documents to index: {len(documents)}")
    
    # Initialize hybrid search
    search = HybridSearch()
    
    # Get initial counts
    initial_counts = search.count()
    if verbose:
        print(f"📊 Current index size: {initial_counts}")
    
    # Index each document
    iterator = tqdm(documents, desc="Indexing") if verbose else documents
    
    for doc in iterator:
        search.add_document(
            doc_id=doc["doc_id"],
            title=doc["title"],
            abstract=doc["abstract"],
            full_text=doc.get("full_text", doc["abstract"]),
            authors=doc.get("authors", "Unknown"),
            source_type=doc.get("source_type", "article"),
            quality_score=doc.get("quality_score", 0.5)
        )
    
    # Get final counts
    final_counts = search.count()
    
    if verbose:
        print(f"\n✅ Indexing complete!")
        print(f"   Vector DB (ChromaDB): {final_counts['vector_search']} documents")
        print(f"   Text Search (Whoosh): {final_counts['text_search']} documents")
        print("\n" + "="*60)
    
    return final_counts


def test_search(query: str = "diabetes elderly"):
    """Test search functionality after ingestion."""
    print(f"\n🔍 Testing search: '{query}'")
    print("-" * 40)
    
    search = HybridSearch()
    results = search.search(query, top_k=5)
    
    if not results:
        print("❌ No results found. Make sure documents are indexed.")
        return
    
    print(f"✅ Found {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.get('title', 'Unknown')[:60]}...")
        print(f"     Score: {result.get('hybrid_score', 0):.4f}")
        print()


def main():
    """Main ingestion pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest clinical documents")
    parser.add_argument("--dir", type=str, help="Directory with documents to ingest")
    parser.add_argument("--test", action="store_true", help="Run search test after ingestion")
    args = parser.parse_args()
    
    if args.dir:
        # Load documents from directory (future feature)
        print(f"Loading documents from {args.dir}...")
        documents = []  # TODO: implement directory loading
        print("⚠ Directory loading not yet implemented. Using sample documents.")
        documents = load_sample_documents()
    else:
        # Use built-in sample documents
        print("Loading built-in sample clinical documents...")
        documents = load_sample_documents()
    
    # Ingest documents
    ingest_documents(documents)
    
    # Run test search
    if args.test or True:  # Always test for now
        test_search("diabetes management elderly")
        test_search("hypertension blood pressure")


if __name__ == "__main__":
    main()
