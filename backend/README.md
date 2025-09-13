# ARTISTING Backend Project Documentation

## Overview

The ARTISTING project is designed to provide a semi-autonomous agent that integrates with the BOE API, focusing on tax and labor queries for artists and cultural professionals. This backend application is built using Django and follows a modular architecture to ensure scalability and maintainability.

## Project Structure

The backend is organized into several apps, each responsible for a specific domain:

- **agent**: Contains the logic for the semi-autonomous agent that interacts with users and processes queries.
- **boe**: Manages interactions with the BOE API, including fetching legal documents and data.
- **tax**: Handles tax-related queries and operations, providing accurate information based on the latest regulations.
- **labor**: Focuses on labor-related queries, offering guidance on labor laws and regulations applicable to artists.

### Directory Structure

```
backend/
├── apps/
│   ├── agent/          # Agent module for user interaction
│   ├── boe/            # BOE API integration
│   ├── tax/            # Tax-related operations
│   └── labor/          # Labor-related operations
├── ovra_backend/       # Main Django application settings and routing
├── requirements.txt    # Python dependencies
├── manage.py           # Command-line utility for Django
└── README.md           # Project documentation
```

## Installation

To set up the backend environment, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd ARTISTING/backend
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run database migrations:
   ```
   python manage.py migrate
   ```

4. Start the development server:
   ```
   python manage.py runserver
   ```

## Usage

The backend provides a RESTful API for the frontend application to interact with. Each app has its own set of endpoints defined in the `urls.py` files. The agent can process user queries related to tax and labor, fetching relevant information from the BOE API as needed.

## Future Development

The architecture is designed to be scalable, allowing for the addition of new features and modules as the project evolves. Future enhancements may include:

- Integration with additional legal resources.
- Improved natural language processing capabilities for the agent.
- User feedback mechanisms to enhance the accuracy of responses.

## Contributing

Contributions to the ARTISTING project are welcome. Please follow the standard Git workflow for submitting changes and improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.