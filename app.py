import os
import math
import glob
import json
import pickle

import numpy as np
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, g, send_from_directory
from datetime import datetime, timedelta, timezone

CACHE = {}
COURSE_DATA = {
    "Undergraduate": {
        "bca": {"name": "BCA", "semesters": ["I", "II", "III", "IV", "V", "VI"]},
        "bcom": {"name": "B.Com", "semesters": ["I", "II", "III", "IV", "V", "VI"]},
        "bba": {"name": "BBA", "semesters": ["I", "II", "III", "IV", "V", "VI"]},
        "b-pharm": {"name": "B.Pharm", "semesters": ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]},
        "b-pharm-l": {"name": "B.Pharm L", "semesters": ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]},
        "d-pharm": {"name": "D.Pharm", "semesters": ["I", "II"]},
        "bsc-cbz": {"name": "B.Sc. CBZ", "semesters": ["I", "II", "III", "IV", "V", "VI"]},
        "bsc-czbt": {"name": "B.Sc. CZBT", "semesters": ["I", "II", "III", "IV", "V", "VI"]},
        "bsc-pcm": {"name": "B.Sc. PCM", "semesters": ["I", "II", "III", "IV", "V", "VI"]},
        "bsc-pmcs": {"name": "B.Sc. PMCS", "semesters": ["I", "II", "III", "IV", "V", "VI"]},
        "bpt": {"name": "BPT", "semesters": ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]},
        "btech-cs": {"name": "B.Tech CS", "semesters": ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]},
        "btech-ai": {"name": "B.Tech AI", "semesters": ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]}
    },
    "Postgraduate": {
        "mca": {"name": "MCA", "semesters": ["I", "II", "III", "IV"]},
        "mba": {"name": "MBA", "semesters": ["I", "II", "III", "IV"]},
        "msc-bt": {"name": "M.Sc. BT", "semesters": ["I", "II", "III", "IV"]},
        "msc-bot": {"name": "M.Sc. BOT", "semesters": ["I", "II", "III", "IV"]},
        "msc-chem": {"name": "M.Sc. CHEM", "semesters": ["I", "II", "III", "IV"]},
        "msc-mathematics": {"name": "M.Sc. Mathematics", "semesters": ["I", "II", "III", "IV"]},
        "msc-phy": {"name": "M.Sc. PHY", "semesters": ["I", "II", "III", "IV"]},
        "msc-zoo": {"name": "M.Sc. ZOO", "semesters": ["I", "II", "III", "IV"]}
    }
}

app = Flask(__name__)
app.secret_key = "0112358132134"

@app.before_request
def capture_ip():
    g.client_ip = get_client_ip()
    print(f"Client IP: {g.client_ip}")

@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/')
def index():
    course_data_json = json.dumps(COURSE_DATA)
    return render_template('selection.html', course_data_json=course_data_json)

