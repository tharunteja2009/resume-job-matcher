import logging
from pathlib import Path
from typing import Optional, Dict, Any
from autogen_agentchat.messages import TextMessage
from util.pdf_to_text_extractor import extract_text_from_pdf
from util.mongo_util import insert_candidate_to_mongo
from model.model_client import get_model_client
from teams.tech_recruiting_team import get_tech_recruiter_team

# Configure logging
logger = logging.getLogger(__name__)


class ResumeParserAgent:
    """Agent responsible for parsing and processing resumes using AI."""

    def __init__(self):
        self.team = get_tech_recruiter_team()

    async def process_resume(self, resume_path: str) -> Optional[Dict[str, Any]]:
        """Process a resume file and store the extracted information."""
        try:
            # Extract text from resume using pdfplumber
            print("\n📄 Reading Resume File...")
            resume_text = extract_text_from_pdf(resume_path)
            if not resume_text:
                logger.error("Failed to extract text from resume")
                return None
            print("✅ Successfully extracted text from resume\n")

            print("\n🤖 Starting Resume Analysis...")
            print("=" * 80)

            # Parse resume using agent with streaming
            last_message = None
            conversation_step = 1

            # Create initial task message
            task = TextMessage(
                content=f"Please parse the following resume:\n\n{resume_text}",
                source="user",
            )
            print("\n🔄 Starting Agent Conversation")
            print("=" * 80)
            print("📤 Initial Task:")
            print(f"From: {task.source}")
            print(f"Message: {task.content[:100]}...")
            print("=" * 80)

            try:
                async for message in self.team.run_stream(task=task):
                    try:
                        print(f"\n📌 Step {conversation_step}")
                        print("=" * 60)
                        # Display interaction flow
                        if hasattr(message, "source"):
                            print(f"🔄 Interaction Flow: {message.source}")

                        # Handle tool calls
                        if hasattr(message, "tool_calls") and message.tool_calls:
                            tool_call = message.tool_calls[0]
                            print("\n🛠️  Tool Execution:")
                            print(f"Tool: {tool_call.name}")

                            # Show tool arguments
                            try:
                                args = eval(tool_call.arguments)
                                if isinstance(args, dict):
                                    print("\n📥 Parameters:")
                                    for key, value in args.items():
                                        if (
                                            isinstance(value, str)
                                            and len(value) > 10000
                                        ):
                                            print(f"  {key}: {value[:100]}...")
                                        else:
                                            print(f"  {key}: {value}")
                            except Exception as arg_err:
                                logger.warning(
                                    f"Error parsing tool arguments: {arg_err}"
                                )
                                print("\n📥 Raw Parameters:")
                                print(tool_call.arguments)

                            # Show tool results
                            if hasattr(message, "results") and message.results:
                                print("\n📤 Tool Response:")
                                result = message.results[0]
                                if result.is_error:
                                    print(f"❌ Error: {result.content}")
                                else:
                                    print(f"✅ Success: {result.content}")

                        # Handle agent messages
                        elif hasattr(message, "content"):
                            content = message.content
                            if isinstance(content, (list, tuple)):
                                content = "\n".join(str(item) for item in content)
                            elif isinstance(content, str) and content.startswith(
                                "Publishing"
                            ):
                                continue

                            print("\n💬 Agent Communication:")
                            print(f"From: {message.source}")
                            if hasattr(message, "target"):
                                print(f"To: {message.target}")
                            print("\nMessage Content:")
                            print("-" * 40)
                            print(content)
                            print("-" * 40)

                        # Track message chain
                        if hasattr(message, "messages"):
                            last_message = message.messages[-1]
                            if hasattr(last_message, "type"):
                                print(f"\n📋 Message Type: {last_message.type}")

                        print("=" * 60)
                        conversation_step += 1

                        conversation_step += 1

                    except Exception as event_err:
                        logger.error(f"Error processing event: {event_err}")
                        print(f"⚠️ Error in step {conversation_step}: {event_err}")
                        continue

            except Exception as stream_err:
                logger.error(f"Error in event stream: {stream_err}")
                print("❌ Error in agent communication")
                raise

            if not last_message:
                logger.error("No response received from agent")
                return None

            print("\n✅ Resume Processing Complete")
            print("=" * 80)
            return last_message

        except Exception as e:
            logger.error(f"Error processing resume: {e}")
            print(f"❌ Fatal error: {e}")
            raise
