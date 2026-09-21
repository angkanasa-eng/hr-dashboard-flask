import pandas as pd
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# ตัวแปรเก็บข้อมูลชั่วคราวใน Memory
global_df = None

def process_data(df):
    """ทำความสะอาดและจัดรูปแบบข้อมูล"""
    df.columns = df.columns.str.strip()
    if 'PayRate' in df.columns:
        df['PayRate'] = pd.to_numeric(df['PayRate'], errors='coerce').fillna(0)
    return df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global global_df
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        filename = file.filename.lower()
        if filename.endswith('.tsv') or filename.endswith('.txt'):
            df = pd.read_csv(file, sep='\t')
        else:
            df = pd.read_csv(file)
            
        global_df = process_data(df)
        
        departments = sorted(global_df['Department'].dropna().str.strip().unique().tolist())
        statuses = sorted(global_df['EmploymentStatus'].dropna().str.strip().unique().tolist())
        perf_scores = sorted(global_df['PerformanceScore'].dropna().str.strip().unique().tolist())
        
        return jsonify({
            'success': True,
            'message': f'โหลดข้อมูลสำเร็จทั้งหมด {len(global_df)} รายการ',
            'filters': {
                'departments': departments,
                'statuses': statuses,
                'perf_scores': perf_scores
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    global global_df
    if global_df is None:
        return jsonify({'error': 'ยังไม่มีข้อมูล กรุณาอัปโหลดไฟล์ก่อน'}), 400

    dept = request.args.get('department', 'All')
    status = request.args.get('status', 'All')
    perf = request.args.get('performance', 'All')

    filtered_df = global_df.copy()

    if dept != 'All':
        filtered_df = filtered_df[filtered_df['Department'].str.strip() == dept]
    if status != 'All':
        filtered_df = filtered_df[filtered_df['EmploymentStatus'].str.strip() == status]
    if perf != 'All':
        filtered_df = filtered_df[filtered_df['PerformanceScore'].str.strip() == perf]

    total_emp = len(filtered_df)
    avg_pay = round(filtered_df['PayRate'].mean(), 2) if total_emp > 0 else 0
    active_emp = len(filtered_df[filtered_df['EmploymentStatus'].str.strip() == 'Active'])
    
    dept_dist = filtered_df['Department'].str.strip().value_counts().to_dict()
    perf_dist = filtered_df['PerformanceScore'].str.strip().value_counts().to_dict()

    table_data = filtered_df.head(100).fillna('').to_dict(orient='records')

    return jsonify({
        'kpi': {
            'total': total_emp,
            'avg_pay': avg_pay,
            'active': active_emp
        },
        'charts': {
            'department': dept_dist,
            'performance': perf_dist
        },
        'table': table_data
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)