@app.route('/results')
def redirect_to_dashboard():
    course = request.args.get('course')
    semester = request.args.get('semester')

    session['allowed'] = {
        'course': course,
        'semester': semester,
        'expires': (datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp()
    }

    return redirect(url_for('dashboard', course_name=course, semester=semester))

@app.route('/course/<course_name>/semester/<semester>')
def dashboard(course_name, semester):
    check = verify_access(course_name, semester)
    if check:
        return check
    _, _, display_name, _, _, _, _, _ = load_and_process_data(course_name, semester)
    if not display_name:
        return render_template('not-found.html'), 404
    return render_template('dashboard.html', course = course_name, semester = semester, display_name = display_name)

@app.route('/course/<course_name>/semester/<semester>/all-results')
def all_results(course_name, semester):
    check = verify_access(course_name, semester)
    if check:
        return check
    data, df, display_name, pie_chart_data, _, _, _, _ = load_and_process_data(course_name, semester)
    if not data:
        return "Results file not found", 404

    data_to_display = data
    active_filter = "All"
    filter_status = request.args.get('status')

    if filter_status and not df.empty:
        filtered_roll_nos = set(df.loc[df['result'] == filter_status, 'roll_no'])
        data_to_display = [student for student in data if student['roll_no'] in filtered_roll_nos]
        active_filter = f"'{filter_status}'"

    return render_template('all-results.html', course = course_name, semester = semester, display_name = display_name, data = data_to_display, active_filter_display = active_filter, stats = pie_chart_data)

@app.route('/course/<course_name>/semester/<semester>/top-10')
def top_10(course_name, semester):
    check = verify_access(course_name, semester)
    if check:
        return check
    _, df, display_name, _, _, _, _, top_10_data = load_and_process_data(course_name, semester)
    if df is None or df.empty:
        return "Results file not found", 404
    return render_template('top-10.html', course = course_name, semester = semester, display_name = display_name, top_10_data = top_10_data)

@app.route('/course/<course_name>/semester/<semester>/search')
def search(course_name, semester):
    check = verify_access(course_name, semester)
    if check:
        return check
    data, df, display_name, _, _, _, _, _ = load_and_process_data(course_name, semester)
    if df is None or df.empty:
        return "Results file not found or is empty", 404
    
    search_results = []
    query = request.args.get('query', '').strip()

    if query:
        mask = (df['roll_no'].str.contains(query, case=False)) | (df['name'].str.contains(query.upper()))
        matching_roll_nos = df[mask]['roll_no'].unique()
        search_results = [student for student in data if student['roll_no'] in matching_roll_nos]

    return render_template('search.html', course = course_name, semester = semester, display_name = display_name, search_query = query, search_results = search_results)

@app.route('/course/<course_name>/semester/<semester>/charts')
def charts(course_name, semester):
    check = verify_access(course_name, semester)
    if check:
        return check
    _, df, display_name, pie_chart_data, pass_fail_bar_chart_data, marks_bar_chart_data, histogram_data, _ = load_and_process_data(course_name, semester)
    if df is None or df.empty:
        return "Results file not found", 404
    return render_template('charts.html', course = course_name, semester = semester, display_name = display_name, pie_chart_data = pie_chart_data, pass_fail_bar_chart_data = pass_fail_bar_chart_data, marks_bar_chart_data = marks_bar_chart_data, histogram_data = histogram_data)

def load_and_process_data(course_name, semester):

    file_path, display_name = find_file_and_create_key(course_name, semester)
    if not file_path:
        return None, None, None, {}, {}, {}, {}, {}
    
    cache_key = display_name
    if cache_key in CACHE:
        print(f"🔄LOADING '{display_name}' FROM CACHE...")
        return CACHE[cache_key]

    print(f"✅PROCESSING AND CACHING '{display_name}'")
    data = read_file_data(file_path)
    if not data:
        return None, None, None, {}, {}, {}, {}, {}

    flat_data = convert_to_flat_data(data)
    if not flat_data:
        return data, pd.DataFrame(), display_name, {}, {}, {}, {}, {}

    df = create_and_clean_dataframe(flat_data)
    pie_chart_data = create_pie_chart_data(df)
    pass_fail_bar_chart_data = create_pass_fail_bar_chart_data(df)
    marks_bar_chart_data = create_marks_bar_chart_data(df)
    histogram_data = create_histogram_chart_data(df)
    top_10_data = create_top_10_data(df)

    processed_data = (data, df, display_name, pie_chart_data, pass_fail_bar_chart_data, marks_bar_chart_data, histogram_data, top_10_data)
    CACHE[cache_key] = processed_data
    
    return data, df, display_name, pie_chart_data, pass_fail_bar_chart_data, marks_bar_chart_data, histogram_data, top_10_data

def find_file_and_create_key(course_name, semester):
    roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}
    sem_num = roman_map[semester]
    season = "Summer" if course_name == "d-pharm" or sem_num % 2 == 0 else "Winter"

    folder = os.path.join("results", course_name)
    
    if course_name == "d-pharm":
        pattern = f"{folder}/*_Year_{semester}_Examination_*_{season}_MainATKT"
    else:
        pattern = f"{folder}/*_Semester_{semester}_Examination_*_{season}_MainATKT"
    
    matches = glob.glob(pattern + ".pkl") or glob.glob(pattern + ".json")
    if not matches:
        return None, None
        
    file_path = matches[0]
    year = file_path.split("_Examination_")[1].split("_")[0]
    course_display = course_name.replace("-", " ").upper()
    
    if course_name == "d-pharm":
        display_name = f"{course_display} Year {semester}, Examination {year}, {season} (Main/ATKT)"
    else:
        display_name = f"{course_display} Semester {semester}, Examination {year}, {season} (Main/ATKT)"

    return file_path, display_name

