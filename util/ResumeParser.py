import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from autogen_agentchat.messages import TextMessage
from util.pdf_to_text_extractor import extract_text_from_pdf
from util.mongo_util import insert_candidate_to_mongo
from model.model_client import get_model_client
from teams.resume_processing_team import get_resume_processing_team
from teams.job_processing_team import get_job_processing_team

# Configure logging
logger = logging.getLogger(__name__)


class ResumeParserAgent:
    """Agent responsible for parsing and processing resumes using AI."""

    def __init__(self):
        self.resume_processing_team = get_resume_processing_team()

    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string."""
        # A rough estimation: 1 token ≈ 4 characters for English text
        return len(text) // 4

    def chunk_text(self, text: str, max_tokens: int = 1500) -> List[str]:
        """Split text into chunks of approximately max_tokens tokens.

        Args:
            text: Text to split into chunks
            max_tokens: Maximum number of tokens per chunk (default 1500 to leave room for prompt)
        """
        chunks = []
        current_chunk = []
        current_tokens = 0

        # Split by double newlines to maintain section structure
        sections = text.split("\n\n")

        for section in sections:
            section_tokens = self.estimate_tokens(section)

            # If a single section is too large, split it by lines
            if section_tokens > max_tokens:
                lines = section.split("\n")
                for line in lines:
                    line_tokens = self.estimate_tokens(line + "\n")

                    if current_tokens + line_tokens > max_tokens and current_chunk:
                        chunks.append("\n".join(current_chunk))
                        current_chunk = []
                        current_tokens = 0

                    current_chunk.append(line)
                    current_tokens += line_tokens
            else:
                # If adding this section would exceed the limit, create a new chunk
                if current_tokens + section_tokens > max_tokens and current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                current_chunk.append(section)
                current_tokens += section_tokens

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    async def process_resume(self, resume_path: str) -> Optional[Dict[str, Any]]:
        """Process a resume file and store the extracted information."""
        try:
            # Extract text from resume using pdfplumber
            print("\n" + "="*80)
            print("� RESUME PROCESSING PIPELINE")
            print("="*80)
            
            # Step 1: Extract Text
            print("\n�📄 STEP 1: Reading Resume File")
            print("-"*40)
            print(f"📂 Source: {Path(resume_path).name}")
            resume_text = extract_text_from_pdf(resume_path)
            if not resume_text:
                logger.error("❌ Failed to extract text from resume")
                return None
            text_length = len(resume_text)
            estimated_tokens = self.estimate_tokens(resume_text)
            print(f"📊 Document Stats:")
            print(f"   • Characters: {text_length:,}")
            print(f"   • Estimated Tokens: {estimated_tokens:,}")
            print("✅ Text extraction complete")

            # Step 2: Chunk Text
            print("\n📑 STEP 2: Chunking Document")
            print("-"*40)
            chunks = self.chunk_text(resume_text)
            print(f"� Number of chunks: {len(chunks)}")
            for i, chunk in enumerate(chunks, 1):
                chunk_tokens = self.estimate_tokens(chunk)
                print(f"   Chunk {i}: ~{chunk_tokens:,} tokens ({len(chunk):,} chars)")
            print("✅ Document chunking complete")

            # Initialize processing variables
            last_message = None
            conversation_step = 1
            combined_results = []

            # Step 3: Process Chunks
            print("\n🤖 STEP 3: Processing Chunks")
            print("="*80)

            for i, chunk in enumerate(chunks, 1):
                print(f"\n� Processing Chunk {i}/{len(chunks)}")
                print("-"*40)
                print(f"📊 Chunk Size: ~{self.estimate_tokens(chunk):,} tokens")

                # Create task message for this chunk
                task = TextMessage(
                    content=f"Please parse the following section of the resume (part {i}/{len(chunks)}):\n\n{chunk}",
                    source="user",
                )
                
                print("\n🎯 Task Configuration:")
                print(f"• Source: {task.source}")
                print(f"• Content Preview: {task.content[:100]}..."
                      if len(task.content) > 100 else task.content)
            print("=" * 80)

            for chunk_index, chunk in enumerate(chunks, 1):
                try:
                    async for message in self.resume_processing_team.run_stream(
                        task=task
                    ):
                        try:
                            print(
                                f"\n📌 Step {conversation_step} (Chunk {chunk_index}/{len(chunks)})"
                            )
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
                                combined_results.append(last_message)

                            print("=" * 60)
                            conversation_step += 1

                        except Exception as event_err:
                            logger.error(f"Error processing event: {event_err}")
                            print(f"⚠️ Error in step {conversation_step}: {event_err}")
                            continue

                except Exception as stream_err:
                    logger.error(
                        f"Error in event stream for chunk {chunk_index}: {stream_err}"
                    )
                    print(f"❌ Error in agent communication for chunk {chunk_index}")
                    continue

            if not combined_results:
                logger.error("No responses received from agent")
                return None

            print("\n✅ Resume Processing Complete")
            print("=" * 80)

            # Return the last message from the final chunk
            return combined_results[-1]

        except Exception as e:
            logger.error(f"Error processing resume: {e}")
            print(f"❌ Fatal error: {e}")
            raise
