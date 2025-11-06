mig:
	python3 manage.py makemigrations
	python3 manage.py migrate

msg:
	python3 manage.py makemessages -l uz -l ru -l en

#compilemsg

# loaddata
load:
	python3 manage.py loaddata language

super:
	python3 manage.py createsuperuser

check:
	flake8 .
	isort .