def read_file_data(file_path):

    if file_path.endswith(".pkl"):
        with open(file_path, "rb") as f:
            print(f"Reading PKL: {file_path}")
            data = pickle.load(f)
    elif file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            print(f"Reading JSON: {file_path}")
            data = json.load(f)
    else:
        data = None

    return data

def convert_to_flat_data(data):

    flat_data = []

    for student in data:
        for subject_code, marks in student['subjects'].items():
            record = {
                'roll_no': student['roll_no'], 'name': student['name'], 'subject_code': subject_code,
                'cia_max': marks['CIA_MAX'], 'cia_obt': marks['CIA_OBT'], 'ese_max': marks['ESE_MAX'],
                'ese_obt': marks['ESE_OBT'], 'total_max': marks['TOTAL_MAX'], 'total_min': marks['TOTAL_MIN'],
                'total_obt': marks['TOTAL_OBT'], 'grand_total': student['grand_total']['TOTAL_OBT'],
                'result': student['result'], 'percentage': student['percentage']
            }
            flat_data.append(record)
    
    return flat_data

def create_and_clean_dataframe(flat_data):

    df = pd.DataFrame(flat_data)

    str_cols = ['roll_no', 'name', 'subject_code', 'result']
    for col in str_cols:
        df[col] = df[col].astype(str)
    df['name'] = df['name'].str.upper()

    marks_cols = ['cia_obt', 'ese_obt', 'total_obt']
    for col in marks_cols:
        df[col] = df[col].str.strip().replace('AB', '-1').str.replace(r'[^\d-]', '', regex=True)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    int_cols = ['cia_max', 'cia_obt', 'ese_max', 'ese_obt', 'total_max', 'total_min', 'total_obt', 'grand_total']
    for col in int_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    df['percentage'] = pd.to_numeric(df['percentage'], errors='coerce').fillna(0.0).astype(float)

    result_mapping = {'Clear': 'SC', 'Fail': 'NC', 'Clear with Grace': 'SCG'}
    df['result'] = df['result'].replace(result_mapping)

    df['subject_status'] = np.where(df['total_obt'] >= df['total_min'], 'Pass', 'Fail')

    student_summary = df[['roll_no', 'grand_total']].drop_duplicates()
    student_summary['rank'] = student_summary['grand_total'].rank(method='dense', ascending=False).astype(int)
    df = df.merge(student_summary[['roll_no', 'rank']], on='roll_no', how='left')

    cat_cols = ['roll_no', 'subject_code', 'result', 'subject_status']
    for col in cat_cols:
        df[col] = df[col].astype('category')

    return df

def create_pie_chart_data(df):
    student_results = df[['roll_no', 'result']].drop_duplicates()

    total_students = len(student_results)
    result_counts = student_results['result'].value_counts()
    sc_count = result_counts.get('SC', 0)
    nc_count = result_counts.get('NC', 0)
    scg_count = result_counts.get('SCG', 0)

    data = {
        'total_students': total_students,
        'sc_count': sc_count,
        'nc_count': nc_count,
        'scg_count': scg_count,
        'sc_percentage': round((sc_count / total_students) * 100) if total_students > 0 else 0,
        'nc_percentage': round((nc_count / total_students) * 100) if total_students > 0 else 0,
        'scg_percentage': round((scg_count / total_students) * 100) if total_students > 0 else 0,
    }

    return data

