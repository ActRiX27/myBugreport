# HONORJMM-AL00 模拟案例输出

本目录展示了基于 `examples/bugreport-HONORJMM-AL00-2024-01-29-15-13-04.txt` 的离线跑分结果，便于在无法连接真实设备时核对流水线产物格式。

## 生成方式

在仓库根目录执行（已将 `src/` 加入 `PYTHONPATH`）：

```bash
python - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, 'src')
from mybugreport.pipeline.collect import collect_existing_artifact, write_artifacts_index
from mybugreport.pipeline.parse import parse_bugreport_lines
from mybugreport.pipeline.analyze import analyze_with_rules
from mybugreport.pipeline.report import render_report_markdown
from mybugreport.models import DeviceInfo

bugreport = Path('examples/bugreport-HONORJMM-AL00-2024-01-29-15-13-04.txt')
workdir = Path('examples/honor_case')

artifact = collect_existing_artifact(bugreport, DeviceInfo(serial='HONORJMM-AL00', model='HONOR JMM-AL00'), workdir / 'artifacts')
artifacts_index = write_artifacts_index([artifact], workdir / 'artifacts' / 'artifacts.json')
records_path = workdir / 'records' / 'records.jsonl'
parse_bugreport_lines(bugreport, records_path, source='bugreport')
findings_path, evidence_path = analyze_with_rules(records_path, Path('samples/rules'), workdir / 'findings')
render_report_markdown(findings_path, workdir / 'report' / 'report.md', artifacts_path=artifacts_index, summary='Simulated HONORJMM bugreport run')
print('done')
PY
```

## 产物说明

- `artifacts/artifacts.json`：指向模拟 bugreport 的索引。
- `records/records.jsonl`：逐行展开的 bugreport 记录（含自动识别的 logcat/dmesg 结构字段）。
- `findings/findings.json`：规则匹配结果（示例中触发了 crash/network/selinux/dropbox/build_fingerprint/baseline.stats/baseline.top_tags 等规则）。
- `findings/findings_evidence.jsonl`：命中规则的证据行（包含时间、等级、tag）。
- `report/report.md` / `report.json`：渲染后的报告（含采集产物与结论）。

> 注：该 bugreport 内容为自造示例，用于演示工具链，不代表真实设备日志。
