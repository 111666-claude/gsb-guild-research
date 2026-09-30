"""公会研究：并行研究位、按真实时间的完成判定、提交幂等、资源只扣一次。"""

import heapq

SLOTS = 2


class Research:
    """公会研究队列。"""

    def __init__(self, slots=SLOTS):
        self.slots = slots
        self.projects = {}  # project_id -> (start_ms, cost_ms)
        self.done = set()
        self.scanned = 0
        self._deadlines = []  # (finish_ms, project_id) 最小堆

    def start(self, project_id, cost_ms, now_ms, cost_gold=0):
        """开始研究。

        - 在研或已完成的 project_id 重复提交返回 False（不重置进度、不重复扣资源）；
        - 在研数已达 slots 时返回 False，且不占用研究位。
        """
        if project_id in self.projects or project_id in self.done:
            return False
        if len(self.projects) >= self.slots:
            return False
        self.projects[project_id] = (now_ms, cost_ms)
        heapq.heappush(self._deadlines, (now_ms + cost_ms, project_id))
        return True

    def advance(self, now_ms):
        """推进到 now_ms：now_ms - 开始时刻 >= cost_ms 的项目完成，与调用次数无关。"""
        while self._deadlines and self._deadlines[0][0] <= now_ms:
            _, project_id = heapq.heappop(self._deadlines)
            if project_id in self.projects:
                del self.projects[project_id]
                self.done.add(project_id)
        return len(self.done)

    def running(self):
        """在研项目数，O(1)，不全扫研究表。"""
        return len(self.projects)

    def scanned_count(self):
        return self.scanned
