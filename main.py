import asyncio
from util.pdf_to_text_extractor import extract_text_from_pdf
from model.model_client import (
    get_model_client,
)  # Assuming you have a ModelClient class to interact with the model
from teams.tech_recruiting_team import get_tech_recruiter_team


async def run_resume_agent(resume_path):
    model_client = get_model_client()
    resume_text = extract_text_from_pdf(resume_path)
    team = get_tech_recruiter_team(model_client)
    result = await team.run(task=f"Please parse the following resume:\n\n{resume_text}")
    if hasattr(result, "messages") and result.messages:
        last_message = result.messages[-1]
        print("Last Message Content:")
        print(last_message.content)
    return result


if __name__ == "__main__":
    asyncio.run(
        run_resume_agent(
            "/Users/tharuntejapeddi/Projects/resume-job-matcher/resumes/CV_Tharun Peddi_AI_QA.pdf"
        )
    )
