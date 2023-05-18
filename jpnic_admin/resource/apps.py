from multiprocessing.shared_memory import SharedMemory

from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import AppConfig


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
            self.post_resource_info,
            "cron",
            year="*",
            month="*",
            day=2,
            week="*",
            hour=9,
            minute=0,
            id="post_resource_info",
        )
        # self.post_resource_info()
        self.scheduler.start()

    def post_resource_info(self):
        from .task import post_resource_info

        post_resource_info()

    def get_addr_process(self):
        from .task import get_task

        self.scheduler.pause_job("get_addr")
        get_task(type1="アドレス情報")
        self.scheduler.resume_job("get_addr")

    def get_resource_process(self):
        from .task import get_task

        self.scheduler.pause_job("get_resource")
        get_task(type1="資源情報")
        self.scheduler.resume_job("get_resource")
