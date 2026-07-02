import os
import sys
import subprocess

def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package} for sample PDF generation...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Ensure reportlab is installed
install_and_import('reportlab')

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_resume_pdf(filename, name, email, phone, title, skills, experience, education, certifications):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, name)
    
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Email: {email}  |  Phone: {phone}")
    c.drawString(50, height - 85, f"Target Role: {title}")
    
    c.setStrokeColorRGB(0.2, 0.4, 0.8)
    c.setLineWidth(1)
    c.line(50, height - 95, width - 50, height - 95)
    
    # Skills Section
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 120, "Technical Skills")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 140, ", ".join(skills))
    
    # Experience Section
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 170, "Professional Experience")
    
    y = height - 195
    for exp in experience:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, exp["role"])
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(width - 150, y, exp["duration"])
        c.setFont("Helvetica", 10)
        
        # Draw description (handle multi-line wrap loosely)
        desc = exp["description"]
        y -= 15
        c.drawString(60, y, desc)
        y -= 25
        
    # Education Section
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Education")
    y -= 20
    for edu in education:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, edu["degree"])
        c.setFont("Helvetica", 10)
        c.drawString(50, y - 15, edu["institution"])
        y -= 35
        
    # Certifications Section
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Certifications")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, ", ".join(certifications))
    
    c.save()
    print(f"Created sample resume: {filename}")

if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample_resumes")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Python Developer Resume
    create_resume_pdf(
        filename=os.path.join(output_dir, "Alice_Miller_Python_Developer.pdf"),
        name="Alice Miller",
        email="alice.miller@email.com",
        phone="555-0192-348",
        title="Senior Python Developer",
        skills=["Python", "SQL", "Docker", "AWS", "FastAPI", "PostgreSQL", "Git", "Kubernetes"],
        experience=[
            {
                "role": "Senior Software Engineer at TechCorp",
                "duration": "2022 - Present",
                "description": "Architected and implemented high-performance backend microservices using FastAPI and Python."
            },
            {
                "role": "Software Developer at CloudSystems",
                "duration": "2019 - 2022",
                "description": "Maintained and scaled PostgreSQL databases and containerized deployments using Docker and AWS."
            }
        ],
        education=[
            {
                "degree": "M.S. in Computer Science",
                "institution": "Stanford University"
            }
        ],
        certifications=["AWS Certified Solutions Architect", "Docker Certified Associate"]
    )
    
    # 2. React Developer Resume
    create_resume_pdf(
        filename=os.path.join(output_dir, "Bob_Chen_React_Developer.pdf"),
        name="Bob Chen",
        email="bob.chen@email.com",
        phone="555-0143-982",
        title="React Frontend Engineer",
        skills=["React", "TypeScript", "JavaScript", "HTML", "CSS", "Tailwind CSS", "Redux", "Git"],
        experience=[
            {
                "role": "Frontend Developer at WebLabs",
                "duration": "2021 - Present",
                "description": "Developed dynamic, highly responsive web interfaces and reusable UI component libraries with React and TypeScript."
            },
            {
                "role": "Junior UI Engineer at DesignStudio",
                "duration": "2020 - 2021",
                "description": "Implemented styling layouts using HTML, CSS, and Tailwind CSS, collaborating closely with UX designers."
            }
        ],
        education=[
            {
                "degree": "B.S. in Computer Engineering",
                "institution": "University of California, Berkeley"
            }
        ],
        certifications=["React Advanced Certification"]
    )

    # 3. Java Developer Resume
    create_resume_pdf(
        filename=os.path.join(output_dir, "Charlie_Davis_Java_Developer.pdf"),
        name="Charlie Davis",
        email="charlie.davis@email.com",
        phone="555-0155-772",
        title="Senior Java Developer",
        skills=["Java", "Spring Boot", "SQL", "PostgreSQL", "Docker", "Git", "Maven", "Hibernate"],
        experience=[
            {
                "role": "Senior Engineer at EnterpriseSolutions",
                "duration": "2022 - Present",
                "description": "Led the development of Spring Boot enterprise applications and streamlined database persistence with Hibernate."
            }
        ],
        education=[
            {
                "degree": "B.S. in Computer Science",
                "institution": "University of Michigan"
            }
        ],
        certifications=["Oracle Certified Professional, Java SE Developer"]
    )
    
    print(f"\nAll sample resumes created in: {output_dir}")
