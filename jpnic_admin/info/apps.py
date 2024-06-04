from multiprocessing.shared_memory import SharedMemory

from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import AppConfig

from django.conf import settings


class Info(AppConfig):
    name = "jpnic_admin.info"
    verbose_name = "アドレス資源"

    def __init__(self, app_name, app_module):
        super().__init__(app_name, app_module)
        self.scheduler = None

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

        self.scheduler.get_job("get_addr").pause()
        try:
            get_task(type1="アドレス情報")
        except:
            print("ERROR: get_addr_process")
            pass
        self.scheduler.get_job("get_addr").resume()

    def get_resource_process(self):
        from .task import get_task

        self.scheduler.get_job("get_resource").pause()
        try:
            get_task(type1="資源情報")
        except:
            print("ERROR: get_resource_process")
            pass
        self.scheduler.get_job("get_resource").resume()
