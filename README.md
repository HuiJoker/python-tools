# Python 工具箱

这里集中存放日常使用的 Python 小工具和相对独立的项目。按用途选择对应目录，并优先阅读子目录中的 `README.md`。

## 目录说明

| 路径 | 用途 | 说明 |
| --- | --- | --- |
| `scripts/dataset_stats/` | 数据集统计 | 统计图片、XML 文件及 Pascal VOC 标签数量。 |
| `scripts/image_tools/` | 图像工具 | 图像坐标、像素距离等交互式测量。 |
| `scripts/label_analysis/` | 标注分析 | Pascal VOC XML 标签统计与标注目录对比。 |
| `scripts/video_tools/` | 视频工具 | 视频裁剪和按间隔提取帧。 |
| `scripts/split_images_by_count.py` | 图片拆分 | 按指定数量拆分图片文件。 |
| `projects/radar_v6/` | 员工能力雷达图 | 从 Excel 评估表生成雷达图的完整项目。 |

## 使用约定

- `scripts/`：功能单一、可直接运行的小脚本，按主题放入子目录。
- `projects/`：有独立依赖、配置或多个模块的完整项目。
- 新增工具时：创建对应目录、补充该目录的 `README.md`，并在本文件的表格中增加入口说明。

## 运行方式

在工具所在目录执行命令。例如统计数据集：

```powershell
cd F:\python-tools\scripts\dataset_stats
python count_images_xml_labels.py "F:\path\to\dataset"
```
