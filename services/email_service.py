from typing import Optional, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
from utils.candidate_utils import encrypt_slug

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL

    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str = "", 
        text_content: str = ""
    ) -> bool:
        """Send email"""
        try:
            print(f"📧 Attempting to send email to: {to_email}")
            print(f"📧 Subject: {subject}")
            print(f"📧 SMTP Server: {self.smtp_server}:{self.smtp_port}")
            print(f"📧 SMTP Username: {self.smtp_username}")
            print(f"📧 From Email: {self.from_email}")
            print(f"📧 HTML Content Length: {len(html_content)}")
            print(f"📧 Text Content Length: {len(text_content)}")
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            if html_content:
                msg.attach(MIMEText(html_content, 'html'))
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))

            print(f"📧 Connecting to SMTP server...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                print(f"📧 Starting TLS...")
                server.starttls()
                print(f"📧 Logging in...")
                server.login(self.smtp_username, self.smtp_password)
                print(f"📧 Sending message...")
                server.send_message(msg)

            print(f"✅ Email sent successfully to: {to_email}")
            return True
        except Exception as e:
            print(f"❌ Error sending email to {to_email}: {e}")
            print(f"❌ Error type: {type(e).__name__}")
            print(f"❌ Error details: {str(e)}")
            return False

    async def send_candidate_email(self, candidate, resend: bool = False) -> bool:
        """Send email to candidate"""
        try:
            # Get company name safely
            company_name = "our company"
            if hasattr(candidate, 'company') and candidate.company:
                company_name = candidate.company.name
            elif hasattr(candidate, 'company_id'):
                # If company relationship not loaded, we can't get the name
                company_name = "our company"
            
            subject = f"Background check for {company_name} | Submit your profile"
            
            # Generate email content
            html_content = self._generate_candidate_email_html(candidate, company_name)
            text_content = self._generate_candidate_email_text(candidate, company_name)
            
            return await self.send_email(candidate.email, subject, html_content, text_content)
        except Exception as e:
            print(f"Error in send_candidate_email: {e}")
            return False

    async def send_reference_email(self, reference_id: int, resend: bool = False) -> bool:
        """Send email to reference"""
        # TODO: Get reference details and generate email
        subject = "Reference check request"
        html_content = "<p>Please provide reference information.</p>"
        
        # For now, return True as placeholder
        return True

    def _generate_candidate_email_html(self, candidate, company_name: str) -> str:
        """Generate HTML email content for candidate"""
        return f"""
        <html>
        <body>
            <h2>Welcome to our background verification process</h2>
            <p>Dear {candidate.first_name},</p>
            <p>You have been invited to complete your background verification for {company_name}.</p>
            <p>Please click the link below to access your verification portal:</p>
            <p><a href=\"{settings.FRONTEND_URL}/login/{encrypt_slug(str(candidate.id))}\">Access Verification Portal</a></p>
            <p>Best regards,<br>HR Team</p>
        </body>
        </html>
        """

    def _generate_candidate_email_text(self, candidate, company_name: str) -> str:
        """Generate text email content for candidate"""
        return f"""
        Welcome to our background verification process

        Dear {candidate.first_name},

        You have been invited to complete your background verification for {company_name}.

        Please visit the following link to access your verification portal:
        {settings.FRONTEND_URL}/login/{encrypt_slug(str(candidate.id))}

        Best regards,
        HR Team
        """ 