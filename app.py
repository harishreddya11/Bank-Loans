from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
import os
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime
import tempfile
import traceback

# Import your custom modules
from database import db, LoanDatabase
from email_service import email_service

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'bank-loan-app-secret-2024')

# Configuration for Render.com
if os.environ.get('RENDER'):
    # Production configuration for Render
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'loan_uploads')
    DATABASE_PATH = os.path.join(tempfile.gettempdir(), 'loan_applications.db')
else:
    # Local development configuration
    UPLOAD_FOLDER = 'uploads'
    DATABASE_PATH = 'loan_applications.db'

ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['DATABASE_PATH'] = DATABASE_PATH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# File type mapping
FILE_TYPES = {
    'aadhar': 'Aadhar Card',
    'pan': 'PAN Card',
    'salary_slips': 'Salary Slips',
    'bank_statement': 'Bank Statement',
    'offer_letter': 'Offer Letter',
    'relieving_letter': 'Relieving Letter'
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_files(application_id, name, files, file_passwords):
    """Save uploaded files with Render.com compatibility"""
    try:
        # Create user folder
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"{safe_name}_{application_id}")
        
        # Ensure directory exists
        os.makedirs(user_folder, exist_ok=True)
        
        file_data = []
        for file_field, file in files.items():
            if file and file.filename != '':
                # Validate file type
                if not allowed_file(file.filename):
                    print(f"⚠️ Invalid file type: {file.filename}")
                    continue
                
                # Get secure filename
                filename = secure_filename(file.filename)
                file_path = os.path.join(user_folder, filename)
                
                try:
                    # Save file
                    file.save(file_path)
                    
                    # Get password for this file
                    password = file_passwords.get(file_field, 'No password')
                    
                    # Save to database
                    db.save_file_record(application_id, FILE_TYPES.get(file_field, file_field), file_path, password)
                    
                    # Add to file data for email
                    file_data.append({
                        'file_type': FILE_TYPES.get(file_field, file_field),
                        'file_path': file_path,
                        'original_filename': file.filename,
                        'password': password
                    })
                    
                    print(f"✅ File saved: {file_path}")
                    
                except Exception as file_error:
                    print(f"⚠️ Error saving file {file_field}: {file_error}")
                    continue
                    
        return file_data
        
    except Exception as e:
        print(f"❌ Error in file upload process: {e}")
        return []

# Routes
@app.route('/')
def index():
    """Main application form"""
    try:
        app_count = db.get_application_count()
        return render_template('index.html', app_count=app_count)
    except Exception as e:
        print(f"Error loading index: {e}")
        return render_template('index.html', app_count=0)

