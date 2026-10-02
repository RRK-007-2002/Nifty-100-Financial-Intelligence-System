# Centralized Financial Analytics Platform (Nifty 100)

## 🎯 Problem Statement
Financial information is often distributed across multiple datasets and requires significant preprocessing before it can be used for meaningful analysis.
This project aims to build a centralized analytical platform that allows an analyst to:

- Explore company financial information.
- Analyze historical growth and profitability.
- Filter companies using configurable financial criteria.
- Compare companies with relevant peers.
- Analyze sector-level trends.
- Identify clusters and potential outliers.
- Generate standardized analytical reports.
- Access analytical results programmatically through APIs.
- Validate data and analytical outputs through automated tests.

---

## 🚀 Key Features

### 1. Company Financial Analysis
Analyze individual companies using:
- Revenue growth
- Profit growth
- Revenue CAGR
- Profit CAGR
- Net profit margin
- ROE
- ROCE
- Stock-price CAGR
- Historical financial statements
- Balance-sheet information
- Cash-flow information

### 2. Financial Screener
The screener allows analysts to filter companies using multiple financial conditions.
Example screening dimensions:

```
Profitability
├── ROE
├── ROCE
└── Profit Margin

Growth
├── Revenue CAGR
└── Profit CAGR

Market Performance
└── Stock Price CAGR

Risk / Quality
├── Drawdown
├── Consistency
└── Cash-flow characteristics

Valuation
└── Available valuation metrics
```

The screening process is designed to be reproducible so that the same criteria can generate the same analytical universe.

### 3. Peer Comparison
The platform supports company-to-company and peer-group analysis.
Analysts can examine:
- Financial ratios
- Growth metrics
- Profitability
- Relative percentile position
- Peer-group distributions
- Company-level differences

Percentile analysis provides relative context rather than relying only on absolute values.

### 4. Sector Analysis
Sector-level analysis helps identify broader patterns across companies.
The platform supports analysis of:
- Sector-level financial metrics
- Growth patterns
- Profitability distributions
- Company concentration
- Sector trends

### 5. Portfolio & Capital Allocation Analytics
The project includes portfolio-oriented analytics for examining:
- Portfolio returns
- Risk characteristics
- Diversification
- Concentration
- Allocation statistics
- Benchmark-relative measures where applicable

The analysis is intended to make portfolio calculations reproducible and transparent.

### 6. Clustering
Machine-learning techniques are used to identify groups of companies with similar financial characteristics.
The clustering workflow includes:

```
Financial Features ──► Data Preparation ──► Feature Scaling ──► Clustering ──► Cluster Labels ──► Cluster Profiles
```

Outputs include:
- Cluster labels
- Cluster profiles
- Elbow analysis
- Cluster-level interpretation

### 7. Outlier Detection
The platform generates an outlier report to identify unusual observations.
An identified outlier is treated as an investigation signal, not automatically as a data error.
Analysts should validate:
- Raw value
- Unit
- Reporting period
- Source data
- Business context
- Data-quality status

### 8. Interactive Dashboard
The Streamlit dashboard provides a user-friendly interface for exploring the platform.
Main analytical areas include:
- Home
- Profile
- Screener
- Peers
- Trends
- Sectors
- Capital Allocation
- Reports

### 9. REST API
The platform includes a FastAPI service layer for programmatic access.
The API is organized into router modules covering areas such as:
- Companies
- Screener
- Sectors
- Peers
- Valuation
- Portfolio
- Documents

**Health endpoint:**
`GET /api/v1/health`

API documentation can be generated through FastAPI/OpenAPI.

### 10. Automated Reports
The project supports generation of analytical reports including:
- Company tearsheets
- Cluster reports
- Outlier reports
- Portfolio statistics
- Analyst documentation
- Analytical visualizations

---

## 🏗️ System Architecture

```
                    ┌──────────────────────┐
                    │   Financial Data     │
                    │  Sources / Datasets  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     ETL Pipeline     │
                    │ Clean / Normalize /  │
                    │       Validate       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   SQLite Database    │
                    │    nifty100.db       │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │ KPI / Ratio │  │  Screener   │  │ Peer /      │
       │ Analytics   │  │   Engine    │  │ Sector      │
       └──────┬──────┘  └──────┬──────┘  │ Analytics   │
              │                │         └──────┬──────┘
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Analytics Layer   │
                    │ Clustering /        │
                    │ Outliers / Portfolio│
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │  Streamlit  │  │   FastAPI   │  │   Reports   │
       │  Dashboard  │  │     API     │  │ PDF / CSV   │
       └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 🗂️ Project Structure

A recommended repository structure is:

```bash
nifty100/
│
├── src/
│   ├── api/
│   │   ├── main.py
│   │   └── routers/
│   │       ├── companies.py
│   │       ├── screener.py
│   │       ├── sectors.py
│   │       ├── peers.py
│   │       ├── valuation.py
│   │       ├── portfolio.py
│   │       └── documents.py
│   │
│   ├── Analytics/
│   │
│   └── dashboard/
│       ├── app.py
│       └── __init__.py
│
├── tests/
│   ├── etl/
│   ├── kpi/
│   ├── dq/
│   └── api/
│
├── scripts/
│
├── docs/
│   ├── openapi.json
│   ├── postman_collection.json
│   └── analyst_guide.pdf
│
├── output/
│   ├── cluster_labels.csv
│   ├── cluster_profile.csv
│   ├── outlier_report.csv
│   └── portfolio_stats.csv
│
├── reports/
│   ├── elbow_plot.png
│   └── correlation_heatmap.png
│
├── README.md
├── requirements.txt
└── .gitignore
```

The exact files included in the public GitHub repository can be adjusted depending on which generated outputs and datasets you want to publish.

---

## 🛠️ Technology Stack

| Area | Technology |
| :--- | :--- |
| **Programming** | Python |
| **Data Processing** | Pandas, NumPy |
| **Database** | SQLite |
| **API** | FastAPI |
| **Dashboard** | Streamlit |
| **Machine Learning** | Scikit-learn |
| **Testing** | Pytest |
| **Documentation** | Markdown / OpenAPI |
| **Reporting** | PDF / CSV / Excel outputs |
| **Development** | VS Code |
| **Version Control** | Git / GitHub |

---

## 🗄️ Database

The platform uses SQLite as its analytical database.
Main data areas include:
- `companies`
- `financial_ratios`
- `balancesheet`
- `cashflow`
- `analysis`
- `peer_groups`
- `valuation`

The database layer supports:
- Company master data
- Historical financial information
- Financial ratios
- Derived analytical metrics
- Peer relationships
- Valuation-related information

### Database Location
For local development:
`db/nifty100.db`

The database should generally not be committed to GitHub if it is large or generated from source data. Instead, document the database-generation process or provide a smaller sample database when appropriate.

---

## 📊 Key Financial Metrics

### Revenue CAGR
$$\text{CAGR} = \left(\frac{\text{Ending Value}}{\text{Beginning Value}}\right)^{\frac{1}{\text{Number of Years}}} - 1$$

### Profitability
The platform uses measures such as:
- Net Profit Margin
- ROE
- ROCE

### Market / Risk Analytics
Depending on the analytical module:
- Stock Price CAGR
- Sharpe Ratio
- Sortino Ratio
- Alpha
- Beta
- Drawdown

When interpreting a metric, always consider:
- Reporting period
- Units
- Missing values
- Peer population
- Benchmark
- Calculation methodology

---

## 🔬 Data Quality Framework

Data quality checks cover:

### Completeness
Checks for:
- Missing records
- Missing financial years
- Incomplete company histories
- Missing analytical fields

### Uniqueness
Checks for:
- Duplicate records
- Duplicate company entries
- Duplicate financial observations

### Referential Integrity
SQLite foreign-key validation is used to identify broken relationships:
```sql
PRAGMA foreign_key_check;
```

### Validity
Checks for:
- Invalid values
- Incorrect formats
- Incorrect data types
- Unexpected values

### Anomaly Detection
Unusual observations are reported separately so that analysts can investigate them before deciding whether they represent errors or legitimate financial characteristics.

---

## 🧪 Testing

The project includes automated tests covering areas such as:
```bash
tests/
├── etl/
├── kpi/
├── dq/
└── api/
```

Testing areas include:
- ETL normalization
- Data loading
- Financial-ratio calculations
- Data-quality rules
- API health
- Company endpoints
- Screener endpoints
- Sector endpoints

Run the complete test suite:
```bash
pytest
```

For a more detailed output:
```bash
pytest -v
```

---

## ⚙️ Installation

1. **Clone the repository:**
   ```bash
   git clone <YOUR_GITHUB_REPOSITORY_URL>
   cd nifty100
   ```

2. **Create a virtual environment:**
   - Windows:
     ```bash
     python -m venv .venv
     ```

3. **Activate the environment:**
   - PowerShell:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Running the Dashboard

From the project root:
```bash
streamlit run src/dashboard/app.py
```
The dashboard will start locally and provide the interactive analytical interface.

---

## 🚀 Running the FastAPI Server

From the project root:
```bash
python -m uvicorn src.api.main:app --reload
```

- **API Base URL:** `http://127.0.0.1:8000`
- **Health Check:** `http://127.0.0.1:8000/api/v1/health`
- **Interactive Documentation:** `http://127.0.0.1:8000/docs`

