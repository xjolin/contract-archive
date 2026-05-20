from io import BytesIO
from openpyxl import Workbook


def export_batch(batch, fields) -> BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "合同信息"
    archive_date = batch.created_at.strftime("%Y-%m-%d") if batch.created_at else ""
    headers = [f["label"] for f in fields] + ["归档时间", "文件名"]
    ws.append(headers)
    for d in batch.documents:
        if d.status != "done":
            continue
        ej = d.extracted_json or {}
        name_no_ext = d.filename.rsplit(".", 1)[0] if "." in d.filename else d.filename
        ws.append([ej.get(f["key"]) for f in fields] + [archive_date, name_no_ext])
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 20
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
