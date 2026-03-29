# AI-Powered-Skill-Gap-Analysis

This project implements a multi-agent system built on **LangGraph** that processes candidate CVs and generates a personalized skill-gap analysis. Four AI agents powered by **Google Gemini 2.0 Flash Lite** work sequentially to: 

1. Extract and structure key information from the candidate's CV.
2. Identify the candidate's explicit and implicit skills.
3. Retrieve real-time job market demands for a target role using **Google Search grounding**.
4. Compare the candidate's skills against market requirements and produce an actionable skill-gap report.

This system enables recruiters to uncover a candidate's true potential and streamline the evaluation of large volumes of CVs, ultimately improving the recruitment process and decision-making efficiency.

![Python Version](https://img.shields.io/badge/python-3.11-blue)
![LangGraph](https://img.shields.io/badge/langgraph-0.3.30-orange)
![Gemini](https://img.shields.io/badge/LLM-Gemini%202.0%20Flash%20Lite-blue)
![Streamlit](https://img.shields.io/badge/frontend-Streamlit-red)
![Docker](https://img.shields.io/badge/docker-supported-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)

# Table of content

- [For Users](#for-users)
  - [Application Demo](#application-demo)
  - [Apps Features](#apps-features)
  - [How to Use the Apps](#how-to-use-the-apps)
- [For Developers](#for-developers)
  - [Project Structure](#project-structure)
  - [Getting Started](#getting-started)
  - [Code Explanation](#code-explanation)
  - [Run the project with Docker (Local)](#run-the-project-with-docker-local)
  - [Deploy to Google Cloud Run](#deploy-to-google-cloud-run)
  - [Contributors](#contributors)
  - [License](#license)


# For Users

## Application Demo

The deployed application is in this link:
_(link to be added after deployment)_


## Apps Features

The application consists of 5 processing steps: 1 file-reading tool and 4 AI agents, all orchestrated by a LangGraph `StateGraph` sequential pipeline that passes a shared `PipelineState` dictionary from node to node.

<p align="center"><img src="Image/Multi AI Agents.png" alt="Multi AI Agents Architecture"></p>

### 1. Tools 1 - Read node
This tool transforms the candidate's CV into a readable string format for further processing. It reads a `.txt` file from the path stored in `state["input_path"]` and writes the raw text into `state["input_text"]`. A `pdf_to_txt` utility powered by `pdfplumber` is also available to pre-convert PDF files before they enter the pipeline.

### 2. Agent 1 - CV Parsing
This agent extracts key candidate information from the CV using `ChatGoogleGenerativeAI` (`gemini-2.0-flash-lite`, temperature=0). It constructs a `SystemMessage` + `HumanMessage` prompt pair with rule-based extraction instructions, then parses the LLM's raw response via `re.search` and `json.loads` into a validated JSON object. The output includes the candidate's summary, job experience, skills, education, and projects.

### 3. Agent 2 - Skills Specialization
This agent processes the structured output from Agent 1 to classify the candidate's skills into two categories:
1. **Explicit skills**: Terms directly mentioned in the CV text.
2. **Implicit skills**: Skills inferred by the LLM from the candidate's experience, projects, and education context.

For each implicit skill the LLM generates a one-line evidence note to justify the inference. Output is a JSON object with `explicit_skills` (list of strings) and `implicit_skills` (list of `{skill, evidence}` objects).

### 4. Agent 3 - Job Market Analysis
In this step, the user specifies the target role for skill comparison. Unlike other agents, this node bypasses the LangChain abstraction and calls the native `google-genai` SDK directly (`genai.Client.models.generate_content`) with `types.Tool(google_search=types.GoogleSearch())`, enabling Gemini to query live web data and synthesize real-time results into:
1. Current job requirements
2. In-demand skills
3. Relevant technologies for the selected role

### 5. Agent 4 - Recommendation report
This agent synthesizes the outputs of Agents 2 and 3 via `ChatGoogleGenerativeAI`. It constructs a comparative prompt aligning the candidate's explicit and implicit skills against market-demanded requirements. The final JSON output contains three markdown-formatted string fields:
- `skill_gap_analysis`: highlights alignment and gaps between candidate profile and job market needs
- `key_strengths`: summarizes the candidate's strongest and most market-relevant skills
- `upskilling_plan`: recommends targeted learning paths, certifications, or experiences to close identified gaps

The output is rendered in Streamlit and available as a downloadable Markdown report.


## How to use the Apps

### 1. Start the Streamlit application
Launch the Streamlit frontend to begin the analysis.
```bash
python -m streamlit run streamlit_app.py
```

### 2. Open the local URL
By default, Streamlit runs at:
```bash
http://localhost:8501
```

### 3. Upload your CV and fill out the role
Prepare your CV in .txt format. Use the Upload File button in the web app to upload it.
<p align="center">
  <img src="Image/Input skill gap analysis.png" alt="Alt text" width="400">
</p>
Then, enter the target role you want to analyze (e.g., Data Scientist, Software Engineer).

### 4. Start the analysis
Click Analyze to process your CV against the selected role using job market insights.
<p align="center">
  <img src="Image/analysis result.png" alt="Alt text" width="400">
</p>

### 5. Final report result
Each agent’s results will be displayed in Streamlit.
<p align="center">
  <img src="Image/final report download.png" alt="Alt text" width="400">
</p>
A comprehensive final report can be downloaded, providing clear insights into your skill-gap analysis and overall candidate profile.


# For Developers

## Project Structure

```
AI-Powered-Skill-Gap-Analysis/
├── main.py                                    # LangGraph pipeline orchestration entry point
├── streamlit_app.py                           # Streamlit frontend application
├── requirements.txt                           # Python package dependencies
├── environment.env                            # Environment variables (API keys)
├── agent_function/
│   ├── __init__.py
│   ├── agent_1_cv_parsing.py                  # Agent 1: structured CV information extraction
│   ├── agent_2_specialize_skills.py           # Agent 2: explicit and implicit skill classification
│   ├── agent_3_market_intelligence.py         # Agent 3: grounded web search for job market data
│   └── agent_4_recommendation_report.py      # Agent 4: skill-gap synthesis and report generation
├── config/
│   ├── constants.py                           # LLM client initialization and model configuration
│   └── utils.py                               # File reading node and PDF-to-text converter
├── schemas/
│   ├── __init__.py
│   └── pipeline_state.py                      # Shared PipelineState TypedDict for LangGraph
├── input/                                     # Directory for input CV files (.txt)
├── output/                                    # Directory for pipeline output (JSON)
└── Image/                                     # Application screenshots
```

## Getting started

Clone the repository and install dependencies:
```bash
git clone https://github.com/nugrahazikry/AI-Powered-Skill-Gap-Analysis.git
cd AI-Powered-Skill-Gap-Analysis
pip install -r requirements.txt
```

Set up your credentials (see [Credentials Setup](#credentials-setup)), then launch the app:
```bash
python -m streamlit run streamlit_app.py
```

## Architectural overview
This project uses a **sequential multi-agent architecture** built on LangGraph's `StateGraph`. All nodes share a single `PipelineState` dictionary that flows linearly through five steps:

```
START → read_file → extract_info → classify_skills → search → report → END
```

Agents 1, 2, and 4 invoke Gemini through the LangChain `ChatGoogleGenerativeAI` abstraction layer. Agent 3 bypasses LangChain and calls the native `google-genai` SDK directly to enable real-time `GoogleSearch` grounding.

<p align="center">
  <img src="Image/Multi AI Agents.png" alt="Alt text" width="400">
</p>

### Dependencies and Prerequisites

Attached are the technical requirements needed to run this project:
1. Multi-AI Agent Framework: LangGraph 0.3.30
2. Programming Language: Python 3.11+
3. LLM: Google Gemini 2.0 Flash Lite (`gemini-2.0-flash-lite`)
4. Web Search Grounding: Google Search via `google-genai` SDK (`types.GoogleSearch`)

| Dependency | Version | Purpose |
|---|---|---|
| `python-dotenv` | 0.21.0 | Load `GEMINI_API_KEY` from `environment.env` into `os.environ` |
| `langchain-core` | 0.3.76 | Core LangChain abstractions: `SystemMessage`, `HumanMessage`, LLM invocation interface |
| `langgraph` | 0.3.30 | `StateGraph` orchestration — defines nodes, directed edges, and shared state flow |
| `langchain-google-genai` | 2.0.5 | `ChatGoogleGenerativeAI` wrapper for invoking Gemini models via LangChain |
| `langchain-community` | 0.3.20 | Community LangChain integrations and shared tooling |
| `pandas` | 2.2.2 | Tabular data handling in the Streamlit frontend |
| `numpy` | 1.26.4 | Numerical computation dependency |
| `pdfplumber` | 0.11.7 | PDF text extraction for CV preprocessing (`pdf_to_txt` utility) |
| `streamlit` | 1.49.1 | Web UI framework — file uploader, expanders, download button |
| `google-genai` | ≥1.7.0 | Native Google Generative AI SDK used in Agent 3 for `GoogleSearch` grounding |

### Tech stack

| Layer | Tech Stack |
|---|---|
| Frontend | Streamlit 1.49.1 |
| Pipeline Orchestration | LangGraph 0.3.30 (`StateGraph`) |
| LLM | Google Gemini 2.0 Flash Lite (`gemini-2.0-flash-lite`, temperature=0) |
| LLM Abstraction (Agents 1, 2, 4) | LangChain-Google-GenAI 2.0.5 (`ChatGoogleGenerativeAI`) |
| Real-time Web Grounding (Agent 3) | Google Search via `google-genai` SDK (`types.Tool(google_search=types.GoogleSearch())`) |
| State Management | `PipelineState` — a `dict` subclass with typed fields passed across all LangGraph nodes |
| Response Parsing | Python `re.search` + `json.loads` for structured JSON extraction from LLM outputs |
| Document Parsing | pdfplumber 0.11.7 |
| Configuration | python-dotenv 0.21.0 |
| Language | Python 3.11+ |

### Credentials setup

This project requires a **Google Gemini API key**. Follow these steps:

1. Obtain an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

2. Copy the example environment file:
```bash
cp environment.env.example environment.env
```

3. Open `environment.env` and fill in your key:
```bash
nano environment.env  # or use any text editor
```

4. Below is the full list of required variables:

| Variable | Description | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key — used by `ChatGoogleGenerativeAI` (Agents 1, 2, 4) and `genai.Client` (Agent 3 grounding) | ✅ Yes |

> ⚠️ **Never commit your `environment.env` file.** Make sure it is listed in your `.gitignore`.

**Example `environment.env.example` file:**
```env
# environment.env.example — copy this to environment.env and fill in your values
GEMINI_API_KEY=your_gemini_api_key_here
```


## Code explanation

### Key Backend files

| Category | File | Description |
|---|---|---|
| Pipeline Orchestration | `main.py` | Builds and compiles the LangGraph `StateGraph`; registers five nodes and wires them with `add_edge` in sequence (`read_file → extract_info → classify_skills → search → report`); exposes `run_pipeline(cv_path, role)` as the callable entry point |
| State Schema | `pipeline_state.py` | Defines `PipelineState` — a `dict` subclass with typed annotations for `input_path`, `role`, `input_text`, and each agent's output key; serves as the single shared context object traversing all nodes |
| LLM Configuration | `constants.py` | Initializes `ChatGoogleGenerativeAI` (LangChain wrapper) and `genai.Client` (native SDK) with model `gemini-2.0-flash-lite` at temperature=0; centralizes the API key via `python-dotenv` |
| File Utilities | `utils.py` | `read_file_node`: LangGraph-compatible node that reads the `.txt` CV from `state["input_path"]` into `state["input_text"]`; `pdf_to_txt`: converts PDF to plain text using `pdfplumber` and saves output to a target directory |
| Agent 1 | `agent_1_cv_parsing.py` | Sends a `[SystemMessage, HumanMessage]` pair to `ChatGoogleGenerativeAI`; extracts a JSON block from the raw string response via `re.search(r"\{.*\}", ..., re.S)` and `json.loads`; returns `{"agent_1_cv_parsing": {summary, experience, skills, education, projects}}` |
| Agent 2 | `agent_2_specialize_skills.py` | Consumes `state["agent_1_cv_parsing"]` and re-prompts Gemini to classify skills into `explicit_skills` (flat string list) and `implicit_skills` (list of `{skill, evidence}` dicts); same JSON parsing pattern as Agent 1 |
| Agent 3 | `agent_3_market_intelligence.py` | Calls `genai.Client.models.generate_content` with `GenerateContentConfig(tools=[Tool(google_search=GoogleSearch())])` to invoke Gemini with live web search grounding; returns `{job_requirements, demanded_skills, list_of_technologies}` |
| Agent 4 | `agent_4_recommendation_report.py` | Synthesizes `agent_2_specialize_skills` and `agent_3_market_intelligence` outputs via a strategist prompt; returns `{skill_gap_analysis, key_strengths, upskilling_plan}` as a JSON object with markdown-formatted string values |

### Key Frontend files

| Category | File | Description |
|---|---|---|
| Frontend Application | `streamlit_app.py` | Streamlit UI: `st.file_uploader` (`.txt` only) writes the upload to `temp.txt` before passing the path to `run_pipeline()`; `st.text_input` captures the target role; results are rendered per-agent inside `st.expander` sections using `st.markdown`; a `st.download_button` exports the Agent 4 output as a `.md` file |


## Run the project with Docker (Local)

### 1. Create a `Dockerfile` at the project root
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Build the Docker image
```bash
docker build -t skill-gap-analysis .
```

### 3. Run the container
Pass your Gemini API key as an environment variable:
```bash
docker run -p 8501:8501 -e GEMINI_API_KEY=your_gemini_api_key_here skill-gap-analysis
```

### 4. Open the application
```
http://localhost:8501
```


## Deploy to Google Cloud Run

### 1. Authenticate and set your project
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Build and push the image to Google Container Registry
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/skill-gap-analysis
```

### 3. Deploy to Cloud Run
```bash
gcloud run deploy skill-gap-analysis \
  --image gcr.io/YOUR_PROJECT_ID/skill-gap-analysis \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Access the deployed application
After deployment, Cloud Run will output a public HTTPS URL:
```
https://skill-gap-analysis-xxxx-uc.a.run.app
```

> ⚠️ **Security note:** Avoid passing `GEMINI_API_KEY` directly via `--set-env-vars` in production. Use **Google Secret Manager** instead:
> ```bash
> gcloud run deploy skill-gap-analysis \
>   --image gcr.io/YOUR_PROJECT_ID/skill-gap-analysis \
>   --set-secrets GEMINI_API_KEY=gemini-api-key:latest
> ```


## Contributors
Contributors names and contact info:
1. **[Zikry Adjie Nugraha](https://github.com/nugrahazikry)**: Full end-to-end development — multi-agent pipeline design, LangGraph `StateGraph` orchestration, Google Gemini integration (LangChain and native SDK), Google Search grounding, Streamlit frontend, and cloud deployment.

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.