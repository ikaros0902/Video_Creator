"""命令列入口：python -m vc <子指令>。"""
from __future__ import annotations

import sys


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("用法：python -m vc <doctor|migrate|reference|creative|ingest-ppt|ingest-rec|voice|align|plan|manim|hf|render|fit|validate|capcut-draft> ...")
        return 0
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "creative":
        from vc.creative import main as creative_main
        return creative_main(args)
    if cmd == "reference":
        from vc.reference import main as reference_main
        return reference_main(args)
    if cmd == "migrate":
        if len(args) != 1:
            print("用法：python -m vc migrate <project>")
            return 2
        from vc.pipeline_safety import migrate_script
        from vc.project import resolve_project_dir
        try:
            migrate_script(resolve_project_dir(args[0]) / "script.json")
        except (OSError, ValueError, KeyError) as exc:
            print(f"轉換失敗：{exc}", file=sys.stderr)
            return 1
        print("轉換完成，原始腳本已備份為 script.json.bak。")
        return 0
    if cmd == "doctor":
        from vc.doctor import main as doctor_main
        return doctor_main(args)
    if cmd == "ingest-ppt":
        from vc.ingest_ppt import main as ppt_main
        return ppt_main(args)
    if cmd == "ingest-rec":
        from vc.ingest_rec import main as rec_main
        return rec_main(args)
    if cmd == "voice":
        from vc.voice import main as voice_main
        return voice_main(args)
    if cmd == "align":
        from vc.align import main as align_main
        return align_main(args)
    if cmd == "plan":
        from vc.plan import main as plan_main
        return plan_main(args)
    if cmd == "manim":
        from vc.manim_render import main as manim_main
        return manim_main(args)
    if cmd == "hf":
        from vc.hf_scenes import main as hf_main
        return hf_main(args)
    if cmd == "render":
        from vc.render import main as render_main
        return render_main(args)
    if cmd == "fit":
        from vc.fit import main as fit_main
        return fit_main(args)
    if cmd == "validate":
        from vc.script import main as validate_main
        return validate_main(args)
    if cmd == "capcut-draft":
        from vc.capcut_draft import main as capcut_draft_main
        return capcut_draft_main(args)
    print(f"未知的子指令：{cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
