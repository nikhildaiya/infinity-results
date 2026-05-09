# Infinity Results – Student Result Analytics Platform

A user-friendly web application that allows students to view, search, filter, rank, and analyze college examination results with detailed insights and charts — all in one place.

Built to solve the limitation of the official college website, which only shows one student result at a time without analytics or comparisons.

<hr>

## Why This Project Exists

The official college result portal:

* Shows only one student result per search

* Requires repeated form filling

* Provides no overall insights

* Has no filters, rankings, or charts

This project transforms raw result data into meaningful insights that help students understand:

* Overall performance

* Result distribution

* Subject-wise trends

* Rank positions

* Percentage analysis

<hr>

## Key Features

Result Exploration

* View all results of a course & semester on a single page

* Filter results by:

    * Semester Cleared (SC)

    * Semester Cleared with Grace (SCG)

    * Not Cleared (NC)
 
Rankings

* Top 10 students by total marks

* Displays Rank, Roll number, Student name, Total marks, Result status, Percentage & Tied ranks too

Smart Search

* Search students by name or roll number

* Shows all matching results

* Displays a clear message if no result is found

Visual Analytics (Charts)

* Result distribution (SC / SCG / NC)

* Subject-wise pass & fail count

* Subject-wise marks analysis (min / avg / max)

* Percentage range distribution of students

Performance Optimized

* Uses pre-scraped result files

* Loads data from PKL (primary) or JSON (backup)

* In-memory caching to avoid repeated processing

<hr>

## Pages Overview

1️⃣ Selection Page

* Select:

    * Course level (Undergraduate / Postgraduate)

    * Course

    * Semester

* Proceed to dashboard

2️⃣ Dashboard

* Central hub with feature buttons:

    * All Results

    * Top 10 Ranks

    * Charts & Statistics

    * Search Results
 
3️⃣ All Results Page

* Summary table with:

    * SC, SCG, NC counts & percentages

    * Total students

* Filter buttons

* Full results table

4️⃣ Top 10 Page

* Ranked list of top 10 students by marks

5️⃣ Charts Page

* Four analytical charts using Chart.js

6️⃣ Search Page

* Search by name or roll number

* Displays all matching student results

<hr>

## How the System Works

1. User selects course and semester.

2. A temporary session (15 minutes) is created for security.

3. Application:

    * Locates the corresponding result file

    * Loads data from PKL or JSON

    * Flattens nested data for analysis

    * Converts it into a cleaned Pandas DataFrame

4. Data is:

    * Cached in memory

    * Reused across pages (no repeated file reads)

5. Charts, rankings, filters, and search results are generated dynamically.

<hr>

## Data Processing Logic (Behind the Scenes)

* Nested result data → converted into flat structure

* Data cleaning & normalization

* Vectorized calculations using Pandas & NumPy

* Rank calculation using dense ranking

* Subject-wise and student-wise aggregations

* Efficient caching for faster performance

<hr>

## Tech Stack

* Backend: Python, Flask

* Data Processing: Pandas, NumPy

* Visualization: Chart.js

* Frontend: HTML, CSS, Bootstrap

* Storage: PKL (primary), JSON (backup)

* Session Handling: Flask sessions

<hr>

## Project Structure

```
infinity-results/
│── app.py
│── requirements.txt
│
├── templates/
│   ├── selection.html
│   ├── dashboard.html
│   ├── all-results.html
│   ├── top-10.html
│   ├── charts.html
│   ├── search.html
│
├── static/
│   ├── styles/
│   ├── images/
│
└── results/
    ├── bca/
    ├── mca/
    ├── b-pharm/
    └── other courses...
```

<hr>

## Installation & Setup

1️⃣ Clone the Repository

```
git clone https://github.com/nikhildaiya/infinity-results.git
cd infinity-results
```

2️⃣ Install Dependencies

```
pip install -r requirements.txt
```

3️⃣ Run the Application

```
python app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

<hr>

## Data Source

* Result data is sourced from the official college website

* Data is displayed only after official publication

* This application does not modify or manipulate result data

<hr>

## Disclaimer

This project is developed for educational and informational purposes only.

All result data belongs to the respective institution.

<hr>

## Author

Nikhil Daiya

Student Result Analytics & Visualization Platform

<hr>