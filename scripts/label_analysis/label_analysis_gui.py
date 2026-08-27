from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from analyze_labels import analyze_directory, compare_xml_folders, normalize_labels


DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "20260601_mobile_ztm_cm"


class LabelAnalysisApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("标签统计工具")
        self.geometry("820x620")
        self.minsize(720, 520)

        self.folder_var = tk.StringVar(value=str(DEFAULT_DATA_DIR if DEFAULT_DATA_DIR.exists() else ""))
        self.labels_var = tk.StringVar(value="all")
        self.v1_folder_var = tk.StringVar()
        self.v2_folder_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        count_tab = ttk.Frame(notebook, padding=12)
        compare_tab = ttk.Frame(notebook, padding=12)
        notebook.add(count_tab, text="标签数量统计")
        notebook.add(compare_tab, text="前后版本对比")

        self._build_count_tab(count_tab)
        self._build_compare_tab(compare_tab)

    def _build_count_tab(self, parent):
        folder_row = ttk.Frame(parent)
        folder_row.pack(fill=tk.X)

        ttk.Label(folder_row, text="文件夹路径").pack(side=tk.LEFT)
        ttk.Entry(folder_row, textvariable=self.folder_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 8))
        ttk.Button(folder_row, text="选择...", command=lambda: self.choose_folder(self.folder_var)).pack(side=tk.LEFT)

        labels_row = ttk.Frame(parent)
        labels_row.pack(fill=tk.X, pady=(12, 0))

        ttk.Label(labels_row, text="标签名").pack(side=tk.LEFT)
        ttk.Entry(labels_row, textvariable=self.labels_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(34, 8))
        ttk.Button(labels_row, text="统计", command=self.run_count_analysis).pack(side=tk.LEFT)

        hint = ttk.Label(parent, text="多个标签可输入：DCC w_rope、DCC,w_rope、'DCC','w_rope'；输入 all 统计全部。")
        hint.pack(anchor=tk.W, pady=(8, 12))

        self.count_result_text = self.create_result_text(parent)

    def _build_compare_tab(self, parent):
        v1_row = ttk.Frame(parent)
        v1_row.pack(fill=tk.X)

        ttk.Label(v1_row, text="v1 XML文件夹").pack(side=tk.LEFT)
        ttk.Entry(v1_row, textvariable=self.v1_folder_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 8))
        ttk.Button(v1_row, text="选择...", command=lambda: self.choose_folder(self.v1_folder_var)).pack(side=tk.LEFT)

        v2_row = ttk.Frame(parent)
        v2_row.pack(fill=tk.X, pady=(12, 0))

        ttk.Label(v2_row, text="v2 XML文件夹").pack(side=tk.LEFT)
        ttk.Entry(v2_row, textvariable=self.v2_folder_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 8))
        ttk.Button(v2_row, text="选择...", command=lambda: self.choose_folder(self.v2_folder_var)).pack(side=tk.LEFT)

        action_row = ttk.Frame(parent)
        action_row.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(action_row, text="对比统计", command=self.run_compare_analysis).pack(side=tk.RIGHT)

        hint = ttk.Label(
            parent,
            text="按同名 XML 对比：v1剩余对象为删除，v2剩余对象为审核新增，两边剩余数量一致时按修改统计。",
        )
        hint.pack(anchor=tk.W, pady=(8, 12))

        self.compare_result_text = self.create_result_text(parent)

    def create_result_text(self, parent):
        result_frame = ttk.Frame(parent)
        result_frame.pack(fill=tk.BOTH, expand=True)

        text = tk.Text(result_frame, wrap=tk.WORD, height=18)
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return text

    def choose_folder(self, target_var):
        folder = filedialog.askdirectory(initialdir=target_var.get() or str(Path.cwd()))
        if folder:
            target_var.set(folder)

    def run_count_analysis(self):
        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showwarning("缺少路径", "请先选择需要统计的文件夹。")
            return

        try:
            result = analyze_directory(folder, normalize_labels(self.labels_var.get()))
        except Exception as exc:
            messagebox.showerror("统计失败", str(exc))
            return

        self.show_count_result(result)

    def run_compare_analysis(self):
        v1_folder = self.v1_folder_var.get().strip()
        v2_folder = self.v2_folder_var.get().strip()

        if not v1_folder or not v2_folder:
            messagebox.showwarning("缺少路径", "请先选择 v1 和 v2 的 XML 文件夹。")
            return

        try:
            result = compare_xml_folders(v1_folder, v2_folder)
        except Exception as exc:
            messagebox.showerror("对比失败", str(exc))
            return

        self.show_compare_result(result)

    def show_count_result(self, result):
        lines = [
            f"文件夹: {result['directory']}",
            f"图片数量: {result['image_count']}",
            f"XML数量: {result['xml_count']}",
            f"缺少XML的图片: {len(result['missing_xml'])}",
            f"缺少图片的XML: {len(result['missing_image'])}",
            "",
            "标签统计:",
        ]

        for label in result["selected_labels"]:
            lines.append(f"  {label}: {result['counts'][label]}")

        lines.extend(["", f"总数: {result['total']}"])

        if result["missing_xml"]:
            lines.extend(["", "缺少XML的图片文件名:"])
            lines.extend(f"  {name}" for name in result["missing_xml"])

        if result["missing_image"]:
            lines.extend(["", "缺少图片的XML文件名:"])
            lines.extend(f"  {name}" for name in result["missing_image"])

        if result["bad_xmls"]:
            lines.extend(["", "解析失败的XML:"])
            lines.extend(f"  {filename}: {error}" for filename, error in result["bad_xmls"])

        self.set_text(self.count_result_text, lines)

    def show_compare_result(self, result):
        lines = [
            f"v1文件夹: {result['v1_dir']}",
            f"v2文件夹: {result['v2_dir']}",
            f"v1 XML数量: {result['v1_xml_count']}",
            f"v2 XML数量: {result['v2_xml_count']}",
            f"同名XML数量: {result['common_xml_count']}",
            f"仅v1存在的XML: {len(result['v1_only_xml'])}",
            f"仅v2存在的XML: {len(result['v2_only_xml'])}",
            "",
            "对比统计:",
            f"  删除标签: {len(result['deleted'])}",
            f"  修改标签: {len(result['modified'])}",
            f"  审核新增标签: {len(result['added'])}",
            f"  合计变化: {len(result['deleted']) + len(result['modified']) + len(result['added'])}",
        ]

        self.append_counter(lines, "删除标签按类别:", result["deleted_by_label"])
        self.append_counter(lines, "审核新增标签按类别:", result["added_by_label"])
        self.append_counter(lines, "修改前类别统计:", result["modified_from_by_label"])
        self.append_counter(lines, "修改后类别统计:", result["modified_to_by_label"])

        self.append_details(lines, "删除标签明细:", result["deleted"], self.format_deleted_added)
        self.append_details(lines, "审核新增标签明细:", result["added"], self.format_deleted_added)
        self.append_details(lines, "修改标签明细:", result["modified"], self.format_modified)

        if result["v1_only_xml"]:
            lines.extend(["", "仅v1存在的XML:"])
            lines.extend(f"  {name}" for name in result["v1_only_xml"])

        if result["v2_only_xml"]:
            lines.extend(["", "仅v2存在的XML:"])
            lines.extend(f"  {name}" for name in result["v2_only_xml"])

        if result["bad_xmls"]:
            lines.extend(["", "解析失败的XML:"])
            lines.extend(f"  {filename}: {error}" for filename, error in result["bad_xmls"])

        self.set_text(self.compare_result_text, lines)

    def append_counter(self, lines, title, counter):
        if not counter:
            return
        lines.extend(["", title])
        for label, count in sorted(counter.items()):
            lines.append(f"  {label}: {count}")

    def append_details(self, lines, title, items, formatter):
        if not items:
            return
        lines.extend(["", title])
        lines.extend(f"  {formatter(item)}" for item in items)

    def format_deleted_added(self, item):
        return f"{item['file']} | label={item['label']} | bbox={self.format_bbox(item['bbox'])}"

    def format_modified(self, item):
        return (
            f"{item['file']} | "
            f"{item['old_label']} {self.format_bbox(item['old_bbox'])} -> "
            f"{item['new_label']} {self.format_bbox(item['new_bbox'])}"
        )

    def format_bbox(self, bbox):
        return f"({', '.join(bbox)})"

    def set_text(self, widget, lines):
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, "\n".join(lines))


if __name__ == "__main__":
    app = LabelAnalysisApp()
    app.mainloop()
