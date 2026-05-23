#!/usr/bin/env python3
"""
Demo test script for Lattice API.

Tests the full pipeline with examples from different domains:
- Oncology
- Chemistry  
- Neuroscience
"""

import requests
import json
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Define test cases across domains
TEST_CASES = [
    {
        "domain": "Oncology",
        "text": "Paclitaxel stabilizes microtubules by preventing their depolymerization, which inhibits the mitotic spindle and prevents cancer cell division.",
        "expected_visualization": "animation",
    },
    {
        "domain": "Oncology (Histology)",
        "text": "Clear cell ovarian carcinoma cells look transparent because glycogen dissolves during H&E staining, leaving vacuolated cytoplasm.",
        "expected_visualization": "comparison",
    },
    {
        "domain": "Chemistry",
        "text": "The Krebs cycle oxidizes acetyl-CoA to produce NADH and FADH2, which donate electrons to the electron transport chain for ATP synthesis.",
        "expected_visualization": "animation",
    },
    {
        "domain": "Neuroscience",
        "text": "Synaptic plasticity occurs through long-term potentiation when calcium influx triggers AMPA receptor insertion, strengthening the synapse.",
        "expected_visualization": "animation",
    },
    {
        "domain": "Biology",
        "text": "Photosynthesis converts light energy into chemical energy through light-dependent and light-independent reactions in the chloroplast.",
        "expected_visualization": "diagram",
    },
]


def test_generate_endpoint(text: str, domain: str) -> dict:
    """Test the /generate endpoint with a given text."""
    try:
        response = requests.post(
            f"{BASE_URL}/generate",
            json={"text": text},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error testing {domain}: {str(e)}")
        return None


def print_result(domain: str, result: dict, expected_viz: str):
    """Pretty-print test results."""
    if not result:
        return

    analysis = result.get("analysis", {})
    plan = result.get("plan", {})
    svg = result.get("svg", "")

    print(f"\n{'=' * 70}")
    print(f"Domain: {domain}")
    print(f"{'=' * 70}")

    print(f"\n✅ Analysis:")
    print(f"  Concept Type: {analysis.get('concept_type')}")
    print(f"  Domain: {analysis.get('domain')}")
    print(f"  Difficulty: {analysis.get('difficulty_reason')}")
    print(f"  Recommended Visualizations: {', '.join(analysis.get('recommended_visualization', []))}")

    print(f"\n✅ Extracted Concepts:")
    print(f"  Entities: {', '.join(analysis.get('entities', [])[:4])}")
    if analysis.get("relationships"):
        print(f"  Relationships: {len(analysis.get('relationships', []))} found")
        for rel in analysis.get("relationships", [])[:2]:
            print(f"    - {rel['source']} → {rel['target']} ({rel['type']})")
    if analysis.get("mechanisms"):
        print(f"  Mechanisms: {', '.join(analysis.get('mechanisms', [])[:3])}")

    print(f"\n✅ Visualization Plan:")
    print(f"  Type: {plan.get('visualization_type')}")
    print(f"  Scenes: {len(plan.get('scenes', []))} scenes")
    for scene in plan.get("scenes", [])[:3]:
        print(f"    - {scene}")
    print(f"  Style: {plan.get('style')}")

    print(f"\n✅ SVG Rendering:")
    print(f"  Generated: {len(svg)} bytes of SVG")
    print(f"  Valid: {'<svg' in svg and '</svg>' in svg}")

    # Check if visualization matched expected
    actual_viz = plan.get("visualization_type")
    match = "✅" if actual_viz == expected_viz else "⚠️"
    print(f"\n{match} Visualization Match:")
    print(f"  Expected: {expected_viz}")
    print(f"  Actual: {actual_viz}")


def main():
    """Run all domain tests."""
    print(f"\n🚀 Testing Lattice API Pipeline")
    print(f"📍 Base URL: {BASE_URL}")

    # Health check
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5).json()
        print(f"✅ Backend Status: {health.get('status')}")
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        sys.exit(1)

    # Run tests
    print(f"\n🧪 Running {len(TEST_CASES)} domain tests...\n")

    results = []
    for test_case in TEST_CASES:
        domain = test_case["domain"]
        text = test_case["text"]
        expected_viz = test_case["expected_visualization"]

        print(f"Testing: {domain}...", end=" ", flush=True)
        result = test_generate_endpoint(text, domain)

        if result:
            print("✅")
            results.append((domain, result, expected_viz))
        else:
            print("❌")

    # Print results
    for domain, result, expected_viz in results:
        print_result(domain, result, expected_viz)

    # Summary
    print(f"\n{'=' * 70}")
    print(f"✅ All tests completed!")
    print(f"📊 Frontend: http://localhost:3001")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
