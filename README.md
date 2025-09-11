# Medimind

Medimind is a Django-based healthcare management system designed to streamline appointments, medication adherence, notifications, and hospital management.

## Project Structure

- **adherence/**: Handles medication adherence tracking.
- **appointments/**: Manages patient appointments.
- **hospitals/**: Hospital-related data and management.
- **medications/**: Medication information and management.
- **notifications/**: Notification system for reminders and alerts.
- **users/**: User authentication and profile management.
- **medimind/**: Project configuration and settings.

## Getting Started

### Prerequisites

- Python 3.x
- Docker (optional)
- pip

### Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd medimind
    ```

2. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Apply migrations:
    ```sh
    python manage.py migrate
    ```

4. Run the development server:
    ```sh
    python manage.py runserver
    ```

### Using Docker

Build and run the project with Docker:
```sh
docker build -t medimind .
docker run -p 8000:8000 medimind
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE)