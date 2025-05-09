@echo off
echo Setting up Marketplace System...

:: Activate virtual environment
call env\Scripts\activate
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Navigate to Django project directory
cd ec
if errorlevel 1 (
    echo Error: Failed to navigate to project directory
    pause
    exit /b 1
)

:: Run migrations
echo Running database migrations...
python manage.py makemigrations
if errorlevel 1 (
    echo Error: Failed to create migrations
    pause
    exit /b 1
)

python manage.py migrate
if errorlevel 1 (
    echo Error: Failed to apply migrations
    pause
    exit /b 1
)

:: Create superuser if it doesn't exist
echo Creating superuser account...
echo Please enter the following information for the admin account:
set /p ADMIN_USERNAME=Username (default: admin): 
if "%ADMIN_USERNAME%"=="" set ADMIN_USERNAME=admin

set /p ADMIN_EMAIL=Email (default: admin@example.com): 
if "%ADMIN_EMAIL%"=="" set ADMIN_EMAIL=admin@example.com

set /p ADMIN_PASSWORD=Password: 

python manage.py createsuperuser --noinput --username %ADMIN_USERNAME% --email %ADMIN_EMAIL%
if errorlevel 1 (
    echo Error: Failed to create superuser
    pause
    exit /b 1
)

:: Run the development server
echo.
echo Starting development server...
echo.
echo The marketplace will be available at http://127.0.0.1:8000/
echo Admin interface will be at http://127.0.0.1:8000/admin/
echo.
echo Press Ctrl+C to stop the server
echo.
python manage.py runserver 