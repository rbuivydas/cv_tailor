import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import re
import os

# --- DOCUMENT GENERATION ENGINE ---
def render_cv_template(template_file, data_map):
    temp_path = "temp_template.docx"
    with open(temp_path, "wb") as f:
        f.write(template_file.getbuffer())
    
    doc = DocxTemplate(temp_path)
    doc.render(data_map)
    
    output_stream = io.BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return output_stream

# --- STREAMLIT UI ---
st.set_page_config(page_title="Pro Template Tailor", layout="wide")

with st.sidebar:
    st.header("API Key")
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("API Key active.")
    else:
        api_key = st.text_input("Gemini API Key", type="password")
    
    docx_template = st.file_uploader("2. Upload .docx Template", type="docx")
    st.caption("Template must use: {{ name }}, {{ email }}, {{ linkedin }}, {{ github }}, {{ summary }}, {{ skills }}, {{ phone }}")

st.title("💼 AI Template Architect")
st.write("Tailoring your CV using your custom Word template for a high-end corporate finish.")

with st.expander("Candidate Information", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("Full Name", "Rimantas Buivydas")
        email = st.text_input("Email", "rimvntas59@gmail.com")
    with c2:
        phone = st.text_input("Phone", "+44 7783 949991")
        linkedin = st.text_input("LinkedIn URL", "linkedin.com/in/rimantas-buivydas/")
    with c3:
        github = st.text_input("GitHub URL", "github.com/rbuivydas")

st.markdown("---")

col_a, col_b = st.columns(2)
with col_a:
    master_cv = st.file_uploader("1. Upload Master CV (PDF)", type="pdf")
with col_b:
    job_desc = st.text_area("2. Paste Job Description", height=200)

if st.button("🚀 Generate Tailored Template"):
    if not all([api_key, docx_template, master_cv, job_desc]):
        st.error("Missing required inputs: API Key, Template, Master CV, or Job Description.")
    else:
        client = genai.Client(api_key=api_key)
        pdf_reader = PyPDF2.PdfReader(master_cv)
        cv_raw_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("AI is populating your template fields..."):
            # REFINED PROMPT for image 2 style layout
            prompt = f"""
            Act as a Senior Resume Writer. Tailor the content for an IT Service Desk Analyst role.
            
            OUTPUT SECTIONS (Separate using EXACTLY '==='):
            1. [SUMMARY SECTION]: A single paragraph of 3-5 high-impact, professional sentences. 
            Do NOT include a title. No bullet points. Just straight prose.
            
            2. [SKILLS SECTION]: A single, dense comma-separated list of technical skills. 
            Do NOT use bullet points, categories, or headers. Just one continuous line of skills.

            RULES:
            - DO NOT include titles like 'Summary' or 'Skills' in the sections.
            - DO NOT use any markdown (*, #, **, ^).
            - Use professional, natural language sentences.
            
            CV: {cv_raw_text}
            JOB: {job_desc}
            """
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            output = response.text
            
            sections = output.split("===")
            
            # Helper function to strip unwanted AI headers/labels
            def clean_text(text):
                # Removes bolding, labels like "SUMMARY:", "SKILLS:", and leading symbols
                t = re.sub(r'(?i)^(SUMMARY|SKILLS|SECTION \d+|ITEM \d+):?\s*', '', text.strip())
                t = re.sub(r'[\*\^#]', '', t)
                return t.strip()

            summary_val = clean_text(sections[0]) if len(sections) > 0 else ""
            # If AI added extra split markers, we look for the next available non-empty block
            skills_val = clean_text(sections[1]) if len(sections) > 1 else ""
            if not skills_val and len(sections) > 2:
                 skills_val = clean_text(sections[2])

            cv_data = {
                'name': name.upper(),
                'phone': phone,
                'email': email,
                'linkedin': linkedin,
                'github': github,
                'summary': summary_val,
                'skills': skills_val
            }

            try:
                final_docx = render_cv_template(docx_template, cv_data)
                st.success("Resume populated and styled!")
                st.download_button(
                    label="📥 Download Tailored Resume (.docx)",
                    data=final_docx,
                    file_name=f"{name.replace(' ', '_')}_Tailored_CV.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Template rendering failed: {e}")
