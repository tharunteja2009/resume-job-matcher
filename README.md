# 🎯 Resume-Job Matcher: AI-Powered Talent Matching System

## 📋 Table of Contents
- [Business Problem](#business-problem)
- [Solution Overview](#solution-overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Usage Guide](#usage-guide)
- [Contributing](#contributing)

## 🎯 Business Problem

**Target Users:** Technical Recruiters and HR Professionals

**Problem Statement:** 
Recruiters spend countless hours manually reviewing resumes against job descriptions, leading to:
- ⏰ Time-consuming manual screening processes
- 🎯 Inconsistent candidate evaluation criteria  
- 📊 Subjective matching without standardized scoring
- 💼 Missed qualified candidates due to keyword-only matching
- 📈 Inefficient talent pipeline management

## 💡 Solution Overview

Our **Resume-Job Matcher** is an AI-powered system that automates the entire talent matching workflow:

### 🔄 **Automated Workflow:**
1. **📤 Document Upload**: Upload candidate resumes (PDF) and job descriptions
2. **🤖 AI Processing**: Multi-agent system extracts structured data using advanced LLMs
3. **💾 Smart Storage**: Data stored in MongoDB with vector embeddings in ChromaDB
4. **⚖️ Intelligent Matching**: AI compares candidates against job requirements
5. **📊 Scoring & Insights**: Generates match scores with detailed recommendations

### 🎯 **Key Benefits:**
- ✅ **95% Time Reduction** in initial screening
- ✅ **Objective Scoring** based on skills, experience, and project relevance  
- ✅ **Semantic Matching** beyond keyword searches
- ✅ **Detailed Insights** with justification for each match
- ✅ **Scalable Processing** for high-volume recruitment

## 🛠️ Technology Stack

- **Microsoft AutoGen**: Multi-agent orchestration and conversation management
- **OpenAI GPT Models**: `gpt-3.5-turbo` for data extraction, `gpt-4` for analysis
- **MongoDB**: Primary database for structured candidate and job data
- **ChromaDB**: Vector database for semantic similarity search
- **Python 3.10+**: Core programming language
- **PDFPlumber**: Advanced PDF text extraction
- **ChromaDB**: Vector database for semantic search and embeddings storage

## 📁 Project Structure

```
resume-job-matcher/
├── 📱 main.py                     # Application entry point
├──  requirement.txt             # Python dependencies
├── 🔐 .env                        # Environment variables
├── 🤖 agents/                     # AI Agents Implementation
│   ├── resume_parser_agent.py
│   ├── job_posting_parser_agent.py
│   ├── resume_rag_builder_agent.py
│   ├── job_rag_builder_agent.py
│   └── talent_matcher_agent.py
├── 👥 teams/                      # Agent Team Orchestration
│   ├── resume_processing_team.py
│   ├── job_processing_team.py
│   └── talent_matching_team.py
├── ⚙️ config/                     # Configuration Management
│   └── settings.py
├── 🛠️ util/                       # Utility Functions & Helpers
│   ├── ResumeParser.py
│   ├── JobParser.py
│   ├── TalentMatchingEngine.py
│   └── mongo_util.py
├── 🗂️ model/                      # AI Model Management
│   └── model_client.py
├── 📄 resumes/                    # Resume Storage
└── 💼 job/                        # Job Description Storage
```

## 🚀 Installation & Setup

### 📋 **Prerequisites**
- Python 3.10 or higher
- MongoDB database (local or cloud)
- OpenAI API key
- Git

### 🔧 **Step-by-Step Installation**

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd resume-job-matcher
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv resume-job-matcher-env
   source resume-job-matcher-env/bin/activate  # On Windows: resume-job-matcher-env\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirement.txt
   ```

4. **Environment Configuration**
   Create `.env` file in the project root:
   ```env
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Database Configuration
   DB_USERNAME=your_mongodb_username
   DB_PASSWORD=your_mongodb_password
   
   # Optional Overrides
   MAX_CHUNK_TOKENS=800
   MAX_TURNS=2
   LOG_LEVEL=INFO
   ```

5. **Database Setup**
   - Ensure MongoDB is running
   - The application will automatically create required collections

6. **Verify Installation**
   ```bash
   python main.py
   ```

## 📖 Usage Guide

### 🚀 **Commands to Run the Complete Project End-to-End**

#### **Prerequisites Setup:**
```bash
# 1. Install dependencies (if not done)
pip install -r requirement.txt

# 2. Set environment variables (ensure .env file has your OpenAI API key)
export OPENAI_API_KEY="your-api-key-here"

# 3. Ensure MongoDB is running (local or cloud connection configured)
```

#### **🎯 Option 1: Complete Pipeline (Recommended)**
```bash
python main.py
```

**What this command does:**
- ✅ **Phase 1**: Processes all resumes and job descriptions from PDF to structured data
- ✅ **Phase 2**: Stores data in both MongoDB (structured) and ChromaDB (vector embeddings)
- ✅ **Phase 3**: Performs comprehensive talent matching analysis
- ✅ **Phase 4**: Demonstrates job-to-candidates and candidate-to-jobs matching
- ✅ **Phase 5**: Shows AI-powered results with similarity scores and recommendations

#### **🎯 Option 2: Demo Only (If data already processed)**
```bash
python talent_matching_demo.py
```

**What this command does:**
- ✅ Runs comprehensive system analysis
- ✅ Finds best candidates for available jobs
- ✅ Finds best jobs for available candidates
- ✅ Shows AI-powered matching results with detailed scores

#### **📊 Expected Output Flow:**
```
🚀 Phase 1: Processing Documents...
================================================================================
🔄 RESUME PROCESSING PIPELINE
📄 STEP 1: Reading RESUME
📄 STEP 2: Processing with AI Agents
✅ Resume processing completed

🔄 JOB DESCRIPTION PROCESSING PIPELINE  
📄 STEP 1: Reading JOB DESCRIPTION
📄 STEP 2: Processing with AI Agents
✅ Job processing completed

🚀 Phase 2: Performing Talent Matching Analysis...
🎯 COMPREHENSIVE MATCHING ANALYSIS
✅ Comprehensive analysis completed

🎯 SPECIFIC MATCHING DEMONSTRATIONS
✅ Job-to-candidates matching completed
✅ Candidate-to-jobs matching completed
```

#### **🎯 What You'll Get:**
1. **📄 Document Processing**: All PDFs processed and extracted to structured JSON
2. **💾 Data Storage**: Information stored in MongoDB for tracking
3. **🔍 Vector Embeddings**: Searchable semantic representations in ChromaDB
4. **🤖 AI Analysis**: GPT-4 powered matching with detailed explanations
5. **📊 Match Scores**: Percentage-based similarity scores (0-100%)
6. **💡 Recommendations**: Actionable insights for hiring decisions

#### **⚡ Single Command for Complete End-to-End Analysis:**
```bash
python main.py
```

**This single command takes you from raw PDF documents to final talent matching analysis!** 🎉

#### **🔧 Help & Options:**
```bash
# Get help for the demo script
python talent_matching_demo.py --help

# Check system requirements
python -c "import sys; print(f'Python version: {sys.version}')"
```

#### **📋 File Input Configuration:**
By default, the system processes files in:
- **Resumes**: `resumes/` directory (PDF files)
- **Job Descriptions**: `job/` directory (PDF files)

To process different files, edit the `documents_path` in `main.py`:
```python
documents_path = {
    "resume_path": [
        "path/to/your/resume1.pdf",
        "path/to/your/resume2.pdf"
    ],
    "job_desc_path": [
        "path/to/your/job_description.pdf"
    ]
}
```

### 🎯 **Basic Usage**

1. **Process Documents**
   ```bash
   python main.py
   ```

2. **Run Demo**
   ```bash
   python talent_matching_demo.py
   ```

### 📊 **Understanding Results**

The system provides detailed output including:
- ✅ **Success/Failure Status** for each document
- 📊 **Processing Statistics** 
- 💾 **Database Storage Confirmation**
- 🔍 **Vector Embedding Creation**
- ⚠️ **Error Reports** with troubleshooting info

## 🤝 Contributing

### 🔧 **Development Setup**
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes with proper testing
4. Submit pull request with detailed description

### 📋 **Coding Standards**
- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include error handling
- Write unit tests for new features

---

**🎯 Ready to revolutionize your recruitment process with AI-powered talent matching!**

## 📚 API Documentation

### 🔗 **Core Endpoints** (Future Implementation)

| Endpoint | Method | Purpose | Request Body |
|----------|--------|---------|--------------|
| `/uploadcv` | POST | Upload candidate resume | PDF file |
| `/uploadjd` | POST | Upload job description | PDF file |
| `/processjobbycv` | GET | Match candidates to jobs | Job ID |
| `/candidates` | GET | List all candidates | - |
| `/jobs` | GET | List all job postings | - |
| `/match-results/{job_id}` | GET | Get matching results | - |

### 📝 **Response Format**

```json
{
  "status": "success",
  "data": {
    "matches": [
      {
        "candidate_id": "string",
        "candidate_name": "string", 
        "match_score": 85,
        "skills_match": ["Python", "AI", "Machine Learning"],
        "experience_match": "5+ years Python development",
        "recommendation": "Strong technical background with relevant AI experience",
        "areas_for_growth": ["Leadership experience", "Domain expertise"]
      }
    ]
  },
  "message": "Matching completed successfully"
}
```

## 🔄 **Development Workflow**

### 🧪 **Testing New Features**

1. **Add Test Data**
   - Place resume PDFs in `resumes/` folder
   - Place job descriptions in `job/` folder

2. **Run Processing Pipeline**
   ```bash
   python main.py
   ```

3. **Verify Database Storage**
   - Check MongoDB for new candidate/job records
   - Confirm ChromaDB vector embeddings

4. **Test Agent Interactions**
   - Monitor agent conversations in logs
   - Validate JSON extraction accuracy

### 📊 **Monitoring & Debugging**

- **Comprehensive Logging**: All agent interactions logged
- **Error Handling**: Robust exception management with detailed error messages
- **JSON Validation**: Built-in validation for data integrity
- **Token Counting**: Prevents API limit exceeded errors

## 🤝 Contributing

### 🔧 **Development Setup**
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes with proper testing
4. Submit pull request with detailed description

### 📋 **Coding Standards**
- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include error handling
- Write unit tests for new features

## 📞 **Support & Contact**

For questions, issues, or contributions:
- 📧 **Email**: tharun.peddi@example.com
- 🐛 **Issues**: Create GitHub issue with detailed description
- 💡 **Feature Requests**: Use GitHub discussions

---

**🎯 Ready to revolutionize your recruitment process with AI-powered talent matching!**

A socity of team in autogen consists with 

agent 1: resume parser agent 
            it will parse the list of resume's then fetch experince details, skills and projects store in mongo DB for tracking and ChromaDB vector database for Agent 
            Note : LLM prompts to extract structured data more accurately from raw PDF text. then store in ChromaDB vector database

agent 2: job document parser agent
            it will parese the job description then fetch expected skills and job responsibilities store in mongo DB for tracking and ChromaDB vector database for Agent 
            Note : LLM prompts to extract structured data more accurately from raw PDF text. then store in ChromaDB vector database

agent 3: talent rater agent
            it will compare 
            a. list of resume's and their skills atleast partial match with  job description document skills
            b. project details partial match with job responsibilities
            c. years of experiance with mentioned skill in resume is higher then high rating score , if the skill match happend in step (a)
            d. Generate summary for each candidate with matching score based on above step a to c also recommendation why he is suitable for role


Technologies :

microsoft autogen - for agents creation and workflow
mongo DB - for tracking of uploads to portal
ChromaDB vector database - for both agents store their context , one is resume another one is job.
python - for programing
pdfplumber - for pdf parsing of resume or job description
fastAPI - for api development of /uploadcv, /uploadjd and /processjobbycv
streamlit - for ui development by integrating with flask api
ngroc - expose API to public environment


Let me know if any gap in my understanding for develpment of above project. Any new technologies used or any easy approch of autogen agent workflow


Here is the rendered diagram for your agent-based recruitment workflow using the Mermaid flowchart:

graph TD
    A[Recruiter Uploads Resume(s)] --> B[Resume Parser Agent]
    A2[Recruiter Uploads JD] --> C[JD Parser Agent]

    B --> D1[Extracted Resume Data]
    C --> D2[Extracted JD Data]

    D1 --> E[Store in MongoDB + ChromaDB VectorDB]
    D2 --> E

    F[Click 'Process Job by CV'] --> G[Talent Rater Agent]
    G --> H[Compare Skills, Projects, Experience]
    H --> I[Generate Score & Summary]
    I --> J[Display in Streamlit UI]



----------------------------------------------------------------------------------------------------------------------------------------------------------Chat GTP analysis on my reqirement :

Your updated project description is very close to being complete and well-structured. You’ve clearly outlined the:
	•	Business Requirement
	•	Workflow
	•	Agent Roles
	•	Technology Stack

However, a few minor gaps, clarifications, and recommendations remain for scalability, clarity, and real-world implementation. Here’s a detailed review with feedback and optional improvements.

⸻

✅ What’s Correct / Clear
	•	✅ Three Agents well defined (Resume Parser, JD Parser, Talent Rater)
	•	✅ LLM prompts for extraction: Yes, good that you’re using LLMs for structured extraction.
	•	✅ Use of ChromaDB vector database: Great for RAG support.
	•	✅ MongoDB for tracking is sensible.
	•	✅ Endpoints /uploadcv, /uploadjd, /processjobbycv are well-scoped.
	•	✅ Technologies chosen are lightweight and good for MVP or production.

⸻

🔍 Minor Gaps & Suggestions

🔸 1. Clarify Data Flow Between Agents

Right now it’s implicit — make it explicit how agents communicate or pass data:
	•	Do they share context via ChromaDB?
	•	Are you chaining them in a custom workflow or orchestrated via AutoGen’s GroupChat?

📌 Recommendation: Define Agent Communication Flow, e.g.,

Recruiter uploads Resume ➝ ResumeParserAgent stores structured data ➝ JDParserAgent runs after JD upload ➝ TalentRaterAgent runs only after both resume and JD are parsed.


⸻

🔸 2. Resume & JD Parsing Output Format

Define a common JSON schema for:
	•	Resume: name, skills, years_of_experience, projects
	•	JD: required_skills, responsibilities, experience_required

📌 Why?
Makes matching deterministic. Otherwise, LLM-based extraction could return varied formats.

⸻

🔸 3. Use Embeddings for Partial Matching

You mentioned “partial match” — this needs semantic similarity (not exact match).

📌 Recommendation:
	•	Use OpenAI embeddings, Instructor, or SentenceTransformers to embed:
	•	Candidate skills / projects
	•	JD skills / responsibilities

Then use cosine similarity threshold (e.g., 0.7) for match logic.

⸻

🔸 4. Vector DB Choice

You’re using “vector DB” — be specific:
	•	ChromaDB (lightweight)
	•	FAISS (local)
	•	Weaviate / Pinecone (cloud, scalable)

📌 Recommendation: Start with ChromaDB if you’re building a local prototype.

⸻

🔸 5. Use LangChain / LlamaIndex with AutoGen (optional)

For RAG and memory management, LangChain or LlamaIndex could enhance:
	•	Chunking logic
	•	Query routing
	•	Memory management

📌 Not mandatory but helpful for better modularity.

⸻

🔸 6. Streamlit ↔ Flask/FastAPI UI

Make sure:
	•	Streamlit UI calls backend endpoints via requests
	•	Show:
	•	Resume Upload
	•	JD Upload
	•	Match Results Table (Name, Match %, Summary, Recommendation)

📌 Recommendation: Cache results with Streamlit session state.

⸻

🔸 7. Async Execution (Optional)

If you plan to process multiple resumes:
	•	Consider using FastAPI + async
	•	Or integrate a background task queue (Celery, RQ, etc.)

⸻

✅ Final Architecture Diagram (Updated)

graph TD
    A[Recruiter Uploads Resume(s)] --> B[Resume Parser Agent]
    A2[Recruiter Uploads JD] --> C[JD Parser Agent]

    B --> D1[Extracted Resume Data]
    C --> D2[Extracted JD Data]

    D1 --> E[Store in MongoDB + ChromaDB VectorDB]
    D2 --> E

    F[Click 'Process Job by CV'] --> G[Talent Rater Agent]
    G --> H[Compare Skills, Projects, Experience]
    H --> I[Generate Score & Summary]
    I --> J[Display in Streamlit UI]


⸻

✅ Summary

Area	Status	Notes
Agent Design	✅ Complete	All agents are defined well
Use of ChromaDB Vector DB	✅ Good	Ensure consistent format of inputs
Resume & JD Parsing	✅/⚠️	Add structured schema definition
Partial Match Logic	⚠️ Needs Embeddings	Use cosine similarity
Tech Stack	✅ Practical	FastAPI + Streamlit is excellent
RAG Implementation	⚠️ Could Improve	Optional use of LangChain/LlamaIndex
Scalability & Performance	⚠️ Optional	Consider async or background tasks


⸻

✅ Do You Need Help With…

Let me know if you want me to:
	•	Draft the AutoGen YAML config for the agents?
	•	Write a starter Python function for parsing resumes with LLM + pdfplumber?
	•	Suggest vector DB schema for embedding + matching?

Let’s implement step by step!
