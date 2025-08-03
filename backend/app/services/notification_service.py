"""
Notification Service - Email service using SendGrid
Following Single Responsibility Principle
"""
import logging
from sendgrid.helpers.mail import Mail, Email, To, Content
import ssl
import os
import sendgrid
from app.models.test import Test
from app.models.user import User
from datetime import datetime
from typing import Dict, Any, List

# Singleton pattern for NotificationService
_notification_service_instance = None

def get_notification_service():
    global _notification_service_instance
    if _notification_service_instance is None:
        _notification_service_instance = NotificationService()
    return _notification_service_instance


# NotificationService class for sending emails
ssl._create_default_https_context = ssl._create_unverified_context


class NotificationService:
    def __init__(self):
        api_key = os.environ.get("SENDGRID_API_KEY")
        self.sg = sendgrid.SendGridAPIClient(api_key=api_key)
        # Use your verified sender email
        self.from_email = Email("kolheyashodip8@gmail.com")

    def send_email(self, to_email: str, subject: str, html_content: str) -> int:
        to = To(to_email)
        content = Content("text/html", html_content)
        mail = Mail(self.from_email, to, subject, content)
        mail_json = mail.get()
        response = self.sg.client.mail.send.post(request_body=mail_json)
        # Optionally log or handle response
        return response.status_code

    def send_account_creation_email(self, to_email: str, username: str, password: str) -> int:
        import html as html_module
        subject = "Your Jatayu Account Created"
        # Escape HTML characters in the password to prevent rendering issues
        escaped_password = html_module.escape(password)
        html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Welcome to Jatayu!</h2>
                <p>Hello,</p>
                <p>Your account has been created successfully.</p>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><b>Username:</b> {html_module.escape(username)}</p>
                    <p><b>Password:</b> <code style="font-size: 14px; background-color: #e9ecef; padding: 2px 4px; border-radius: 3px;">{escaped_password}</code></p>
                </div>
                <p><strong>Important:</strong> Please change your password after your first login for security purposes.</p>
                <p>You can now log in to your account using these credentials.</p>
                <p>Best regards,<br>Team Garuda From Virtusa</p>
            </div>
        """
        return self.send_email(to_email, subject, html_content)

    def send_shortlisting_status_email(self, to_email: str, status: str, extra_info: str = None) -> int:
        subject = "Your Application Status Update"
        html_content = f"<p>Hello,</p><p>Your application status: <b>{status}</b>.</p>"
        if extra_info:
            html_content += f"<p>{extra_info}</p>"
        return self.send_email(to_email, subject, html_content)

    def notify_test_deleted(self, test_name: str, test_id: int, recruiter_email: str) -> int:
        subject = "Test Deleted Notification"
        html_content = f"""
            <p>Hello,</p>
            <p>The test <b>{test_name}</b> (ID: {test_id}) has been deleted from your account.</p>
            <p>If this was not intended, please contact support.</p>
        """
        return self.send_email(recruiter_email, subject, html_content)

    def send_test_scheduled_notification_to_candidate(self, candidate_name: str, candidate_email: str, test_name: str, scheduled_at: datetime, assessment_deadline: datetime = None) -> int:
        """Send test scheduled notification to a shortlisted candidate."""
        subject = f"Test Scheduled: {test_name}"
        
        # Format dates for display
        scheduled_date = scheduled_at.strftime("%B %d, %Y at %I:%M %p") if scheduled_at else "TBD"
        deadline_info = ""
        if assessment_deadline:
            deadline_date = assessment_deadline.strftime("%B %d, %Y at %I:%M %p")
            deadline_info = f"<p><b>Assessment Deadline:</b> {deadline_date}</p>"
        
        html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Congratulations! You've Been Shortlisted</h2>
                <p>Dear {candidate_name},</p>
                
                <p>We're pleased to inform you that you have been shortlisted for the following assessment:</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #2c3e50; margin-top: 0;">{test_name}</h3>
                    <p><b>Scheduled Date:</b> {scheduled_date}</p>
                    {deadline_info}
                </div>
                
                <p>Please make sure to:</p>
                <ul>
                    <li>Log in to your account before the scheduled time</li>
                    <li>Ensure you have a stable internet connection</li>
                    <li>Complete the assessment before the deadline</li>
                </ul>
                
                <p>Good luck with your assessment!</p>
                
                <p>Best regards,<br>
                Team Garuda From Virtusa</p>
            </div>
        """
        
        return self.send_email(candidate_email, subject, html_content)

    async def send_test_scheduled_notification(self, test: Test, creator: User) -> None:
        """Send test scheduled notification to recruiter (existing functionality)."""
        # This method can be implemented for recruiter notifications if needed
        # For now, we'll just log the event
        logging.info(f"Test {test.test_name} (ID: {test.test_id}) has been scheduled by {creator.name}")

    async def send_test_scheduled_notifications_to_shortlisted_candidates(self, test: Test, db) -> List[int]:
        """Send test scheduled notifications to all shortlisted candidates for a test."""
        from app.repositories.candidate_application_repo import CandidateApplicationRepository
        
        # Get all shortlisted candidates for this test
        shortlisted_candidates = await CandidateApplicationRepository.get_shortlisted_candidates_with_emails(db, test.test_id)
        
        response_codes = []
        
        for candidate in shortlisted_candidates:
            try:
                # Send email to each shortlisted candidate
                response_code = self.send_test_scheduled_notification_to_candidate(
                    candidate_name=candidate['name'],
                    candidate_email=candidate['email'],
                    test_name=test.test_name,
                    scheduled_at=test.scheduled_at,
                    assessment_deadline=getattr(test, 'assessment_deadline', None)
                )
                response_codes.append(response_code)
                
                logging.info(f"Sent test scheduled notification to {candidate['email']} for test {test.test_id}")
                
            except Exception as e:
                logging.error(f"Failed to send test scheduled notification to {candidate['email']}: {str(e)}")
                response_codes.append(500)  # Error code
        
        return response_codes