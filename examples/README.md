# 示例与占位数据

本目录预留示例输入/输出文件位置，便于后续补充可复现的流水线样例。目前可参考：

```bash
# 运行完整流水线（占位实现）
mybugreport-pipeline pipeline examples/bugreport.sample.txt .pipeline-work demo-serial "Demo Model"

# 仅执行解析阶段
mybugreport-pipeline parse examples/bugreport.sample.txt /tmp/records.jsonl
```

> 提示：`bugreport.sample.txt` 尚未提供，可按需要放置到本目录后使用。
