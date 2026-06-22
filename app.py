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
from config import DEVELOPMENT_MODE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import score
score.DEVELOPMENT_MODE = False

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
