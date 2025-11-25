# LinguaTime Project Documentation

## 1. Project Overview

This document provides a comprehensive overview of the LinguaTime project, a Django-based web application designed to connect clients with language interpreters. The platform facilitates the entire process from order creation to interpreter assignment and payment.

The core functionality includes:

*   **User Roles:** The system distinguishes between two main user types: **Clients**, who can post job orders, and **Interpreters**, who can accept and fulfill these orders.
*   **Order Management:** Clients can create detailed orders specifying requirements such as language pairs, location (online or onsite), time, and formality level.
*   **Interpreter Profiles:** Interpreters have profiles showcasing their languages, translation types, and other relevant information.
*   **Availability and Booking:** Interpreters can manage their availability, and the system handles the booking process.
*   **Google Calendar Integration:** The application integrates with Google Calendar to synchronize interpreter availability and bookings, preventing scheduling conflicts.
*   **Authentication:** The platform supports standard email/password registration and login, as well as social authentication using Google.

## 2. Project Structure

The project follows a standard Django layout, with a central `root` project directory and a single `apps` directory containing the core application logic.

```
/
├───.env.example
├───.flake8
├───.gitignore
├───Makefile
├───manage.py
├───pyproject.toml
├───TODO
├───uv.lock
├───apps/
│   ├───models/
│   ├───services/
│   ├───static/
│   ├───templates/
│   └───views/
├───root/
│   ├───settings.py
│   └───urls.py
└───templates/
```

*   **`root/`**: The main Django project directory containing global settings (`settings.py`) and the root URL configuration (`urls.py`).
*   **`apps/`**: This is the primary Django app for the project. It contains all the models, views, forms, and templates related to the application's functionality.
    *   **`apps/models/`**: Defines the database schema through Django models.
    *   **`apps/views/`**: Contains the business logic for handling user requests.
    *   **`apps/services/`**: Includes services for interacting with external APIs, such as the Google Calendar API.
    *   **`apps/static/`**: Static files (CSS, JavaScript, images).
    *   **`apps/templates/`**: Django templates for rendering the user interface.
*   **`templates/`**: Global templates that can be used across the entire project.

## 3. Key Models

The data model is central to the application's functionality. Here is a detailed description of the key models:

### User Management (`apps/models/users.py`)

*   **`User`**: The base user model, inheriting from Django's `AbstractUser`. It uses the email field for authentication instead of a username.
*   **`Interpreter`**: A proxy model of `User` representing an interpreter. It includes additional fields such as gender, availability for trips, and moderation status. It also has relationships with `Language`, `TranslationType`, and `City`.
*   **`Client`**: A proxy model of `User` representing a client.

### Languages and Locations (`apps/models/languages.py`, `apps/models/cities.py`)

*   **`Language`**: Stores a list of languages that interpreters can speak.
*   **`LanguagePair`**: Represents a pair of languages for translation (e.g., English to Spanish).
*   **`TranslationType`**: Defines the types of translation services offered (e.g., simultaneous, consecutive).
*   **`Country`**, **`Region`**, **`City`**: These models create a hierarchical structure for locations, used for onsite interpreting jobs.

### Availability and Bookings (`apps/models/availabilitys.py`, `apps/models/bookings.py`)

*   **`Availability`**: Allows interpreters to specify their available and busy time slots. It includes fields for integrating with Google Calendar.
*   **`Booking`**: Represents the interaction between an order and an interpreter. It tracks the status of an offer (e.g., offered, accepted, declined), the actual hours worked, and the payout for the interpreter.
*   **`Review`**: Allows clients to leave reviews and ratings for interpreters after a job is completed.

### Orders (`apps/models/orders.py`)

*   **`Order`**: This is the central model representing a client's request for an interpreter. It contains all the details of the job, including:
    *   Client who created the order.
    *   Start and end date/time.
    *   Location type (onsite or online).
    *   Required languages and translation types.
    *   Number of interpreters needed.
    *   Order status (e.g., new, searching, assigned, completed).
*   **`OrderInterpreter`**: A through model that links an `Order` to one or more `Interpreter`s who have been assigned to the job.

### Google Integration (`apps/models/google_credentials.py`)

*   **`GoogleCalendarCredentials`**: Stores the OAuth2 credentials for users who have connected their Google Calendar. This allows the application to access their calendar data on their behalf.

## 4. Technologies Used

*   **Backend:** Django
*   **Database:** PostgreSQL
*   **Asynchronous Tasks:** Celery with Redis
*   **Frontend:** Django templates
*   **Authentication:** Django's built-in authentication with Google OAuth2 for social login.
*   **Package Management:** `uv`
*   **Other Key Libraries:**
    *   `django-jazzmin`: For a modern and customizable admin interface.
    *   `django-ckeditor-5`: For rich text editing capabilities.
    *   `django-filter`: To enable filtering of querysets based on user input.
    *   `location_field`: For location-based fields and maps.
    *   `google-api-python-client`: The official Google API client library for Python.
    *   `argon2-cffi`: For a strong password hashing algorithm.

## 5. Building and Running

### Prerequisites

*   Python 3.12+
*   `uv` (or `pip`)
*   PostgreSQL
*   Redis

### Setup and Execution

1.  **Install Dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```
2.  **Configure Environment:**
    *   Copy the `.env.example` file to `.env`.
    *   Fill in the required environment variables, including database credentials, email settings, and Google API keys.
3.  **Database Migrations:**
    *   The `make mig` command is a convenient shortcut for running `makemigrations` and `migrate`.
    ```bash
    make mig
    ```
4.  **Load Initial Data (Optional):**
    *   The `make load` command loads initial data for countries, regions, and cities from fixture files.
    ```bash
    make load
    ```
5.  **Create a Superuser:**
    *   The `make super` command is a shortcut for `createsuperuser`.
    ```bash
    make super
    ```
6.  **Run the Development Server:**
    ```bash
    python3 manage.py runserver
    ```

## 6. Development Conventions

*   **Code Style:** The project enforces a consistent code style using `flake8` for linting and `isort` for organizing imports. You can run these checks using the `make check` command.
*   **Testing:** The project includes a `tests.py` file, but it is currently empty. It is highly recommended to add unit and integration tests to ensure the reliability and correctness of the application.
*   **Version Control:** The project is managed with Git. While no specific branching strategy is defined, a feature-branch workflow (e.g., GitFlow) is recommended for collaborative development.
