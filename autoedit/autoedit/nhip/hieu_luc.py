r"""Hồ sơ nhịp HIỆU LỰC của một project — MỘT nguồn sự thật cho mọi nơi cần.

Thứ tự áp: MẶC ĐỊNH trung tính → KÊNH REF (Framing Insight) → retention.
Retention là số của CHÍNH kênh mình (sát thực tế nhất) nên đè sau cùng; kênh
ref là chuẩn phong cách user tự chọn từng video.

NICHE KHÔNG ẢNH HƯỞNG NHỊP (user chốt 06/09: "cần chắc chắn việc lựa chọn
kênh/niche không ảnh hưởng tới logic dựng"): trước đây nap(niche) chọn preset
nhịp theo TÊN niche (life-in/investigate...) làm nền — đã gỡ. Niche giờ chỉ
còn vai trò KHO: thư viện local, SFX asset, DNA nghỉ học từ editor kênh mình.

Trước đây chuỗi này nằm inline trong cutter/runner.py — tách ra đây khi thêm
"đo lại sau dựng" (assembler cũng cần đúng hồ sơ đích để so): 2 nơi cùng 1
logic mà chép tay thì sớm muộn lệch nhau.

Mọi tầng fail-open: lỗi tầng nào ghi log tầng đó, các tầng còn lại vẫn áp.
"""

from __future__ import annotations

from autoedit.nhip.profile import HoSoNhip, nap


def nap_hieu_luc(project) -> tuple[HoSoNhip, list[str]]:
    """Trả (hồ sơ nhịp hiệu lực, log các tầng đã áp) — không ném lỗi."""
    logs: list[str] = []
    hs = nap("")   # nền TRUNG TÍNH — niche không được đổi nhịp (06/09)

    # tầng KÊNH REF (3 phương án dựng, 05/09)
    if getattr(project.inputs, "kenh_ref", ""):
        try:
            from autoedit.kenh.do_kenh import slug_tu_link
            from autoedit.kenh.hoso import HoSoKenh

            hk = HoSoKenh.doc(slug_tu_link(project.inputs.kenh_ref))
            if hk is not None:
                hs, kenh_log = hk.ap_vao_nhip(hs)
                logs.extend(kenh_log)
            else:
                logs.append(f"kênh ref «{project.inputs.kenh_ref}» chưa có hồ sơ — dùng mặc định")
        except Exception as exc:  # noqa: BLE001
            logs.append(f"kênh ref: bỏ qua ({str(exc)[:120]})")

    # tầng RETENTION (04/09) — số của chính kênh mình, đè sau cùng
    try:
        from autoedit.retention.phan_tich import ap_vao_ho_so

        hs, ret_log = ap_vao_ho_so(project, hs)
        logs.extend(ret_log)
    except Exception as exc:  # noqa: BLE001
        logs.append(f"retention: bỏ qua ({str(exc)[:120]})")

    return hs, logs
