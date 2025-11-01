<?php
// Start session to store user info after login
session_start();

// Check if form was submitted
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Get the form data
    $telephone = $_POST['telephone'];
    $email = $_POST['email'];
    $password = $_POST['password'];

    // Basic validation
    if (empty($telephone) || empty($email) || empty($password)) {
        echo "All fields are required!";
    } else {
        // Establish database connection (assuming MySQL here)
        $servername = "localhost"; // Change this if needed
        $username = "root"; // Your DB username
        $dbpassword = ""; // Your DB password
        $dbname = "ikiraro_db"; // Your DB name

        // Create connection
        $conn = new mysqli($servername, $username, $dbpassword, $dbname);

        // Check connection
        if ($conn->connect_error) {
            die("Connection failed: " . $conn->connect_error);
        }

        // Prepare the SQL statement (avoiding SQL injection using prepared statements)
        $stmt = $conn->prepare("SELECT * FROM users WHERE telephone = ? AND email = ?");
        $stmt->bind_param("ss", $telephone, $email);
        $stmt->execute();
        $result = $stmt->get_result();

        // Check if user exists
        if ($result->num_rows > 0) {
            $user = $result->fetch_assoc();
            
            // Verify password (assuming the password is hashed in the database)
            if (password_verify($password, $user['password'])) {
                // Store user information in session
                $_SESSION['user_id'] = $user['id'];
                $_SESSION['user_email'] = $user['email'];
                $_SESSION['user_telephone'] = $user['telephone'];

                // Redirect to the service page
                header("Location: service.html");
                exit();
            } else {
                echo "Invalid password!";
            }
        } else {
            echo "No user found with the provided telephone and email.";
        }

        // Close the statement and connection
        $stmt->close();
        $conn->close();
    }
}
?>