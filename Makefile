mig:
	python3 manage.py makemigrations
	python3 manage.py migrate

# loaddata
load:
	python3 manage.py loaddata country region city

super:
	python3 manage.py createsuperuser

check:
	flake8 .
	isort .