def create_pass_fail_bar_chart_data(df):
    subject_counts = pd.crosstab(df['subject_code'], df['subject_status'])
    subject_labels = subject_counts.index.tolist()

    pass_data = subject_counts['Pass'].tolist() if 'Pass' in subject_counts else [0] * len(subject_labels)
    fail_data = subject_counts['Fail'].tolist() if 'Fail' in subject_counts else [0] * len(subject_labels)

    max_val = 0
    if pass_data or fail_data:
        max_val = max(pass_data + fail_data)

    suggested_max = math.ceil(max_val * 1.2)
    if suggested_max == max_val:
        suggested_max += 1

    data = {
        'labels': subject_labels,
        'pass_counts': pass_data,
        'fail_counts': fail_data,
        'suggested_max': suggested_max
    }

    return data

def create_marks_bar_chart_data(df):
    df_present = df[df['total_obt'] != -1].copy()

    subject_marks_stats = df_present.groupby('subject_code', observed=True)['total_obt'].agg(['min', 'max', 'mean'])
    subject_marks_stats['mean'] = subject_marks_stats['mean'].round().astype(int)

    max_mark = subject_marks_stats['max'].max()
    suggested_max = math.ceil(max(100, max_mark * 1.1))

    labels = subject_marks_stats.index.tolist()
    min_data = subject_marks_stats['min'].tolist()
    max_data = subject_marks_stats['max'].tolist()
    avg_data = subject_marks_stats['mean'].tolist()

    data = {
        'labels': labels,
        'min_marks': min_data,
        'max_marks': max_data,
        'avg_marks': avg_data,
        'suggested_max': suggested_max
    }

    return data
    
def create_histogram_chart_data(df):
    student_percentages = df[['roll_no', 'percentage']].drop_duplicates()

    bins = [0, 20, 40, 60, 70, 80, 90, 100]
    labels = ['0-20%', '20-40%', '40-60%', '60-70%', '70-80%', '80-90%', '90-100%']
    student_percentages['range'] = pd.cut(student_percentages['percentage'], bins=bins, labels=labels, right=True, include_lowest=True)
    histogram_counts = student_percentages['range'].value_counts().sort_index()

    max_val = 0
    if not histogram_counts.empty:
        max_val = histogram_counts.max()
    suggested_max = math.ceil(max_val * 1.2) + 1

    data = {
        'labels': histogram_counts.index.tolist(),
        'data': histogram_counts.values.tolist(),
        'suggested_max': suggested_max
    }

    return data

def create_top_10_data(df):
    student_summary = df[['roll_no', 'name', 'grand_total', 'percentage', 'result', 'rank']].drop_duplicates().copy()
    grouped_ranks = student_summary.groupby('rank').agg(
        roll_no=('roll_no', lambda r: '<br>'.join(r)),
        name=('name', lambda n: '<br>'.join(n)),
        grand_total=('grand_total', 'first'),
        percentage=('percentage', 'first'),
        result=('result', lambda n: '<br>'.join(n))
    ).reset_index()

    top_10_ranks_df = grouped_ranks[grouped_ranks['rank'] <= 10]
    top_10_data = top_10_ranks_df.to_dict('records')

    return top_10_data

def get_client_ip():
    ip = request.headers.get("CF-Connecting-IP")
    if ip:
        return ip.strip()

    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()

    return request.remote_addr

def verify_access(course_name, semester):
    data = session.get("allowed")

    if not data:
        return redirect(url_for('index'))

    if datetime.now(timezone.utc).timestamp() > data["expires"]:
        session.pop("allowed", None)
        return redirect(url_for('index'))

    if data["course"] != course_name or data["semester"] != semester:
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()