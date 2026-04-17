// ================================================
// SkillGap AI – Frontend Logic
// ================================================

const form = document.getElementById("analyzeForm");
const fileInput = document.getElementById("cvFile");
const fileUploadZone = document.getElementById("fileUploadZone");
const fileNameDisplay = document.getElementById("fileName");
const analyzeBtn = document.getElementById("analyzeBtn");            
const previewCvBtn = document.getElementById("previewCvBtn");
const emptyState = document.getElementById("emptyState");
const loadingState = document.getElementById("loadingState");
const resultsState = document.getElementById("resultsState");
const errorState = document.getElementById("errorState");
const topNav = document.getElementById("topNav");

let analysisResult = null;
let previewCvObjectUrl = null;
let loadingInterval = null;
let analyzePollTimer = null;

// ---------- Demo Data ----------

const DEMO_DATA = {
    agent_1_cv_parsing: {
        summary: "AI Engineer with 4 years of experience in AI, LLMs, Machine Learning, NLP, and Computer Vision, specializing in solving complex business problems across mining, e-commerce, and digital marketing industries. Proficient in Python, SQL, and major cloud platforms (GCP, AWS, Azure), with a track record of leading and deploying over 20 impactful AI and data science projects.",
        experience: [
            {
                title: "Senior Full-stack AI Engineer",
                company: "PT. Merdeka Copper Gold Tbk.",
                period_start: "December 2025",
                period_end: "Present",
                descriptions: [
                    "Lead end-to-end AI pipeline development for mining operations including LLM-based document intelligence systems",
                    "Architect multi-agent workflows using LangGraph and Google Gemini, improving operational decision-making speed by 40%",
                    "Deploy and maintain production services on GCP with Docker, CI/CD, and automated cloud schedulers"
                ]
            },
            {
                title: "AI Data Scientist",
                company: "NucleusX BV",
                period_start: "February 2024",
                period_end: "November 2025",
                descriptions: [
                    "Developed NLP pipelines for automated contract clause extraction, reducing manual review time by 65%",
                    "Built computer vision defect detection system achieving 94% accuracy on a high-speed production line",
                    "Collaborated with European clients to define AI product roadmaps and validate proof-of-concept models"
                ]
            },
            {
                title: "Data Scientist",
                company: "IlmuOne Data",
                period_start: "March 2022",
                period_end: "January 2024",
                descriptions: [
                    "Designed and delivered 15+ machine learning solutions across e-commerce and digital marketing clients",
                    "Built real-time recommendation engines using collaborative filtering and feature engineering on GCP BigQuery",
                    "Presented data-driven insights to C-level stakeholders, translating complex models into business strategies"
                ]
            }
        ],
        total_experience: "3 Years, 11 Months",
        education: [
            {
                degree: "B.Sc. Chemical Engineering",
                institution: "Institut Teknologi Bandung",
                period_start: "2017",
                period_end: "2022",
                gpa: "3.52"
            }
        ],
        certifications: [
            { name: "TensorFlow Developer Certificate", issuer: "Google", year: "2022" },
            { name: "AWS Certified Machine Learning – Specialty", issuer: "Amazon Web Services", year: "2023" },
            { name: "Professional Scrum Master I", issuer: "Scrum.org", year: "2021" }
        ],
        organization: [
            {
                title: "Head of Data Science Division",
                organization: "ITB Data Science Club",
                period_start: "August 2019",
                period_end: "July 2020",
                descriptions: [
                    "Led a team of 12 student members in national data science competitions, winning 2 top-3 placements",
                    "Organized 4 internal Python and ML workshops attended by 80+ participants"
                ]
            }
        ],
        projects: [
            {
                name: "AI-powered Inventory Forecasting System",
                period_start: "March 2023",
                period_end: "June 2023",
                descriptions: [
                    "Built LSTM and XGBoost ensemble for mining spare-parts demand forecasting",
                    "Reduced stockout incidents by 23% and inventory holding costs by 18% in production"
                ]
            },
            {
                name: "LLM-based Document Extraction Pipeline",
                period_start: "September 2023",
                period_end: "December 2023",
                descriptions: [
                    "Designed RAG pipeline using LangChain and Azure OpenAI for legal contract clause extraction",
                    "Achieved 91% extraction accuracy across 500+ contract templates"
                ]
            },
            {
                name: "Real-time Computer Vision Defect Detection",
                period_start: "January 2024",
                period_end: "April 2024",
                descriptions: [
                    "Trained YOLOv8 model on 12,000 labeled images for production line defect classification",
                    "Deployed edge inference system with 40ms latency on industrial camera hardware"
                ]
            },
            {
                name: "Multi-agent Recommendation Engine",
                period_start: "June 2024",
                period_end: "October 2024",
                descriptions: [
                    "Built multi-agent e-commerce recommendation system using LangGraph and Vertex AI",
                    "Increased click-through rate by 31% in A/B test with 50,000 daily active users"
                ]
            }
        ]
    },
    agent_2_specialize_skills: {
        skill_summary: "Your profile reads as a full-stack AI engineer who bridges research-style experimentation with production deployment. Explicitly, you emphasize Python, SQL, cloud platforms (GCP, AWS, Azure), and modern LLM tooling such as LangChain and FastAPI. Implicitly, the work history shows strong system design, MLOps discipline, and the ability to decompose ambiguous business problems into reliable pipelines and agent workflows—skills that sit alongside the technical stack and matter for senior IC and tech-lead expectations.",
        explicit_skills: ["Python", "SQL", "LangChain", "FastAPI", "Agentic AI", "Prompt Engineering", "GCP", "AWS", "Azure", "Docker", "CI/CD", "OpenCV", "JavaScript"],
        implicit_skills: [
            { skill: "System Design", evidence: "Led deployment of 20+ end-to-end AI pipelines across multiple cloud platforms" },
            { skill: "Cross-functional Communication", evidence: "Collaborated with mining engineers and business stakeholders to define requirements" },
            { skill: "MLOps", evidence: "Built CI/CD pipelines, containerised workloads, and cloud schedulers for ML models" },
            { skill: "Problem Decomposition", evidence: "Broke complex multi-domain business problems into structured AI agent workflows" },
            { skill: "Data Pipeline Engineering", evidence: "Designed GCP Pub/Sub and Lambda-based event-driven data ingestion systems" }
        ]
    },
    agent_3_market_intelligence: {
        job_requirements: [
            "Design, build, and maintain production-grade AI/ML systems and LLM-powered applications",
            "Collaborate with product and engineering teams to define AI feature requirements",
            "Develop and fine-tune large language models and generative AI pipelines",
            "Implement robust evaluation, monitoring, and observability frameworks for AI systems",
            "Translate research prototypes into scalable, well-tested production services"
        ],
        sources: [
            {
                title: "LinkedIn Jobs — AI Engineer", uri: "https://www.linkedin.com/jobs", portal: "Web",
                role_overview: "An AI Engineer designs, builds, and deploys AI-powered systems including LLM applications, ML pipelines, and generative AI products at scale.",
                key_responsibilities: ["Design and implement LLM-powered applications and agentic workflows", "Collaborate with product and engineering teams to define AI feature requirements", "Deploy and monitor ML models in production environments", "Develop evaluation and observability frameworks for AI systems", "Translate research prototypes into scalable production services"],
                demanded_skills: ["LLM Fine-tuning", "RAG Pipelines", "Prompt Engineering", "MLOps", "System Design"],
                soft_skills: ["Communication", "Problem-solving", "Adaptability", "Collaboration"],
                tools_software: ["PyTorch", "LangChain", "Hugging Face", "AWS SageMaker", "Docker"],
                certifications: ["AWS Certified Machine Learning Specialty", "Google Professional ML Engineer"]
            },
            {
                title: "Glassdoor — AI Engineer Salaries & Reviews", uri: "https://www.glassdoor.com", portal: "Web",
                role_overview: "AI Engineers build and maintain intelligent systems, focusing on LLM integration, model deployment, and cross-functional collaboration with product teams.",
                key_responsibilities: ["Build and integrate LLM APIs into production applications", "Implement CI/CD pipelines for ML model deployment", "Conduct code reviews and ensure engineering best practices", "Monitor model performance and retrain as needed"],
                demanded_skills: ["API Integration", "Vector Databases", "Cloud Architecture", "CI/CD"],
                soft_skills: ["Critical Thinking", "Time Management", "Continuous Learning"],
                tools_software: ["Python", "FastAPI", "Pinecone", "GitHub Actions", "OpenAI API"],
                certifications: ["Certified Kubernetes Administrator (CKA)", "Microsoft Azure AI Engineer Associate"]
            }
        ],
        certifications: ["AWS Certified Machine Learning Specialty", "Google Professional ML Engineer", "Certified Kubernetes Administrator (CKA)", "Microsoft Azure AI Engineer Associate"],
        demanded_skills: ["LLM Fine-tuning", "RAG Pipelines", "Vector Databases", "MLOps", "Python", "PyTorch", "Kubernetes", "REST APIs", "Prompt Engineering", "LangChain / LlamaIndex", "Cloud Platforms", "CI/CD", "System Design"],
        soft_skills: ["Communication", "Collaboration", "Problem-solving", "Critical Thinking", "Adaptability", "Attention to Detail", "Time Management", "Continuous Learning"],
        list_of_technologies: ["OpenAI API", "Anthropic Claude", "Google Gemini", "Hugging Face", "Pinecone", "Weaviate", "PostgreSQL", "Redis", "FastAPI", "Docker", "Kubernetes", "GitHub Actions", "GCP Vertex AI", "AWS SageMaker", "Azure ML"]
    },
    agent_4_recommendation_report: {
        certifications_to_pursue: [
            "AWS Certified Machine Learning Specialty",
            "Google Professional ML Engineer",
            "Certified Kubernetes Administrator (CKA)",
            "Microsoft Azure AI Engineer Associate"
        ],
        market_aligned_skills: ["Python", "FastAPI", "LangChain (Agentic AI)", "SQL", "Cloud (GCP, AWS, Azure)", "System Design"],
        missing_skills: ["Kubernetes (Market demand focus)", "Pinecone / Weaviate (Vector DBs)", "GitHub Actions", "LLM Fine-tuning", "RAG Pipelines"],
        summary_analysis: "The candidate possesses a strong foundation in core AI engineering skills, with explicit proficiencies in Python, FastAPI, and Agentic AI workflows. However, to fully align with market demands for production-ready applications, they need to bridge gaps in container orchestration (Kubernetes) and specialized LLM tooling such as Vector Databases and fine-tuning pipelines.",
        key_strengths: [
            { title: "End-to-End Deployment", description: "Proven experience building and scaling AI pipelines across GCP, AWS, and Azure." },
            { title: "Problem Decomposition", description: "Strong ability to translate complex business needs into actionable AI agent workflows." },
            { title: "Cross-Functional Collaboration", description: "Demonstrated success leading deployments and bridging gaps between engineering, product, and business teams." }
        ],
        resume_action_items: [
            { instead_of: "Experienced in Docker and CI/CD", change_to: "Implemented automated ML CI/CD pipelines using GitHub Actions and Docker" },
            { instead_of: "Built AI applications", change_to: "Developed scalable RAG Pipelines and Agentic AI workflows using LangChain" },
            { instead_of: "Worked with AWS and GCP", change_to: "Deployed production-grade models using AWS SageMaker and GCP Vertex AI" },
            { instead_of: "Managed databases", change_to: "Architected vector search solutions using Pinecone and PostgreSQL for LLM retrieval" }
        ],
        upskilling_plan: {
            low_effort: [
                { skill: "LlamaIndex Framework", timeframe: "2-3 Days", description: "Learn syntax for connecting LLMs to custom data sources." }
            ],
            medium_effort: [
                { skill: "Vector Databases (Pinecone/Weaviate)", timeframe: "1-2 Weeks", description: "Build practical, hands-on semantic search and retrieval apps." },
                { skill: "GitHub Actions for ML", timeframe: "2 Weeks", description: "Translate generic CI/CD knowledge into specific GitHub workflows." }
            ],
            high_effort: [
                { skill: "LLM Fine-Tuning Optimization", timeframe: "1-2 Months", description: "Deep dive into PEFT, LoRA, and training mechanics." },
                { skill: "AWS SageMaker / GCP Vertex AI Deep-Dive", timeframe: "1-2 Months", description: "Gain market-leading expertise in managed cloud ML platforms." }
            ]
        }
    }
};

