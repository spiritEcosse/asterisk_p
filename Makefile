#!/usr/bin/env bash
makemessages:
	docker-compose exec web ./manage.py makemessages -a

compilemessages:
	docker-compose exec web ./manage.py compilemessages

migrate:
	docker-compose exec web ./manage.py makemigrations && docker-compose exec web ./manage.py migrate

bash:
	docker-compose exec web bash

shell:
	docker-compose exec web ./manage.py shell

deploy_hard:
	sudo rm celerybeat.pid celerybeat-schedule || docker-compose stop && docker-compose rm -f && docker-compose up --build

deploy:
	docker-compose up

collectstatic:
	docker-compose exec web ./manage.py collectstatic --noinput

freeze:
	docker-compose exec web pip freeze > requirements.txt

restart_web:
	docker-compose stop web && docker-compose start web

restart_web_hard:
	docker-compose rm web && docker-compose stop web && docker-compose start web
