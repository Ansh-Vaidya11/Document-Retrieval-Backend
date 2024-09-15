# Document Retrieval Backend

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [System Architecture](#system-architecture)
4. [Prerequisites](#prerequisites)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Running the Application](#running-the-application)
   - [Locally](#locally)
   - [Using Docker](#using-docker)
8. [API Documentation](#api-documentation)
9. [Data Model](#data-model)
10. [Background Processes](#background-processes)
11. [Caching Strategy](#caching-strategy)
12. [Rate Limiting](#rate-limiting)
13. [Logging and Monitoring](#logging-and-monitoring)
14. [Error Handling](#error-handling)
15. [Security Considerations](#security-considerations)
16. [Performance Optimization](#performance-optimization)
17. [Testing](#testing)
18. [Deployment](#deployment)
19. [Maintenance and Updating](#maintenance-and-updating)
20. [Troubleshooting](#troubleshooting)
21. [Contributing](#contributing)
22. [License](#license)
23. [Contact Information](#contact-information)

## Introduction

The Document Retrieval Backend is a sophisticated system designed to provide context for Large Language Models (LLMs) by efficiently storing, retrieving, and processing documents. This system incorporates advanced features such as semantic search, real-time web scraping, and intelligent caching to deliver high-performance document retrieval capabilities.

## Features

- Document storage and retrieval using MongoDB
- Semantic search using SentenceTransformer models
- Redis-based caching for faster query responses
- Real-time web scraping of news articles
- Rate limiting to prevent API abuse
- Comprehensive logging and error handling
- Dockerized application for easy deployment
- Scalable architecture suitable for production environments

## System Architecture

The system is built using the following components:

- **Web Server**: Flask
- **Database**: MongoDB
- **Cache**: Redis
- **Search Engine**: SentenceTransformer
- **Web Scraping**: BeautifulSoup4
- **Rate Limiting**: Flask-Limiter
- **Containerization**: Docker

![System Architecture Diagram](https://your-image-hosting-service.com/system_architecture.png)

## Prerequisites

- Python 3.7+
- MongoDB 4.4+
- Redis 6.0+
- Docker 20.10+ (for containerized deployment)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/document-retrieval-backend.git
   cd document-retrieval-backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the root directory with the following content:
   ```
   MONGO_URI=mongodb://username:password@host:port/database
   REDIS_HOST=your_redis_host
   REDIS_PORT=6379
   PORT=5000
   SCRAPE_INTERVAL=3600
   LOG_LEVEL=INFO
   ```

2. Adjust the values according to your environment.

## Running the Application

### Locally

To run the application locally:

```
python app.py
```

The server will start on `http://localhost:5000`.

### Using Docker

1. Build the Docker image:
   ```
   docker build -t document-retrieval-backend .
   ```

2. Run the container:
   ```
   docker run -p 5000:5000 --env-file .env document-retrieval-backend
   ```

## API Documentation

### GET /health

Returns the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "message": "The system is operational. Random number: 42"
}
```

### POST /search

Performs a semantic search on the document database.

**Request Body:**
```json
{
  "text": "Your search query",
  "top_k": 5,
  "threshold": 0.5,
  "user_id": "unique_user_identifier"
}
```

**Parameters:**
- `text` (required): The search query
- `top_k` (optional, default: 5): Number of top results to return
- `threshold` (optional, default: 0.5): Minimum similarity score for results
- `user_id` (required): Unique identifier for the user

**Response:**
```json
{
  "results": [
    {
      "title": "Document Title",
      "similarity": 0.85
    }
  ],
  "inference_time": 0.1234
}
```

**Error Responses:**
- 400 Bad Request: If `user_id` is missing
- 429 Too Many Requests: If rate limit is exceeded
- 500 Internal Server Error: For unexpected server errors

## Data Model

### MongoDB Collections

1. **documents**
   - `_id`: ObjectId
   - `title`: String
   - `content`: String
   - `encoding`: Array of floats
   - `created_at`: DateTime
   - `updated_at`: DateTime

2. **users**
   - `_id`: String (user_id)
   - `request_count`: Integer
   - `last_request`: DateTime

## Background Processes

### Web Scraping

The application runs a background thread that scrapes news articles from Hacker News every hour. This process:

1. Fetches the top 5 stories from Hacker News
2. Extracts the content from each story's URL
3. Encodes the content using the SentenceTransformer model
4. Stores the encoded documents in MongoDB

The scraping interval can be adjusted using the `SCRAPE_INTERVAL` environment variable.

## Caching Strategy

Redis is used for caching search results to improve response times for repeated queries. The caching strategy involves:

1. Using a composite key: `{query}:{top_k}:{threshold}`
2. Storing serialized search results
3. Setting an expiration time of 1 hour for each cache entry

Cache hits are logged for monitoring cache effectiveness.

## Rate Limiting

Rate limiting is implemented to prevent API abuse. The current limits are:

- 5 requests per minute per user

When a user exceeds this limit, the API returns a 429 (Too Many Requests) status code. The rate limit is based on the `user_id` provided in the request.

## Logging and Monitoring

The application uses Python's built-in `logging` module with a `RotatingFileHandler`. Logs are stored in `app.log` with a maximum size of 10,000 bytes and one backup.

Log levels can be adjusted using the `LOG_LEVEL` environment variable.

Key events that are logged include:
- API requests and responses
- Cache hits and misses
- Background scraping activities
- Errors and exceptions

For production environments, consider integrating with a log aggregation service like ELK Stack or Splunk.

## Error Handling

The application includes a global error handler to catch and log any unexpected exceptions. These are returned to the client as a 500 Internal Server Error with a generic error message to avoid exposing sensitive information.

Custom error handling is implemented for common scenarios like missing parameters or rate limit exceeded.

## Security Considerations

1. Use HTTPS in production environments
2. Implement proper authentication and authorization mechanisms
3. Regularly update dependencies to patch known vulnerabilities
4. Use environment variables for sensitive configuration (as implemented)
5. Implement input validation and sanitization for all API inputs

## Performance Optimization

1. Use indexing in MongoDB for faster queries
2. Implement database connection pooling
3. Consider using a load balancer for horizontal scaling
4. Optimize the SentenceTransformer model or consider using quantized versions for faster inference

## Testing

To run the test suite:

```
pytest tests/
```

Ensure you have a test database set up and configured in your `.env.test` file.

## Deployment

For production deployment:

1. Set up a reverse proxy (e.g., Nginx) in front of the application
2. Use a process manager like Gunicorn to manage the Flask application
3. Set up monitoring and alerting (e.g., Prometheus and Grafana)
4. Use a container orchestration platform like Kubernetes for managing Docker containers

## Maintenance and Updating

1. Regularly update dependencies:
   ```
   pip install --upgrade -r requirements.txt
   ```

2. Monitor the application logs for errors and performance issues
3. Periodically review and optimize database indices
4. Keep the SentenceTransformer model up-to-date with the latest versions

## Troubleshooting

Common issues and their solutions:

1. **Connection errors to MongoDB or Redis**: Check network connectivity and credentials
2. **Slow search performance**: Review database indices and consider scaling resources
3. **High memory usage**: Monitor the SentenceTransformer model memory footprint and consider using a smaller model if necessary

## Contributing

We welcome contributions to the Document Retrieval Backend project! Please follow these steps:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes and write tests if applicable
4. Submit a pull request with a clear description of your changes

Please adhere to the project's coding standards and include appropriate documentation.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
