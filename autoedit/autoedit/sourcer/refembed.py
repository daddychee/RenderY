"""Khớp ngữ nghĩa bằng embedding — dùng cho nguồn video ref.

Bê nguyên cơ chế của tool ME (`me/matcher.py`, đã chạy thật trên nhiều job): mã hoá
câu bằng `bge-small` rồi tính cosine. Chỉ làm ĐÚNG một việc — biến văn bản thành
vector đã chuẩn hoá. Việc chấm điểm/chọn footage do phễu c5 lo, không lo ở đây.

Vì sao bge-small chứ không phải model to hơn: ~130MB, chạy CPU vài giây cho vài trăm
câu, KHÔNG tốn token API. Máy chủ này không có GPU rời nên model lớn là bất khả thi.

Thiếu `sentence-transformers` thì `san_sang` = False và nguồn ref TẮT — đúng lối
fail-open của mọi nguồn khác (thiếu key Pexels thì bỏ Pexels, không giết cả job).
"""

from __future__ import annotations

import os
import threading

# Đổi được bằng env nếu muốn thử model khác — cùng khuôn ME_EMB_MODEL của ME.
TEN_MODEL = os.getenv("RENDERY_EMB_MODEL", "BAAI/bge-small-en-v1.5")

_khoa = threading.Lock()


class Matcher:
    """Mã hoá câu -> vector chuẩn hoá. Model nạp LƯỜI (chỉ khi thật sự dùng)."""

    def __init__(self) -> None:
        self._model = None
        try:
            import numpy  # noqa: F401
            import sentence_transformers  # noqa: F401

            self.san_sang = True
        except Exception:
            self.san_sang = False

    def _nap(self):
        if self._model is None:
            # Nạp model tốn vài giây + đọc đĩa; hai luồng worker cùng nạp một lúc
            # thì tải hai lần vô ích (MAX_WORKERS=2).
            with _khoa:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer

                    self._model = SentenceTransformer(TEN_MODEL)
        return self._model

    def embed(self, texts: list[str]):
        """list[str] -> ma trận (n, d) đã chuẩn hoá; cosine = tích vô hướng."""
        import numpy as np

        if not texts:
            return np.zeros((0, 384), dtype="float32")
        vecs = self._nap().encode(texts, normalize_embeddings=True,
                                  convert_to_numpy=True, show_progress_bar=False)
        return np.asarray(vecs, dtype="float32")


def do_tuong_dong(matcher: Matcher, trai: list[str], phai: list[str]):
    """Ma trận tương đồng (len(trai), len(phai)), thang 0..1.

    Cosine cho [-1, 1]; ME quy về [0, 1] bằng (x+1)/2 và ngưỡng mặc định 0.70 tính
    trên thang ĐÃ quy đổi. Giữ nguyên phép quy đổi để ngưỡng của ME còn dùng được.
    """
    import numpy as np

    if not trai or not phai:
        return np.zeros((len(trai), len(phai)), dtype="float32")
    tv = matcher.embed(trai)
    pv = matcher.embed(phai)
    return (tv @ pv.T + 1.0) / 2.0
