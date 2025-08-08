#!/usr/bin/env python3
"""
Talent Matching Demo Script

This script demonstrates the new talent matching capabilities:
1. Find best candidates for a job
2. Find best jobs for a candidate
3. Comprehensive system analysis

Usage: python talent_matching_demo.py
"""

import asyncio
import sys
import os
from util.TalentMatchingEngine import TalentMatchingEngine
from util.mongo_util import get_mongo_client, get_collection_names


async def get_sample_ids():
    """Get sample job and candidate IDs from the database."""
    try:
        db = get_mongo_client()
        collections = get_collection_names()

        # Get sample candidate ID
        candidate_collection = db[collections["candidates"]]
        sample_candidate = candidate_collection.find_one(
            {}, {"_id": 1, "candidate_name": 1}
        )

        # Get sample job ID
        job_collection = db[collections["jobs"]]
        sample_job = job_collection.find_one({}, {"_id": 1, "job_title": 1})

        return {
            "candidate_id": str(sample_candidate["_id"]) if sample_candidate else None,
            "candidate_name": (
                sample_candidate.get("candidate_name", "Unknown")
                if sample_candidate
                else None
            ),
            "job_id": str(sample_job["_id"]) if sample_job else None,
            "job_title": sample_job.get("job_title", "Unknown") if sample_job else None,
        }
    except Exception as e:
        print(f"⚠️ Error getting sample IDs: {e}")
        return {
            "candidate_id": None,
            "job_id": None,
            "candidate_name": None,
            "job_title": None,
        }


async def demo_talent_matching():
    """Demonstrate talent matching capabilities."""
    print("🎯 TALENT MATCHING SYSTEM DEMO")
    print("=" * 80)

    # Initialize the matching engine
    engine = TalentMatchingEngine("gpt-4")

    # Get sample IDs from database
    print("📋 Getting sample data from database...")
    sample_data = await get_sample_ids()

    try:
        # Demo 1: Comprehensive Analysis
        print("\n" + "=" * 60)
        print("📊 DEMO 1: COMPREHENSIVE SYSTEM ANALYSIS")
        print("=" * 60)
        result1 = await engine.perform_comprehensive_analysis()
        if result1:
            print("✅ Comprehensive analysis completed")
        else:
            print("❌ Comprehensive analysis failed")

        # Demo 2: Find Candidates for Job (if job ID available)
        print("\n" + "=" * 60)
        print("🎯 DEMO 2: FIND CANDIDATES FOR JOB")
        print("=" * 60)
        if sample_data["job_id"]:
            print(
                f"🔍 Searching candidates for job: {sample_data['job_title']} (ID: {sample_data['job_id']})"
            )
            result2 = await engine.find_candidates_for_job(
                sample_data["job_id"], top_k=3
            )
            if result2:
                print("✅ Job-to-candidates matching completed")
            else:
                print("❌ Job-to-candidates matching failed")
        else:
            print(
                "⚠️ No job data found in database. Please process job descriptions first."
            )

        # Demo 3: Find Jobs for Candidate (if candidate ID available)
        print("\n" + "=" * 60)
        print("👤 DEMO 3: FIND JOBS FOR CANDIDATE")
        print("=" * 60)
        if sample_data["candidate_id"]:
            print(
                f"🔍 Searching jobs for candidate: {sample_data['candidate_name']} (ID: {sample_data['candidate_id']})"
            )
            result3 = await engine.find_jobs_for_candidate(
                sample_data["candidate_id"], top_k=3
            )
            if result3:
                print("✅ Candidate-to-jobs matching completed")
            else:
                print("❌ Candidate-to-jobs matching failed")
        else:
            print(
                "⚠️ No candidate data found in database. Please process resumes first."
            )

        print("\n" + "=" * 80)
        print("🎉 TALENT MATCHING DEMO COMPLETED!")
        print("=" * 80)
        print("\n💡 Key Features:")
        print("   ✅ AI-powered semantic similarity matching")
        print("   ✅ ChromaDB vector search for accurate results")
        print("   ✅ Comprehensive analysis with actionable insights")
        print("   ✅ Real-time matching with scoring and explanations")

        print("\n📚 How to Use:")
        print("   1. Process resumes using: python main.py (with resume paths)")
        print("   2. Process job descriptions using: python main.py (with job paths)")
        print("   3. Run talent matching: python talent_matching_demo.py")
        print("   4. Use specific job/candidate IDs for targeted matching")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


def print_usage():
    """Print usage instructions."""
    print("🎯 Talent Matching System")
    print("=" * 50)
    print("Usage: python talent_matching_demo.py")
    print("\nThis demo showcases:")
    print("• Comprehensive talent pool analysis")
    print("• Job-to-candidates matching")
    print("• Candidate-to-jobs matching")
    print("• AI-powered similarity scoring")
    print("\nPrerequisites:")
    print("• Run 'python main.py' first to process documents")
    print("• Ensure MongoDB and ChromaDB are configured")
    print("• Set OPENAI_API_KEY in .env file")


async def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print_usage()
        return

    await demo_talent_matching()


if __name__ == "__main__":
    asyncio.run(main())
