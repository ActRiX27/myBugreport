# Ingest (待实现)

目标：在合规授权下通过 ADB 获取 bugreport 或日志快照，输出为本工具现有 CLI 所需的文本文件。当前仓库的 `src/mybugreport/pipeline/collect/` 提供了索引已有 bugreport 的骨架实现，未来可在此基础上接入 ADB 采集。

当前状态：未实现。预期步骤（占位）：
- adb 指令选择与参数（如 bugreport、logcat 导出）
- 日志/历史文本的保存路径与命名
- 采集完成后的校验与摘要
