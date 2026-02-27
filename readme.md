# Uma Fraction Tutor 🤖

An AI-powered Fraction tutoring system with adaptive feedback and formative assessment for junior high school students (SMP).

## Overview

Uma Fraction Tutor is an intelligent tutoring system that provides personalized formative feedback to students learning Fraction. The system uses:
- **RAG (Retrieval-Augmented Generation)** with LangChain and FAISS for context-aware responses
- **LLM-based evaluation** to assess student answers and achievement levels  
- **Adaptive task selection** based on student performance
- **Supabase database** for persistent data storage
- **Streamlit** for an interactive web interface

## Features

### 🎓 For Students
- **Interactive Chat with Uma**: Get real-time feedback on Fraction problems
- **Adaptive Difficulty**: System adjusts task difficulty based on your performance
- **Progress Tracking**: View your learning history and statistics
- **Formative Feedback**: Receive targeted feedback types (FFFs, Informative Tutoring Feedback, Corrective Response)
- **Achievement Levels**: Track your growth with Low/High achievement assessments

### 🔧 For Educators/Researchers
- **RAG Architecture**: Uses vector embeddings for knowledge retrieval
- **LLM Integration**: OpenAI GPT-4o for feedback generation and GPT-4o-mini for evaluations
- **Database Persistence**: All interactions and progress are logged
- **Configurable Knowledge Base**: Easy to add new Fraction content

## Project Structure

```
thesis_ff_math_rag/
├── app/
│   ├── main.py                      # Application entry point
│   ├── sidebar.py                   # Navigation sidebar
│   ├── ai/                          # AI/LLM components
│   │   ├── answer_evaluator.py     # LLM-based answer checking
│   │   ├── achievement_evaluator.py # Student level assessment
│   │   ├── feedback_generator.py    # Feedback generation
│   │   ├── feedback_decision.py     # Feedback type selection
│   │   ├── retrieval.py             # RAG with LangChain
│   │   └── rag_pipeline.py          # Main pipeline orchestration
│   ├── auth/                        # Authentication
│   │   └── session.py               # Session management
│   ├── database/                    # Database services
│   │   ├── supabase_client.py       # Supabase connection
│   │   ├── student_service.py       # Student CRUD
│   │   ├── task_service.py          # Task management
│   │   ├── log_service.py           # Session logging
│   │   ├── chat_service.py          # Chat persistence
│   │   ├── import_tasks.py          # CSV import script
│   │   └── seed_test_data.py        # Test data seeder
│   └── pages/                       # Streamlit pages
│       ├── Login.py                 # Authentication page
│       ├── Register.py              # Registration page
│       ├── Homepage.py              # Dashboard
│       ├── Study_Chat.py            # Main learning interface
│       ├── History.py               # Learning history
│       ├── Session_Detail.py        # Session details
│       ├── Quiz.py                  # Quiz feature
│       └── Resources.py             # Learning resources
├── data/
│   ├── documents/                   # Source CSV files
│   ├── processed/                   # Processed data
│   └── vector_store/                # FAISS embeddings
│       ├── index.faiss              # Vector index
│       └── chunks.json              # Text chunks
├── database_schema.sql              # Database schema
├── .env.example                     # Environment variables template
├── .streamlit/secrets.toml.example  # Streamlit secrets template
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Conda (recommended) or virtualenv
- Supabase account (free tier available)
- OpenAI API key

### 2. Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd thesis_ff_math_rag
```

2. **Create and activate conda environment**
```bash
conda create -n thesis_rag python=3.10
conda activate thesis_rag
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

### 3. Database Setup

1. **Create a Supabase project**
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note your project URL and anon key

2. **Run database schema**
   - Open your Supabase SQL editor
   - Copy and paste contents of `database_schema.sql`
   - Execute to create all tables

3. **Verify tables created**
   - Check that these tables exist:
     - `students`
     - `tasks`
     - `student_logs`
     - `chat_messages`

### 4. Configuration

1. **Set up environment variables**

Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
OPENAI_API_KEY=sk-your-openai-api-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

2. **Set up Streamlit secrets** (for deployment)

Create `.streamlit/secrets.toml`:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit with same credentials as `.env`

### 5. Seed Database with Test Data

1. **Create test students and sample tasks**
```bash
cd app/database
python seed_test_data.py
```

This creates:
- 3 test student accounts (YPSSTUDENT_1, YPSSTUDENT_2, YPSSTUDENT_3)
- 6 sample Fraction tasks (3 Low, 3 High)
- Sample learning sessions

2. **Import tasks from CSV** (optional)
```bash
python import_tasks.py ../../data/documents/Fraction_train.csv --level Low
```

### 6. Running the Application

```bash
# Make sure you're in the thesis_rag environment
conda activate thesis_rag

# Navigate to app directory
cd app

# Run Streamlit
streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Student Workflow

