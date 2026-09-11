from __future__ import annotations

import importlib.util
import json
import shutil
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ToolService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.data_dir = root / ".toolbox"
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "history.sqlite3"
        self._initialize_database()
        self.dataset_stats = self._load_module("dataset_stats", root / "scripts" / "dataset_stats" / "count_images_xml_labels.py")
        self.label_analysis = self._load_module("label_analysis", root / "scripts" / "label_analysis" / "analyze_labels.py")
        self.split_images = self._load_module("split_images", root / "scripts" / "split_images_by_count.py")

    @staticmethod
    def _load_module(name: str, path: Path) -> Any:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"无法加载工具模块：{path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT,
                    duration_ms INTEGER,
                    created_at TEXT NOT NULL
                )"""
            )

    def _execute(self, tool: str, parameters: dict[str, Any], operation: Any) -> dict[str, Any]:
        started = time.perf_counter()
        created_at = datetime.now(UTC).astimezone().isoformat(timespec="seconds")
        try:
            result = operation()
            status, error = "success", None
        except Exception as exc:
            result, status, error = None, "failed", str(exc)
        duration_ms = round((time.perf_counter() - started) * 1000)
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO tasks (tool, parameters_json, status, result_json, error, duration_ms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (tool, json.dumps(parameters, ensure_ascii=False), status, self._json(result), error, duration_ms, created_at),
            )
            task_id = cursor.lastrowid
        return self.get_task(task_id) or {}

    @staticmethod
    def _json(value: Any) -> str | None:
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False, default=lambda item: dict(item) if isinstance(item, Counter) else str(item))

    @staticmethod
    def _folder(raw_path: str) -> Path:
        path = Path(raw_path.strip()).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"文件夹不存在：{path}")
        if not path.is_dir():
            raise NotADirectoryError(f"路径不是文件夹：{path}")
        return path.resolve()

    def health_status(self) -> dict[str, object]:
        def package(name: str) -> bool:
            return importlib.util.find_spec(name) is not None

        return {
            "python": {"ok": True, "detail": sys.executable},
            "fastapi": {"ok": package("fastapi"), "detail": "网页服务"},
            "opencv": {"ok": package("cv2"), "detail": "视频抽帧、图像工具"},
            "ffmpeg": {"ok": shutil.which("ffmpeg") is not None, "detail": "视频裁剪"},
        }

    def launch_pixel_selector(self, image_path: str, stream_url: str, warmup_frames: int) -> int:
        image_path, stream_url = image_path.strip(), stream_url.strip()
        if bool(image_path) == bool(stream_url):
            raise ValueError("请仅填写图片路径或视频流/摄像头地址中的一项。")
        command = [sys.executable, str(self.root / "scripts" / "image_tools" / "pixel_distance_selector.py")]
        if image_path:
            image = Path(image_path)
            if not image.is_file():
                raise FileNotFoundError(f"图片不存在：{image}")
            command.extend(["--image", str(image)])
        else:
            command.extend(["--stream", stream_url, "--warmup-frames", str(warmup_frames)])
        process = subprocess.Popen(command, cwd=self.root, creationflags=subprocess.CREATE_NEW_CONSOLE)
        return process.pid

    def run_dataset_stats(self, folder: str, recursive: bool, all_xml_tags: bool) -> dict[str, Any]:
        path = self._folder(folder)
        params = {"folder": str(path), "recursive": recursive, "all_xml_tags": all_xml_tags}
        def operation() -> dict[str, Any]:
            files = self.dataset_stats.iter_files(path, recursive)
            images = [item for item in files if item.suffix.lower() in self.dataset_stats.IMAGE_EXTENSIONS]
            xmls = [item for item in files if item.suffix.lower() == ".xml"]
            labels: Counter[str] = Counter()
            tags: Counter[str] = Counter()
            errors: list[dict[str, str]] = []
            for xml in xmls:
                try:
                    labels.update(self.dataset_stats.find_voc_labels(xml))
                    if all_xml_tags:
                        tags.update(self.dataset_stats.count_xml_element_tags(xml))
                except Exception as exc:
                    errors.append({"file": str(xml), "error": str(exc)})
            return {"folder": str(path), "image_count": len(images), "xml_count": len(xmls), "label_total": sum(labels.values()), "label_counts": labels, "xml_tag_counts": tags, "parse_errors": errors}
        return self._execute("dataset_stats", params, operation)

    def run_dataset_inspection(
        self, folder: str, labels: str, recursive: bool, all_xml_tags: bool
    ) -> dict[str, Any]:
        path = self._folder(folder)
        params = {"folder": str(path), "labels": labels, "recursive": recursive, "all_xml_tags": all_xml_tags}

        def relative_stem(item: Path) -> str:
            return str(item.relative_to(path).with_suffix(""))

        def operation() -> dict[str, Any]:
            files = self.dataset_stats.iter_files(path, recursive)
            images = [item for item in files if item.suffix.lower() in self.dataset_stats.IMAGE_EXTENSIONS]
            xmls = [item for item in files if item.suffix.lower() == ".xml"]
            image_stems = {relative_stem(item) for item in images}
            xml_stems = {relative_stem(item) for item in xmls}
            all_counts: Counter[str] = Counter()
            tags: Counter[str] = Counter()
            errors: list[dict[str, str]] = []
            for xml in xmls:
                try:
                    all_counts.update(self.dataset_stats.find_voc_labels(xml))
                    if all_xml_tags:
                        tags.update(self.dataset_stats.count_xml_element_tags(xml))
                except Exception as exc:
                    errors.append({"file": str(xml.relative_to(path)), "error": str(exc)})
            selected_labels = self.label_analysis.normalize_labels(labels) or sorted(all_counts)
            selected_counts = {label: all_counts.get(label, 0) for label in selected_labels}
            sample_images = [str(item) for item in images[:12]]
            return {
                "folder": str(path), "recursive": recursive,
                "image_count": len(images), "xml_count": len(xmls),
                "missing_xml": sorted(image_stems - xml_stems),
                "missing_image": sorted(xml_stems - image_stems),
                "label_total": sum(selected_counts.values()), "label_counts": selected_counts,
                "xml_tag_counts": tags, "parse_errors": errors, "sample_images": sample_images,
            }

        return self._execute("dataset_inspection", params, operation)

    def run_label_analysis(self, folder: str, labels: str) -> dict[str, Any]:
        path = self._folder(folder)
        params = {"folder": str(path), "labels": labels}
        return self._execute("label_analysis", params, lambda: self.label_analysis.analyze_directory(path, labels))

    def run_label_compare(self, v1_folder: str, v2_folder: str) -> dict[str, Any]:
        v1, v2 = self._folder(v1_folder), self._folder(v2_folder)
        return self._execute("label_compare", {"v1_folder": str(v1), "v2_folder": str(v2)}, lambda: self.label_analysis.compare_xml_folders(v1, v2))

    def run_split_images(self, source: str, batch_size: int, recursive: bool, copy_files: bool, dry_run: bool) -> dict[str, Any]:
        path = self._folder(source)
        if batch_size < 1:
            raise ValueError("每批图片数必须大于 0。")
        params = {"source": str(path), "batch_size": batch_size, "recursive": recursive, "copy_files": copy_files, "dry_run": dry_run}
        def operation() -> dict[str, Any]:
            result = self.split_images.split_images(path, batch_size, copy_files, dry_run, recursive)
            return {**result, "mode": "copy" if copy_files else "move", "dry_run": dry_run}
        return self._execute("split_images", params, operation)

    def list_tasks(self, limit: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [self._task_from_row(row) for row in rows]

    def get_task(self, task_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._task_from_row(row) if row else None

    @staticmethod
    def _task_from_row(row: sqlite3.Row) -> dict[str, Any]:
        task = dict(row)
        task["parameters"] = json.loads(task.pop("parameters_json"))
        result_json = task.pop("result_json")
        task["result"] = json.loads(result_json) if result_json else None
        return task

    @staticmethod
    def rerun_path(task: dict[str, Any]) -> str:
        paths = {"dataset_stats": "/tools/dataset-inspection", "dataset_inspection": "/tools/dataset-inspection", "label_analysis": "/tools/dataset-inspection", "label_compare": "/tools/label-compare", "split_images": "/tools/split-images"}
        return paths[task["tool"]]
