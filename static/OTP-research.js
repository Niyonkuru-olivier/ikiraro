document.getElementById('otpForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the form from submitting normally

    const otpInput = document.getElementById('otp').value;
    const messageElement = document.getElementById('message');

    // Here, you would typically send the OTP to your server for verification
    // For demonstration purposes, let's assume the valid OTP is "123456"
    const validOTP = "123456";

    if (otpInput === validOTP) {
        messageElement.textContent = "OTP verified successfully!";
        messageElement.style.color = "green";
        // Redirect or perform next steps after successful verification
    } else {
        messageElement.textContent = "Invalid OTP. Please try again.";
    }
    window.location.href="input.html";
});
