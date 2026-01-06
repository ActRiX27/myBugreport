# myBugReport 流水线契约（占位草案）

## 阶段输入/输出约定
- **collect**：输入 bugreport 文本路径、设备信息；输出 `artifacts.json`（列表）。
- **parse**：输入 `artifacts.json` 或单个 bugreport 文本；输出 `*.records.jsonl`（一行一条 `LogRecord`）。
- **analyze**：输入 records jsonl；输出 `findings.json`（列表）。
- **report**：输入 findings（可选 artifacts）；输出 `report.md` 与同名 JSON。

## 数据模型字段摘要（JSON 可序列化）
- `DeviceInfo`: serial, model?, android_version?, build_fingerprint?, notes?
- `CollectArtifact`: path, captured_at, device, artifact_type, sha256?, size_bytes?
- `LogRecord`: ts?, level?, tag?, msg, raw, source
- `Finding`: rule_id, severity, evidence (dict), confidence, summary?
- `ReportData`: device?, artifacts[], findings[], generated_at, summary?, template?

## 文件命名示例
- `collect/artifacts.json`
- `parse/<artifact>.records.jsonl`
- `analyze/findings.json`
- `report/report.md` 与 `report/report.json`

## CLI 子命令草案
- `mybugreport-pipeline collect <bugreport> <artifacts_dir> <serial> [model]`
- `mybugreport-pipeline parse <bugreport> <records> [--source bugreport]`
- `mybugreport-pipeline analyze <records> <findings>`
- `mybugreport-pipeline report <findings> <report_md> [--artifacts artifacts.json] [--summary text]`
- `mybugreport-pipeline pipeline <bugreport> <workdir> <serial> [model]`

## 未来完善方向
- collect 阶段支持通过 ADB 自动拉取并校验文件
- parse 阶段补充分析逻辑（时间戳、日志级别、tag 抽取）
- analyze 阶段接入取证特征与融合模型
- report 阶段支持 HTML/JSON 模板化输出
