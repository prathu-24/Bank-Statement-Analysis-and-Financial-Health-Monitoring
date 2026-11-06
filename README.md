# Bank-Statement-Analysis-and-Financial-Health-Monitoring

# FinSight – AI-Based Bank Statement Intelligence & Financial Health Analyzer

**Transform bank statements into actionable financial intelligence.**

FinSight is an AI-powered financial analysis platform that helps users understand their spending habits, monitor financial health, detect unusual transactions, identify recurring payments, and forecast future cash flow.

Upload a bank statement in CSV or PDF format and get a comprehensive view of your financial activity through interactive dashboards, explainable insights, and personalized recommendations.

---

## Key Features

### 1. Bank Statement Processing
- Upload bank statements in CSV and PDF formats.
- Support for different bank statement formats.
- Automatic statement format detection.
- Intelligent transaction extraction and normalization.
- Validation of transaction records and account balances.
- Detection of duplicate and incomplete transactions.

### 2. Expense Categorization
- Automatically categorize transactions.
- Identify spending across categories such as:
  - Food & Dining
  - Shopping
  - Transportation
  - Entertainment
  - Bills & Utilities
  - Healthcare
  - EMI & Loan Payments
  - ATM Withdrawals
- Support manual category corrections.

### 3. Financial Dashboard
- Monthly income and expense analysis.
- Category-wise spending breakdown.
- Top merchant analysis.
- Monthly spending trends.
- Interactive financial visualizations.

### 4. Recurring Payment Detection
- Identify recurring subscriptions and payments.
- Detect monthly bills and EMI payments.
- Recognize potential forgotten subscriptions.
- Analyze payment frequency and amount variations.

### 5. Unusual Transaction Detection
- Identify unusually high transactions.
- Detect new merchants.
- Identify potential duplicate charges.
- Provide alerts for transactions that require review.

### 6. Financial Health Score
- Generate a transparent financial health score out of 100.
- Evaluate savings rate.
- Analyze expense stability.
- Monitor debt-to-income ratio.
- Identify low-balance periods.
- Explain how each score component is calculated.

### 7. Cash Flow Forecasting
- Predict account balance for the next 30 days.
- Analyze recurring income and expenses.
- Estimate future spending patterns.
- Highlight potential low-balance periods.
- Identify possible cash-flow shortages.

### 8. Explainable Financial Insights
- Compare actual spending with the 50/30/20 budgeting rule.
- Generate personalized financial recommendations.
- Identify potential savings opportunities.
- Explain why an alert or recommendation was generated.

### 9. Privacy & Security
- Mask sensitive personal information.
- Avoid exposing raw transaction details to external AI services.
- Provide data deletion functionality.
- Process core financial analytics locally.

---

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React.js, Vite |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Backend | Python, FastAPI |
| Database | SQLite |
| Data Processing | Pandas |
| PDF Processing | pdfplumber |
| Machine Learning / Analytics | Statistical Analysis, Anomaly Detection |
| AI Integration | Google Gemini API (optional) |
| Testing | Pytest |

---

## System Architecture

```text
        USER
          |
          v
   React Frontend
          |
          v
     FastAPI Backend
          |
          v
  Statement Processing
          |
          v
  Transaction Validation
          |
          v
  Expense Categorization
          |
          v
  Financial Analytics
     /    |     \
    /     |      \
Recurring Anomaly Financial
Payments  Detection Scoring
    \      |      /
     \     |     /
          v
   Cash Flow Forecast
          |
          v
  Explainable Insights
          |
          v
  Financial Dashboard
```

---

## Project Structure

```text
Bank-Statement-Analysis-and-Financial-Health-Monitoring/
│
├── backend/
│   ├── app/
│   │   ├── parsers/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── routes/
│   │   ├── database.py
│   │   ├── config.py
│   │   └── main.py
│   │
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── services/
│   │   └── App.jsx
│   │
│   └── package.json
│
├── demo_data/
│   ├── hdfc_sample.csv
│   ├── sbi_sample.csv
│   ├── generic_sample.csv
│   └── sample_statement.pdf
│
├── scripts/
│   └── generate_demo_data.py
│
└── README.md
```

---

## Installation & Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/prathu-24/Bank-Statement-Analysis-and-Financial-Health-Monitoring.git
```

```bash
cd Bank-Statement-Analysis-and-Financial-Health-Monitoring
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend server:

```bash
uvicorn app.main:app --reload
```

Backend API:

`http://127.0.0.1:8000`

API Documentation:

`http://127.0.0.1:8000/docs`

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm.cmd install
```

Start the development server:

```bash
npm.cmd run dev
```

Frontend:

`http://localhost:5173`

---

## How It Works

1. Upload a bank statement in CSV or PDF format.
2. FinSight automatically extracts transaction information.
3. The validation engine checks transaction consistency.
4. Transactions are categorized based on merchant descriptions.
5. The analytics engine identifies spending patterns and recurring payments.
6. Unusual transactions are flagged for review.
7. A financial health score is generated.
8. The forecasting engine estimates future cash flow.
9. The dashboard presents financial insights and recommendations.

---

## Sample Use Cases

- Understanding monthly spending habits.
- Tracking unnecessary expenses.
- Identifying recurring subscriptions.
- Detecting unusual financial activity.
- Monitoring savings performance.
- Predicting potential cash shortages.
- Making better personal budgeting decisions.

---

## Privacy Disclaimer

FinSight is designed with privacy as a core consideration. Financial information is sensitive, and users should only upload statements they are authorized to access.

Use synthetic or anonymized bank statements for demonstrations and testing. Never commit real bank statements, account numbers, API keys, or other sensitive information to this repository.

---

## Future Enhancements

- Support for additional Indian and international banks.
- Advanced machine learning-based transaction classification.
- Improved anomaly detection.
- Multi-account financial analysis.
- Exportable financial health reports.
- Enhanced financial forecasting.
- Mobile application integration.

---

## Project Information

**Project Name:** FinSight

**Problem Statement:** PS-04 – Fintech

**Project Category:** Artificial Intelligence / FinTech

**Project Type:** Full-Stack Financial Intelligence Platform

**Developed for:** Technovate Hackathon

---

## Contributors

Developed as part of the Technovate Hackathon.

---

## License

This project is intended for educational, research, and demonstration purposes.