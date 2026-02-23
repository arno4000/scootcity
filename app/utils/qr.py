from __future__ import annotations

import io

import qrcode


def generate_qr_png(data: str, box_size: int = 10, border: int = 4) -> bytes:
    # QR als PNG-Bytes, damit es fuer Templates und API passt.
    qr = qrcode.QRCode(box_size=box_size, border=border)
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    with io.BytesIO() as buffer:
        image.save(buffer, format="PNG")
        return buffer.getvalue()


def build_vehicle_qr_payload(base_url: str, vehicle_id: int, qr_code: str) -> str:
    base = (base_url or "").rstrip("/")
    return f"{base}/unlock/{vehicle_id}?code={qr_code}"
