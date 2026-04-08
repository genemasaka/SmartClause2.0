import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails via Hostinger SMTP."""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.hostinger.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_user)
        self.app_url = os.getenv("APP_URL", "http://smartclause.net").rstrip("/")
        
    def _get_template(self, template_name: str, placeholders: Dict[str, Any]) -> str:
        """Read template file and replace placeholders."""
        template_path = os.path.join("templates", template_name)
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
                for key, value in placeholders.items():
                    content = content.replace(f"{{{{{key}}}}}", str(value))
                return content
        except FileNotFoundError:
            logger.error(f"Template not found: {template_path}")
            return ""
        except Exception as e:
            logger.error(f"Error reading template {template_name}: {e}")
            return ""

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send a general HTML email."""
        if not self.smtp_user or not self.smtp_pass or not self.smtp_from:
            logger.error("SMTP credentials (user, pass, or from) not configured in environment variables.")
            return False
            
        try:
            # Get values first to avoid potential race conditions/type narrowing issues
            smtp_user = self.smtp_user
            smtp_pass = self.smtp_pass
            smtp_from = self.smtp_from

            if not smtp_user or not smtp_pass or not smtp_from:
                logger.error("SMTP credentials (user, pass, or from) not configured.")
                return False

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = smtp_from
            message["To"] = to_email
            
            part = MIMEText(html_content, "html")
            message.attach(part)
            
            # Use SMTP_SSL for port 465
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, to_email, message.as_string())
                
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_invitation(self, to_email: str, org_name: str, role: str, invite_token: str) -> bool:
        """Send team invitation email."""
        invite_link = f"{self.app_url}/?invite_token={invite_token}"
        placeholders = {
            "org_name": org_name,
            "role": role,
            "invite_link": invite_link,
            "app_url": self.app_url
        }
        
        html_content = self._get_template("email_invitation.html", placeholders)
        if not html_content:
            # Fallback plain text if template fails
            html_content = f"""
            <h2>You've been invited to join {org_name} on SmartClause</h2>
            <p>You have been invited as a <strong>{role}</strong>.</p>
            <p>Click the link below to accept the invitation:</p>
            <p><a href="{invite_link}">{invite_link}</a></p>
            """
            
        return self.send_email(to_email, f"Invitation to join {org_name} on SmartClause", html_content)

    def send_confirmation(self, to_email: str, user_name: Optional[str] = None) -> bool:
        """Send sign-up confirmation/welcome email."""
        placeholders = {
            "user_name": user_name or to_email.split("@")[0],
            "app_url": self.app_url
        }
        
        html_content = self._get_template("email_confirmation.html", placeholders)
        if not html_content:
            # Fallback
            html_content = f"""
            <h2>Welcome to SmartClause!</h2>
            <p>Hi {placeholders['user_name']},</p>
            <p>Thank you for signing up for SmartClause. We're excited to have you on board!</p>
            <p>You can start drafting smarter right away at <a href="{self.app_url}">{self.app_url}</a>. If you have any questions, contact us at <a href="mailto:support@smartclause.net">support@smartclause.net</a>.</p>
            """
            
        return self.send_email(to_email, "Welcome to SmartClause", html_content)
    def send_password_reset(self, to_email: str, reset_link: str) -> bool:
        """Send password reset email."""
        placeholders = {
            "reset_link": reset_link,
            "app_url": self.app_url
        }
        
        html_content = self._get_template("email_password_reset.html", placeholders)
        if not html_content:
            # Fallback
            html_content = f"""
            <h2>Reset Your Password</h2>
            <p>Hi there,</p>
            <p>We received a request to reset your password. Click the link below to set a new password:</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
            <p>If you didn't request this, you can safely ignore this email.</p>
            """
            
        return self.send_email(to_email, "Reset Your SmartClause Password", html_content)
