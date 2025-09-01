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
        """Generate formatted HTML email content for candidate"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
          <p>Dear <b>{candidate.first_name} {candidate.last_name}</b>,</p>

          <p>
            Greetings from <b>InfinitiAI</b> - the Fastest, most Reliable and Innovative Indian 
            Employee Background Verification company.
          </p>

          <p>
            We have been engaged by <b>{company_name}</b> to conduct your background verification 
            as a part of their hiring process. We require you to submit some information in that regard.
          </p>

          <p>
            Please refer below enclosed a link to our platform <b>InfinitiAI</b>, for you to register 
            and submit this information. Instructions for filling the form are mentioned later in this 
            email to provide you with a seamless experience. Kindly note that the information shared by 
            you will be used only for the purpose of background verification.
          </p>

          <p>
            Background verification is an extremely important part of your hiring process at 
            <b>{company_name}</b>, and it's our priority to keep this process simple and convenient for you.
          </p>

          <p><b>Steps to follow:</b></p>
          <ol>
            <li>
              Please arrange the scanned copies of your documents like Identity proof, education 
              mark sheets, degree, work experience (or relieving letter), etc.
            </li>
            <li>
              Use the link below to register at our InfinitiAI portal. Once registered, you should 
              fill the form and upload the documents with utmost care and attention.
            </li>
          </ol>

          <p>
            <b>InfinitiAI Portal:</b> 
            <a href="{settings.FRONTEND_URL}/login/{encrypt_slug(str(candidate.id))}">
              Click here to login
            </a>
            <br>
            <b>User ID:</b> {candidate.email}
          </p>

          <p><b>Important Instructions:</b></p>
          <ul>
            <li>Your login credentials will expire in <b>7 days</b> from receipt of this mail.</li>
            <li>Since Background Verification is an important step in the hiring process, please ensure accuracy.</li>
            <li>We recommend completing your submission in a single sitting.</li>
            <li>Please ensure that the scanned copies of the documents uploaded are clear.</li>
          </ul>

          <p>
            Best Regards,<br>
            <b>HR Team</b><br>
            InfinitiAI
          </p>
        </body>
        </html>
        """

    def _generate_candidate_email_text(self, candidate, company_name: str) -> str:
        """Generate formatted email content for candidate"""
        return f"""
        Dear {candidate.first_name} {candidate.last_name},

        Greetings from InfinitiAI - the Fastest, most Reliable and Innovative Indian Employee Background Verification company.

        We have been engaged by {company_name} to conduct your background verification as a part of their hiring process. 
        We require you to submit some information in that regard.

        Please refer below enclosed a link to our platform InfinitiAI, for you to register and submit this information. 
        Instructions for filling the form are mentioned later in this email to provide you with a seamless experience. 
        Kindly note that the information shared by you will be used only for the purpose of background verification.

        Background verification is an extremely important part of your hiring process at {company_name}, and it's our priority 
        to keep this process simple and convenient for you.

        All you need to do is carefully follow some simple steps and instructions as mentioned below:

        Step 1: Please arrange the scanned copies of your documents like Identity proof, education mark sheets, degree, 
        work experience (or relieving letter), etc.

        Step 2: Use the link below to register at our InfinitiAI portal. Once registered, you should fill the form and upload 
        the documents with utmost care and attention.

        InfinitiAI Portal: {settings.FRONTEND_URL}/login/{encrypt_slug(str(candidate.id))}
        User ID: {candidate.email}

        Important Instructions:
        • Your login credentials will expire in 7 days from receipt of this mail, so please complete this process within this time-period.
        • Since Background Verification is an important step in the hiring process, please ensure that you fill the form with utmost care and accuracy.
        • We recommend completing your submission in a single sitting.
        • Please ensure that the scanned copies of the documents uploaded are clear.

        Best Regards,
        HR Team
        InfinitiAI
        """