1. **Register/Login**
   - Create new account or use test account (YPSSTUDENT_1 / test123)
   
2. **Homepage**
   - View your learning statistics
   - See achievement level

3. **Study Chat**
   - Receive an Fraction problem based on your level
   - Chat with Uma to solve the problem
   - Get formative feedback on your answers
   - System tracks errors (max 3 per problem)
   - Click "Next Problem" when done

4. **View History**
   - See all past sessions
   - Click to view detailed chat history
   - Review your progress

### For Educators/Administrators

**Import Custom Tasks:**
```bash
cd app/database
python import_tasks.py path/to/your/tasks.csv --level High
```

CSV format:
```csv
question,solution,level,menyederhanakan,sifat_operasi,pemodelan
"Solve: 2x + 3 = 11","x = 4","Low","true","true","false"
```

## Database Schema

### students
- `student_id` (UUID, PK)
- `username` (format: YPSSTUDENT_X, unique)
- `name`, `password_hash`
- `email` (optional)
- `achievement_level` (Low/High)
- `prior_knowledge_*` (Low/High for each knowledge area)

### tasks
- `task_id` (UUID, PK)
- `level` (Low/High)
- `question`, `solution`
- `knowledge_area_*` (boolean flags)

### student_logs
- `log_id` (UUID, PK)
- `student_id`, `task_id`, `session_id`
- `question`, `student_answer`
- `is_correct_final`, `error_count`
- `feedback_given`, `feedback_type`
- `achievement_level_assessed`

### chat_messages
- `message_id` (UUID, PK)
- `session_id`, `student_id`
- `role` (user/assistant)
- `content`, `contexts` (JSONB)

## RAG Architecture

The system uses a Retrieval-Augmented Generation (RAG) pipeline:

1. **Vector Store**: FAISS with OpenAI text-embedding-3-small
2. **Knowledge Base**: Fraction teaching materials and examples
3. **Retrieval**: Top-k semantic search for relevant contexts
4. **Generation**: OpenAI GPT-4o generates feedback using retrieved contexts

See [RAG_ARCHITECTURE.md](RAG_ARCHITECTURE.md) for detailed documentation.

## Feedback Types

The system provides three types of formative feedback:

1. **Focused Formative Feedback (FFF)**: Hints without revealing answers
2. **Informative Tutoring Feedback (ITF)**: Explains concepts and common errors
3. **Corrective Response (CR)**: Direct correction with explanation

Selection based on:
- Student Prior Knowledge (SPK): Low/High
- Student Achievement Level (SAL): Low/High  
- Time of Feedback (TOF): Immediate/Delayed

## Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.10
- **Database**: Supabase (PostgreSQL)
- **LLM**: OpenAI GPT-4o, GPT-4o-mini
- **Vector Store**: FAISS
- **Embeddings**: OpenAI text-embedding-3-small
- **RAG Framework**: LangChain

## Troubleshooting

### "Missing API Key" Error
- Check that OPENAI_API_KEY is set in `.env` or `.streamlit/secrets.toml`
- Verify key is valid by testing in OpenAI playground

### "Supabase connection failed"
- Verify SUPABASE_URL and SUPABASE_KEY are correct
- Check that your Supabase project is active
- Ensure database tables have been created (run `database_schema.sql`)

### "No tasks available"
- Run `seed_test_data.py` to create sample tasks
- Or import tasks from CSV using `import_tasks.py`

### Vector store not found
- Check that `data/vector_store/index.faiss` exists
- Check that `data/vector_store/chunks.json` exists
- These files should be included in the repository

## Development

### Adding New Feedback Types

Edit `app/ai/feedback_decision.py` to add new rules.

### Modifying RAG Behavior

Edit `app/ai/retrieval.py` to adjust:
- Number of retrieved contexts (top_k)
- Similarity threshold
- Embedding model

### Customizing UI

Pages are in `app/pages/`. Modify Streamlit components as needed.

## Test Accounts

After running `seed_test_data.py`:

| Username | Password | Name |
|----------|----------|------|
| YPSSTUDENT_1 | test123 | Andi Pratama |
| YPSSTUDENT_2 | test123 | Budi Santoso |
| YPSSTUDENT_3 | test123 | Citra Dewi |

## Contributing

This is a thesis project. For questions or contributions, please contact the author.

## License

[Add your license information]

## Acknowledgments

- Advisor: [Name]
- Institution: [Name]
- Based on research in formative feedback and intelligent tutoring systems

## Citation

If you use this work, please cite:
```
[Your citation format]
```

---

## Quick Start (For Uma)

1. **Activate environment**: `conda activate thesis_rag`
2. **Navigate to app**: `cd app`
3. **Run**: `streamlit run main.py`
4. **Login with**: YPSSTUDENT_1 / test123

**Note**: Make sure database is set up and `.env` is configured first!
