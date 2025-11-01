// Handle form submission
document.getElementById('contactForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission behavior

    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const message = document.getElementById('message').value.trim();
    const responseMessage = document.getElementById('responseMessage');

    // Clear any previous messages
    responseMessage.innerText = '';
    
    // Basic validation
    if (name === '' || email === '' || message === '') {
        responseMessage.innerText = 'Please fill in all fields before submitting.';
        responseMessage.style.color = 'red';
    } else if (!validateEmail(email)) {
        responseMessage.innerText = 'Please enter a valid email address.';
        responseMessage.style.color = 'red';
    } else {
        // If everything is valid, redirect to the "contact-appreciate.html" page
        responseMessage.innerText = 'Thank you for your message! Redirecting...';
        responseMessage.style.color = 'green';

        // Simulate a small delay to show the message before redirecting
        setTimeout(function() {
            window.location.href = 'contact-appreciate.html'; // Redirect to appreciation page
        }, 1500);
    }
});

// Helper function to validate email format
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}
