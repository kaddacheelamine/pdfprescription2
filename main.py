from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import weasyprint
from datetime import datetime
import tempfile
import supabase
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os


def send(f,t,s):
# Email details
  from_email = f
  to_email = t
  subject = s
  html = """
  <html lang="ar" dir="rtl">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">

      <title>Rushita - وصفتك الطبية الرقمية</title>
      <style>
          body {
              font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
              margin: 0;
              padding: 0;
              background-color: #f5f5f5;
              color: #333;
              direction: rtl;
          }
          .container {
              max-width: 600px;
              margin: 0 auto;
              background-color: #ffffff;
              border-radius: 8px;
              overflow: hidden;
              box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
          }
          .header {
              background-color: #1e88e5;
              color: white;
              padding: 20px;
              text-align: center;
          }
          .logo {
              font-size: 28px;
              font-weight: bold;
              letter-spacing: 1px;
          }
          .content {
              padding: 30px;
          }
          .prescription-info {
              background-color: #f1f8ff;
              border-radius: 6px;
              padding: 20px;
              margin-bottom: 20px;
          }
          .info-row {
              display: flex;
              justify-content: space-between;
              margin-bottom: 10px;
          }
          .info-title {
              font-weight: bold;
              color: #0d47a1;
          }
          .button-container {
              text-align: center;
              margin: 30px 0;
          }
          .button {
              display: inline-block;
              background-color: #1e88e5;
              color: white;
              font-weight: bold;
              text-decoration: none;
              padding: 12px 30px;
              border-radius: 4px;
              transition: background-color 0.3s;
          }
          .button:hover {
              background-color: #0d47a1;
          }
          .footer {
              background-color: #1e88e5;
              color: white;
              text-align: center;
              padding: 15px;
              font-size: 14px;
          }
      </style>
  </head>
  <body>
      <div class="container">
          <div class="header">
              <div class="logo">Rushita</div>
              <p>منصتك الرقمية للوصفات الطبية</p>
          </div>
          
          <div class="content">
              <h2>مرحباً بك في Rushita</h2>
              <p>تم إصدار وصفة طبية جديدة لك. يمكنك الوصول إليها والاطلاع على تفاصيلها من خلال الرابط أدناه.</p>
              
              
              
              <div class="button-container">
                  <a href="""
  
  html1=f"https://wyypjyfyldeqnzvylsmt.supabase.co/storage/v1/object/public/pdfs//{s}" 
              
              
  html2="""
  class="button">عرض الوصفة الطبية</a>
  </div>
              <p>إذا كانت لديك أية استفسارات، يرجى التواصل مع طبيبك أو الاتصال بفريق دعم Rushita.</p>
              <p>نتمنى لك دوام الصحة والعافية.</p>
          </div>
          
          <div class="footer">
              <p>© 2025 Rushita - جميع الحقوق محفوظة</p>
              <p>هذه الرسالة سرية وموجهة فقط للشخص المعني</p>
          </div>
      </div>
  </body>
  </html>
  """



  # Create message container
  message = MIMEMultipart("alternative")
  message["Subject"] = subject
  message["From"] = from_email
  message["To"] = to_email

  # Attach the HTML part
  html_part = MIMEText(html+html1+html2, "html")
  message.attach(html_part)

  # SMTP settings
  smtp_server = "smtp.gmail.com"
  smtp_port = 587
  smtp_user = os.getenv("USERTP")
  smtp_password = os.getenv("PWDTP")

  # Send the email
  try:
      server = smtplib.SMTP(smtp_server, smtp_port)
      server.starttls()
      server.login(smtp_user, smtp_password)
      server.sendmail(from_email, to_email, message.as_string())
      print("Email sent successfully.")
      server.quit()
  except Exception as e:
      print("Error sending email:", e)



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
    sendToValue : str
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
            send(os.getenv("USERTP"),data.sendToValue,filename)
            
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

