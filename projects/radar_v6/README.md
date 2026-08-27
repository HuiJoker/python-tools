# 员工能力雷达图 V6

这是从 `radar_ui_v6.py` 整理出的工程化项目结构，用于从 Excel 员工能力评估表生成能力雷达图。

## 目录结构

```text
projects/radar_v6/
  src/radar_v6/
    app.py          # 主程序
    __main__.py     # python -m radar_v6 入口
    ui.py           # Tkinter 界面
    data.py         # Excel 数据读取
    mapping.py      # 模板和列映射
    export.py       # 雷达图绘制和导出
  scripts/
    run.ps1         # 本地运行
    build_exe.ps1   # 打包 EXE
  config/
    默认模板.json    # 模板示例
  pyproject.toml
  requirements.txt
  .gitignore
```

## 开发运行

```powershell
cd python-tools\projects\radar_v6
python -m pip install -r requirements.txt
.\scripts\run.ps1
```

也可以使用模块入口：

```powershell
$env:PYTHONPATH = "src"
python -m radar_v6
```

## 打包 EXE

```powershell
cd python-tools\projects\radar_v6
python -m pip install -r requirements.txt
.\scripts\build_exe.ps1
```

打包输出：

```text
dist\员工能力雷达图V6.exe
```

## 默认数据文件

程序默认从运行目录读取：

- `附件3 员工能力评估汇总表.xlsx`
- `默认模板.json`

仓库中只保留代码和模板配置，没有提交包含人员信息的 Excel 数据文件。运行后可在界面中选择本地 Excel 文件。

首次运行会在程序目录生成：

```text
radar_v6_settings.json
```

## 说明

- 后续迭代建议改 `src/radar_v6/` 下的工程化代码，不再维护旧版单文件脚本。
- 模板配置可从界面保存和加载。
- 支持批量导出人员雷达图。
