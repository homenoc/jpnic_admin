from multiprocessing.shared_memory import SharedMemory

from django.apps import AppConfig


class Data(AppConfig):
    name = "jpnic_admin.resource"
    verbose_name = "アドレス資源"

    def ready(self):
        from .task import start_getting_addr, start_getting_resource

        try:
            SharedMemory(create=False, name="apscheduler_start")
            return
        except:
            SharedMemory(create=True, size=1, name="apscheduler_start")

        start_getting_addr()
        start_getting_resource()
