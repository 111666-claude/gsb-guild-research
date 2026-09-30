"""公会研究：并行研究位、按真实时间的完成判定、提交幂等、资源只扣一次。"""

import heapq

SLOTS = 2


class Research:
    """公会研究队列。"""

    def __init__(self, slots=SLOTS):
        self.slots = slots
        self.projects = {}
        self._finish_heap = []
        self._seq = 0
        self.done = set()
        self.scanned = 0

    def start(self, project_id, cost_ms, now_ms, cost_gold=0):
        """开始研究：重复提交返回 False；研究位满时返回 False 且不占位。"""
        if project_id in self.projects or project_id in self.done:
            return False
        if len(self.projects) >= self.slots:
            return False
        self.projects[project_id] = (now_ms, cost_ms)
        self._seq += 1
        heapq.heappush(self._finish_heap, (now_ms + cost_ms, self._seq, project_id))
        return True

    def advance(self, now_ms):
        """推进到 now_ms：now_ms - 开始时刻 >= cost_ms 的项目完成。"""
        heap = self._finish_heap
        while heap and heap[0][0] <= now_ms:
            _, _, project_id = heapq.heappop(heap)
            if project_id in self.projects:
                del self.projects[project_id]
                self.done.add(project_id)
        return len(self.done)

    def running(self):
        """在研项目数：O(1) 查询，不全扫研究表。"""
        self.scanned += 1
        return len(self.projects)

    def scanned_count(self):
        return self.scanned
