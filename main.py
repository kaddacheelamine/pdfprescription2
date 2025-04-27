from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import weasyprint
from datetime import datetime
import tempfile
import supabase


# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
supabase_client = supabase.create_client(supabase_url, supabase_key)

app = FastAPI()

# CORS configuration
origins = [
    "*",  # Allow all origins (modify for production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model for HTML content
class PrescriptionRequest(BaseModel):
    html_content: str
    patient_name: str  # Optional fields to use in filename

@app.post("/generate-prescription")
async def generate_prescription(data: PrescriptionRequest):
    try:
        # Generate a unique filename based on date, time, and patient name if provided
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        patient_slug = data.patient_name.lower().replace(" ", "_") if data.patient_name else "patient"
        filename = f"prescription_{patient_slug}_{timestamp}.pdf"
        
        # Create a temporary file to store the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            # Generate PDF from the HTML content received from frontend
            weasyprint.HTML(string=data.html_content).write_pdf(temp_file.name)
            
            # Upload the PDF to Supabase storage
            with open(temp_file.name, 'rb') as pdf_file:
                # Upload to the 'pdfs' bucket
                upload_response = supabase_client.storage.from_('pdfs').upload(
                    file=pdf_file,
                    path=filename,
                    file_options={"content-type": "application/pdf"}
                )
            
            # Remove the temporary file
            os.unlink(temp_file.name)
        
        # Get the public URL of the uploaded file
        file_url = supabase_client.storage.from_('pdfs').get_public_url(filename)
        
        return {
            "status": "success",
            "message": "Prescription PDF generated and uploaded successfully",
            "filename": filename,
            "url": file_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating prescription PDF: {str(e)}")

@app.post("/generate-prescription-with-download")
async def generate_prescription_with_download(data: PrescriptionRequest):
    """Alternative endpoint that returns both the URL and binary data for direct download"""
    try:
        # Generate a unique filename based on date and time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        patient_slug = data.patient_name.lower().replace(" ", "_") if data.patient_name else "patient"
        filename = f"prescription_{patient_slug}_{timestamp}.pdf"
        
        # Create a temporary file to store the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            # Generate PDF from the HTML content received from frontend
            weasyprint.HTML(string=data.html_content).write_pdf(temp_file.name)
            
            # Upload the PDF to Supabase storage
            with open(temp_file.name, 'rb') as pdf_file:
                # Read binary data for response
                pdf_binary = pdf_file.read()
                
                # Reset file pointer to beginning of file
                pdf_file.seek(0)
                
                # Upload to the 'pdfs' bucket
                upload_response = supabase_client.storage.from_('pdfs').upload(
                    file=pdf_file,
                    path=filename,
                    file_options={"content-type": "application/pdf"}
                )
            
            # Remove the temporary file
            os.unlink(temp_file.name)
        
        # Get the public URL of the uploaded file
        file_url = supabase_client.storage.from_('pdfs').get_public_url(filename)
        
        from fastapi.responses import Response
        return Response(
            content=pdf_binary,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Supabase-URL": file_url
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating prescription PDF: {str(e)}")

@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