function extractPythonTraceback(text) {
    if (!text) return "";
    const marker = "Traceback (most recent call last):";
    const idx = text.indexOf(marker);
    return idx >= 0 ? text.slice(idx).trim() : "";
}

async function parseApiResponse(response, label) {
    const rawText = await response.text();
    let data = {};

    try {
        data = rawText ? JSON.parse(rawText) : {};
    } catch {
        const err = new Error(`${label} failed`);
        const tb = extractPythonTraceback(rawText);
        err.stack = tb || rawText || "(no traceback available)";
        throw err;
    }

    if (!response.ok || data.error) {
        const err = new Error(data.error || `${label} failed (${response.status})`);
        err.stack = data.traceback || extractPythonTraceback(rawText) || "(no traceback available)";
        throw err;
    }

    return data;
}

document.getElementById("demoBtn").addEventListener("click", async () => {
    try {
        // Render agents 1–3 immediately with demo data; agent 4 shows a loading placeholder
        const demoPartial = { ...DEMO_DATA, agent_4_recommendation_report: {} };
        analysisResult = { ...DEMO_DATA };
        renderResults(demoPartial);
        showState("results");

        // Scroll to agent 4 section after a brief moment so user sees the placeholder
        setTimeout(() => {
            const sec = document.getElementById("sec-report");
            if (sec) sec.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 400);

        // Call backend to generate real agent 4 result from demo agent_2 + agent_3 data
        const resp = await fetch("/api/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                role: "AI Engineer",
                agent_2_specialize_skills: DEMO_DATA.agent_2_specialize_skills,
                agent_3_market_intelligence: DEMO_DATA.agent_3_market_intelligence,
            }),
        });
        const a4 = await parseApiResponse(resp, "Recommend API");

        // Patch result and update only agent 4 section
        analysisResult.agent_4_recommendation_report = a4;
        renderAgent4(a4);
    } catch (err) {
        showRenderError(err);
    }
});

