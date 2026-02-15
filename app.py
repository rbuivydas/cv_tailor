import streamlit as st
from docxtpl import DocxTemplate
import PyPDF2
from google import genai
import io
import pypandoc
import os

# --- ACCESSING SECRETS ---
# In Streamlit Cloud, go to Settings -> Secrets and add: GEMINI_API_KEY = "your_key"
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

# --- DOCUMENT GENERATION ENGINE ---
def render_cv_template(template_file, data_map):
    # Save the uploaded template to a temporary file for docxtpl to process
    temp_path = "temp_template.docx"
    with open(temp_path, "wb") as f:
        f.write(template_file.getbuffer())
    
    doc = DocxTemplate(temp_path)
    
    # Render the data into the Jinja2 placeholders
    doc.render(data_map)
    
    # Save the result to a byte stream
    output_stream = io.BytesIO()
    doc.save(output_stream)
    output_stream.seek(0)
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return output_stream

# --- STREAMLIT UI ---
st.set_page_config(page_title="Pro Template Tailor", layout="wide")

with st.sidebar:
    st.title("System Config")
    api_key = st.text_input("Gemini API Key", type="password")
    # THE TEMPLATE: User must upload a .docx version of the ATS template
    docx_template = st.file_uploader("📂 Upload .docx Template", type="docx")
    st.markdown("---")
    st.info("Ensure your .docx has tags like {{ summary }}, {{ experience }}, etc.")

st.title("💼 AI Template Architect")
st.write("Tailoring your CV using your custom Word template for a high-end corporate finish.")

# Candidate Details
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

# File Uploads
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
        
        # Extract text from PDF
        pdf_reader = PyPDF2.PdfReader(master_cv)
        cv_raw_text = " ".join([p.extract_text() for p in pdf_reader.pages])

        with st.spinner("AI is populating your template fields..."):
            # We prompt the AI to return chunks that match your template placeholders
            prompt = f"""
            Act as an Executive Resume Writer. Rewrite the CV for this Job Description.
            
            STRICT OUTPUT FORMAT:
            Split your response into 4 sections using the marker '===':
            1. SUMMARY: A professional summary.
            2. EXPERIENCE: Work history with bullet points.
            3. EDUCATION: Degree and School details.
            4. SKILLS: A comma-separated list of technical skills.

            RULES:
            - Focus on Windows 10, O365, and Active Directory.
            - Highlight the 1st Class Honours in Cybersecurity.
            - DO NOT use markdown symbols (*, #).

            CV: {cv_raw_text}
            JOB: {job_desc}
            """
            
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            output = response.text
            
            # Parsing the chunks
            sections = output.split("===")
            # Failsafe parsing
            summary_val = sections[1].strip() if len(sections) > 1 else ""
            experience_val = sections[2].strip() if len(sections) > 2 else ""
            education_val = sections[3].strip() if len(sections) > 3 else ""
            skills_val = sections[4].strip() if len(sections) > 4 else ""

            # Prepare the data map for the Word Template
            cv_data = {
                'name': name.upper(),
                'phone': phone,
                'email': email,
                'linkedin': linkedin,
                'github': github,
                'summary': summary_val,
                'experience': experience_val,
                'education': education_val,
                'skills': skills_val
            }

            # Generate the final Word Document
            try:
                final_docx = render_cv_template(docx_template, cv_data)
                
                st.success("Resume populated and styled!")
                st.download_button(
                    label="📥 Download Tailored Resume (.docx)",
                    data=final_docx,
                    file_name=f"{name}_Tailored_CV.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Template rendering failed: {e}")