@app.route('/apply', methods=['POST'])
def apply_loan():
    """Handle loan application submission with comprehensive error handling"""
    print("🚀 Loan application submission started...")
    
    if request.method == 'POST':
        try:
            # Log basic request info
            print(f"📝 Form fields received: {len(request.form)}")
            print(f"📁 Files received: {len([f for f in request.files.values() if f and f.filename])}")
            
            # Extract form data with validation
            required_fields = [
                'name', 'dob', 'phone', 'mother_name', 'qualification', 'email',
                'present_address', 'present_years', 'permanent_address', 'permanent_years',
                'total_experience', 'company_experience', 'company_name', 'company_address',
                'designation', 'office_contact', 'official_email', 'bank_name', 'bank_years',
                'branch', 'loan_amount', 'tenure', 'friend_name', 'friend_contact',
                'friend_address', 'relative_name', 'relative_contact', 'relative_address'
            ]
            
            form_data = {}
            missing_fields = []
            
            for field in required_fields:
                value = request.form.get(field, '').strip()
                if not value:
                    missing_fields.append(field)
                form_data[field] = value
            
            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                print(f"❌ {error_msg}")
                return jsonify({
                    'success': False, 
                    'error': error_msg
                }), 400
            
            # Convert numeric fields
            try:
                form_data['present_years'] = float(form_data['present_years'])
                form_data['permanent_years'] = float(form_data['permanent_years'])
                form_data['total_experience'] = float(form_data['total_experience'])
                form_data['company_experience'] = float(form_data['company_experience'])
                form_data['bank_years'] = float(form_data['bank_years'])
                form_data['loan_amount'] = float(form_data['loan_amount'])
                form_data['tenure'] = int(form_data['tenure'])
            except ValueError as e:
                error_msg = f"Invalid number format: {str(e)}"
                print(f"❌ {error_msg}")
                return jsonify({
                    'success': False, 
                    'error': error_msg
                }), 400
            
            # Optional fields
            form_data['alt_phone'] = request.form.get('alt_phone', '').strip()
            form_data['landmark'] = request.form.get('landmark', '').strip()
            form_data['existing_loan'] = request.form.get('existing_loan', '').strip()
            
            # Get file passwords
            file_passwords = {
                'aadhar': request.form.get('aadhar_password', 'No password').strip(),
                'pan': request.form.get('pan_password', 'No password').strip(),
                'salary_slips': request.form.get('salary_slips_password', 'No password').strip(),
                'bank_statement': request.form.get('bank_statement_password', 'No password').strip(),
                'offer_letter': request.form.get('offer_letter_password', 'No password').strip(),
                'relieving_letter': request.form.get('relieving_letter_password', 'No password').strip()
            }
            
            print("✅ Form data validation passed")
            
            # Save to database
            application_id = db.save_application(form_data)
            
            if not application_id:
                error_msg = "Failed to save application to database"
                print(f"❌ {error_msg}")
                return jsonify({
                    'success': False, 
                    'error': error_msg
                }), 500
            
            print(f"✅ Application saved with ID: {application_id}")
            
            # Handle file uploads
            files_data = []
            try:
                files = {
                    'aadhar': request.files.get('aadhar'),
                    'pan': request.files.get('pan'),
                    'salary_slips': request.files.get('salary_slips'),
                    'bank_statement': request.files.get('bank_statement'),
                    'offer_letter': request.files.get('offer_letter'),
                    'relieving_letter': request.files.get('relieving_letter')
                }
                
                files_data = save_uploaded_files(application_id, form_data['name'], files, file_passwords)
                print(f"✅ Successfully processed {len(files_data)} files")
                
            except Exception as file_error:
                print(f"⚠️ File upload error (non-critical): {file_error}")
                # Continue processing even if file upload fails
            
            # Send email notification
            email_sent = False
            email_error = None
            
            try:
                print(f"📧 Starting email process for application {application_id}")
                
                if not email_service.is_configured():
                    print("⚠️ Email not configured - skipping email notification")
                else:
                    print("✅ Email service is configured - attempting to send...")
                    email_sent = email_service.send_application_notification(application_id, form_data, files_data)
                    
                    if email_sent:
                        print(f"✅ Email sent successfully for application {application_id}")
                    else:
                        print(f"❌ Email failed for application {application_id}")
                        
            except Exception as e:
                email_error = str(e)
                print(f"❌ Email process error: {email_error}")
                # Don't crash the application if email fails
            
            print(f"🎉 Application {application_id} processed successfully!")
            
            return jsonify({
                'success': True, 
                'application_id': application_id,
                'message': 'Application submitted successfully! Our team will contact you soon.',
                'files_uploaded': len(files_data),
                'email_sent': email_sent,
                'email_error': email_error if email_error else None
            })
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            print(traceback.format_exc())
            
            return jsonify({
                'success': False, 
                'error': 'An unexpected error occurred. Please try again.',
                'debug_error': str(e)
            }), 500

@app.route('/admin/applications')
def admin_applications():
    """Admin view to see all applications"""
    try:
        applications = db.get_all_applications()
        return render_template('admin.html', applications=applications)
    except Exception as e:
        return f"Error accessing applications: {str(e)}", 500

@app.route('/admin/application/<int:app_id>')
def view_application(app_id):
    """View specific application details"""
    try:
        application = db.get_application(app_id)
        files = db.get_application_files(app_id)
        
        if not application:
            return "Application not found", 404
            
        return render_template('application_detail.html', 
                             application=application, 
                             files=files)
    except Exception as e:
        return f"Error viewing application: {str(e)}", 500

