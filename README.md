# 🎯 Resume-Job Matcher: AI-Powered Talent Matching System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![AutoGen](https://img.shields.io/badge/AutoGen-Multi--Agent-green.svg)](https://github.com/microsoft/autogen)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com/)

AI-powered system that automates resume-job matching with semantic understanding and real-time cost tracking.

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/tharunteja2009/autogen-with-rag.git
cd resume-job-matcher

# 2. Install dependencies
pip install -r requirement.txt

# 3. Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# 4. Run the system
python main.py
```

## 🏗️ System Architecture

**Multi-Agent AI System** built on Microsoft AutoGen:
- **Resume Parser Agent** → Extracts structured data from PDFs
- **Job Description Agent** → Processes requirements and responsibilities  
- **Talent Matching Agent** → AI-powered similarity scoring
- **RAG Builder Agents** → Creates vector embeddings for semantic search

**Technology Stack:**
- **Microsoft AutoGen**: Multi-agent orchestration
- **OpenAI GPT-3.5/4**: Language understanding and processing
- **MongoDB**: Structured data storage and reporting
- **ChromaDB**: Vector database for semantic matching

## 📁 Project Structure

```
resume-job-matcher/
├── main.py              # Entry point
├── requirement.txt      # Dependencies  
├── src/
│   ├── ai/agents/      # AutoGen agents
│   ├── database/       # MongoDB & ChromaDB
│   └── data/           # PDF files (resumes & jobs)
```

## 💰 Cost Tracking

The system provides real-time cost monitoring for all OpenAI API usage:
- Automatic tracking of token counts and costs
- Detailed breakdowns by operation type
- Session summaries with complete cost analysis

**Typical Costs:**
- Resume Processing: $0.002 - $0.005 each
- Job Analysis: $0.001 - $0.003 each  
- Complete Session: $0.030 - $0.120

## 🔧 Setup

**Prerequisites:**
- Python 3.10+
- OpenAI API key
- MongoDB (local or cloud)

**Installation:**
```bash
git clone https://github.com/tharunteja2009/autogen-with-rag.git
cd resume-job-matcher
pip install -r requirement.txt
export OPENAI_API_KEY="your-api-key-here"
```

**Add PDF files:**
- Place resumes in `src/data/resumes/` 
- Place job descriptions in `src/data/job/`

## 📖 Usage

Run the system with three execution modes:

```bash
python main.py
```

**Execution Options:**

**1️⃣ PARSE & ANALYZE (Full Pipeline)**
- Complete processing of all PDF files from scratch
- Stores data in both MongoDB and ChromaDB databases  
- Performs AI-powered talent matching analysis
- Best for: First time setup or when adding new documents
- Cost: $0.030 - $0.120 per session

**2️⃣ DIRECT MATCHING (Use Existing Data)**
- Skips document parsing entirely
- Uses previously processed data from ChromaDB
- Runs analysis on existing data only
- Best for: Re-running analysis without reprocessing files
- Cost: $0.000 - $0.010 per session (90% cost savings)
- Requires: ChromaDB data from previous Option 1 run

**3️⃣ CLEAN & RESTART (Fresh Start)**
- Completely cleans both MongoDB and ChromaDB databases
- Processes all documents from scratch with fresh databases
- Ensures no corrupted or duplicate data
- Best for: System reset or troubleshooting issues
- Cost: $0.030 - $0.120 per session

---

---

**⭐ Star this repository if you found it helpful!**

Built with Microsoft AutoGen, OpenAI GPT models, and modern Python architecture.
```

---

### **2️⃣ DIRECT MATCHING (Use Existing Data)**
**Best for**: Re-running analysis on already processed documents

**Process:**
- 🔄 Skip parsing phase entirely (saves time and money)
- 📊 Use existing data from ChromaDB collections
- 🎯 Run talent matching analysis directly
- 💰 **Cost**: $0.001 - $0.010 per session (analysis only)

**What Happens:**
1. **Skip Document Processing**: No PDF parsing or AI extraction
2. **Use Existing Data**: Leverages previously processed ChromaDB embeddings
3. **Direct Analysis**: Immediate talent matching without re-processing
4. **Cost Optimization**: ~90% cost reduction compared to Option 1

