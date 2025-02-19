const express = require("express");
const path = require("path");
const axios = require("axios");
const app = express();
const port = 3000;

// Middleware to parse JSON request bodies
app.use(express.json());

// Serve static files (login page, dashboard page, etc.)
app.use(express.static(path.join(__dirname, "public")));

// Route to handle login and get the JWT token
app.post("/login", async (req, res) => {
  console.log("Sending login request to auth-service");
  const { username, password } = req.body;
  try {
    // Send a request to the Python authentication service to get the token
    const response = await axios.post("http://auth-service:8001/login", {
      username,
      password,
    });
    const token = response.data.access_token;

    // Return the token to the client
    res.json({ token });
  } catch (error) {
    res.status(400).json({ message: "Authentication failed", error: error.message });
  }
});

// Route to access a protected resource
app.get("/protected", async (req, res) => {
  const token = req.headers["authorization"].split(" ")[1]; // Extract token from the header

  try {
    // Send a request to the Python service with the token to access protected route
    const response = await axios.get("http://auth-service:8001/protected", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    res.json(response.data); // Send back the protected resource
  } catch (error) {
    res.status(401).json({ message: "Unauthorized", error: error.message });
  }
});

// Function to delay execution for a certain amount of time
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Directly sending a test POST request to the backend after a delay
const sendTestRequest = async () => {
  const floatValue = 3.14; // The float value you want to send

  try {
    // Wait for 10 seconds before sending the request
    await delay(10000);

    const response = await axios.post("http://backend:8002/insert-float/", {
      value: floatValue,
    }, {
      headers: {
        "Content-Type": "application/json",  // Ensure the correct content type
        // You can add any other headers here if needed, like Authorization
      }
    });

    console.log("Backend response:", response.data);
  } catch (error) {
    console.error("Error sending request:", error.message);
  }
};

// Call the function to send the request
sendTestRequest();

// Start the server
app.listen(port, () => {
  console.log(`Frontend server running at http://localhost:${port}`);
});
