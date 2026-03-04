import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
# e.g. smtp.gmail.com
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

logger = logging.getLogger(__name__)

def generate_email_html(user_name, keyword, location, jobs):
    """Generates an HTML body for the job alert email."""
    
    jobs_html = ""
    for job in jobs[:10]: # Max 10 in email to avoid enormous spam
        salary_str = f"💰 {job.get('salary', 'Not specified')}" if job.get('salary') else ""
        location_str = f"📍 {job.get('location', 'Remote')}"
        
        jobs_html += f"""
        <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px; background-color: #ffffff;">
            <h3 style="margin: 0 0 8px 0; color: #1e293b; font-size: 18px;">
                <a href="{job.get('url', '#')}" style="color: #2563eb; text-decoration: none;">{job.get('title', 'Unknown Title')}</a>
            </h3>
            <p style="margin: 0 0 8px 0; color: #475569; font-size: 16px; font-weight: bold;">{job.get('company', 'Unknown Company')}</p>
            <p style="margin: 0 0 8px 0; color: #64748b; font-size: 14px;">
                <span style="display: inline-block; margin-right: 12px; background: #f1f5f9; padding: 4px 8px; border-radius: 4px;">{location_str}</span>
                <span style="display: inline-block; margin-right: 12px; background: #f1f5f9; padding: 4px 8px; border-radius: 4px;">{job.get('site', 'Source')}</span>
            </p>
            {f'<p style="margin: 0; color: #059669; font-weight: 500; font-size: 14px;">{salary_str}</p>' if salary_str else ''}
        </div>
        """

    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8fafc;">
            <div style="background-color: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h1 style="color: #0f172a; margin-top: 0;">Job Aggregator Alerts</h1>
                <p style="font-size: 16px; color: #334155;">Hello {user_name or 'there'},</p>
                <p style="font-size: 16px; color: #334155;">We found <strong>{len(jobs)}</strong> new jobs matching your alert for <strong>"{keyword}"</strong>{f' in <strong>"{location}"</strong>' if location else ''}!</p>
                
                <div style="margin-top: 30px;">
                    {jobs_html}
                </div>
                
                <p style="margin-top: 30px; font-size: 14px; color: #94a3b8; text-align: center;">
                    You are receiving this because you subscribed to daily job alerts.<br>
                    Manage your alerts in your dashboard.
                </p>
            </div>
        </body>
    </html>
    """
    return html

def send_job_alert_email(to_email, user_name, keyword, location, jobs):
    """
    Dispatches the email via SMTP.
    If no SMTP credentials exist in .env, it simulates sending by logging to console.
    """
    if not jobs:
        return False
        
    subject = f"New {keyword} Jobs Available! 🚀"
    html_content = generate_email_html(user_name, keyword, location, jobs)
    
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.warning("SMTP Config Missing: Simulating Email Dispatch")
        print("\n" + "="*50)
        print(f"📧 SIMULATED EMAIL TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"BODY:\n{html_content[:300]}... [TRUNCATED HTML]")
        print("="*50 + "\n")
        return True
        
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Job Aggregator <{SMTP_EMAIL}>"
        msg['To'] = to_email
        
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        logger.info(f"Successfully sent job alert to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

def send_password_reset_email(to_email, user_name, reset_link):
    subject = "Password Reset Request - Job Aggregator"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8fafc;">
            <div style="background-color: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center;">
                <h1 style="color: #0f172a; margin-top: 0;">Password Reset Request</h1>
                <p style="font-size: 16px; color: #334155;">Hello {user_name or 'there'},</p>
                <p style="font-size: 16px; color: #334155;">We received a request to reset your password. Click the button below to choose a new one. This link will expire in 1 hour.</p>
                
                <a href="{reset_link}" style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 20px;">
                    Reset Password
                </a>
                
                <p style="margin-top: 30px; font-size: 14px; color: #94a3b8;">
                    If you did not request this, you can safely ignore this email.
                </p>
            </div>
        </body>
    </html>
    """
    
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.warning("SMTP Config Missing: Simulating Password Reset Email")
        print("\n" + "="*50)
        print(f"📧 SIMULATED RESET EMAIL TO: {to_email}")
        print(f"LINK: {reset_link}")
        print("="*50 + "\n")
        return True
        
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Job Aggregator Support <{SMTP_EMAIL}>"
        msg['To'] = to_email
        
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        logger.info(f"Successfully sent password reset to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send reset email to {to_email}: {e}")
        return False