@app.route('/admin/uploads')
def admin_uploads():
    """Admin view to see uploads structure"""
    try:
        uploads_path = app.config['UPLOAD_FOLDER']
        structure = {
            'total_folders': 0,
            'total_files': 0,
            'folders': [],
            'upload_path': uploads_path,
            'path_exists': os.path.exists(uploads_path)
        }
        
        if os.path.exists(uploads_path):
            for folder_name in os.listdir(uploads_path):
                folder_path = os.path.join(uploads_path, folder_name)
                if os.path.isdir(folder_path):
                    folder_info = {
                        'name': folder_name,
                        'files': [],
                        'file_count': 0,
                        'size': 0
                    }
                    
                    for file_name in os.listdir(folder_path):
                        file_path = os.path.join(folder_path, file_name)
                        if os.path.isfile(file_path):
                            folder_info['files'].append({
                                'name': file_name,
                                'size': os.path.getsize(file_path)
                            })
                            folder_info['file_count'] += 1
                            folder_info['size'] += os.path.getsize(file_path)
                            structure['total_files'] += 1
                    
                    structure['folders'].append(folder_info)
                    structure['total_folders'] += 1
        
        return render_template('uploads_admin.html', structure=structure)
    except Exception as e:
        return f"Error accessing uploads: {str(e)}", 500

@app.route('/status')
def status():
    """System status page"""
    try:
        status_info = {
            'status': 'healthy',
            'database_file': app.config['DATABASE_PATH'],
            'database_exists': os.path.exists(app.config['DATABASE_PATH']),
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'upload_folder_exists': os.path.exists(app.config['UPLOAD_FOLDER']),
            'total_applications': db.get_application_count(),
            'email_configured': email_service.is_configured(),
            'environment': 'production' if os.environ.get('RENDER') else 'development',
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(status_info)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        # Test database connection
        db_status = db.get_application_count() >= 0
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected' if db_status else 'error',
            'timestamp': datetime.now().isoformat(),
            'environment': 'production' if os.environ.get('RENDER') else 'development'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/test-email')
def test_email():
    """Test email configuration endpoint"""
    try:
        print("🧪 Testing email configuration via endpoint...")
        
        # Test if email service is configured
        if not email_service.is_configured():
            return jsonify({
                'success': False,
                'message': 'Email not configured',
                'details': 'Please set EMAIL_ADDRESS, EMAIL_PASSWORD, and ADMIN_EMAIL environment variables in Render dashboard'
            })
        
        # Test SMTP connection
        connection_test = email_service.test_connection()
        
        if connection_test:
            # Try to send a test email
            test_data = {
                'name': 'Test User',
                'phone': '1234567890',
                'email': 'test@example.com',
                'dob': '2000-01-01',
                'company_name': 'Test Company',
                'designation': 'Test Designation',
                'total_experience': 5.0,
                'company_experience': 2.0,
                'loan_amount': 100000.0,
                'tenure': 36
            }
            
            test_files = []
            email_sent = email_service.send_application_notification(999, test_data, test_files)
            
            return jsonify({
                'success': email_sent,
                'message': 'Test email sent successfully' if email_sent else 'Failed to send test email',
                'smtp_server': email_service.smtp_server,
                'from_email': email_service.email_address,
                'to_email': email_service.admin_email,
                'connection_test': connection_test
            })
        else:
            return jsonify({
                'success': False,
                'message': 'SMTP connection failed',
                'smtp_server': email_service.smtp_server,
                'from_email': email_service.email_address
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Email test failed: {str(e)}'
        })

@app.route('/email-status')
def email_status():
    """Check email configuration status"""
    status = {
        'configured': email_service.is_configured(),
        'from_email': email_service.email_address,
        'admin_email': email_service.admin_email,
        'smtp_server': email_service.smtp_server,
        'environment_variables_set': {
            'EMAIL_ADDRESS': bool(os.environ.get('EMAIL_ADDRESS')),
            'EMAIL_PASSWORD': bool(os.environ.get('EMAIL_PASSWORD')),
            'ADMIN_EMAIL': bool(os.environ.get('ADMIN_EMAIL'))
        }
    }
    return jsonify(status)

# CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed_error(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large'}), 413

# Initialize database with production path
try:
    db = LoanDatabase(app.config['DATABASE_PATH'])
    print("✅ Production database initialized!")
except Exception as e:
    print(f"❌ Database initialization failed: {e}")

# Production startup
if __name__ == '__main__':
    # Get port from environment variable (Render provides this)
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 60)
    print("🚀 Bank Loan Application System - PRODUCTION READY!")
    print(f"📍 Running on port: {port}")
    print(f"🏠 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"💾 Database: {app.config['DATABASE_PATH']}")
    print(f"📧 Email: {'Configured' if email_service.is_configured() else 'Not Configured'}")
    print(f"🌍 Environment: {'Production' if os.environ.get('RENDER') else 'Development'}")
    print("=" * 60)
    
    # Run with production settings
    app.run(host='0.0.0.0', port=port, debug=False)