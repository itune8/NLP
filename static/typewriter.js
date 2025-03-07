document.addEventListener('DOMContentLoaded', function() {
    const questions = document.querySelectorAll('.question-container');
    let currentIndex = 0;

    function displayNextQuestion() {
        if (currentIndex < questions.length) {
            const questionContainer = questions[currentIndex];
            questionContainer.style.display = 'block'; // Show the current question container
            const questionText = questionContainer.querySelector('.question-text');
            typeWriter(questionText, () => {
                const options = questionContainer.querySelectorAll('.option-text');
                displayOptionsSequentially(options, 0, () => {
                    currentIndex++;
                    displayNextQuestion();
                });
            });
        }
    }

    function displayOptionsSequentially(options, optIndex, callback) {
        if (optIndex < options.length) {
            typeWriter(options[optIndex], () => {
                displayOptionsSequentially(options, optIndex + 1, callback);
            });
        } else {
            callback();
        }
    }

    function typeWriter(element, callback) {
        const text = element.getAttribute('data-text');
        element.innerText = '';
        let i = 0;
        function type() {
            if (i < text.length) {
                element.innerText += text.charAt(i) === ' ' ? '\u00A0' : text.charAt(i); // Ensures spaces are handled correctly
                i++;
                setTimeout(type, 10);
            } else {
                element.style.borderRight = 'none'; // Remove cursor after typing
                if (callback) callback();
            }
        }
        type();
    }

    displayNextQuestion();
});
