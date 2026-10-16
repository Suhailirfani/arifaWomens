# Arifa Women's Academy, Kodampuzha - Web Application

A modern, responsive, bento-grid based Django ERP web application engineered for **Arifa Women's Academy, Kodampuzha, Kozhikode**.

---

## 🌟 Key Features

### 1. Multi-Role User Dashboards
- **Administrator Dashboard:** High-level KPI metrics, academy-wide attendance breakdown by class, current due fee tracker, fee defaulters PDF generation, and quick operations.
- **Office Staff Dashboard:** Student registration & admissions, fee collections, receipt generation, and pending dues tracking.
- **Teacher Dashboard:** Class teacher workspace, today's attendance status & 1-click marking, class student roster, and exam marks entry.
- **Student & Parent Dashboard:** Real-time indicator showing if student attended today, monthly attendance & percentage, academic year attendance & percentage, exam marks breakdown, and downloadable Progress Report Card PDF.

### 2. Academic Architecture (High School & Higher Secondary)
- **High School Section:** Class 8, Class 9, Class 10 (General stream).
- **Higher Secondary (HSS):** Plus One (+1) and Plus Two (+2) with **Humanities** and **Commerce** streams.
- **Class Structure:** A class combines Grade and Course with Section (e.g., *Plus One Humanities - Section A*, *Class 10 - Section A*).

### 3. Student Register CRUD & Bulk Excel Upload
- **Single Entry:** Comprehensive form capturing student details, guardian info, contact numbers, address, class assignment, vehicle opt-in, and photo.
- **Bulk Excel Upload:** Pre-formatted `.xlsx` workbook parser with downloadable sample template, row-by-row validation, and automatic class resolution.
- **Student Profile:** Complete student dossier with interactive **12-Week Attendance Calendar Heatmap** (Green for Present, Red for Absent, Amber for Late), fee ledger, and exam report history.

### 4. Staff Register CRUD
- Complete staff directory with qualifications, departments, designations, assigned subjects, and managed classes.

### 5. Daily Class-Wise Attendance
- Fast daily attendance recording sheet.
- 1-Click status toggles (`P` Present, `A` Absent, `L` Late) with real-time live counters.
- Bulk shortcuts: *Mark All Present* and *Mark All Absent*.
- Class-wise attendance history and logs.

### 6. Fee Management System (Monthly & Installment-Wise)
- **Installment-Wise Course Fees:** Multi-stage course fee structures (e.g., 1st Installment - Admission, 2nd Installment - Term 2, 3rd Installment - Final Term).
- **Monthly Recurring Fees:** Transportation/bus fee billing for students opting for academy vehicle routes.
- **Who Paid vs Defaulters List:** Instant filterable audit table showing who paid the active due fee and who has NOT paid.
- **Fee Defaulters PDF Export:** Professional, computer-generated PDF report with financial summaries and student contact numbers.
- **Receipt Generation:** Single-click receipt printing and downloadable PDF receipts.

### 7. Examinations & Progress Reports
- Terminal and Mid-Term examination schedules.
- Spreadsheet-like class marks entry register with pass/fail and auto-grade calculations.
- Official Student Progress Report Card view and downloadable PDF report cards.

### 8. Bento Grid Design System & Aesthetics
- Mobile-first, fully responsive design.
- Bento grid modular cards with soft borders, shadows, and hover lifts.
- **Dark and Light Mode Toggle:** Seamless theme switcher with persistent local storage.
- Curated soft pastel color palette (Rose, Lavender, Sage, Amber, Sky) tailored for a prestigious women's academy.

---

## 🔑 Default Login Credentials

| Role | Username | Password | Access Portal |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Administrator Dashboard & Full Control |
| **Office Staff** | `staff` | `staff123` | Admissions, Fees & Registers |
| **Teacher** | `teacher` | `teacher123` | Class Teacher & Marks Entry |
| **Student / Parent** | `student` | `student123` | Student Dashboard & Progress Reports |

*(Tip: The login page includes 1-click demo autofill buttons for each role).*

---

## 🚀 Running the Application

1. **Apply Migrations (if needed):**
   ```bash
   python manage.py migrate
   ```

2. **Seed Sample Data (Optional, already seeded):**
   ```bash
   python populate_sample_data.py
   ```

3. **Start the Development Server:**
   ```bash
   python manage.py runserver 8000
   ```

4. **Access the Application:**
   Open your browser and navigate to:
   [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
