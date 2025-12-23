# myBugReport

myBugReport 聚焦移动终端取证行为的实时识别：针对传统依赖单点指纹、滞后且易被规避的问题，在合规授权下仅基于 ADB 只读日志与系统历史文本，构建“ADB 鉴权 → Provider/URI 激活 → Shell 命令族”的多阶段链，进行时序模板匹配与概率融合，判定是否存在取证式批量枚举/导出行为。实现不读取用户内容、仅保存统计摘要的前提下提升检出率与可解释性，降低误报/漏报与检测延迟，并保持对主流 Android 版本与 OEM 的适配性，使反取证检测从被动响应转向主动且可审计的闭环。

myBugReport 仍是一个用于对 Android bugreport 文本进行后处理的开发者工具，保留原有 CLI 兼容性并提供可选扩展能力。

## 功能概览
- 根据指定时间戳（支持多个）提取上下文日志片段。
- 按 `rule2.txt`（可被环境变量覆盖）抽取媒体 Provider 相关段落。
- 按 `rule.txt` 的键值对替换关键字为中文描述。
- 将 `2h`、`15m`、`-3s` 等时长标记转换为中文可读格式。
- 提供可选的调试日志、严格校验与容错策略，默认关闭以保持兼容。

## 使用方法
```bash
python my_bugreport.py <timestamp> [<timestamp> ...] <input_bugreport> <output_file> [context_lines]
```

参数说明：
- `<timestamp>`：一个或多个时间戳字符串，每个会作为 `grep -e` 模式使用（例如 `2024-06-21`、`12:34:56`）。
- `<input_bugreport>`：原始 bugreport 文本路径。
- `<output_file>`：处理后的输出文件路径。
- `[context_lines]`（可选）：匹配行的前后上下文行数，默认 `1`。

示例：
```bash
python my_bugreport.py "2024-06-21" "12:34:56" bugreport.txt processed.txt 3
```

## 配置与可选开关
- `MYBUGREPORT_RULE_FILE`：覆盖 `rule.txt` 路径。
- `MYBUGREPORT_SECTION_RULE_FILE`：覆盖 `rule2.txt` 路径。
- `MYBUGREPORT_DEBUG`：开启调试输出（默认关闭）。
- `MYBUGREPORT_STRICT_VALIDATION`：启用规则文件存在性校验（默认关闭）。
- `MYBUGREPORT_ALLOW_MISSING_RULES`：允许规则文件缺失时跳过并记录调试日志（默认关闭）。
- `MYBUGREPORT_WARN_ON_MISSING_RULES`：在容错开启且规则缺失时输出警告（默认关闭）。
- `MYBUGREPORT_CHECK_OUTPUT_NONEMPTY`：可选输出一致性检查（默认关闭），用于严格场景提醒输出为空。
- Hook 扩展：`processor.apply_translations_and_time` 接受可选后置处理函数列表，便于插件式扩展（默认不传）。

## 配置文件格式
- `rule.txt`：`key:value` 对，定义关键字替换；格式错误的行会被忽略。
- `rule2.txt`：以冒号分隔的起止模式，供 awk 抽取媒体 Provider 段落。

## 输出
输出文件包含：
1. 针对时间戳匹配的上下文日志片段。
2. 根据 section 规则抽取的媒体 Provider 段落（若规则存在）。
3. 关键字替换后的内容与中文可读的时长标记。

## 模块化结构
- `my_bugreport.py`：CLI 入口，保持原有参数与行为。
- `mybugreport/processor.py`：提取与替换管线，支持可选 hook。
- `mybugreport/rules.py`：规则读取与转义，支持校验/容错开关。
- `mybugreport/time_utils.py`：时长解析与转换。
- `mybugreport/config.py`：环境变量配置与调试开关。
- `mybugreport/io_utils.py`：带可选校验/容错的文件读取工具。
- `mybugreport/hooks.py`：可插拔的后置处理 hook 工具。
- `mybugreport/forensic_analysis.py`：可选的取证评分与特征说明（默认未接入 CLI）。
- `tests/data/`：预留的样例数据目录（当前为空），便于未来添加回归测试输入输出。

## 扩展能力说明
- 调试/校验/容错开关见“配置与可选开关”章节，全部默认关闭以保证兼容。
- Hook 机制：可向 `apply_translations_and_time` 传入自定义回调，对输出文件做额外处理。
- 取证评分模块：`forensic_analysis` 提供 L1~L4 特征、子特征及基于 S 形函数的可选融合/分层逻辑，默认不启用。
  - 四类特征：L1 连接/鉴权（ADB 高权限通道）、L2 电量/充电锚点、L3 Provider/URI 迹象、L4 Shell 命令族。
  - 子特征示例：L1（鉴权成功/adb 功能/root 迹象/5555 提示），L2（USB 比例/稳定时长/电量斜率），L3（Provider 数量/URI 授权数量或速率/授权主体/事件集中度），L4（命令 n-gram 匹配/突发密度/命令类型数/高权限执行提示）。
  - 阈值示例：S = σ(Σ w_i · φ_i(Li) + b)；S≥τ_high 判定高嫌疑，τ_med≤S<τ_high 预警，其余常态；可按召回/精准需求调整阈值与权重。
  - “销毁/隐藏/规避”映射：销毁对应 L4 清理指令簇与 L3 改写痕迹；隐藏对应 L4 路径/可见性变形与 L3 索引/授权异常；规避通过节奏打散但保留 L3/L4 子序列结构，并结合 L2 长会话锚点与 L1 高权限信道确认。

## 已知限制
- 未引入第三方依赖，所有扩展均为可选开关或插拔式接口。
- CLI 语义保持不变；未默认启用的模块不会影响现有输出。
