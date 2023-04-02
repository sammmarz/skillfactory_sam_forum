import logging

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.core.mail import EmailMultiAlternatives


logger = logging.getLogger(__name__)


# наша задача по выводу текста на экран
def my_job1():
	from board.models import Response, Post
	from datetime import datetime, timedelta
	from django.contrib.auth.models import User

	now = datetime.now()-timedelta(days=7)


	posts = list(Post.objects.filter(dateCreation__gte=now))
	if posts:
		list_email = []
		for user in User.objects.filter():
			print("пользователь",user)
			list_email.append(user.email)
		subject, from_email = f'Forum MMORPG: Посты  за неделю в категории ', 'petrovskill23@yandex.ru'
		to = list_email
		text_content = f'Привет! Посты за неделю'
		list_a=[]
		for post in posts:
			list_a.append(f'<a href="http://127.0.0.1:8000/post/{post.id}">{post.title}</a>')
		html_content = f'<p>{list_a}</p>'
		msg = EmailMultiAlternatives(subject, text_content, from_email, to)
		msg.attach_alternative(html_content, "text/html")
		msg.send()



# функция которая будет удалять неактуальные задачи
def delete_old_job_executions(max_age=604_800):
	"""This job deletes all apscheduler job executions older than `max_age` from the database."""
	DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
	help = "Runs apscheduler."


	def handle(self, *args, **options):
		scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
		scheduler.add_jobstore(DjangoJobStore(), "default")

		# добавляем работу нашему задачнику
		scheduler.add_job(
			my_job1,
			trigger=CronTrigger(day_of_week="sun"),
			id="my_job1",  # уникальный айди
			max_instances=1,
			replace_existing=True,
		)
		logger.info("Added job 'my_job1'.")

		scheduler.add_job(
			delete_old_job_executions,
			trigger=CronTrigger(
				day_of_week="mon", hour="00", minute="00"
			),
			# Каждую неделю будут удаляться старые задачи, которые либо не удалось выполнить, либо уже выполнять не надо.
			id="delete_old_job_executions",
			max_instances=1,
			replace_existing=True,
		)
		logger.info(
			"Added weekly job: 'delete_old_job_executions'."
		)

		try:
			logger.info("Starting scheduler...")
			scheduler.start()
		except KeyboardInterrupt:
			logger.info("Stopping scheduler...")
			scheduler.shutdown()
			logger.info("Scheduler shut down successfully!")