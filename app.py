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

# --- ROBUST CLEANING LOGIC ---
def clean_ai_text(text):
    # 1. Remove common AI headers like "1. SUMMARY:", "SKILLS:", "[SUMMARY]", "SECTION 1:", etc.
    # This regex looks for numbering and titles at the start of the text block
    text = re.sub(r'(?i)^(\d+\.\s*)?(\[)?(SUMMARY|SKILLS|SECTION|ITEM|OVERVIEW|PROFESSIONAL SUMMARY)(\])?[:\- \t]*', '', text.strip())
    
    # 2. Strip out all markdown symbols (*, #, ^, **)
    text = re.sub(r'[\*\^#]', '', text)
    
    # 3. Clean up leading/trailing whitespace and ensure single spacing
    text = text.strip().replace("  ", " ")
    return text

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
    st.caption("Template tags: {{ name }}, {{ email }}, {{ linkedin }}, {{ github }}, {{ summary }}, {{ skills }}, {{ phone }}")

st.title("💼 AI CV Architect")
st.write("Tailoring your CV with zero AI artifacts for a human-written feel.")

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
        st.error("Missing required inputs.")
    else:
        client = genai.Client(api_key=api_key)
        pdf_reader = PyPDF2.PdfReader(master_cv)
        cv_raw_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("AI is generating clean prose..."):
            prompt = f"""
            Act as a Senior Resume Writer. Tailor the CV for an IT Service Desk Analyst role.
            
            STRICT OUTPUT FORMAT (Separate sections with EXACTLY '==='):
            1. Provide ONLY a single paragraph of professional prose for the summary. 
               Do NOT include any titles, labels, or numbering.
            2. Provide ONLY a single continuous comma-separated list of technical skills. 
               Do NOT include labels or bullet points.

            CV: {cv_raw_text}
            JOB: {job_desc}
            """
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            sections = response.text.split("===")
            
            # Apply the cleaning filter to the AI output
            summary_val = clean_ai_text(sections[0]) if len(sections) > 0 else ""
            skills_val = clean_ai_text(sections[1]) if len(sections) > 1 else ""

            # --- PREVIEW SECTION ---
            st.markdown("### 🔍 Content Preview")
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                st.info("**Cleaned Summary:**")
                st.write(summary_val)
            with p_col2:
                st.info("**Cleaned Skills:**")
                st.write(skills_val)

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
                st.success("Template populated successfully!")
                
                # Dynamic professional filename
                file_label = f"{name.replace(' ', '_')}_Tailored_CV.docx"
                
                st.download_button(
                    label="📥 Download Tailored Resume (.docx)",
                    data=final_docx,
                    file_name=file_label,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Template rendering failed: {e}")
