#!/bin/bash
echo "Creating virtual environment..."
python3 -m venv venv

if [ -d "venv" ]; then
    echo "Virtual environment created successfully."
else
    echo "Failed to create virtual environment. Exiting."
    exit 1
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip and setuptools..."
pip install --upgrade pip setuptools

echo "Installing dependencies..."
pip install asgiref==3.8.1 \
            certifi==2025.4.26 \
            distlib==0.3.9 \
            Django==5.2.1 \
            django-cors-headers==4.7.0 \
            djangorestframework==3.16.0 \
            djangorestframework_simplejwt==5.5.0 \
            ecdsa==0.19.1 \
            filelock==3.18.0 \
            MarkupSafe==3.0.2 \
            packaging==25.0 \
            pillow==11.2.1 \
            pipenv==2025.0.2 \
            platformdirs==4.3.8 \
            PyJWT==2.9.0 \
            python-dotenv==1.1.0 \
            python-http-client==3.3.7 \
            sendgrid==6.12.2 \
            setuptools==80.8.0 \
            six==1.17.0 \
            sqlparse==0.5.3 \
            tzdata==2025.2 \
            virtualenv==20.31.2 \
            Werkzeug==3.1.3

echo "Saving dependencies to requirements.txt..."
pip freeze > requirements.txt

echo "Setup complete! Your virtual environment is ready and dependencies are installed."

echo "Setting up automatic activation for the virtual environment..."
echo "source $(pwd)/venv/bin/activate" >> ~/.bashrc
echo "Done! Next time you open a new terminal, the virtual environment will activate automatically."

source ~/.bashrc

echo "You're now inside the virtual environment!"
