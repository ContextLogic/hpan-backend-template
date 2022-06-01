from celery import Celery

from app.tasks.clroot_worker_jobs import BaseQueuedJob, QueueType

celery_app = Celery()
celery_app.config_from_object("worker_config")

SmsJobCls = BaseQueuedJob.queue_job_cls(QueueType.SMS_QUEUE_NAME_V2)

input_dict = {
    'user_id': 'rgao-wish',
    'phone_number': '5197293902',
    'country_code': 'US',
    'message': 'hello 123',
    'sms_type': '',
    'campaign_id': '',
}
event1 = SmsJobCls("id_sms", 'stage_roy_sweeper_sms_v2', input_dict)

celery_app.send_task("queued_task", args=(event1,))

