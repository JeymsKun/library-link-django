# Library Link Django Project

A step-by-step tutorial for building a library management system using Django.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Running Tests](#running-tests)
- [Contributing](#contributing)
- [License](#license)

## Introduction

This tutorial guides you through creating a Django-based library management system, covering setup, models, views, templates, and more.

## Features

- User authentication
- Book catalog management
- Borrowing and returning books
- Admin dashboard

## Prerequisites

- Python 3.x
- Django 4.x
- Git

## Installation

```bash
git clone https://github.com/JeymsKun/library-link-django.git
cd library-link-django
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Installing Additional Packages

To add support for environment variables, SSL certificates, and email sending, install the following packages:

```bash
pip install python-dotenv
pip install certifi
pip install sendgrid
```

### Updating requirements.txt

If you add or update packages in your virtual environment, you should update `requirements.txt` to keep track of dependencies.  
To do this, run:

```bash
pip freeze > requirements.txt
```

This command will overwrite `requirements.txt` with the current list of installed packages and their versions.

## Project Structure

```
library-link-django/
├── library/
├── users/
├── manage.py
├── requirements.txt
└── README.md
```

## Usage

1. **Apply migrations:**
   ```bash
   python manage.py migrate
   ```
2. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```
3. **Run the server:**
   ```bash
   python manage.py runserver
   ```
4. Visit `http://127.0.0.1:8000/` in your browser.

## Running Tests

```bash
python manage.py test
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

## License

[MIT](LICENSE)
