import logging
from pathlib import Path
from typing import Optional, Dict, Any
from autogen_agentchat.messages import TextMessage
from util.pdf_to_text_extractor import extract_text_from_pdf
from util.mongo_util import insert_job_to_mongo
from model.model_client import get_model_client
from teams.job_processing_team import get_job_processing_team

# Configure logging
logger = logging.getLogger(__name__)


class JobParserAgent:
    """Agent responsible for parsing and processing job descriptions using AI."""

    def __init__(self):
        self.job_processing_team = get_job_processing_team()

    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string."""
        # A rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4

    async def process_job(self, job_desc_path: str) -> Optional[Dict[str, Any]]:
        """Process a job description file and extract structured information."""
        try:
            print("\n" + "="*80)
            print("🔄 JOB DESCRIPTION PROCESSING PIPELINE")
            print("="*80)
            
            # Step 1: Extract Text
            print("\n📄 STEP 1: Reading Job Description")
            print("-"*40)
            print(f"📂 Source: {Path(job_desc_path).name}")
            job_text = extract_text_from_pdf(job_desc_path)
            if not job_text:
                logger.error("❌ Failed to extract text from job description")
                return None
            
            text_length = len(job_text)
            estimated_tokens = self.estimate_tokens(job_text)
            print(f"📊 Document Stats:")
            print(f"   • Characters: {text_length:,}")
            print(f"   • Estimated Tokens: {estimated_tokens:,}")
            print("✅ Text extraction complete")

            # Step 2: Initialize Processing
            print("\n🤖 STEP 2: Preparing Analysis")
            print("-"*40)
            last_message = None
            conversation_step = 1

            # Create enriched task message
            task_prompt = (
                "Please analyze this job description and extract:\n"
                "1. Basic Information (title, company, location)\n"
                "2. Required Skills and Experience\n"
                "3. Key Responsibilities\n"
                "4. Qualifications and Requirements\n"
                "5. Benefits and Additional Information\n\n"
                f"Job Description Text:\n{job_text}"
            )
            
            task = TextMessage(content=task_prompt, source="user")
            
            print("🎯 Analysis Configuration:")
            print(f"• Task Type: Job Description Analysis")
            print(f"• Source: {task.source}")
            print(f"• Content Length: {len(task.content):,} characters")
            print(f"• Estimated Tokens: {self.estimate_tokens(task.content):,}")
            
            # Step 3: Start Processing
            print("\n🔄 STEP 3: Processing Job Description")
            print("="*80)

            try:
                async for message in self.job_processing_team.run_stream(task=task):
                    try:
                        print(f"\n� Processing Phase {conversation_step}")
                        print("-" * 40)

                        # Display agent interaction
                        if hasattr(message, "source"):
                            print(f"🤖 Active Agent: {message.source}")
                            if hasattr(message, "target"):
                                print(f"🎯 Target Agent: {message.target}")

                        # Handle tool executions
                        if hasattr(message, "tool_calls") and message.tool_calls:
                            tool_call = message.tool_calls[0]
                            print("\n⚙️ Tool Operation:")
                            print(f"🔧 Tool: {tool_call.name}")

                            # Process and display tool arguments
                            try:
                                args = eval(tool_call.arguments)
                                if isinstance(args, dict):
                                    print("\n📥 Input Parameters:")
                                    for key, value in args.items():
                                        if isinstance(value, str) and len(value) > 10000:
                                            print(f"  • {key}: {value[:100]}... [truncated]")
                                        else:
                                            print(f"  • {key}: {value}")
                            except Exception as arg_err:
                                logger.warning(f"⚠️ Parameter parsing error: {arg_err}")
                                print("\n📥 Raw Input:")
                                print(tool_call.arguments)

                            # Process and display tool results
                            if hasattr(message, "results") and message.results:
                                result = message.results[0]
                                if result.is_error:
                                    print("\n❌ Operation Failed:")
                                    print(f"Error: {result.content}")
                                else:
                                    print("\n✅ Operation Successful:")
                                    print(f"Result: {result.content}")

                        # Handle agent messages
                        elif hasattr(message, "content"):
                            content = message.content
                            if isinstance(content, (list, tuple)):
                                content = "\n".join(str(item) for item in content)
                            elif isinstance(content, str) and content.startswith("Publishing"):
                                continue

                            print("\n� Agent Message:")
                            print("-" * 40)
                            content_preview = content[:200] + "..." if len(content) > 200 else content
                            print(content_preview)
                            if len(content) > 200:
                                print(f"\n[Message truncated, total length: {len(content)} chars]")

                        # Track processing progress
                        if hasattr(message, "messages"):
                            last_message = message.messages[-1]
                            if hasattr(last_message, "type"):
                                print(f"\n📋 Message Type: {last_message.type}")

                        print("-" * 40)
                        conversation_step += 1

                    except Exception as event_err:
                        logger.error(f"Error processing event: {event_err}")
                        print(f"\n⚠️ Processing Error:")
                        print(f"• Phase: {conversation_step}")
                        print(f"• Error: {event_err}")
                        print("• Status: Attempting to continue processing")
                        continue

            except Exception as stream_err:
                logger.error(f"Error in event stream: {stream_err}")
                print("\n❌ Communication Error:")
                print(f"• Error: {stream_err}")
                print("• Status: Processing halted")
                raise

            if not last_message:
                logger.error("No response received from agent")
                print("\n❌ Processing Failed:")
                print("• Error: No response from processing agents")
                print("• Status: Operation incomplete")
                return None

            # Final Status Report
            print("\n" + "="*80)
            print("📊 JOB DESCRIPTION PROCESSING SUMMARY")
            print("="*80)
            print(f"• Source File: {Path(job_desc_path).name}")
            print(f"• Processing Steps Completed: {conversation_step}")
            print(f"• Final Status: ✅ Success")
            print("="*80)
            
            return last_message

        except Exception as e:
            logger.error(f"Error processing job description: {e}")
            print("\n❌ Fatal Error:")
            print(f"• Error Type: {type(e).__name__}")
            print(f"• Description: {str(e)}")
            print("• Status: Processing terminated")
            print("="*80)
            raise
