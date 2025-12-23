# 模拟输出示例（adb pipeline）

当无法连接真实设备时，可通过本示例文件快速了解 `mybugreport-pipeline tool run adb` 的典型输出形态。内容完全为模拟，仅用于展示格式与目录结构。

## CLI 日志（模拟）

```bash
$ mybugreport-pipeline tool run adb --serial demo-serial --rules samples/rules --out .case-demo --format md
[collect] collected bugreport (模拟) -> .case-demo/artifacts/bugreport.txt
[collect] collected logcat_threadtime (模拟) -> .case-demo/artifacts/logcat_threadtime.txt
[collect] collected dmesg (模拟) -> .case-demo/artifacts/dmesg.txt
[parse] wrote records to .case-demo/records/records.jsonl
[analyze] findings -> .case-demo/findings/findings.json (evidence: findings_evidence.jsonl)
[report] report generated at .case-demo/report/report.md
Pipeline finished (simulated)
```

## 报告 Markdown 片段（模拟）

```markdown
# myBugReport Delivery (Simulated)
- Device: demo-serial / Demo Model
- Artifacts (simulated): bugreport.txt, logcat_threadtime.txt, dmesg.txt
- Findings (sample):
  - baseline.count (info): total records = 5
  - crash.fatal (warn): detected 1 fatal exception entry
  - selinux.avc (info): observed 2 avc denial lines

## Notes
- 本报告仅为格式示例，不包含真实设备数据。
```

## 目录结构（模拟）

```
.case-demo/
  artifacts/
    bugreport.txt
    dmesg.txt
    logcat_threadtime.txt
    artifacts.json
  records/
    records.jsonl
    parse_summary.json
  findings/
    findings.json
    findings_evidence.jsonl
  report/
    report.md
```
