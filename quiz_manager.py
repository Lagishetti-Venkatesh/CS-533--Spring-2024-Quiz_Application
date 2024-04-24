import random
import json
import os
import datetime


def read_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.readlines()
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return []
    except IOError as e:
        print(f"An error occurred while reading the file: {e}")
        return []

def parse_questions(text_in_lines):
    questions = []
    question = None
    expecting_answer = False

    for line in text_in_lines:
        line = line.strip()
        if line.startswith('@Q'):
            question = {'question': '', 'answers': [], 'correct_answer': None}
        elif line.startswith('@ANSWERS'):
            expecting_answer = True
        elif expecting_answer:
            question['correct_answer'] = int(line)
            expecting_answer = False
        elif line.startswith('@E') and question is not None:
            questions.append(question)
            question = None
        elif question is not None and not expecting_answer:
            if question['correct_answer'] is not None:
                question['answers'].append(line)
            else:
                question['question'] += line + ' '

    return questions

def log_asked_questions(file_path, asked_questions):
    try:
        with open(file_path, 'a') as log_file:
            for question in asked_questions:
                log_file.write(f"{question}\n")
    except IOError as e:
        print(f"An error occurred while logging questions: {e}")

def get_asked_questions(file_path):
    try:
        with open(file_path, 'r') as log_file:
            return [line.strip() for line in log_file.readlines()]
    except FileNotFoundError:
        return []


def read_log_file(log_file_path, user_name):
    """Safely reads and returns records from the log file, filtered by user, skipping corrupt lines."""
    records = []
    try:
        with open(log_file_path, 'r') as file:
            for line_number, line in enumerate(file, 1):
                try:
                    record = json.loads(line.strip())
                    if record['user_name'] == user_name:
                        records.append(record)
                except json.JSONDecodeError:
                    pass
    except FileNotFoundError:
        print("Log file not found.")
    return records


def get_asked_questions(log_file_path, user_name):
    """Retrieve a list of previously asked questions for the user."""
    if not os.path.exists(log_file_path):
        return []

    asked_questions = []
    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            try:
                entry = json.loads(line.strip())
                if entry['user_name'] == user_name:
                    asked_questions.extend(entry['questions_asked'])
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")

    return asked_questions

def select_random_questions(questions, num_questions, log_file_path, user_name):
    """Select a set of random questions not previously asked to the user."""
    asked_questions = get_asked_questions(log_file_path, user_name)
    # Filter to get only those questions that have not been asked before
    available_questions = [q for q in questions if q['question'] not in asked_questions]

    # Safely handle the case where there are fewer available questions than requested
    num_to_select = min(num_questions, len(available_questions))
    if num_to_select == 0:
        print("Warning: No available questions left to select. Please update the question bank.")
        return []

    selected_questions = random.sample(available_questions, num_to_select)
    return selected_questions


def write_to_log(log_file_path, user_name, file_path, num_questions, questions_asked, correct_answers, unasked_questions=0, read=False):
    # Ensure the log directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    records = []
    
    if read:
        try:
            found_records = read_log_file(log_file_path)
    
            if len(found_records):
                i = 0
                for record in found_records:
                    if record['user_name'] == user_name:
                        records.append(record)
                        print(f"Quiz Record: {i+1}")
                        i += 1
                if i == 0:
                    print("No records found for user:", user_name)
        except FileNotFoundError:
            print("Log file not found.")
        return records

    else:
        # Include the current timestamp
        current_time = datetime.datetime.utcnow().isoformat()  # You can use .now() if you want local time
        
        record = {
            "user_name": user_name,
            "file_path": file_path,
            "num_questions": num_questions,
            "questions_asked": questions_asked,
            "correct_answers": correct_answers,
            "unasked": unasked_questions,
            "timestamp": current_time  # Adding the timestamp here
        }
        try:
            with open(log_file_path, 'a') as log_file:
                json_record = json.dumps(record)
                log_file.write(json_record + "\n")
        except IOError as e:
            print(f"An error occurred while writing to the log: {e}")


