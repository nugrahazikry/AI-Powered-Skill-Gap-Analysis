import streamlit as st
import pandas as pd


def main():
    st.title("CV & Skills Parsing Demo")

    # Frontend inputs
    uploaded_file = st.file_uploader("Upload a TXT file", type="txt")
    target_role = st.text_input("Enter target role")

    if uploaded_file and target_role:
        
        # Save uploaded file to temporary path
        temp_path = "temp.txt"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())

        # Initialize pipeline state
        state = PipelineState(input_path=temp_path, role=target_role)

        # Process file
        result = read_file_node(state)
        input_text = result.get("input_text", "")

        # ---- Mock backend logic ----
        # In your real pipeline, you'd generate these dynamically
        agent_1_cv_parsing = {
            "title": "ZIKRY ADJIE NUGRAHA",
            "summary": "Data Scientist specializing in AI, LLM, Machine Learning, and Data Analytics with over 3 years of experience. He has worked on numerous projects for national and international companies, utilizing Python, SQL, and cloud platforms like GCP, AWS, and Azure. Zikry has a proven track record of leading and delivering impactful data science solutions.",
            "experience": [
                "AI Data Scientist at NucleusX BV (February 2024 – Present): Specialized in AI LLM, NLP, and Data Analytics projects, implementing 10+ data science projects focusing on AI, ML, NLP, and chatbot development, integrating with Microsoft Azure and AWS cloud services.",
            ],
        }

        agent_2_specialize_skills = {
            "explicit_skills": [
                "Data Scientist",
                "AI",
                "LLM",
            ],
            "implicit_skills": [
                {
                    "skill": "IT consulting",
                    "evidence": "solving complex business problems for over 10 top national and international companies across e-commerce, digital marketing, finance, and banking industries."
                }
            ]
        }

        # ---- Display results in Markdown ----
        st.subheader("Agent 1 - CV Parsing")
        df_cv = pd.DataFrame({
            "Field": list(agent_1_cv_parsing.keys()),
            "Value": [str(v) for v in agent_1_cv_parsing.values()]
        })
        st.markdown(df_cv.to_markdown(index=False))

        st.subheader("Agent 2 - Specialized Skills")
        explicit_df = pd.DataFrame(agent_2_specialize_skills["explicit_skills"], columns=["Explicit Skills"])
        implicit_df = pd.DataFrame(agent_2_specialize_skills["implicit_skills"])
        st.markdown(explicit_df.to_markdown(index=False))
        st.markdown(implicit_df.to_markdown(index=False))

if __name__ == "__main__":
    main()