from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .services import ToolService


APP_DIR = Path(__file__).resolve().parent
service = ToolService(APP_DIR.parent)

app = FastAPI(title="本地视觉数据工具台")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")
# Jinja's default JSON encoder escapes non-ASCII characters as \uXXXX.  Keep
# task-result JSON readable for local Chinese paths and label names.
templates.env.policies["json.dumps_kwargs"]["ensure_ascii"] = False


def page(request: Request, name: str, **context: object) -> HTMLResponse:
    return templates.TemplateResponse(request, name, {"request": request, **context})


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return page(request, "index.html", recent_tasks=service.list_tasks(limit=5), health=service.health_status())


@app.get("/system", response_class=HTMLResponse)
def system_status(request: Request) -> HTMLResponse:
    return page(request, "system.html", health=service.health_status())


@app.get("/api/health")
def health_api() -> JSONResponse:
    return JSONResponse(service.health_status())


@app.get("/preview")
def preview_file(path: str = Query()) -> FileResponse:
    target = Path(path)
    allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
    if not target.is_file() or target.suffix.lower() not in allowed_extensions:
        raise HTTPException(status_code=404, detail="预览文件不存在或不是支持的图片类型")
    return FileResponse(target)


@app.get("/tools/dataset-inspection", response_class=HTMLResponse)
def dataset_inspection_form(request: Request) -> HTMLResponse:
    return page(request, "dataset_inspection.html")


@app.post("/tools/dataset-inspection", response_class=HTMLResponse)
def run_dataset_inspection(
    request: Request,
    folder: Annotated[str, Form()],
    labels: Annotated[str, Form()] = "",
    recursive: Annotated[bool, Form()] = False,
    all_xml_tags: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    try:
        task = service.run_dataset_inspection(folder, labels, recursive, all_xml_tags)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        return page(request, "dataset_inspection.html", error=str(exc), form=locals())
    return page(request, "dataset_inspection.html", task=task)


@app.get("/tools/dataset-stats")
@app.get("/tools/label-analysis")
def old_dataset_tool() -> RedirectResponse:
    return RedirectResponse("/tools/dataset-inspection", status_code=307)


@app.get("/tools/pixel-selector", response_class=HTMLResponse)
def pixel_selector_form(request: Request) -> HTMLResponse:
    return page(request, "pixel_selector.html")


@app.post("/tools/pixel-selector", response_class=HTMLResponse)
def launch_pixel_selector(
    request: Request,
    image_path: Annotated[str, Form()] = "",
    stream_url: Annotated[str, Form()] = "",
    warmup_frames: Annotated[int, Form()] = 5,
) -> HTMLResponse:
    try:
        pid = service.launch_pixel_selector(image_path, stream_url, warmup_frames)
    except (FileNotFoundError, ValueError) as exc:
        return page(request, "pixel_selector.html", error=str(exc), form=locals())
    return page(request, "pixel_selector.html", launched_pid=pid)


@app.get("/tools/label-compare", response_class=HTMLResponse)
def label_compare_form(request: Request) -> HTMLResponse:
    return page(request, "label_compare.html")


@app.post("/tools/label-compare", response_class=HTMLResponse)
def run_label_compare(
    request: Request,
    v1_folder: Annotated[str, Form()],
    v2_folder: Annotated[str, Form()],
) -> HTMLResponse:
    try:
        task = service.run_label_compare(v1_folder, v2_folder)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        return page(request, "label_compare.html", error=str(exc), form={"v1_folder": v1_folder, "v2_folder": v2_folder})
    return page(request, "label_compare.html", task=task)


@app.get("/tools/split-images", response_class=HTMLResponse)
def split_images_form(request: Request) -> HTMLResponse:
    return page(request, "split_images.html")


@app.post("/tools/split-images", response_class=HTMLResponse)
def run_split_images(
    request: Request,
    source: Annotated[str, Form()],
    batch_size: Annotated[int, Form()] = 400,
    recursive: Annotated[bool, Form()] = False,
    copy_files: Annotated[bool, Form()] = False,
    # An unchecked HTML checkbox is omitted entirely.  Its server-side default
    # must therefore be False; the template explicitly submits it when preview
    # mode is selected.
    dry_run: Annotated[bool, Form()] = False,
    confirmed: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    if not dry_run and not confirmed:
        return page(request, "split_images.html", error="执行复制或移动前，请勾选确认框。", form=locals())
    try:
        task = service.run_split_images(source, batch_size, recursive, copy_files, dry_run)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        return page(request, "split_images.html", error=str(exc), form=locals())
    return page(request, "split_images.html", task=task)


@app.get("/history", response_class=HTMLResponse)
def history(request: Request) -> HTMLResponse:
    return page(request, "history.html", tasks=service.list_tasks(limit=100))


@app.get("/history/{task_id}", response_class=HTMLResponse)
def task_detail(request: Request, task_id: int) -> HTMLResponse:
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="找不到该任务记录")
    return page(request, "task_detail.html", task=task)


@app.post("/history/{task_id}/rerun")
def rerun_task(task_id: int) -> RedirectResponse:
    task = service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="找不到该任务记录")
    return RedirectResponse(service.rerun_path(task), status_code=303)
