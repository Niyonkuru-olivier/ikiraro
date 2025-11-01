function validateForm() {
    const telephone = document.getElementById('telephone').value;
    
    const email = document.getElementById('email').value;
    const errorMessage = document.getElementById('error-message');

    // Clear previous error messages
    errorMessage.textContent = '';

    // Validate telephone number (must be 10 digits)
    const telephonePattern = /^[0-9]{10}$/;
    if (!telephonePattern.test(telephone)) {
        errorMessage.textContent = 'Please enter a valid telephone number (10 digits).';
        return false;
    }

    

    // Validate email format using regex
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email)) {
        errorMessage.textContent = 'Please enter a valid email address.';
        return false;
    }

    // If all validations pass, redirect to the "market.html"
    window.location.href = "OTP-dealer.html";
    return false;  // Prevent actual form submission since you are redirecting
}

