from flask import Flask, render_template, request, session, redirect, url_for, flash
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from quiz_manager import read_file, parse_questions, select_random_questions, write_to_log, read_log_file

app = Flask(__name__)
app.secret_key = '#800434365'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(),'uploads')
app.config['LOG_FILE_PATH'] = os.path.join(os.getcwd(),'log_files\\app_log_data.json')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt'}

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        session['user_name'] = request.form['name']
        return redirect(url_for('menu'))
    return render_template('home.html')

@app.route('/menu')
def menu():
    if 'user_name' not in session:
        return redirect(url_for('home'))
    return render_template('menu.html')

@app.route('/run_quiz', methods=['GET', 'POST'])
def run_quiz():
    if 'user_name' not in session:
        flash("Please enter your name first.")
        return redirect(url_for('home'))

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            num_questions = int(request.form['num_questions'])
            time_limit = int(request.form['time_limit'])
            session['filepath'] = filepath
            session['num_questions'] = num_questions
            session['time_limit'] = time_limit
            session['start_time'] = datetime.utcnow().isoformat()
            session['current_question_index'] = 0
            session['correct_answers'] = 0
            
            questions = parse_questions(read_file(filepath))
            session['questions'] = select_random_questions(questions, num_questions, app.config['LOG_FILE_PATH'], session['user_name'])
            
            return redirect(url_for('display_question'))
        else:
            flash("Invalid file. Please upload a .txt file.")
            return redirect(url_for('run_quiz'))
    return render_template('run_quiz.html')

@app.route('/view_history')
def view_history():
    if 'user_name' not in session:
        flash("Please login to view history.")
        return redirect(url_for('home'))
    
    user_name = session['user_name']
    history_records = read_log_file(app.config['LOG_FILE_PATH'], user_name)
    
    return render_template('view_history.html', history_records=history_records)

@app.route('/display_question', methods=['GET', 'POST'])
def display_question():
    if 'questions' not in session:
        flash("Start a quiz first.")
        return redirect(url_for('menu'))

    current_index = session.get('current_question_index', 0)
    questions = session.get('questions', [])
    
    if current_index >= len(questions):
        return redirect(url_for('show_results'))

    if request.method == 'POST':
        current_index = session.get('current_question_index', 0)
        user_answer = int(request.form.get('answer'))
        correct_answer = questions[current_index]['correct_answer']
        
        if user_answer == correct_answer:
            session['correct_answers'] += 1
        
        session['current_question_index'] = current_index + 1
        return redirect(url_for('display_question'))
    
    question = questions[current_index]
    time_limit = session.get('time_limit', 0)
    start_time = datetime.fromisoformat(session.get('start_time'))
    elapsed_time = (datetime.utcnow() - start_time).total_seconds()
    remaining_time = max(time_limit - elapsed_time, 0)

    if remaining_time <= 0:
        return redirect(url_for('show_results'))

    return render_template('display_question.html', question=question, question_number=current_index+1, remaining_time=int(remaining_time))

@app.route('/show_results')
def show_results():
    # Placeholder for showing results and cleaning up the session
    # Placeholder for showing results and cleaning up the session
    user_name = session.get('user_name')
    filepath = session.get('filepath')
    num_questions = session.get('num_questions')
    correct_answers = session.get('correct_answers')
    questions_asked = session.get('questions')

    # Log quiz data
    write_to_log(app.config['LOG_FILE_PATH'], user_name, filepath, num_questions, [q['question'] for q in questions_asked], correct_answers)

    # Implement according to your existing logic or preferences
    session.pop('questions', None)
    # More session cleanup as necessary
    return render_template('results.html', correct_answers=session.get('correct_answers'), num_questions=session.get('num_questions'))

@app.route('/exit')
def exit():
    session.clear()  # Clears the session before exiting
    return render_template('exit.html')

#if __name__ == '__main__':
 #   app.run(debug=True)