// ---------- File Upload ----------

fileUploadZone.addEventListener("click", () => fileInput.click());

fileUploadZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    fileUploadZone.classList.add("dragover");
});

fileUploadZone.addEventListener("dragleave", () => {
    fileUploadZone.classList.remove("dragover");
});

fileUploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    fileUploadZone.classList.remove("dragover");
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === "application/pdf") {
        fileInput.files = files;
        handleFileSelected(files[0]);
    }
});

fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        handleFileSelected(fileInput.files[0]);
    }
});

function handleFileSelected(file) {
    fileNameDisplay.textContent = file.name;
    fileUploadZone.classList.add("has-file");
    updatePreviewCvButton(file);
}

function updatePreviewCvButton(file) {
    if (!previewCvBtn) return;
    if (previewCvObjectUrl) {
        URL.revokeObjectURL(previewCvObjectUrl);
        previewCvObjectUrl = null;
    }

    if (!file) {
        previewCvBtn.classList.add("hidden");
        return;
    }

    previewCvObjectUrl = URL.createObjectURL(file);
    previewCvBtn.classList.remove("hidden");
}

if (previewCvBtn) {
    previewCvBtn.addEventListener("click", () => {
        if (!previewCvObjectUrl) return;
        window.open(previewCvObjectUrl, "_blank", "noopener,noreferrer");
    });
}

if (fileInput && fileInput.files && fileInput.files.length > 0) {
    updatePreviewCvButton(fileInput.files[0]);
}

// ---------- Form Submit ----------

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const file = fileInput.files[0];
    const targetRole = document.getElementById("targetRole").value.trim();

    if (!file || !targetRole) return;

    showState("loading");
    analyzeBtn.disabled = true;
    resetLoadingUI();
    setLoadingFromBackend({
        stage_index: 1,
        stage_heading: "Reading your CV",
        stage_label: "Parsing your CV",
        stage_subdetail: "Extracting your work experience, education, projects, and qualifications from the uploaded document",
        status: "running",
        stage_status: "running",
    });

    const formData = new FormData();
    formData.append("file", file);
    formData.append("target_role", targetRole);

    try {
        const response = await fetch("/api/analyze/start", {
            method: "POST",
            body: formData,
        });
        const startData = await parseApiResponse(response, "Start Analysis API");
        const finalPayload = await pollAnalysisJob(startData.job_id);
        const data = finalPayload.result;

        analysisResult = data || {};
        renderResults(analysisResult);
        showState("results");
        if (finalPayload && finalPayload.timings_ms) {
            console.log("[Pipeline timings ms]", finalPayload.timings_ms, "total:", finalPayload.total_elapsed_ms);
        }
    } catch (err) {
        showRenderError(err);
    } finally {
        stopAnalyzePolling();
        analyzeBtn.disabled = false;
    }
});

// ---------- Error display ----------

function showRenderError(err) {
    const msgEl = document.getElementById("errorMessage");
    const stackEl = document.getElementById("errorStack");
    if (msgEl) msgEl.textContent = err.message || String(err);
    if (stackEl) {
        const stack = err.stack || "(no stack trace available)";
        stackEl.textContent = stack;
        stackEl.style.display = "block";
    }
    showState("error");
    console.error("[renderResults error]", err);
}

// ---------- States ----------

function showState(state) {
    // Prevent overlapping loading animations when user runs multiple analyses.
    if (loadingInterval) {
        clearInterval(loadingInterval);
        loadingInterval = null;
    }
    stopAnalyzePolling();

    emptyState.classList.add("hidden");
    loadingState.classList.add("hidden");
    resultsState.classList.add("hidden");
    errorState.classList.add("hidden");
    topNav.classList.add("hidden");

    switch (state) {
        case "empty":    emptyState.classList.remove("hidden"); break;
        case "loading":  loadingState.classList.remove("hidden"); break;
        case "results":
            resultsState.classList.remove("hidden");
            topNav.classList.remove("hidden");
            break;
        case "error":    errorState.classList.remove("hidden"); break;
    }
}

function stopAnalyzePolling() {
    if (analyzePollTimer) {
        clearInterval(analyzePollTimer);
        analyzePollTimer = null;
    }
}

function resetLoadingUI() {
    const steps = ["step1", "step2", "step3", "step4"];
    steps.forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.classList.remove("active", "done");
    });
    const heading = document.getElementById("loadingHeading");
    const stepLabel = document.getElementById("loadingStep");
    const subText = document.getElementById("loadingSubdetailText");
    if (heading) heading.textContent = "Analyzing your profile";
    if (stepLabel) stepLabel.textContent = "Starting multi-agent pipeline";
    if (subText) subText.textContent = "Preparing to analyze your profile";
}

function setLoadingFromBackend(payload) {
    if (!payload) return;
    const stageIndex = Math.min(Math.max(Number(payload.stage_index || 1), 1), 4);
    const steps = ["step1", "step2", "step3", "step4"];
    const stageRunning = (payload.stage_status || payload.status) === "running";
    const stageCompleted = (payload.stage_status || payload.status) === "completed";

    steps.forEach((id, idx) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.remove("active", "done");
        const stepNo = idx + 1;
        if (stepNo < stageIndex) {
            el.classList.add("done");
        } else if (stepNo === stageIndex) {
            if (stageRunning) el.classList.add("active");
            if (stageCompleted) el.classList.add("done");
        }
    });

    const heading = document.getElementById("loadingHeading");
    const stepLabel = document.getElementById("loadingStep");
    const subText = document.getElementById("loadingSubdetailText");
    const subDetail = document.getElementById("loadingSubdetail");
    if (heading && payload.stage_heading) heading.textContent = payload.stage_heading;
    if (stepLabel && payload.stage_label) stepLabel.textContent = payload.stage_label;
    if (subText && payload.stage_subdetail) subText.textContent = payload.stage_subdetail;
    if (subDetail) {
        subDetail.classList.remove("fade-in");
        void subDetail.offsetWidth;
        subDetail.classList.add("fade-in");
    }
}

function pollAnalysisJob(jobId) {
    return new Promise((resolve, reject) => {
        if (!jobId) {
            reject(new Error("Analysis job ID is missing."));
            return;
        }
        stopAnalyzePolling();

        const pollOnce = async () => {
            try {
                const resp = await fetch(`/api/analyze/status/${encodeURIComponent(jobId)}`);
                const payload = await parseApiResponse(resp, "Analysis Status API");

                setLoadingFromBackend(payload);

                if (payload.status === "completed") {
                    stopAnalyzePolling();
                    resolve(payload);
                    return;
                }
                if (payload.status === "error") {
                    stopAnalyzePolling();
                    const err = new Error(payload.error || "Analysis job failed.");
                    err.stack = payload.traceback || err.stack;
                    reject(err);
                }
            } catch (err) {
                stopAnalyzePolling();
                reject(err);
            }
        };

        pollOnce();
        analyzePollTimer = setInterval(pollOnce, 1200);
    });
}

