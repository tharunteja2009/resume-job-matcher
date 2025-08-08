import logging
from pathlib import Path
from typing import Optional, Dict, Any
from autogen_agentchat.messages import TextMessage
from util.base_document_parser import BaseDocumentParser, DocumentProcessingError
from teams.job_processing_team import get_job_processing_team

# Configure logging
logger = logging.getLogger(__name__)


class JobParserAgent(BaseDocumentParser):
    """Agent responsible for parsing and processing job descriptions using AI."""

    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize the job parser agent.

        Args:
            model_name: The model name to use for processing
        """
        super().__init__(model_name)
        self._processing_team = None

    def get_processing_team(self):
        """Get the job processing team."""
        if self._processing_team is None:
            self._processing_team = get_job_processing_team()
        return self._processing_team

    async def process_job(self, job_desc_path: str) -> Optional[Dict[str, Any]]:
        """Process a job description file and extract structured information."""
        try:
            self._print_processing_header("JOB DESCRIPTION", job_desc_path)

            # Step 1: Extract and process text
            job_text = self.extract_text_from_file(job_desc_path)
            chunks = self.prepare_text_for_processing(job_text)

            if not chunks:
                self.logger.error("❌ No processable chunks generated")
                return None

            # Step 2: Process chunks with AI agents
            self._print_step_header(2, "Processing with AI Agents")
            processing_team = self.get_processing_team()

            last_message = None
            conversation_step = 1

            for chunk_index, chunk in enumerate(chunks, 1):
                print(f"\n🔄 Processing Chunk {chunk_index}/{len(chunks)}")
                print("-" * 40)
                print(
                    f"📊 Chunk Size: ~{self.text_processor.estimate_tokens(chunk):,} tokens"
                )

                # Create enriched task message for this chunk
                task_prompt = (
                    f"Please analyze this part ({chunk_index}/{len(chunks)}) of the job description and extract:\n"
                    "1. Basic Information (title, company, location)\n"
                    "2. Required Skills and Experience\n"
                    "3. Key Responsibilities\n"
                    "4. Qualifications and Requirements\n"
                    "5. Benefits and Additional Information\n\n"
                    f"Job Description Text Part {chunk_index}:\n{chunk}"
                )

                task = TextMessage(content=task_prompt, source="user")

                try:
                    async for message in processing_team.run_stream(task=task):
                        result = await self._process_agent_message(
                            message, chunk_index, len(chunks), conversation_step
                        )
                        if result:
                            last_message = result.get("last_message")
                        conversation_step += 1

                except Exception as stream_err:
                    self.logger.error(
                        f"Error processing chunk {chunk_index}: {stream_err}"
                    )
                    continue

            if not last_message:
                self.logger.error("No response received from processing agents")
                return None

            self._print_completion_message(
                "JOB DESCRIPTION", job_desc_path, conversation_step
            )
            return last_message

        except DocumentProcessingError as e:
            self.logger.error(f"Document processing error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error processing job description: {e}")
            raise

    async def process_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Implement the abstract method to process job descriptions."""
        return await self.process_job(file_path)

    async def _process_agent_message(
        self, message, chunk_index: int, total_chunks: int, step: int
    ) -> Optional[Dict[str, Any]]:
        """Process a message from the agent processing stream."""
        try:
            print(f"\n📌 Step {step} (Chunk {chunk_index}/{total_chunks})")
            print("=" * 60)

            # Display interaction flow
            if hasattr(message, "source"):
                print(f"🔄 Interaction Flow: {message.source}")

            # Handle tool calls
            if hasattr(message, "tool_calls") and message.tool_calls:
                self._handle_tool_calls(message)

            # Handle agent messages
            elif hasattr(message, "content"):
                self._handle_agent_content(message)

            # Track message chain
            last_message = None
            if hasattr(message, "messages"):
                last_message = message.messages[-1]
                if hasattr(last_message, "type"):
                    print(f"\n📋 Message Type: {last_message.type}")

            print("=" * 60)

            return {"last_message": last_message}

        except Exception as e:
            self.logger.error(f"Error processing agent message: {e}")
            return None

    def _handle_tool_calls(self, message) -> None:
        """Handle tool calls in agent messages."""
        tool_call = message.tool_calls[0]
        print("\n🛠️  Tool Execution:")
        print(f"Tool: {tool_call.name}")

        # Show tool arguments
        try:
            args = eval(tool_call.arguments)
            if isinstance(args, dict):
                print("\n📥 Parameters:")
                for key, value in args.items():
                    if isinstance(value, str) and len(value) > 10000:
                        print(f"  {key}: {value[:100]}...")
                    else:
                        print(f"  {key}: {value}")
        except Exception as arg_err:
            self.logger.warning(f"Error parsing tool arguments: {arg_err}")
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

    def _handle_agent_content(self, message) -> None:
        """Handle content in agent messages."""
        content = message.content
        if isinstance(content, (list, tuple)):
            content = "\n".join(str(item) for item in content)
        elif isinstance(content, str) and content.startswith("Publishing"):
            return

        print("\n💬 Agent Communication:")
        print(f"From: {message.source}")
        if hasattr(message, "target"):
            print(f"To: {message.target}")
        print("\nMessage Content:")
        print("-" * 40)
        print(content)
        print("-" * 40)
