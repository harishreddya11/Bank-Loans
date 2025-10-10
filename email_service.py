import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

class EmailService:
    def __init__(self):
        # Email Configuration - Use environment variables
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.email_address = os.environ.get('EMAIL_ADDRESS', 'mohanreddya13@gmail.com')
        self.email_password = os.environ.get('EMAIL_PASSWORD', 'ndehjjtarbfaglzk')
        self.admin_email = os.environ.get('ADMIN_EMAIL', 'mohanreddya13@gmail.com')
        
        print(f"📧 Email Service Initialized:")
        print(f"   From: {self.email_address}")
        print(f"   To: {self.admin_email}")
        print(f"   Configured: {self.is_configured()}")
    
    def is_configured(self):
        """Check if email is properly configured"""
        return (self.email_address and 
                self.email_address != 'your.email@gmail.com' and
                self.email_password and
                self.email_password != 'your_app_password')
    
    def send_application_notification(self, application_id, application_data, files_data):
        """Send email notification for new loan application with file attachments"""
        print(f"📧 Attempting to send email for application {application_id}...")
        
        # Check if email is configured
        if not self.is_configured():
            print("❌ Email not configured - using default credentials")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = self.admin_email
            msg['Subject'] = f"🚀 New Loan Application - {application_data['name']} (ID: {application_id})"
            
            # Create email body
            body = self._create_email_body(application_id, application_data, files_data)
            msg.attach(MIMEText(body, 'plain'))
            
            print(f"✅ Email content created for application {application_id}")
            
            # Attach files if they exist
            files_attached = 0
            for file_data in files_data:
                if self._attach_file(msg, file_data.get('file_path')):
                    files_attached += 1
            
            print(f"📎 Attached {files_attached} files to email")
            
            # Try to send email
            success = self._send_email(msg)
            
            if success:
                print(f"✅ Email sent successfully for application {application_id}")
                print(f"   📎 Files attached: {files_attached}")
                print(f"   👤 Applicant: {application_data['name']}")
                print(f"   💰 Loan Amount: ₹{application_data['loan_amount']:,.2f}")
            else:
                print(f"❌ Failed to send email for application {application_id}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error in email sending process: {str(e)}")
            return False
    
    def _create_email_body(self, application_id, data, files_data):
        """Create email body content with file passwords"""
        
        # Create file passwords section
        files_section = "\n📎 DOCUMENT PASSWORDS:\n"
        files_section += "=" * 60 + "\n"
        
        if files_data:
            for file_data in files_data:
                files_section += f"📄 {file_data['file_type']}:\n"
                files_section += f"   🔐 Password: {file_data['password']}\n"
                files_section += f"   📁 File: {file_data.get('original_filename', 'N/A')}\n"
                files_section += "-" * 40 + "\n"
        else:
            files_section += "   No documents uploaded with this application.\n"
        
        return f"""
🚀 NEW LOAN APPLICATION RECEIVED
==========================================
📋 Application ID: {application_id}
📅 Submission Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

👤 PERSONAL INFORMATION:
=======================
🏷️ Name: {data['name']}
📅 Date of Birth: {data['dob']}
📞 Phone: {data['phone']}
📱 Alternative Phone: {data.get('alt_phone', 'N/A')}
📧 Email: {data['email']}
👩‍👦 Mother's Name: {data['mother_name']}
🎓 Qualification: {data['qualification']}

🏠 ADDRESS DETAILS:
===================
📍 Present Address: {data['present_address']}
⏳ Years at Present Address: {data['present_years']} years

📍 Permanent Address: {data['permanent_address']}
⏳ Years at Permanent Address: {data['permanent_years']} years

💼 EMPLOYMENT INFORMATION:
==========================
🏢 Company: {data['company_name']}
💼 Designation: {data['designation']}
📞 Office Contact: {data['office_contact']}
📧 Official Email: {data['official_email']}
📍 Company Address: {data['company_address']}
🏷️ Landmark: {data.get('landmark', 'N/A')}

📊 EXPERIENCE:
==============
⏳ Total Experience: {data['total_experience']} years
🏢 Current Company Experience: {data['company_experience']} years

🏦 BANK DETAILS:
================
🏦 Bank Name: {data['bank_name']}
⏳ Account Years: {data['bank_years']} years
📍 Branch: {data['branch']}

💰 LOAN DETAILS:
================
💵 Loan Amount: ₹{data['loan_amount']:,.2f}
📅 Tenure: {data['tenure']} months
🏦 Existing Loan: {data.get('existing_loan', 'None')}

📞 REFERENCES:
==============
👥 Friend Reference:
   - Name: {data['friend_name']}
   - Contact: {data['friend_contact']}
   - Address: {data['friend_address']}

👨‍👩‍👧‍👦 Relative Reference:
   - Name: {data['relative_name']}
   - Contact: {data['relative_contact']}
   - Address: {data['relative_address']}

{files_section}
📝 NOTE: All documents are attached to this email. Use the passwords above to open protected files.

This is an automated notification from the Bank Loan Application System.
🔗 Application Link: [Available in Admin Panel]
        """
    
    def _attach_file(self, msg, file_path):
        """Attach file to email"""
        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{os.path.basename(file_path)}"'
                    )
                    msg.attach(part)
                return True
            return False
        except Exception as e:
            print(f"⚠️ Error attaching file {file_path}: {e}")
            return False
    
    def _send_email(self, msg):
        """Send the email with proper error handling"""
        try:
            print(f"🔐 Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            
            # Create SMTP connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()
            
            print(f"🔑 Attempting login with: {self.email_address}")
            server.login(self.email_address, self.email_password)
            print("✅ Login successful")
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.email_address, self.admin_email, text)
            server.quit()
            
            print("✅ Email sent successfully")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication Failed: {e}")
            print("💡 Tips:")
            print("   - Use App Password, not regular Gmail password")
            print("   - Enable 2-factor authentication")
            print("   - Generate App Password at: https://myaccount.google.com/apppasswords")
            return False
            
        except smtplib.SMTPException as e:
            print(f"❌ SMTP Error: {e}")
            return False
            
        except Exception as e:
            print(f"❌ Unexpected email error: {e}")
            return False
    
    def test_connection(self):
        """Test email connection and configuration"""
        print("🧪 Testing email configuration...")
        
        if not self.is_configured():
            print("❌ Email not configured properly")
            return False
        
        try:
            # Test SMTP connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.quit()
            
            print("✅ Email configuration test passed!")
            return True
            
        except Exception as e:
            print(f"❌ Email configuration test failed: {e}")
            return False

# Create global email service instance
email_service = EmailService()