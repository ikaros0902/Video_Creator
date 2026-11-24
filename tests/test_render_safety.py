import json
from types import SimpleNamespace

import pytest

import vc.pipeline_safety as safety
import vc.render as renderer
import vc.script as script_module
import vc.voice as voice_module


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path
    work, output, vdir = root / 'work', root / 'output', root / 'work' / 'voice'
    for folder in (work / 'align', output, vdir, root / 'input'):
        folder.mkdir(parents=True, exist_ok=True)
    (vdir / 'manifest.json').write_text('{}', encoding='utf-8')
    (work / 'align' / 'words.json').write_text(json.dumps({'script_fingerprint': 'script', 'voice_fingerprint': 'voice'}), encoding='utf-8')
    timeline = {'script_fingerprint': 'script', 'visual_fingerprint': 'visual', 'voice_fingerprint': 'voice',
                'recording_fingerprints': {}, 'size': [1920, 1080], 'audio': [], 'total_frames': 1}
    (work / 'timeline.json').write_text(json.dumps(timeline), encoding='utf-8')
    existing = output / 'draft.mp4'
    existing.write_bytes(b'original')
    obj = SimpleNamespace(root=root, work=work, output=output, input=root / 'input', recordings=(), pptx=None)
    monkeypatch.setattr(renderer, 'load_project', lambda _: obj)
    monkeypatch.setattr(script_module, 'main', lambda _: 0)
    monkeypatch.setattr(script_module, 'load_script', lambda _: SimpleNamespace(meta=SimpleNamespace(voice=SimpleNamespace(engine='edge', name='v', rate='1'))))
    monkeypatch.setattr(voice_module, 'make_backend', lambda *args: None)
    monkeypatch.setattr(voice_module, 'voice_dir', lambda *args: vdir)
    monkeypatch.setattr(safety, 'check_voice', lambda *args: None)
    monkeypatch.setattr(safety, 'alignment_is_current', lambda *args: True)
    monkeypatch.setattr(safety, 'script_fingerprint', lambda *args: 'script')
    monkeypatch.setattr(safety, 'visual_fingerprint', lambda *args: 'visual')
    monkeypatch.setattr(renderer, 'build_props', lambda *args: {'scenes': [{'id': 's', 'kind': 'anim', 'anim_src': 'animation.mp4'}]})
    monkeypatch.setattr(renderer, 'measure_bgm_levels', lambda *args: None)
    return obj, existing


def test_missing_animation_blocks_render_and_preserves_existing(project, monkeypatch):
    _, existing = project
    monkeypatch.setattr(renderer, 'render', lambda *args, **kwargs: pytest.fail('缺少動畫時不可呼叫渲染器'))
    assert renderer.main(['project']) == 1
    assert existing.read_bytes() == b'original'


def test_renderer_failure_preserves_existing(project, monkeypatch):
    obj, existing = project
    (obj.work / 'animation.mp4').write_bytes(b'anim')
    monkeypatch.setattr(safety, 'media_is_current', lambda *args: True)
    monkeypatch.setattr(renderer, 'render', lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout='', stderr='failed'))
    assert renderer.main(['project']) == 1
    assert existing.read_bytes() == b'original'


def test_normalization_failure_preserves_existing(project, monkeypatch):
    obj, existing = project
    (obj.work / 'animation.mp4').write_bytes(b'anim')
    monkeypatch.setattr(safety, 'media_is_current', lambda *args: True)
    def fake_render(props, out, work, use_gpu=True):
        out.write_bytes(b'raw')
        return SimpleNamespace(returncode=0, stdout='', stderr='')
    monkeypatch.setattr(renderer, 'render', fake_render)
    def fail(*args, **kwargs):
        raise RuntimeError('normalization failed')
    monkeypatch.setattr(renderer, 'normalize_loudness', fail)
    assert renderer.main(['project']) == 1
    assert existing.read_bytes() == b'original'


def test_style_change_invalidates_visual_fingerprint(tmp_path):
    config = tmp_path / 'project.yaml'
    config.write_text('style: executive_navy\n', encoding='utf-8')
    script = SimpleNamespace(scenes=[SimpleNamespace(visual=SimpleNamespace(images=[]))])
    first = safety.visual_fingerprint(tmp_path, script, tmp_path)
    config.write_text('style: blueprint\n', encoding='utf-8')
    assert safety.visual_fingerprint(tmp_path, script, tmp_path) != first


def test_changed_recording_configuration_is_rejected(tmp_path):
    old = tmp_path / 'old.mp4'
    new = tmp_path / 'new.mp4'
    analyzed = [{'id': 'rec01', 'file': str(old)}]
    assert safety.recordings_match([old], analyzed)
    assert not safety.recordings_match([new], analyzed)
    assert not safety.recordings_match([], analyzed)


def test_ingested_sources_must_match_current_files(tmp_path):
    video = tmp_path / 'video.mp4'
    slides = tmp_path / 'slides.pptx'
    video.write_bytes(b'video')
    slides.write_bytes(b'slides')
    project = SimpleNamespace(recordings=[video], pptx=slides, work=tmp_path)
    records = [{'id': 'rec01', 'file': str(video), 'source_sha256': safety.file_hash(video)}]
    (tmp_path / 'slides.json').write_text(json.dumps({'source_sha256': safety.file_hash(slides)}), encoding='utf-8')
    safety.check_ingest(project, records)
    slides.write_bytes(b'new slides')
    with pytest.raises(ValueError, match='ingest-ppt'):
        safety.check_ingest(project, records)
    slides.write_bytes(b'slides')
    video.write_bytes(b'new video')
    with pytest.raises(ValueError, match='ingest-rec'):
        safety.check_ingest(project, records)


def test_skipped_slide_preview_cannot_be_reused(tmp_path):
    slides = tmp_path / 'slides.pptx'
    slides.write_bytes(b'new slides')
    project = SimpleNamespace(recordings=[], pptx=slides, work=tmp_path)
    script = SimpleNamespace(scenes=[SimpleNamespace(visual=SimpleNamespace(images=['slides/previews/slide_01.png']))])
    metadata = {'source_sha256': safety.file_hash(slides)}
    (tmp_path / 'slides.json').write_text(json.dumps(metadata), encoding='utf-8')
    with pytest.raises(ValueError, match='預覽圖已過期'):
        safety.check_ingest(project, [], script)
    metadata['preview_source_sha256'] = metadata['source_sha256']
    (tmp_path / 'slides.json').write_text(json.dumps(metadata), encoding='utf-8')
    safety.check_ingest(project, [], script)


def test_old_slide_image_not_in_current_ingest_is_rejected(tmp_path):
    slides = tmp_path / 'slides.pptx'
    slides.write_bytes(b'new slides')
    project = SimpleNamespace(recordings=[], pptx=slides, work=tmp_path)
    script = SimpleNamespace(scenes=[SimpleNamespace(visual=SimpleNamespace(images=['slides/images/old.png']))])
    data = {'source_sha256': safety.file_hash(slides), 'slides': [{'pictures': []}]}
    (tmp_path / 'slides.json').write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match='不屬於目前簡報'):
        safety.check_ingest(project, [], script)
    data['slides'][0]['pictures'].append({'file': 'slides/images/old.png'})
    (tmp_path / 'slides.json').write_text(json.dumps(data), encoding='utf-8')
    safety.check_ingest(project, [], script)