// ---------- Loading Animation ----------

function animateLoadingSteps(startStep = 0) {
    const steps = ["step1", "step2", "step3", "step4"];

    const labels = [
        "Parsing your CV",
        "Classifying your skills",
        "Analyzing job market",
        "Generating recommendations",
    ];

    const headings = [
        "Reading your CV",
        "Mapping your skills",
        "Researching the market",
        "Building your report",
    ];

    const subdetails = [
        "Extracting your work experience, education, projects, and qualifications from the uploaded document",
        "Categorizing each skill as explicitly stated or implicitly demonstrated through your experience",
        "Searching live job market sources to identify what skills and tools employers demand for your target role",
        "Comparing your skill profile against market demand and writing a personalized gap analysis with action steps",
    ];

    // Reset any stale state from previous runs.
    steps.forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.classList.remove("active", "done");
    });

    if (loadingInterval) {
        clearInterval(loadingInterval);
        loadingInterval = null;
    }

    // Mark all steps before startStep as done immediately
    for (let j = 0; j < startStep; j++) {
        const el = document.getElementById(steps[j]);
        if (el) el.classList.add("done");
    }

    function applyStep(i) {
        const cur = document.getElementById(steps[i]);
        if (cur) cur.classList.add("active");
        const stepLabel   = document.getElementById("loadingStep");
        const heading     = document.getElementById("loadingHeading");
        const subText     = document.getElementById("loadingSubdetailText");
        const subDetail   = document.getElementById("loadingSubdetail");
        if (stepLabel) stepLabel.textContent = labels[i];
        if (heading)   heading.textContent   = headings[i];
        if (subText)   subText.textContent   = subdetails[i];
        if (subDetail) {
            subDetail.classList.remove("fade-in");
            void subDetail.offsetWidth; // force reflow for animation restart
            subDetail.classList.add("fade-in");
        }
    }

    applyStep(startStep);
    let i = startStep + 1;
    loadingInterval = setInterval(() => {
        if (i >= steps.length) {
            clearInterval(loadingInterval);
            loadingInterval = null;
            return;
        }
        const prev = document.getElementById(steps[i - 1]);
        if (prev) { prev.classList.remove("active"); prev.classList.add("done"); }
        applyStep(i);
        i++;
    }, 3000);
}

// ---------- Render Results ----------

function renderResults(data) {
    // If input was empty/null, show error state
    if (!data.agent_1_cv_parsing && !data.agent_2_specialize_skills) {
        showRenderError({ message: "No CV content found. Please upload a non-empty file.", stack: "" });
        return;
    }

    // Agent 1 – CV Parsing
    const a1 = data.agent_1_cv_parsing || {};
    setText("cvSummary", a1.summary);
    console.log("[Agent 1 raw response]", a1._raw);
    console.log("[Agent 1 parsed]", a1);
    renderCvExperience("cvExperience", "cvExpLabel", a1.experience || [], a1.total_experience);
    renderCvEducation("cvEducation", a1.education || []);
    renderCvCertifications("cvCertifications", a1.certifications || []);
    renderCvOrganization("cvOrganization", a1.organization || []);
    renderCvProjects("cvProjects", a1.projects || []);

    // Agent 2 – Skills Specialization
    const a2 = data.agent_2_specialize_skills || {};
    // Skill summary
    const skillSummaryEl = document.getElementById("skillSummary");
    if (skillSummaryEl) skillSummaryEl.textContent = a2.skill_summary || "";
    // Skill tags
    setTags("explicitSkills", a2.explicit_skills);
    renderImplicitSkills("implicitSkills", a2.implicit_skills);

    // Agent 3 – Market Intelligence
    const a3 = data.agent_3_market_intelligence || {};
    renderSourceCards("jobRequirementsGrid", a3.sources);
    setTags("demandedSkills", a3.demanded_skills);
    setTags("softSkills", a3.soft_skills);
    setTags("technologies", a3.list_of_technologies);
    setTags("marketCertifications", a3.certifications);

    // Agent 4 – Recommendation Report
    renderAgent4(data.agent_4_recommendation_report);
}

function renderAgent4(a4data) {
    const a4 = a4data || {};
    const isLoading = !a4.summary_analysis && !a4.market_aligned_skills && !a4.key_strengths;

    if (isLoading) {
        const placeholder = "Generating recommendations based on your profile and market data...";
        const el = document.getElementById("a4SummaryAnalysis");
        if (el) el.textContent = placeholder;
        return;
    }

    // Dynamic subtitle from role input
    const roleInput = document.getElementById("targetRole");
    const subEl = document.getElementById("a4SubTitle");
    if (subEl) {
        const role = (roleInput && roleInput.value.trim()) ? roleInput.value.trim() : "your target role";
        subEl.textContent = `Automated structural analysis against live market demands for ${role}.`;
    }

    // Market aligned skills — rendered as pill tags (green, like Agent 3 tech tags)
    const alignedEl = document.getElementById("a4AlignedSkills");
    if (alignedEl) {
        alignedEl.innerHTML = "";
        const alignedSkills = a4.market_aligned_skills || [];
        alignedSkills.forEach(skill => {
            const span = document.createElement("span");
            span.className = "tag a4-tag-aligned";
            span.textContent = skill;
            alignedEl.appendChild(span);
        });
        applyTagScrollLimit(alignedEl, alignedSkills.length, 7);
    }

    // Missing / high-demand skills — rendered as pill tags (yellow, like Agent 3 market tags)
    const missingEl = document.getElementById("a4MissingSkills");
    if (missingEl) {
        missingEl.innerHTML = "";
        const missingSkills = a4.missing_skills || [];
        missingSkills.forEach(skill => {
            const span = document.createElement("span");
            span.className = "tag a4-tag-missing";
            span.textContent = skill;
            missingEl.appendChild(span);
        });
        applyTagScrollLimit(missingEl, missingSkills.length, 7);
    }

    // Summary analysis
    const summaryEl = document.getElementById("a4SummaryAnalysis");
    if (summaryEl) summaryEl.textContent = a4.summary_analysis || "";

    // Key strengths
    const strengthsEl = document.getElementById("a4KeyStrengths");
    if (strengthsEl) {
        strengthsEl.innerHTML = "";
        (a4.key_strengths || []).forEach(item => {
            const card = document.createElement("div");
            card.className = "a4-strength-card";
            card.innerHTML = `
                <div class="a4-strength-title">${escapeHtml(item.title || "")}</div>
                <div class="a4-strength-desc">${escapeHtml(item.description || "")}</div>
            `;
            strengthsEl.appendChild(card);
        });
    }

    // Resume action items (ATS)
    const atsEl = document.getElementById("a4ResumeActions");
    if (atsEl) {
        atsEl.innerHTML = "";
        const atsItems = a4.resume_action_items || [];
        atsItems.forEach(item => {
            const card = document.createElement("div");
            card.className = "a4-ats-card";
            card.innerHTML = `
                <div class="a4-ats-instead">Instead of: <span>"${escapeHtml(item.instead_of || "")}"</span></div>
                <div class="a4-ats-change">Change to: <span>"${escapeHtml(item.change_to || "")}"</span></div>
            `;
            atsEl.appendChild(card);
        });
        if (atsItems.length === 0) {
            const note = document.createElement("div");
            note.className = "a4-empty-note";
            note.textContent = "No ATS action items generated because work experience job descriptions are unavailable.";
            atsEl.appendChild(note);
        }
    }

    // Upskilling plan – Estimated Time to Upskill
    const plan = a4.upskilling_plan || {};
    renderTteItems("a4TteLow",    plan.low_effort    || []);
    renderTteItems("a4TteMedium", plan.medium_effort || []);
    renderTteItems("a4TteHigh",   plan.high_effort   || []);
}