**Example Output:**
```
🚀 DIRECT MATCHING MODE - Using Existing Data
============================================================
📊 Using existing ChromaDB data for analysis
   • Found 3 candidate profiles
   • Found 1 job descriptions
🎯 Performing talent matching analysis...
💰 Session Cost: $0.00 (using cached data)
```

**Requirements:** ChromaDB collections must exist (run Option 1 first)

---

### **3️⃣ CLEAN & RESTART (Fresh Start)**
**Best for**: Complete system reset or troubleshooting

**Process:**
- 🗑️ Clean up existing ChromaDB collections (vector embeddings)
- 🗑️ Clean up existing MongoDB collections (candidate/job metadata)  
- 📝 Parse all PDF files from scratch
- 💾 Store processed data in both databases
- 🎯 Run comprehensive talent matching analysis
- 💰 **Cost**: Same as Option 1 ($0.030 - $0.120)

**What Happens:**
1. **Complete Database Cleanup**: Removes all existing data from both databases
2. **Fresh Processing**: Treats all documents as new (no duplicate detection)
3. **Full Pipeline**: Complete end-to-end processing like Option 1
4. **Clean State**: Ensures no corrupted or partial data affects results

**Example Output:**
```
� CLEAN & RESTART MODE - Fresh Start
============================================================
🗑️  Cleaning up existing ChromaDB collections...
   ✅ Deleted collection: candidate_profiles
   ✅ Deleted collection: job_descriptions
   🗑️  Removing ChromaDB directory for complete cleanup...
   
🗑️  Cleaning up existing MongoDB collections...
   ✅ Deleted 7 candidates
   ✅ Deleted 1 jobs
   
🚀 Processing documents with fresh databases...
💰 Total Cost: $0.0344 (fresh processing)
```

---

### **🎯 Choosing the Right Mode**

| **Scenario** | **Recommended Mode** | **Why** |
|--------------|---------------------|---------|
| **First time setup** | Option 1 | Complete processing needed |
| **Adding new documents** | Option 1 | Process new + skip existing |
| **Re-analyzing same data** | Option 2 | Save time and costs |
| **System troubleshooting** | Option 3 | Clean slate approach |
| **Data corruption issues** | Option 3 | Fresh start guaranteed |
| **Testing changes** | Option 2 | Quick validation |

### **💰 Cost Comparison**
- **Option 1**: $0.030 - $0.120 (full processing)
- **Option 2**: $0.000 - $0.010 (analysis only) 
- **Option 3**: $0.030 - $0.120 (full processing after cleanup)

### **Expected Session Output**
```
🚀 RESUME-JOB MATCHER PIPELINE
═══════════════════════════════
📄 Resumes Processed: 3 (✅ 3 successful, ❌ 0 failed)
💼 Job Descriptions Processed: 1 (✅ 1 successful, ❌ 0 failed)

🎯 TALENT MATCHING RESULTS:
┌─────────────────────┬─────────────┬──────────────────────────────┐
│ Candidate           │ Match Score │ Key Strengths                │
├─────────────────────┼─────────────┼──────────────────────────────┤
│ THARUN TEJA PEDDI   │ 87.5%       │ Java, Python, Selenium, AWS │
│ MOUNIKA SOMA        │ 83.2%       │ API Testing, Playwright     │
│ Rohini Thyagarajan  │ 79.8%       │ Team Lead, Automation       │
└─────────────────────┴─────────────┴──────────────────────────────┘

💰 SESSION ANALYTICS:
⏱️  Duration: 2.1 minutes
🔢 API Calls: 12 
💵 Total Cost: $0.0344
🎯 Cost per Resume: $0.0115
```

## 🤝 Contributing

This project demonstrates production-ready AI system development with:

- ✅ **Clean Architecture**: Professional code organization
- ✅ **Cost Optimization**: Real-time OpenAI API monitoring  
- ✅ **Comprehensive Documentation**: Clear setup and usage guides
- ✅ **Production Ready**: Enterprise-grade code quality

The system serves as an excellent foundation for AI-powered document processing and matching applications.

---

**⭐ Star this repository if you found it helpful!**

Built with Microsoft AutoGen, OpenAI GPT models, and modern Python architecture.
