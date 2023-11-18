from multiprocessing.shared_memory import SharedMemory

from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import AppConfig

from django.conf import settings


class Data(AppConfig):
    name = "jpnic_admin.resource"
    verbose_name = "アドレス資源"

    def __init__(self, app_name, app_module):
        super().__init__(app_name, app_module)

    def ready(self):
        try:
            SharedMemory(create=False, name="apscheduler_start")
            return
        except:
            SharedMemory(create=True, size=1, name="apscheduler_start")

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.get_addr_process, "interval", seconds=20, id="get_addr")
        self.scheduler.add_job(self.get_resource_process, "interval", seconds=20, id="get_resource")
        self.scheduler.add_job(
            self.notice_etc,
            "cron",
            year="*",
            month=settings.NOTICE_MONTH,
            day=settings.NOTICE_DAY,
            week="*",
            hour=settings.NOTICE_HOUR,
            minute=settings.NOTICE_MINUTE,
            id="notice_etc",
        )
        self.scheduler.start()

    def notice_etc(self):
        from .notify import NoticeResource, NoticeCertExpired

        NoticeResource().to_slack()
        NoticeCertExpired().to_slack()

    def get_addr_process(self):
        from .task import get_task

        try:
            self.scheduler.pause_job("get_addr")
            get_task(type1="アドレス情報")
            self.scheduler.resume_job("get_addr")
        except:
            print("ERROR: get_addr_process")
            pass

    def get_resource_process(self):
        from .task import get_task
        try:
            self.scheduler.pause_job("get_resource")
            get_task(type1="資源情報")
            self.scheduler.resume_job("get_resource")
        except:
            print("ERROR: get_resource_process")
            pass

