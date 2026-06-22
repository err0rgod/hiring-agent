import os
import shutil
import tempfile
import logging
import markdown
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from score import main as score_resume_main
from config import DEVELOPMENT_MODE, RESEND_API_KEY, RECRUITER_EMAIL
import base64
import resend

# Configure Resend
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import score
score.DEVELOPMENT_MODE = False

def send_candidate_email_via_resend(
    pdf_path: str,
    original_filename: str,
    candidate_name: str,
    score: Optional[float] = None,
    evaluation_data = None
) -> bool:
    if not RESEND_API_KEY:
        logger.warning("⚠️ RESEND_API_KEY is not set. Skipping recruiter email notification.")
        return False
    
    try:
        # Read and base64-encode the file
        with open(pdf_path, "rb") as f:
            encoded_pdf = base64.b64encode(f.read()).decode("utf-8")
        
        # Prepare HTML body with basic evaluation summary
        html_content = f"""
        <h2>New Candidate Application</h2>
        <p><strong>Candidate Name:</strong> {candidate_name}</p>
        <p><strong>Original File:</strong> {original_filename}</p>
        """
        
        if score is not None:
            html_content += f"<p><strong>Evaluation Score:</strong> {score:.1f}/100</p>"
            
        if evaluation_data:
            html_content += "<h3>Score Breakdown</h3><ul>"
            if hasattr(evaluation_data, "scores") and evaluation_data.scores:
                for cat, val in evaluation_data.scores.model_dump().items():
                    html_content += f"<li><strong>{cat.replace('_', ' ').title()}:</strong> {val['score']}/{val['max']}</li>"
            html_content += "</ul>"
            
            if hasattr(evaluation_data, "key_strengths") and evaluation_data.key_strengths:
                html_content += "<h3>Key Strengths</h3><ul>"
                for strength in evaluation_data.key_strengths:
                    html_content += f"<li>{strength}</li>"
                html_content += "</ul>"
        
        html_content += """
        <p>The candidate's original resume is attached to this email.</p>
        <hr/>
        <p>Sent via Hiring Agent Platform</p>
        """
        
        params = {
            "from": "Hiring Agent <onboarding@resend.dev>",
            "to": [RECRUITER_EMAIL],
            "subject": f"New Candidate Resume & Evaluation: {candidate_name}",
            "html": html_content,
            "attachments": [
                {
                    "filename": original_filename,
                    "content": encoded_pdf
                }
            ]
        }
        
        resend.Emails.send(params)
        logger.info(f"📧 Candidate application email sent successfully to {RECRUITER_EMAIL}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send email via Resend: {e}")
        return False

app = FastAPI(title="Hiring Agent Web")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse(request=request, name="privacy.html")

@app.post("/evaluate", response_class=HTMLResponse)
async def evaluate(
    request: Request,
    resume: UploadFile = File(...),
    groq_api_key: str = Form(...),
    job_description: Optional[str] = Form(None)
):
    # Validate file extension
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Use a temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, resume.filename)
        
        # Save the uploaded file securely
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        
        try:
            # Run the scoring orchestration with the dynamic API key
            score, ats_suggestions, resume_data = score_resume_main(
                temp_file_path, 
                api_key=groq_api_key,
                job_description=job_description
            )
            
            if not score:
                error_msg = ats_suggestions if ats_suggestions else "Failed to analyze resume"
                raise HTTPException(status_code=500, detail=error_msg)

            # Convert ATS suggestions from Markdown to HTML
            ats_html = markdown.markdown(ats_suggestions)

            # Get candidate name from resume_data
            candidate_name = resume.filename.replace(".pdf", "")
            if resume_data and resume_data.basics and resume_data.basics.name:
                candidate_name = resume_data.basics.name

            # Calculate final score out of 100 for email notification
            final_score_val = 0.0
            if score and score.scores:
                cat_total = (
                    score.scores.open_source.score +
                    score.scores.self_projects.score +
                    score.scores.production.score +
                    score.scores.technical_skills.score
                )
                deduction = score.deductions.total if score.deductions else 0
                final_score_val = max(min(cat_total - deduction, 100.0), 0.0)

            # Securely forward candidate resume and evaluation to the recruiter
            send_candidate_email_via_resend(
                pdf_path=temp_file_path,
                original_filename=resume.filename,
                candidate_name=candidate_name,
                score=final_score_val,
                evaluation_data=score
            )

            return templates.TemplateResponse(
                request=request,
                name="result.html",
                context={
                    "score": score,
                    "ats_suggestions": ats_html,
                    "candidate_name": candidate_name
                }
            )
            
        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
        finally:
            resume.file.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
