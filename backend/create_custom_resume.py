import os
import sys

def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Ensure reportlab is installed
install_and_import('reportlab')

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def build_custom_resume():
    print("="*50)
    print("      HIREGENIE AI - CUSTOM RESUME GENERATOR      ")
    print("="*50)
    
    # Prompt for input
    name = input("Enter Candidate Full Name (e.g. John Doe): ") or "John Doe"
    email = input("Enter Email Address: ") or "john.doe@email.com"
    phone = input("Enter Phone Number: ") or "555-0100-200"
    skills_raw = input("Enter Skills (comma-separated, e.g. Python, SQL, FastAPI, AWS): ")
    if not skills_raw:
        skills = ["Python", "SQL", "Git"]
    else:
        skills = [s.strip() for s in skills_raw.split(",")]
        
    experience_years = input("Enter Years of Experience (e.g. 3): ") or "3"
    education_degree = input("Enter Degree (e.g. B.S. in Computer Science): ") or "B.S. in Computer Science"
    education_school = input("Enter University Name: ") or "State University"
    
    output_filename = f"{name.replace(' ', '_')}_Resume.pdf"
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample_resumes")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, output_filename)
    
    # Generate PDF
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, name)
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Email: {email}  |  Phone: {phone}")
    c.drawString(50, height - 85, "Role: Software Developer")
    c.line(50, height - 95, width - 50, height - 95)
    
    # Skills
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 120, "Technical Skills")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 140, ", ".join(skills))
    
    # Experience
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 170, "Professional Experience")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 195, "Software Developer")
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(width - 150, height - 195, f"{experience_years} years")
    c.setFont("Helvetica", 10)
    c.drawString(60, height - 210, f"Designed and deployed application systems utilizing modern frameworks.")
    
    # Education
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 245, "Education")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 265, education_degree)
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 280, education_school)
    
    c.save()
    print("="*50)
    print(f"Success! Custom resume generated at:")
    print(filepath)
    print("="*50)

if __name__ == "__main__":
    build_custom_resume()