function renderTteItems(id, items) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = "";
    items.forEach(item => {
        const card = document.createElement("div");
        card.className = "a4-tte-card";
        card.innerHTML = `
            <div class="a4-tte-card-header">
                <span class="a4-tte-skill">${escapeHtml(item.skill || "")}</span>
                <span class="a4-tte-timeframe">${escapeHtml(item.timeframe || "")}</span>
            </div>
            <div class="a4-tte-desc">${escapeHtml(item.description || "")}</div>
        `;
        el.appendChild(card);
    });
}

// ---------- Scroll-Spy ----------

function initScrollSpy() {
    const sections = ["sec-cv", "sec-skills", "sec-market", "sec-report"];
    const navLinks = document.querySelectorAll(".nav-link");
    const mainContent = document.querySelector(".main-content");

    mainContent.addEventListener("scroll", () => {
        let current = "";
        const navbarHeight = 52;

        sections.forEach((id) => {
            const el = document.getElementById(id);
            if (!el) return;
            const rect = el.getBoundingClientRect();
            // Account for the sticky nav offset relative to main-content
            if (rect.top <= navbarHeight + 32) current = id;
        });

        navLinks.forEach((link) => {
            link.classList.toggle("active", link.dataset.section === current);
        });
    }, { passive: true });

    // Smooth scroll on nav click within main-content
    navLinks.forEach((link) => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const target = document.getElementById(link.dataset.section);
            if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
        });
    });
}

initScrollSpy();

// ---------- CV-specific helpers ----------

const MONTH_MAP = {
    // English
    january:0, february:1, march:2, april:3, may:4, june:5,
    july:6, august:7, september:8, october:9, november:10, december:11,
    // English abbreviated
    jan:0, feb:1, mar:2, apr:3, jun:5, jul:6, aug:7, sep:8, oct:9, nov:10, dec:11,
    // Indonesian
    januari:0, februari:1, maret:2, mei:4, juni:5,
    juli:6, agustus:7, oktober:9, desember:11,
};

const PRESENT_TOKENS = new Set([
    "present", "now", "current", "currently",
    "saat ini", "sekarang", "kini", "sampai sekarang",
]);

function parseExpDate(str) {
    if (!str) return null;
    const norm = str.trim().toLowerCase();
    if (PRESENT_TOKENS.has(norm)) return new Date();
    const tokens = norm.split(/\s+/);
    if (tokens.length === 1) {
        if (PRESENT_TOKENS.has(tokens[0])) return new Date();
        const y = parseInt(tokens[0]);
        return isNaN(y) ? null : new Date(y, 0, 1);
    }
    // Try both orderings: "Month YYYY" and "YYYY Month"
    let monthNum = undefined, yearNum = NaN;
    for (const tok of tokens.slice(0, 2)) {
        if (MONTH_MAP[tok] !== undefined) monthNum = MONTH_MAP[tok];
        else { const n = parseInt(tok); if (!isNaN(n) && n > 1900) yearNum = n; }
    }
    if (monthNum !== undefined && !isNaN(yearNum)) return new Date(yearNum, monthNum, 1);
    // Month only — infer year
    if (monthNum !== undefined) {
        const now = new Date();
        const year = monthNum <= now.getMonth() ? now.getFullYear() : now.getFullYear() - 1;
        return new Date(year, monthNum, 1);
    }
    return null;
}

// Safely read a field trying multiple possible key names
function pick(obj, ...keys) {
    for (const k of keys) if (obj[k] !== undefined && obj[k] !== null && obj[k] !== "") return obj[k];
    return "";
}

// Normalize an experience/org/project item to canonical field names
function normExp(exp) {
    return {
        title:        pick(exp, "title", "position", "job_title", "role", "designation"),
        company:      pick(exp, "company", "employer", "company_name", "organization", "org"),
        period_start: pick(exp, "period_start", "start_date", "start", "from", "date_start"),
        period_end:   pick(exp, "period_end",   "end_date",   "end",   "to",   "date_end", "until"),
        descriptions: exp.descriptions || exp.responsibilities || exp.duties || exp.achievements || exp.tasks || [],
    };
}

function normEdu(edu) {
    return {
        degree:       pick(edu, "degree", "qualification", "program", "major", "field", "course"),
        institution:  pick(edu, "institution", "university", "school", "college", "institute"),
        period_start: pick(edu, "period_start", "start_date", "start", "from", "year_start"),
        period_end:   pick(edu, "period_end",   "end_date",   "end",   "graduation_year", "year_end"),
        gpa:          pick(edu, "gpa", "grade", "cgpa", "score"),
    };
}

function normOrg(org) {
    return {
        title:        pick(org, "title", "position", "role", "designation"),
        organization: pick(org, "organization", "org", "club", "association", "event", "company"),
        period_start: pick(org, "period_start", "start_date", "start", "from"),
        period_end:   pick(org, "period_end",   "end_date",   "end",   "to"),
        descriptions: org.descriptions || org.responsibilities || org.contributions || org.activities || [],
    };
}

function normProj(proj) {
    return {
        name:         pick(proj, "name", "title", "project_name", "project"),
        period_start: pick(proj, "period_start", "start_date", "start", "from"),
        period_end:   pick(proj, "period_end",   "end_date",   "end",   "to"),
        descriptions: proj.descriptions || proj.details || proj.highlights || proj.achievements || [],
    };
}

function calcTotalExperience(items) {
    let totalMonths = 0;
    items.forEach(raw => {
        const exp = normExp(raw);
        const start = parseExpDate(exp.period_start);
        const end   = parseExpDate(exp.period_end) || new Date();
        if (!start) return;
        const diff = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
        if (diff > 0) totalMonths += diff;
    });
    if (totalMonths === 0) return null;
    const years  = Math.floor(totalMonths / 12);
    const months = totalMonths % 12;
    const parts  = [];
    if (years  > 0) parts.push(`${years} Year${years  !== 1 ? "s" : ""}`);
    if (months > 0) parts.push(`${months} Month${months !== 1 ? "s" : ""}`);
    return parts.join(", ");
}