---

## 📈 Analytical Workflow

A typical analyst workflow is:

```
1. Open Dashboard
       ↓
2. Select Company / Screener
       ↓
3. Review Financial History
       ↓
4. Analyze Ratios
       ↓
5. Compare with Peers
       ↓
6. Review Sector / Trend Context
       ↓
7. Investigate Outliers
       ↓
8. Review Portfolio / Risk Metrics
       ↓
9. Generate Report
       ↓
10. Validate Result
```

---

## 📄 Sample Outputs

Selected analytical outputs can include:

| Output | Purpose |
| :--- | :--- |
| `cluster_labels.csv` | Company-to-cluster mapping |
| `cluster_profile.csv` | Characteristics of clusters |
| `outlier_report.csv` | Identified unusual observations |
| `portfolio_stats.csv` | Portfolio-level statistics |
| `elbow_plot.png` | Clustering diagnostic |
| `correlation_heatmap.png` | Feature correlation analysis |
| `openapi.json` | API specification |
| `postman_collection.json` | API testing collection |
| `analyst_guide.pdf` | Analyst documentation |

---

## 🔌 API Architecture

The API uses a modular router structure:

```bash
src/api/
│
├── main.py
│
└── routers/
    ├── companies.py
    ├── screener.py
    ├── sectors.py
    ├── peers.py
    ├── valuation.py
    ├── portfolio.py
    └── documents.py
```

This structure keeps business functionality separated into domain-specific API modules.

---

## 🔍 Reproducibility

The project is designed around reproducible analytics. For a reproducible analysis, record:

```
Company ──► Reporting Period ──► Data Source ──► Metric Definition ──► Filter Parameters ──► Peer Group ──► Benchmark ──► Calculation Method ──► Output File
```

This makes it easier to audit and reproduce analytical results.

---

## 📋 Validation & Acceptance

The project includes acceptance checks covering:
- Company-data coverage
- Historical financial coverage
- Database integrity
- Financial-ratio coverage
- CAGR validation
- ROE validation
- Screener output
- Dashboard performance
- API health
- Peer-percentile coverage
- Cluster-label coverage
- Pros/cons coverage
- PDF report generation
- Automated testing
- Data-quality failure reporting
- Analyst documentation

The acceptance process should verify both:
1. **The output exists**
2. **The output is correct, complete, and reproducible**

---

## 🔐 GitHub / Security

Do not commit sensitive or unnecessary local files.

Recommended `.gitignore` entries include:
```text
.venv/
__pycache__/
*.pyc
.env
*.db
*.sqlite
*.sqlite3
.vscode/
.pytest_cache/
.ipynb_checkpoints/
```

Before pushing to GitHub:
```bash
git status
```
Review the files carefully, then run:
```bash
git add .
git commit -m "Initial project release"
git push
```

---

## 🧑‍‍💻 Author

**Ravi Roshan Kumar**  
*M.Sc. Mathematics & Computing*  
**IIT (ISM) Dhanbad**

### Areas of Interest:
- Data Analytics
- Financial Analytics
- Machine Learning
- Python
- SQL
- Business Intelligence
- AI / Data Science

---

## ⭐ Project Highlights

```
End-to-End Financial Analytics
              +
   Data Quality & Validation
              +
    Financial KPI Engine
              +
       Stock Screener
              +
       Peer Analytics
              +
      Machine Learning
              +
          FastAPI
              +
    Streamlit Dashboard
              +
     Automated Reports
```

---

## 📌 Future Enhancements

Potential future improvements include:
- Automated data-refresh pipelines
- Additional valuation models
- More advanced portfolio optimization
- Automated alerting
- Expanded benchmark analysis
- Enhanced dashboard interactivity
- Authentication and API access control
- Cloud deployment
- Scheduled report generation
- More comprehensive data lineage tracking