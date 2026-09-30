# guild-research

公会研究：并行研究位、按真实时间的完成判定、提交幂等、资源只扣一次，只用 Python 标准库。

```
python3 -m research.cli --sample slots
python3 -m research.cli --sample time
python3 -m research.cli --sample dup
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **并行上限**：同时在研的项目数不超过 `slots`，超出时 `start` 返回 `False` 且不占用研究位。
- **按真实时间完成**：项目在 `now_ms - 开始时刻 >= cost_ms` 时就完成，与 `advance` 调用次数无关。
- **提交幂等**：同一 `project_id` 重复提交返回 `False`，不重置进度、不重复扣资源。
- **不变量**：完成集合只增不减；在研数量永远不大于 `slots`；同一串操作重复执行结果相同。
- **查询代价**：`running` 不许每次全扫研究表，`scanned_count` 不随在研项目数线性增长。
- **规模**：公会有 20 万条研究记录、每秒 10 万次查询，单次摊还 O(1)。

## 输出契约（不改格式）

```
third=false running=2
done=1
second=false running=1
scanned<=3000
```

## 目录

```
research/core.py   研究位、完成与幂等
research/cli.py    命令行入口
tests/             unittest 用例
```
