import sqlite3
import os
from datetime import datetime

class LoanDatabase:
    def __init__(self, db_name='loan_applications.db'):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        """Create and return database connection"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database with tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create applications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    dob TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    mother_name TEXT NOT NULL,
                    qualification TEXT NOT NULL,
                    alt_phone TEXT,
                    email TEXT NOT NULL,
                    present_address TEXT NOT NULL,
                    present_years REAL NOT NULL,
                    permanent_address TEXT NOT NULL,
                    permanent_years REAL NOT NULL,
                    total_experience REAL NOT NULL,
                    company_experience REAL NOT NULL,
                    company_name TEXT NOT NULL,
                    company_address TEXT NOT NULL,
                    landmark TEXT,
                    designation TEXT NOT NULL,
                    office_contact TEXT NOT NULL,
                    official_email TEXT NOT NULL,
                    bank_name TEXT NOT NULL,
                    bank_years REAL NOT NULL,
                    branch TEXT NOT NULL,
                    loan_amount REAL NOT NULL,
                    tenure INTEGER NOT NULL,
                    existing_loan TEXT,
                    friend_name TEXT NOT NULL,
                    friend_contact TEXT NOT NULL,
                    friend_address TEXT NOT NULL,
                    relative_name TEXT NOT NULL,
                    relative_contact TEXT NOT NULL,
                    relative_address TEXT NOT NULL,
                    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create file_uploads table with password field
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id INTEGER,
                    file_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_password TEXT NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (application_id) REFERENCES applications (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Database initialized successfully!")
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
    
    def save_application(self, data):
        """Save loan application to database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO applications (
                    name, dob, phone, mother_name, qualification, alt_phone, email,
                    present_address, present_years, permanent_address, permanent_years,
                    total_experience, company_experience, company_name, company_address,
                    landmark, designation, office_contact, official_email, bank_name,
                    bank_years, branch, loan_amount, tenure, existing_loan, friend_name,
                    friend_contact, friend_address, relative_name, relative_contact, relative_address
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['name'], data['dob'], data['phone'], data['mother_name'],
                data['qualification'], data.get('alt_phone', ''), data['email'],
                data['present_address'], data['present_years'], data['permanent_address'],
                data['permanent_years'], data['total_experience'], data['company_experience'],
                data['company_name'], data['company_address'], data.get('landmark', ''),
                data['designation'], data['office_contact'], data['official_email'],
                data['bank_name'], data['bank_years'], data['branch'], data['loan_amount'],
                data['tenure'], data.get('existing_loan', ''), data['friend_name'],
                data['friend_contact'], data['friend_address'], data['relative_name'],
                data['relative_contact'], data['relative_address']
            ))
            
            application_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"✅ Application saved with ID: {application_id}")
            return application_id
            
        except Exception as e:
            print(f"❌ Error saving application: {e}")
            return None
    
    def save_file_record(self, application_id, file_type, file_path, file_password):
        """Save file upload record to database with password"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO file_uploads (application_id, file_type, file_path, file_password)
                VALUES (?, ?, ?, ?)
            ''', (application_id, file_type, file_path, file_password))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error saving file record: {e}")
            return False
    
    def get_application(self, application_id):
        """Get application by ID"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM applications WHERE id = ?', (application_id,))
            application = cursor.fetchone()
            
            conn.close()
            return application
            
        except Exception as e:
            print(f"❌ Error getting application: {e}")
            return None
    
    def get_all_applications(self):
        """Get all applications"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM applications ORDER BY submission_date DESC')
            applications = cursor.fetchall()
            
            conn.close()
            return applications
            
        except Exception as e:
            print(f"❌ Error getting applications: {e}")
            return []
    
    def get_application_count(self):
        """Get total number of applications"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM applications')
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            return 0
    
    def get_application_files(self, application_id):
        """Get all files for an application"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM file_uploads WHERE application_id = ?', (application_id,))
            files = cursor.fetchall()
            
            conn.close()
            return files
            
        except Exception as e:
            print(f"❌ Error getting application files: {e}")
            return []

# Create global database instance
db = LoanDatabase()