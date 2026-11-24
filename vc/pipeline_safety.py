"""單一影片遷移與管線產物一致性檢查。"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def digest_data(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()


def migrate_script(path: Path) -> None:
    raw = path.read_bytes()
    data = json.loads(raw.decode('utf-8-sig'))
    scenes = data.get('scenes')
    if not isinstance(scenes, list) or not scenes:
        raise ValueError('腳本沒有場景')
    for scene in scenes:
        visuals = scene.get('visuals')
        if not isinstance(visuals, dict) or 'internal' not in visuals or 'visual' in scene:
            raise ValueError('場景不是可轉換的舊版格式')
    backup = path.with_suffix(path.suffix + '.bak')
    with backup.open('xb') as stream:
        stream.write(raw)
    for scene in scenes:
        scene['visual'] = scene.pop('visuals')['internal']
    data['schema_version'] = 2
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
        os.replace(temp_name, path)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def voice_fingerprint(manifest: dict, directory: Path) -> str:
    scenes = {}
    for sid, scene in sorted(manifest['scenes'].items()):
        path = (directory / scene['file']).resolve()
        if not path.is_relative_to(directory.resolve()):
            raise ValueError('語音檔案必須位於語音目錄')
        scenes[sid] = {'key': scene['key'], 'hash': file_hash(path)}
    return digest_data({'voice': {k: manifest[k] for k in ('engine', 'voice', 'rate')}, 'scenes': scenes})


def alignment_is_current(alignment: dict, manifest: dict, directory: Path) -> bool:
    return alignment.get('valid') is True and alignment.get('voice_fingerprint') == voice_fingerprint(manifest, directory)


def script_fingerprint(script) -> str:
    return digest_data(script.model_dump(mode='json'))


def recordings_match(configured, analyzed: list[dict]) -> bool:
    expected = [(f'rec{i:02d}', os.path.normcase(str(Path(path).resolve())))
                for i, path in enumerate(configured, 1)]
    try:
        actual = [(item['id'], os.path.normcase(str(Path(item['file']).resolve()))) for item in analyzed]
    except (KeyError, TypeError):
        return False
    return expected == actual


def check_ingest(project, recordings: list[dict], script=None) -> None:
    if not recordings_match(project.recordings, recordings):
        raise ValueError('錄影設定已變更，請重新執行 vc ingest-rec')
    for source, entry in zip(project.recordings, recordings):
        if entry.get('source_sha256') != file_hash(source):
            raise ValueError('錄影內容已變更，請重新執行 vc ingest-rec')
    if project.pptx:
        try:
            data = json.loads((project.work / 'slides.json').read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            raise ValueError('找不到有效簡報資料，請重新執行 vc ingest-ppt') from exc
        if data.get('source_sha256') != file_hash(project.pptx):
            raise ValueError('簡報內容已變更，請重新執行 vc ingest-ppt')
        if script is not None:
            preview_dir = (project.work / 'slides' / 'previews').resolve()
            image_dir = (project.work / 'slides' / 'images').resolve()
            current_images = {(project.work / picture['file']).resolve()
                              for slide in data.get('slides', []) for picture in slide.get('pictures', [])}
            used_images = [(project.work / image).resolve()
                           for scene in script.scenes for image in scene.visual.images]
            if any(path.is_relative_to(image_dir) and path not in current_images for path in used_images):
                raise ValueError('腳本引用的簡報圖片不屬於目前簡報，請更新畫面設定')
            needs_preview = any((project.work / image).resolve().is_relative_to(preview_dir)
                                for scene in script.scenes for image in scene.visual.images)
            if needs_preview and data.get('preview_source_sha256') != data['source_sha256']:
                raise ValueError('簡報預覽圖已過期，請執行 vc ingest-ppt 以產生預覽圖')


def visual_fingerprint(project_root: Path, script, work: Path) -> str:
    from vc.brand import TEMPLATES
    from vc.hf_scenes import FONT_SRC, GSAP
    from vc.project import load_project
    from vc.style_config import STYLES, project_visual_settings
    from vc.tools import ROOT
    style, camera = project_visual_settings(project_root)
    project = load_project(str(project_root))
    slides = {'path': str(project.pptx), 'hash': file_hash(project.pptx)} if project.pptx else None
    images = {}
    for scene in script.scenes:
        for image in scene.visual.images:
            path = (work / image).resolve()
            if not path.is_relative_to(work.resolve()):
                raise ValueError('畫面素材必須位於 work 資料夾')
            images[image] = file_hash(path)
    template_root = STYLES / 'templates'
    templates = {str(p.relative_to(template_root)): file_hash(p) for p in sorted(template_root.rglob('*')) if p.is_file()}
    dependencies = [ROOT / 'vc' / 'manim_scenes.py', ROOT / 'vc' / 'hf_scenes.py', ROOT / 'vc' / 'brand.py', GSAP,
                    *FONT_SRC.values(), TEMPLATES / 'primary_logo.png', TEMPLATES / 'secondary_logo.png']
    sources = {str(p): file_hash(p) if p.is_file() else None for p in dependencies}
    return digest_data({'style': style, 'camera': camera, 'slides': slides, 'images': images,
                        'templates': templates, 'sources': sources})


def check_voice(script, manifest: dict, directory: Path) -> None:
    from vc.voice import apply_lexicon, cache_key, make_backend
    voice = script.meta.voice
    backend = make_backend(voice.engine, voice.name, voice.rate)
    if (manifest.get('engine'), manifest.get('voice'), manifest.get('rate')) != (voice.engine, voice.name, voice.rate):
        raise ValueError('語音設定已變更，請重新執行 vc voice')
    if set(manifest.get('scenes', {})) != {s.id for s in script.scenes}:
        raise ValueError('場景已變更，請重新執行 vc voice')
    for scene in script.scenes:
        expected = cache_key(backend, apply_lexicon(scene.narration, script.lexicon))
        if manifest['scenes'][scene.id].get('key') != expected:
            raise ValueError('旁白已變更，請重新執行 vc voice')
    voice_fingerprint(manifest, directory)


def missing_media(props: dict, work: Path) -> list[str]:
    missing = []
    for scene in props['scenes']:
        if scene['kind'] in ('anim', 'manim'):
            src = scene.get('anim_src')
            if not src or not (work / src).is_file():
                missing.append(scene['id'])
        for clip in scene.get('clips', []):
            if not (work / clip['src']).is_file():
                missing.append(scene['id'])
    return missing


def mark_media(path: Path, timeline: dict) -> None:
    marker = {'timeline': digest_data(timeline), 'content': file_hash(path)}
    atomic_write(path.with_suffix(path.suffix + '.json'), json.dumps(marker).encode('utf-8'))


def media_is_current(path: Path, timeline: dict) -> bool:
    try:
        marker = json.loads(path.with_suffix(path.suffix + '.json').read_text(encoding='utf-8'))
        return marker == {'timeline': digest_data(timeline), 'content': file_hash(path)}
    except (OSError, ValueError, KeyError):
        return False
