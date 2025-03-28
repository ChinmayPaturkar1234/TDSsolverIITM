document.addEventListener('DOMContentLoaded', function() {
    const questionForm = document.getElementById('question-form');
    const resultSection = document.getElementById('result-section');
    const errorSection = document.getElementById('error-section');
    const loadingSection = document.getElementById('loading-section');
    const answerText = document.getElementById('answer-text');
    const errorText = document.getElementById('error-text');
    const copyButton = document.getElementById('copy-button');

    // Form submission handler
    questionForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading indicator and hide other sections
        loadingSection.classList.remove('d-none');
        resultSection.classList.add('d-none');
        errorSection.classList.add('d-none');
        
        // Get form data
        const formData = new FormData(questionForm);
        
        try {
            // Send request to API
            const response = await fetch('/api/', {
                method: 'POST',
                body: formData
            });
            
            // Parse JSON response
            const data = await response.json();
            
            // Hide loading indicator
            loadingSection.classList.add('d-none');
            
            if (response.ok) {
                // Show result section
                answerText.textContent = data.answer;
                resultSection.classList.remove('d-none');
            } else {
                // Show error message
                errorText.textContent = data.error || 'An unknown error occurred.';
                errorSection.classList.remove('d-none');
            }
        } catch (error) {
            // Hide loading indicator and show error
            loadingSection.classList.add('d-none');
            errorText.textContent = 'Network error. Please try again.';
            errorSection.classList.remove('d-none');
            console.error('Error:', error);
        }
    });
    
    // Copy to clipboard functionality
    copyButton.addEventListener('click', function() {
        const text = answerText.textContent;
        navigator.clipboard.writeText(text).then(
            function() {
                // Temporarily change button text to indicate success
                const originalText = copyButton.textContent;
                copyButton.textContent = 'Copied!';
                copyButton.classList.replace('btn-secondary', 'btn-success');
                
                // Reset button after 2 seconds
                setTimeout(function() {
                    copyButton.textContent = originalText;
                    copyButton.classList.replace('btn-success', 'btn-secondary');
                }, 2000);
            },
            function(err) {
                console.error('Could not copy text: ', err);
                errorText.textContent = 'Failed to copy to clipboard.';
                errorSection.classList.remove('d-none');
            }
        );
    });
});
