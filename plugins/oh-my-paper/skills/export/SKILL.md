---
description: C22 导出发布：LaTeX 导出并适配目标会议模板
---

> **必须使用 AskUserQuestion 工具进行所有确认步骤，不得用纯文字替代。**

你是 Oh My Paper Orchestrator。此命令实现 C22 导出发布，将论文导出为适配目标会议模板的 LaTeX。

## 第一步：确认目标会议和模板

```bash
cat .pipeline/docs/research_brief.json
ls paper/[目标会议模板]/ 2>/dev/null || echo "TEMPLATE_NOT_FOUND"
```

用 `AskUserQuestion` 确认：

> **导出发布**
>
> 目标会议：[会议名称]
> 模板位置：paper/[会议缩写]/
>
> 选项：
> - `确认，开始导出`
> - `更换会议模板`
> - `取消`

## 第二步：检查 LaTeX 模板文件

```bash
# 检查必要文件
ls paper/[会议缩写]/*.tex
ls paper/[会议缩写]/*.sty
ls paper/[会议缩写]/*.bib
ls paper/[会议缩写]/*.bst

# 检查论文文件
ls paper/sections/
cat paper/main.tex
```

用 `AskUserQuestion` 确认：

> **模板检查**
>
> | 文件 | 状态 |
> |------|------|
> | main.tex | ✅/❌ |
> | [会议].sty | ✅/❌ |
> | [会议].bib | ✅/❌ |
> | natbib.sty | ✅/❌ |
>
> 选项：
> - `确认，继续`
> - `修复缺失文件`
> - `取消`

## 第三步：运行 LaTeX 编译检查

```bash
cd paper
pdflatex -interaction=nonstopmode main.tex 2>&1 | head -50
```

检查是否有编译错误。

用 `AskUserQuestion` 展示：

> **编译检查**
>
> | 检查项 | 状态 |
> |-------|------|
> | LaTeX 编译 | [成功/失败] |
> | 参考文献 | [N 条] |
> | 图表引用 | [M 处] |
>
> 选项：
> - `编译成功，继续`
> - `有错误，修复`
> - `取消`

## 第四步：检查页数限制

```bash
# 统计页数（如果编译成功）
pdfinfo main.pdf 2>/dev/null | grep Pages || echo "PDF_NOT_GENERATED"

# 检查各部分字数
wc -w paper/sections/*.tex
```

用 `AskUserQuestion` 展示：

> **页数检查**
>
> | 部分 | 字数 | 限制 |
> |------|-----|------|
> | Introduction | ~800 | ≥800 ✅ |
> | Method | ~1200 | ≥1000 ✅ |
> | Experiments | ~900 | ≥800 ✅ |
> | ... | ... | ... |
>
> **总页数**：{N} 页
>
> 选项：
> - `页数达标，继续`
> - `需要调整内容`
> - `取消`

## 第五步：生成最终 PDF

```bash
# 完整编译
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# 生成 PDF
ls -la main.pdf
```

## 第六步：导出检查清单

```markdown
## C22 导出检查清单

### 格式检查
- [ ] 使用正确的 LaTeX 模板
- [ ] 双栏格式正确
- [ ] 字体符合要求
- [ ] 图表位置正确

### 内容检查
- [ ] Abstract 在首页
- [ ] Introduction 从新页开始
- [ ] 参考文献格式正确
- [ ] 页数在限制内

### 可复现性检查
- [ ] 代码链接已添加
- [ ] 数据集链接已添加
- [ ] 超参数表格完整
```

用 `AskUserQuestion` 确认导出：

> **导出准备完成**
>
> PDF 文件：paper/main.pdf
>
> 下一步：
>
> 选项：
> - `生成 submission package`
> - `本地查看 PDF`
> - `上传到 Overleaf`
> - `取消`

## 第七步：生成提交包

```bash
# 创建提交目录
mkdir -p submission/[会议缩写]_[年份]
cp paper/main.pdf submission/[会议缩写]_[年份]/
cp paper/main.tex submission/[会议缩写]_[年份]/
cp paper/*.bib submission/[会议缩写]_[年份]/
cp -r paper/sections submission/[会议缩写]_[年份]/

# 打包
cd submission
zip -r [会议缩写]_[年份]_submission.zip [会议缩写]_[年份]/

echo "提交包已生成：submission/[会议缩写]_[年份]_submission.zip"
```

## Overleaf 导出

如果用户选择上传到 Overleaf：

```bash
# 调用 Overleaf MCP
# 上传所有文件到 Overleaf 项目
```

用 `AskUserQuestion` 确认：

> **Overleaf 上传**
>
> 正在上传到 Overleaf...
>
> 选项：
> - `上传成功，查看`
> - `重新上传`
> - `取消`

## 最终输出

| 文件 | 位置 |
|------|------|
| main.pdf | paper/main.pdf |
| main.tex | paper/main.tex |
| Submission.zip | submission/[会议缩写]_[年份]_submission.zip |
| Overleaf项目 | [Overleaf URL] |

## 错误处理

执行过程中遇到以下情况请统一处理：

| 场景 | 处理方式 |
|------|---------|
| 文件或目录不存在 | 提示用户："⚠️ 未找到 {文件名}，请检查是否已完成前置步骤" |
| 命令执行失败 | 提示用户："⚠️ 执行失败：{错误原因}，请检查后重试" 并提供重试/跳过/退出选项 |
| 用户输入无效 | 提示用户："❌ 无效选项，请重新选择" 并重新展示选项 |
| 其他意外错误 | 提示用户："⚠️ 发生意外错误：{描述}，[重试] [返回] [退出]" |

所有交互均使用 AskUserQuestion 工具，不要用纯文字替代。

