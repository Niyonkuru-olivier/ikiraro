function handleSubmit() {
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const message = document.getElementById('message').value;
    const responseMessage = document.getElementById('responseMessage');

    // Here you can add functionality to send the message to your server

    // For now, just simulate a successful submission
    responseMessage.textContent = "Thank you for contacting us, " + name + "!";
    responseMessage.style.color = 'green';

    // Clear the form fields
    document.getElementById('contactForm').reset();

    return false; // Prevent form submission
}