function calcJobDuration(startStr, endStr) {
    const start = parseExpDate(startStr);
    const end   = parseExpDate(endStr) || new Date();
    if (!start) return null;
    const diff = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
    if (diff <= 0) return null;
    const years  = Math.floor(diff / 12);
    const months = diff % 12;
    const parts  = [];
    if (years  > 0) parts.push(`${years} yr${years  !== 1 ? "s" : ""}`);
    if (months > 0) parts.push(`${months} mo`);
    return parts.join(" ");
}

function renderCvExperience(listId, labelId, items, totalExperience) {
    const el = document.getElementById(listId);
    if (!el) { console.warn(`[renderCvExperience] element not found: #${listId}`); return; }
    el.innerHTML = "";

    // Total experience badge beside the section heading
    const totalBadge = document.getElementById("cvTotalExpBadge");
    if (totalBadge) {
        const total = totalExperience || calcTotalExperience(items || []);
        totalBadge.textContent = total ? `${total} Exp` : "";
        totalBadge.style.display = total ? "" : "none";
    }

    if (!items || items.length === 0) {
        el.innerHTML = "<p class='cv-side-empty'>No experience data</p>";
        return;
    }

    items.forEach(raw => {
        const exp      = normExp(raw);
        const duration = raw.duration || calcJobDuration(exp.period_start, exp.period_end);
        const company  = exp.company || "";
        const period   = [exp.period_start, exp.period_end].filter(Boolean).join(" \u2013 ");

        // Bullet descriptions
        const descHtml = exp.descriptions.length > 0
            ? `<ul class="cv-exp-bullets">${exp.descriptions.map(d => `<li>${escapeHtml(d)}</li>`).join("")}</ul>`
            : "";

        // Skill tags — extract keywords from description lines (capitalised tokens or known abbrevs)
        const skillTags = extractExpSkillTags(exp.descriptions);
        const tagsHtml  = skillTags.length > 0
            ? `<div class="cv-exp-tags">${skillTags.map(t => `<span class="cv-exp-tag">${escapeHtml(t)}</span>`).join("")}</div>`
            : "";

        const card = document.createElement("div");
        card.className = "cv-exp-card-new";
        card.innerHTML = `
            <div class="cv-exp-card-header">
                <div>
                    <div class="cv-exp-card-title">${escapeHtml(exp.title || "")}</div>
                    <div class="cv-exp-card-company">
                        ${company ? `<span class="cv-exp-meta-tag">${escapeHtml(company)}</span>` : ""}
                        ${period ? `<span class="cv-exp-meta-tag">${escapeHtml(period)}</span>` : ""}
                    </div>
                </div>
                ${duration ? `<span class="cv-exp-card-duration">${escapeHtml(duration)}</span>` : ""}
            </div>
            ${descHtml}
            ${tagsHtml}
        `;
        el.appendChild(card);
    });
}

// Extract short skill labels from experience bullet text
const SKILL_PATTERN = /\b(Python|SQL|LangChain|LangGraph|FastAPI|Docker|Kubernetes|GCP|AWS|Azure|CI\/CD|MLOps|NLP|LLM|RAG|YOLO|PyTorch|TensorFlow|OpenAI|Gemini|Vertex AI|SageMaker|BigQuery|OpenCV|Pub\/Sub|Lambda|React|Node\.js|Spark|Airflow|Kafka|Redis|PostgreSQL|MongoDB|Pinecone|Weaviate|Hugging Face|LoRA|PEFT|LSTM|XGBoost|A\/B|REST|API|ML|AI|CV)\b/g;

function extractExpSkillTags(descriptions) {
    const found = new Set();
    descriptions.forEach(d => {
        const matches = d.match(SKILL_PATTERN);
        if (matches) matches.forEach(m => found.add(m));
    });
    return [...found].slice(0, 6);
}

function setCvList(id, items) {
    const el = document.getElementById(id);
    if (!el) { console.warn(`[setCvList] element not found: #${id}`); return; }
    el.innerHTML = "";
    if (!items || items.length === 0) {
        el.innerHTML = "<li>No data available</li>";
        return;
    }
    items.forEach(item => {
        const li = document.createElement("li");
        li.textContent = item;
        el.appendChild(li);
    });
}

function renderCvEducation(listId, items) {
    const el = document.getElementById(listId);
    if (!el) { console.warn(`[renderCvEducation] element not found: #${listId}`); return; }
    el.innerHTML = "";
    if (!items || items.length === 0) {
        el.innerHTML = "<p class='cv-side-empty'>No education data</p>";
        return;
    }
    items.forEach(raw => {
        const edu    = normEdu(raw);
        const period = [edu.period_start, edu.period_end].filter(Boolean).join(" \u2013 ");
        const card = document.createElement("div");
        card.className = "cv-side-card";
        card.innerHTML = `
            <div class="cv-side-card-title">${escapeHtml(edu.degree || "")}</div>
            <div class="cv-side-card-sub">${escapeHtml(edu.institution || "")}</div>
            <div class="cv-side-card-meta">
                ${escapeHtml(period)}
                ${edu.gpa ? `<span class="cv-side-card-gpa">GPA ${escapeHtml(String(edu.gpa))}</span>` : ""}
            </div>
        `;
        el.appendChild(card);
    });
}

function renderCvCertifications(listId, items) {
    const el = document.getElementById(listId);
    if (!el) { console.warn(`[renderCvCertifications] element not found: #${listId}`); return; }
    el.innerHTML = "";
    if (!items || items.length === 0) {
        el.innerHTML = "<p class='cv-side-empty'>No certification data</p>";
        return;
    }
    items.forEach(raw => {
        const name   = raw.name   || raw.title       || "";
        const issuer = raw.issuer || raw.organization || "";
        const year   = raw.year   || raw.date         || "";
        const score  = raw.score  || "";
        const card = document.createElement("div");
        card.className = "cv-side-card";
        card.innerHTML = `
            <div class="cv-side-card-row">
                <div class="cv-side-card-title">${escapeHtml(name)}${score ? ` &middot; ${escapeHtml(score)}` : ""}</div>
                ${year ? `<span class="cv-side-card-badge">${escapeHtml(year)}</span>` : ""}
            </div>
            ${issuer ? `<div class="cv-side-card-sub">${escapeHtml(issuer)}</div>` : ""}
        `;
        el.appendChild(card);
    });
}

