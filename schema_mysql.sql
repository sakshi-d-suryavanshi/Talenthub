-- MySQL 8 version of the TalentHub eight-table schema (Lab 4 design).
-- The Flask app runs on SQLite by default; use this script to create the same
-- schema in MySQL if you port the repository layer (app/repositories.py).
CREATE DATABASE IF NOT EXISTS talenthub;
USE talenthub;

CREATE TABLE students (
  student_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  department VARCHAR(80) NOT NULL,
  year INT NOT NULL,
  cgpa DECIMAL(4,2) NOT NULL,
  active_backlogs INT NOT NULL DEFAULT 0,
  skills TEXT,
  CONSTRAINT chk_year CHECK (year BETWEEN 1 AND 6),
  CONSTRAINT chk_cgpa CHECK (cgpa BETWEEN 0 AND 10),
  CONSTRAINT chk_backlogs CHECK (active_backlogs >= 0)
);

CREATE TABLE companies (
  company_id INT AUTO_INCREMENT PRIMARY KEY,
  company_name VARCHAR(150) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  industry VARCHAR(100),
  location VARCHAR(100)
);

CREATE TABLE job_listings (
  job_id INT AUTO_INCREMENT PRIMARY KEY,
  company_id INT NOT NULL,
  job_title VARCHAR(150) NOT NULL,
  description TEXT,
  eligibility_criteria TEXT,
  min_cgpa DECIMAL(4,2) NOT NULL DEFAULT 0,
  max_backlogs INT NULL,
  allowed_departments VARCHAR(255) DEFAULT '',
  required_skills TEXT,
  salary DECIMAL(12,2),
  deadline DATE,
  FOREIGN KEY (company_id) REFERENCES companies(company_id),
  CONSTRAINT chk_min_cgpa CHECK (min_cgpa BETWEEN 0 AND 10)
);

CREATE TABLE applications (
  application_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  job_id INT NOT NULL,
  application_date DATE NOT NULL,
  status ENUM('Applied','Shortlisted','Rejected','Scheduled','Selected') NOT NULL DEFAULT 'Applied',
  UNIQUE KEY uq_student_job (student_id, job_id),
  FOREIGN KEY (student_id) REFERENCES students(student_id),
  FOREIGN KEY (job_id) REFERENCES job_listings(job_id)
);

CREATE TABLE interview_slots (
  interview_id INT AUTO_INCREMENT PRIMARY KEY,
  application_id INT NOT NULL,
  interview_date DATE NOT NULL,
  interview_time TIME NOT NULL,
  interview_mode ENUM('Online','Offline') NOT NULL,
  status ENUM('Scheduled','Completed','Cancelled') NOT NULL DEFAULT 'Scheduled',
  FOREIGN KEY (application_id) REFERENCES applications(application_id)
);

CREATE TABLE offers (
  offer_id INT AUTO_INCREMENT PRIMARY KEY,
  application_id INT NOT NULL UNIQUE,
  offer_date DATE NOT NULL,
  salary DECIMAL(12,2),
  joining_date DATE,
  status ENUM('Pending','Accepted','Declined') NOT NULL DEFAULT 'Pending',
  FOREIGN KEY (application_id) REFERENCES applications(application_id)
);

CREATE TABLE skills (
  skill_id INT AUTO_INCREMENT PRIMARY KEY,
  skill_name VARCHAR(80) NOT NULL UNIQUE,
  skill_type VARCHAR(50)
);

CREATE TABLE notifications (
  notification_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  message VARCHAR(500) NOT NULL,
  notification_date DATETIME NOT NULL,
  is_read TINYINT(1) NOT NULL DEFAULT 0,
  FOREIGN KEY (student_id) REFERENCES students(student_id)
);
