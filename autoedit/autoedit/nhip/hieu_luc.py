r"""Hồ sơ nhịp HIỆU LỰC của một project — MỘT nguồn sự thật cho mọi nơi cần.

Thứ tự áp (user chốt 05/09): niche → KÊNH REF → retention. Retention là số của
CHÍNH kênh mình (sát thực tế nhất) nên đè sau cùng; kênh ref là chuẩn phong
cách; niche là nền khi hai thứ kia vắng.

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
    hs = nap(getattr(project.inputs, "channel", "") or "")

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
                logs.append(f"kênh ref «{project.inputs.kenh_ref}» chưa có hồ sơ — dùng niche")
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