function renderCvOrganization(listId, items) {
    const el = document.getElementById(listId);
    if (!el) { console.warn(`[renderCvOrganization] element not found: #${listId}`); return; }
    el.innerHTML = "";
    if (!items || items.length === 0) {
        el.innerHTML = "<p class='cv-side-empty'>No organization data</p>";
        return;
    }
    items.forEach(raw => {
        const org   = normOrg(raw);
        const desc  = (org.descriptions || []).slice(0, 2).join(" ");
        const card  = document.createElement("div");
        card.className = "cv-side-card";
        card.innerHTML = `
            <div class="cv-side-card-title">${escapeHtml(org.title || "")}</div>
            <div class="cv-side-card-sub">${escapeHtml(org.organization || "")}</div>
            ${desc ? `<div class="cv-side-card-desc">"${escapeHtml(desc)}"</div>` : ""}
        `;
        el.appendChild(card);
    });
}

function renderCvProjects(listId, items) {
    const el = document.getElementById(listId);
    if (!el) { console.warn(`[renderCvProjects] element not found: #${listId}`); return; }
    el.innerHTML = "";
    if (!items || items.length === 0) {
        el.innerHTML = "<p class='cv-side-empty'>No project data</p>";
        return;
    }
    items.forEach(raw => {
        const proj  = normProj(raw);
        const period = [proj.period_start, proj.period_end].filter(Boolean).join(" \u2013 ");
        const desc  = (proj.descriptions || []).slice(0, 2).join(" ");
        const card  = document.createElement("div");
        card.className = "cv-side-card cv-side-card-proj";
        card.innerHTML = `
            <div class="cv-side-card-row">
                <div class="cv-side-card-title">${escapeHtml(proj.name || "")}</div>
                <svg class="cv-side-card-ext-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
            </div>
            ${period ? `<div class="cv-side-card-meta">${escapeHtml(period)}</div>` : ""}
            ${desc   ? `<div class="cv-side-card-desc">${escapeHtml(desc)}</div>`   : ""}
        `;
        el.appendChild(card);
    });
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (!el) { console.warn(`[setText] element not found: #${id}`); return; }
    el.textContent = text || "—";
}

function setList(id, items) {
    const el = document.getElementById(id);
    if (!el) { console.warn(`[setList] element not found: #${id}`); return; }
    el.innerHTML = "";
    if (!items || items.length === 0) {
        el.innerHTML = "<li>No data available</li>";
        return;
    }
    items.forEach((item) => {
        const li = document.createElement("li");
        li.textContent = item;
        el.appendChild(li);
    });
}

const PORTAL_COLORS = {
    "LinkedIn":       { bg: "rgba(10,102,194,0.15)",  fg: "#4a9fd4", border: "rgba(10,102,194,0.4)"  },
    "Indeed":         { bg: "rgba(104,77,199,0.15)",   fg: "#a78bfa", border: "rgba(104,77,199,0.4)"  },
    "Glassdoor":      { bg: "rgba(13,192,111,0.15)",   fg: "#34d399", border: "rgba(13,192,111,0.4)"  },
    "JobStreet":      { bg: "rgba(251,146,60,0.15)",   fg: "#fb923c", border: "rgba(251,146,60,0.4)"  },
    "SmartRecruiters": { bg: "rgba(232,76,61,0.15)",   fg: "#f87171", border: "rgba(232,76,61,0.4)"  },
    "_default":       { bg: "rgba(99,179,237,0.15)",   fg: "#63b3ed", border: "rgba(99,179,237,0.35)" },
};

function renderSourceLinks(id, sources) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = "";
    if (!sources || sources.length === 0) {
        el.innerHTML = '<p class="source-grid-empty">No reference links available.</p>';
        return;
    }
    sources.forEach((s, i) => {
        const card = document.createElement("a");
        card.className = "source-card";
        if (s.uri) {
            card.href = s.uri;
            card.target = "_blank";
            card.rel = "noopener noreferrer";
        }
        const c = PORTAL_COLORS[s.portal] || PORTAL_COLORS["_default"];
        card.style.borderColor = c.border;

        const portalBadge = document.createElement("span");
        portalBadge.className = "source-card-portal";
        portalBadge.textContent = s.portal || "Web";
        portalBadge.style.background = c.bg;
        portalBadge.style.color = c.fg;
        portalBadge.style.borderColor = c.border;

        const title = document.createElement("p");
        title.className = "source-card-title";
        title.textContent = s.title || `Source ${i + 1}`;

        const uri = document.createElement("p");
        uri.className = "source-card-uri";
        uri.textContent = s.uri || "";

        card.appendChild(portalBadge);
        card.appendChild(title);
        card.appendChild(uri);
        el.appendChild(card);
    });
}

function renderSourceCards(id, sources) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = "";
    const cards = (sources || []).filter(s => s.title);
    if (cards.length === 0) {
        el.innerHTML = '<p class="source-grid-empty">No data available.</p>';
        return;
    }

    const PAGE_SIZE = 4;
    let currentPage = 0;
    const totalPages = Math.ceil(cards.length / PAGE_SIZE);

    const grid = document.createElement("div");
    grid.className = "source-req-grid";

    const pagination = document.createElement("div");
    pagination.className = "source-req-pagination";

           const FIELD_DEFS = [
               { label: "Role Overview",        key: "role_overview",        type: "text" },
               { label: "Key Responsibilities", key: "key_responsibilities", type: "list" },
               { label: "Demanded Skills",      key: "demanded_skills",      type: "list" },
               { label: "Soft Skills",          key: "soft_skills",          type: "list" },
               { label: "Tools & Software",     key: "tools_software",       type: "list" },
               { label: "Certifications",       key: "certifications",       type: "list" },
           ];

    function buildCard(s, idx) {
        const card = document.createElement("div");
        card.className = "source-req-card";
        const c = PORTAL_COLORS[s.portal] || PORTAL_COLORS["_default"];
        card.style.borderColor = c.border;

        // Header: title + domain
        const header = document.createElement("div");
        header.className = "source-req-header";

        const titleEl = document.createElement("a");
        titleEl.className = "source-req-title";
        titleEl.textContent = s.title || `Source ${idx + 1}`;
        if (s.uri) {
            titleEl.href = s.uri;
            titleEl.target = "_blank";
            titleEl.rel = "noopener noreferrer";
        }

        const subtitle = document.createElement("span");
        subtitle.className = "source-req-subtitle";
        try { subtitle.textContent = new URL(s.uri).hostname.replace(/^www\./, ""); }
        catch { subtitle.textContent = s.uri || "Web"; }

        header.appendChild(titleEl);
        header.appendChild(subtitle);
        card.appendChild(header);

        // Structured fields
        FIELD_DEFS.forEach(({ label, key, type }) => {
            const value = s[key];
            const isEmpty = !value ||
                (Array.isArray(value) && value.filter(Boolean).length === 0) ||
                value === "";
            if (isEmpty) return;

            const field = document.createElement("div");
            field.className = "source-req-field";

            const labelEl = document.createElement("span");
            labelEl.className = "source-req-field-label";
            labelEl.textContent = label;
            field.appendChild(labelEl);

            if (type === "text") {
                const textEl = document.createElement("p");
                textEl.className = "source-req-field-text";
                textEl.textContent = value;
                field.appendChild(textEl);
            } else {
                const items = Array.isArray(value) ? value.filter(Boolean) : [value];
                if (items.length === 0) return;
                const ol = document.createElement("ol");
                ol.className = "source-req-field-list";
                items.forEach(item => {
                    const li = document.createElement("li");
                    li.textContent = item;
                    ol.appendChild(li);
                });
                field.appendChild(ol);
            }

            card.appendChild(field);
        });

        return card;
    }

    function renderPage(page) {
        grid.innerHTML = "";
        const start = page * PAGE_SIZE;
        cards.slice(start, start + PAGE_SIZE).forEach((s, i) => {
            grid.appendChild(buildCard(s, start + i));
        });
    }

    function renderPagination() {
        pagination.innerHTML = "";
        if (totalPages <= 1) return;

        const prev = document.createElement("button");
        prev.className = "source-req-page-btn nav";
        prev.textContent = "\u2039";
        prev.disabled = currentPage === 0;
        prev.style.opacity = currentPage === 0 ? "0.35" : "1";
        prev.addEventListener("click", () => { if (currentPage > 0) { currentPage--; renderPage(currentPage); renderPagination(); } });
        pagination.appendChild(prev);

        for (let p = 0; p < totalPages; p++) {
            const btn = document.createElement("button");
            btn.className = "source-req-page-btn" + (p === currentPage ? " active" : "");
            btn.textContent = p + 1;
            btn.addEventListener("click", () => {
                currentPage = p;
                renderPage(currentPage);
                renderPagination();
            });
            pagination.appendChild(btn);
        }

        const next = document.createElement("button");
        next.className = "source-req-page-btn nav";
        next.textContent = "\u203A";
        next.disabled = currentPage === totalPages - 1;
        next.style.opacity = currentPage === totalPages - 1 ? "0.35" : "1";
        next.addEventListener("click", () => { if (currentPage < totalPages - 1) { currentPage++; renderPage(currentPage); renderPagination(); } });
        pagination.appendChild(next);
    }

    renderPage(currentPage);
    renderPagination();

    el.appendChild(grid);
    el.appendChild(pagination);
}

