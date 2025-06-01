from dataclasses import dataclass
from enum import Enum


class WorkerType(Enum):
    working = "working"
    started = "started"
    inactive = "inactive"

@dataclass
class WorkerData:
    type: str
    version: str
    status: WorkerType
    f1_score: int

class WorkerService:


    def get_all_workers(self)-> list[WorkerData]:
        pass

    def get_worker(self)-> WorkerData:
        pass

    def start_worker(self):
        pass

    def delete_worker(self):
        pass