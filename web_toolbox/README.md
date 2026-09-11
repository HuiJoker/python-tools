# 本地视觉数据工具台

这是对现有 Python 脚本的本地 Web 操作层：不上传文件、不改写原脚本，任务记录默认保存在仓库根目录的 `.toolbox/history.sqlite3`。

## 启动

```powershell
cd F:\python-tools
python -m pip install -r requirements-web.txt
.\run_toolbox.ps1
```

也可以直接双击仓库根目录的 `启动本地工具台.cmd`。如需桌面入口，请为这个 `.cmd` 文件创建快捷方式。

浏览器打开 `http://127.0.0.1:8765`。

## 首版接入

- 数据集检查（标签、图片/XML 配对、解析异常、可选递归与 XML 元素统计）
- Pascal VOC 标注版本对比
- 按数量拆分图片（输出到源目录内部；不足半批的余数并入最后一批；默认预演，实际复制/移动必须手动确认）

原来的命令行脚本仍可独立使用。
