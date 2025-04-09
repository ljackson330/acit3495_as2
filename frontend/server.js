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
    console.log(
      "Attempting to contact auth-service at http://auth-service:8001/login"
    );
    const response = await axios.post(
      "http://auth-service:8001/login",
      {
        username,
        password,
      },
      {
        timeout: 5000, // Add timeout to prevent hanging
      }
    );
    console.log("Received response from auth-service:", response.status);
    const token = response.data.access_token;
    res.json({ token });
  } catch (error) {
    console.error("Auth service error:", error.message);
    if (error.response) {
      // The request was made and the server responded with a status code
      console.error("Auth service response data:", error.response.data);
      console.error("Auth service status:", error.response.status);
      console.error("Auth service headers:", error.response.headers);
    } else if (error.request) {
      // The request was made but no response was received
      console.error(
        "No response received from auth service. Request:",
        error.request
      );
    } else {
      // Something happened in setting up the request
      console.error("Error setting up request:", error.message);
    }
    res.status(400).json({
      message: "Authentication failed",
      error: error.message,
      details: error.response?.data || "No response from auth service",
    });
  }
});

// Route to access a protected resource
app.get("/protected", async (req, res) => {
  const token = req.headers["authorization"].split(" ")[1];
  try {
    const response = await axios.get("http://auth-service:8001/protected", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    res.json(response.data);
  } catch (error) {
    res.status(401).json({ message: "Unauthorized", error: error.message });
  }
});

// Proxy routes for backend services
app.post("/api/insert-float", async (req, res) => {
  const token = req.headers["authorization"].split(" ")[1];
  try {
    const response = await axios.post(
      "http://backend:8002/insert-float/",
      req.body,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    res.json(response.data);
  } catch (error) {
    res
      .status(error.response?.status || 500)
      .json({ message: "Error inserting float", error: error.message });
  }
});

app.get("/api/get-stats", async (req, res) => {
  const token = req.headers["authorization"].split(" ")[1];
  try {
    const response = await axios.get("http://backend:8002/get-stats/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    res.json(response.data);
  } catch (error) {
    res
      .status(error.response?.status || 500)
      .json({ message: "Error getting stats", error: error.message });
  }
});

app.get("/api/run-analytics", async (req, res) => {
  const token = req.headers["authorization"].split(" ")[1];
  try {
    const response = await axios.get("http://analytics:8003/run-analytics/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    res.json(response.data);
  } catch (error) {
    res
      .status(error.response?.status || 500)
      .json({ message: "Error running analytics", error: error.message });
  }
});

// Start the server
app.listen(port, "0.0.0.0", () => {
  console.log(`Frontend server running at http://0.0.0.0:${port}`);
});
