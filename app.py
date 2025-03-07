from flask import Flask, render_template, request, session
import random
import matplotlib.pyplot as plt
import io
import base64
import os
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generates a random 24-byte key

# Directory containing JSON files
PROJECTS_DIR = 'projects'

def load_questions(selected_files, proficiency, num_questions=20):
    questions = []
    questions_per_file = max(1, num_questions // len(selected_files))  # Prevent zero division error
    additional_questions_needed = num_questions % len(selected_files)

    for filename in selected_files:
        filepath = os.path.join(PROJECTS_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                file_questions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Error: Unable to load {filename}. Skipping...")
            continue

        # Filter questions based on proficiency
        if proficiency <= 3:
            filtered_questions = [q for q in file_questions if q.get('difficulty', 'Basic') == 'Basic']
        elif proficiency <= 6:
            basic_questions = [q for q in file_questions if q.get('difficulty', 'Basic') == 'Basic']
            intermediate_questions = [q for q in file_questions if q.get('difficulty', 'Basic') == 'Intermediate']
            filtered_questions = basic_questions + intermediate_questions
        else:
            filtered_questions = [q for q in file_questions if q.get('difficulty', 'Basic') in ['Intermediate', 'Advanced']]

        # Ensure enough questions are available
        if len(filtered_questions) < questions_per_file:
            selected_questions = filtered_questions
        else:
            selected_questions = random.sample(filtered_questions, questions_per_file)

        for q in selected_questions:
            q["language"] = filename.split('.')[0]  # Add language info to each question
        questions.extend(selected_questions)

    # Handle additional questions if needed
    additional_questions = []
    for filename in selected_files:
        if additional_questions_needed <= 0:
            break
        filepath = os.path.join(PROJECTS_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                file_questions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            continue

        remaining_questions = [q for q in file_questions if q not in questions]
        if proficiency <= 3:
            remaining_filtered_questions = [q for q in remaining_questions if q.get('difficulty', 'Basic') == 'Basic']
        elif proficiency <= 6:
            basic_questions = [q for q in remaining_questions if q.get('difficulty', 'Basic') == 'Basic']
            intermediate_questions = [q for q in remaining_questions if q.get('difficulty', 'Basic') == 'Intermediate']
            remaining_filtered_questions = basic_questions + intermediate_questions
        else:
            remaining_filtered_questions = [q for q in remaining_questions if q.get('difficulty', 'Basic') in ['Intermediate', 'Advanced']]

        additional_questions_selected = random.sample(remaining_filtered_questions, min(len(remaining_filtered_questions), additional_questions_needed))
        for q in additional_questions_selected:
            q["language"] = filename.split('.')[0]  # Add language info to each question
        additional_questions.extend(additional_questions_selected)
        additional_questions_needed -= len(additional_questions_selected)

    questions.extend(additional_questions)
    return questions

@app.route('/')
def home():
    languages = ["Java", "Python", "CPP", "C", "JavaScript", "HTML", "CSS"]
    return render_template('home.html', languages=languages)

@app.route('/quiz', methods=['POST'])
def quiz():
    selected_languages = request.form.getlist('languages')
    proficiency = int(request.form.get('proficiency', 3))  # Default to 3 if missing
    selected_projects = [f"{lang.lower()}.json" for lang in selected_languages]

    questions = load_questions(selected_projects, proficiency)
    session['questions'] = questions  # Store questions in session

    return render_template('quiz.html', questions=questions)

@app.route('/result', methods=['POST'])
def result():
    questions = session.get('questions', [])
    score = 0
    incorrect_answers = []
    total_questions = len(questions)

    for idx, question in enumerate(questions):
        user_answer = request.form.get(f'question-{idx}')
        if user_answer == question['answer']:
            score += 1
        else:
            incorrect_answers.append({
                "question": question['question'],
                "user_answer": user_answer,
                "correct_answer": question['answer'],
                "topic": question['topic'],
                "language": question['language']
            })

    incorrect_count_by_language = {}
    for answer in incorrect_answers:
        language = answer['language']
        incorrect_count_by_language[language] = incorrect_count_by_language.get(language, 0) + 1

    show_visualize = 'visualize' in request.form

    if show_visualize and incorrect_answers:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))

        languages = list(incorrect_count_by_language.keys())
        counts = list(incorrect_count_by_language.values())
        colors = plt.cm.Paired(range(len(languages)))
        explode = [0.1] * len(languages)

        ax1.pie(counts, explode=explode, labels=languages, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
        ax1.axis('equal')
        ax1.set_title('Incorrect Answers by Language')

        ax2.bar(languages, counts, color=colors)
        ax2.set_title('Incorrect Answers by Language')
        ax2.set_xlabel('Language')
        ax2.set_ylabel('Number of Incorrect Answers')

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()

        return render_template('result.html', score=score, total_questions=total_questions, incorrect_answers=incorrect_answers, image_base64=image_base64)

    return render_template('result.html', score=score, total_questions=total_questions, incorrect_answers=incorrect_answers)

# Pass enumerate to Jinja2 environment
@app.context_processor
def utility_processor():
    return dict(enumerate=enumerate)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # Fixed deployment issues
