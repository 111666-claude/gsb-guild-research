"""公会研究：并行研究位、按真实时间的完成判定、提交幂等、资源只扣一次。

缺陷：不看并行位上限、重复提交重复生效、完成按推进调用次数、每次查询全扫研究表。
"""

SLOTS = 2
TICK_MS = 1000


class Research:
    """公会研究队列。"""

    def __init__(self, slots=SLOTS):
        self.slots = slots
        self.projects = {}
        self.done = set()
        self.scanned = 0

    def start(self, project_id, cost_ms, now_ms, cost_gold=0):
        """开始研究。缺陷：不看并行位上限、同一项目重复提交也照收。"""
        self.projects[project_id] = [now_ms, cost_ms]
        return True

    def advance(self, now_ms):
        """推进研究。缺陷：按调用次数各减一个 tick，与传入的 now_ms 无关。"""
        for project_id in list(self.projects):
            self.projects[project_id][1] -= TICK_MS
            if self.projects[project_id][1] <= 0:
                self.done.add(project_id)
                del self.projects[project_id]
        return len(self.done)

    def running(self):
        """在研项目数。缺陷：每次全扫研究表。"""
        self.scanned += len(self.projects)
        return len(self.projects)

    def scanned_count(self):
        return self.scanned
