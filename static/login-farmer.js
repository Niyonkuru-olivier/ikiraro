function validateForm() {
    const telephone = document.getElementById('telephone').value.trim();
    //const nid = document.getElementById('nid').value.trim();
    const email = document.getElementById('email').value.trim();
    const errorMessage = document.getElementById('error-message');

    // Clear previous error messages
    errorMessage.textContent = '';

    // Validate telephone number (must be 10 digits)
    const telephonePattern = /^[0-9]{10}$/;
    if (!telephonePattern.test(telephone)) {
        errorMessage.textContent = 'Please enter a valid telephone number (10 digits).';
        return false;
    }

    // Validate National ID/Passport (must be exactly 16 digits and numeric)
    /*const nidPattern = /^[0-9]{16}$/;
    if (!nidPattern.test(nid)) {
        errorMessage.textContent = 'National ID/Passport must be exactly 16 digits.';
        return false;
    }*/

    // Validate email format using regex
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email)) {
        errorMessage.textContent = 'Please enter a valid email address.';
        return false;
    }

    // If all validations pass, redirect to the "service.html"
    window.location.href = "OTP-farmer.html";
    return false;  // Prevent actual form submission since you are redirecting
}