function renderJobRequirements(id, items, sources) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = "";
    if (!items || items.length === 0) {
        el.innerHTML = "<li>No data available</li>";
        return;
    }
    sources = sources || [];
    items.forEach((item) => {
        const li = document.createElement("li");
        const text = typeof item === "string" ? item : (item.text || "");
        const portals = (typeof item === "object" && Array.isArray(item.portals)) ? item.portals : [];

        const span = document.createElement("span");
        span.textContent = text;
        li.appendChild(span);

        if (portals.length > 0) {
            const badges = document.createElement("span");
            badges.className = "req-sources";
            portals.forEach(portal => {
                const src = sources.find(s => s.portal === portal);
                const a = document.createElement("a");
                a.className = "req-source-badge";
                a.textContent = portal;
                a.title = src ? (src.title || portal) : portal;
                if (src && src.uri) {
                    a.href = src.uri;
                    a.target = "_blank";
                    a.rel = "noopener noreferrer";
                } else {
                    a.role = "note";
                }
                const c = PORTAL_COLORS[portal] || PORTAL_COLORS["_default"];
                a.style.background = c.bg;
                a.style.color = c.fg;
                a.style.borderColor = c.border;
                badges.appendChild(a);
            });
            li.appendChild(badges);
        }

        el.appendChild(li);
    });
}

function setTags(id, items) {
    const el = document.getElementById(id);
    if (!el) { console.warn(`[setTags] element not found: #${id}`); return; }
    el.innerHTML = "";
    if (!items || items.length === 0) {
        el.innerHTML = '<span class="tag">—</span>';
        return;
    }
    items.forEach((item) => {
        const span = document.createElement("span");
        span.className = "tag";
        span.textContent = normalizeTagLabel(item);
        el.appendChild(span);
    });
    applyTagScrollLimit(el, items.length, 7);
}

function applyTagScrollLimit(el, itemCount, maxVisibleItems = 7) {
    if (!el) return;
    const shouldScroll = (itemCount || 0) > maxVisibleItems;
    el.classList.toggle("tag-scrollable-7", shouldScroll);
}

// ---------- Implicit Skills Popup ----------

let _popup = null;

function createPopup() {
    if (_popup) return;
    _popup = document.createElement("div");
    _popup.className = "skill-popup";
    _popup.innerHTML = `
        <div class="skill-popup-name" id="popupName"></div>
        <div class="skill-popup-label">Evidence</div>
        <div class="skill-popup-evidence" id="popupEvidence"></div>
    `;
    document.body.appendChild(_popup);
}

function openPopup(tag, name, evidence) {
    createPopup();
    const nameEl = document.getElementById("popupName");
    const evidenceEl = document.getElementById("popupEvidence");
    if (nameEl) nameEl.textContent = name;
    if (evidenceEl) evidenceEl.textContent = evidence;

    const rect = tag.getBoundingClientRect();
    const pw = 320;
    let left = rect.left;
    let top  = rect.bottom + 8;

    if (left + pw > window.innerWidth - 12) left = window.innerWidth - pw - 12;
    if (top + 120 > window.innerHeight) top = rect.top - 130;

    _popup.style.left = left + "px";
    _popup.style.top  = top  + "px";
    _popup.style.display = "block";
}

function closePopup() {
    if (_popup) _popup.style.display = "none";
}

function renderImplicitSkills(id, items) {
    const el = document.getElementById(id);
    if (!el) { console.warn(`[renderImplicitSkills] element not found: #${id}`); return; }
    el.innerHTML = "";
    if (!items || items.length === 0) {
        el.innerHTML = "<p>No implicit skills detected</p>";
        return;
    }
    items.forEach((item) => {
        const skillName = normalizeTagLabel(item.skill || item.name || "");
        const evidence  = item.evidence || item.reason || item.proof || "";
        const span = document.createElement("span");
        span.className = "tag tag-implicit";
        span.textContent = skillName;
        span.addEventListener("mouseenter", () => openPopup(span, skillName, evidence));
        span.addEventListener("mouseleave", closePopup);
        el.appendChild(span);
    });
    applyTagScrollLimit(el, items.length, 7);
}

function normalizeTagLabel(value) {
    if (value === null || value === undefined) return "";
    return String(value).replace(/\s+/g, " ").trim();
}

// ---------- Download Report ----------

document.getElementById("downloadBtn").addEventListener("click", async () => {
    if (!analysisResult) return;
    const role = document.getElementById("targetRole")?.value?.trim() || "";
    const srcName = (fileInput.files && fileInput.files[0] && fileInput.files[0].name)
        ? fileInput.files[0].name
        : "skill_gap_report";
    const baseName = srcName.replace(/\.[^.]+$/, "");
    const filename = `${baseName}_skill_gap_report.pdf`;

    try {
        const resp = await fetch("/api/report-pdf", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                analysis: analysisResult,
                role,
                filename,
            }),
        });
        if (!resp.ok) {
            const errBody = await resp.text();
            throw new Error(`PDF download failed: ${resp.status} ${errBody}`);
        }

        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    } catch (err) {
        showRenderError(err);
    }
});
