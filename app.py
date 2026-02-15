import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import os
import re

# --- TEMPLATE FILLING ENGINE ---
def render_from_template(template_file, data_map):
    """Fills the .docx template with AI-generated data."""
    # Temporarily save the uploaded template to disk
    temp_path = "input_template.docx"
    with open(temp_path, "wb") as f:
        f.write(template_file.getbuffer())
    
    doc = DocxTemplate(temp_path)
    doc.render(data_map)
    
    output_stream = io.BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    
    # Cleanup temporary file
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return output_stream

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Pro CV Architect", layout="wide")

with st.sidebar:
    st.header("Admin Settings")
    # Securely handle Gemini API Key via Streamlit Secrets or Manual Input
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("Gemini API Key loaded from Secrets.")
    else:
        api_key = st.text_input("Enter Gemini API Key", type="password")
        st.info("Get your key at aistudio.google.com")

    docx_template = st.file_uploader("📂 Upload CV Template (.docx)", type="docx")
    cl_template = st.file_uploader("📂 Upload Cover Letter Template (.docx)", type="docx")

st.title("💼 Professional CV & Cover Letter Tailor")

# Application Identity
with st.container():
    st.subheader("Applicant & Company Details")
    c1, c2, c3 = st.columns(3)
    with c1:
        full_name = st.text_input("Applicant Name", "Rimantas Buivydas")
    with c2:
        target_company = st.text_input("Target Company", "e.g., London Law Firm")
    with c3:
        target_role = st.text_input("Target Role", "e.g., IT Service Desk Analyst")

st.markdown("---")

col_a, col_b = st.columns(2)
with col_a:
    uploaded_cv = st.file_uploader("1. Upload Master CV (PDF)", type="pdf")
with col_b:
    job_desc = st.text_area("2. Paste Job Description", height=200)

if st.button("🚀 Generate Professional Documents"):
    if not all([api_key, docx_template, uploaded_cv, job_desc]):
        st.error("Missing requirements: API Key, Template, Master CV, or Job Description.")
    else:
        client = genai.Client(api_key=api_key)
        
        # Extract Master CV Text
        pdf_reader = PyPDF2.PdfReader(uploaded_cv)
        master_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("Rewriting content into natural sentences..."):
            # REFINED PROMPT: Instructing AI to avoid titles and use natural flow
            prompt = f"""
            Act as a Senior Executive Resume Writer. Rewrite the CV and Cover Letter for {full_name} for the {target_role} position at {target_company}.
            
            STRICT INSTRUCTIONS FOR NATURAL TEXT:
            - Split sections using '==='.
            - Part 1 (Summary): Write 3-4 professional, flowing sentences that bridge Cybersecurity with IT Support. DO NOT include a title like 'Summary:'.
            - Part 2 (Experience): Use clear, result-oriented bullet points.
            - Part 3 (Skills): Provide a clean, comma-separated list of technical skills. DO NOT include a title like 'Skills:'.
            - Part 4 (Cover Letter): A full, natural cover letter tailored to the job description.
            - DO NOT use markdown like **bold**, ## headers, or asterisks. Use plain text only.

            CV: {master_text}
            JOB: {job_desc}
            """
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            sections = response.text.split("===")
            
            # Cleaning function to ensure no stray AI formatting breaks the Word doc
            def clean(text):
                # Removes bolding, headers, and trailing whitespace
                return re.sub(r'[\*\^#]', '', text).strip()

            # Dynamic Filename Base
            file_base = f"{full_name.replace(' ', '_')}_{target_company.replace(' ', '_')}"

            # --- DATA MAPPING ---
            cv_data = {
                'name': full_name.upper(),
                'summary': clean(sections[1]) if len(sections) > 1 else "",
                'experience': clean(sections[2]) if len(sections) > 2 else "",
                'skills': clean(sections[3]) if len(sections) > 3 else ""
            }
            
            cl_content = clean(sections[4]) if len(sections) > 4 else "Cover Letter generation failed."
            cl_data = {
                'name': full_name,
                'company': target_company,
                'role': target_role,
                'letter_body': cl_content
            }

            try:
                # Render CV
                cv_docx = render_from_template(docx_template, cv_data)
                
                st.success(f"Tailored documents for {target_company} created successfully!")
                
                res_col, cl_col = st.columns(2)
                with res_col:
                    st.download_button(
                        label="📄 Download Tailored CV (.docx)",
                        data=cv_docx,
                        file_name=f"{file_base}_CV.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                
                # Render Cover Letter if template exists
                if cl_template:
                    cl_docx = render_from_template(cl_template, cl_data)
                    with cl_col:
                        st.download_button(
                            label="✉️ Download Cover Letter (.docx)",
                            data=cl_docx,
                            file_name=f"{file_base}_CoverLetter.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                else:
                    st.info("Upload a Cover Letter template in the sidebar to generate the document.")

            except Exception as e:
                st.error(f"Processing Error: {e}")
