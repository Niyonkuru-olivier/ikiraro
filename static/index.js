document.getElementById('contact-form').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const message = document.getElementById('message').value;

    // Here you can handle form submission, e.g., send data to your server
    console.log('Form submitted:', { name, email, message });
    
    // Clear the form
    document.getElementById('contact-form').reset();
    alert('Thank you for your message! We will get back to you soon.');
});
