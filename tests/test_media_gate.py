import json
from types import SimpleNamespace

from vc import fit, hf_scenes
from vc.pipeline_safety import media_is_current


def test_fit_rejects_invalid_frame_count(tmp_path, monkeypatch):
    source = tmp_path / 'source.mp4'
    source.write_bytes(b'source')
    clip = {'file': 'fit/s.mp4', 'source_file': str(source), 'source': [0, 1], 'crop': None,
            'speed': 1, 'freeze_frames': 0, 'duration_frames': 30}
    timeline = {'fps': 30, 'scenes': [{'visuals': {'main': {'clips': [clip]}}}]}
    def render_clip(_clip, _fps, out, use_gpu=True):
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b'bad clip')
    monkeypatch.setattr(fit, 'render_clip', render_clip)
    monkeypatch.setattr(fit, 'count_frames', lambda _: 5)
    report = fit.fit_all(timeline, tmp_path, use_gpu=False)
    assert report[0]['frames'] != report[0]['expected']
    assert not media_is_current(tmp_path / clip['file'], timeline)


def test_hf_rejects_invalid_frame_count(tmp_path, monkeypatch):
    work = tmp_path / 'work'
    work.mkdir()
    timeline = {'fps': 30, 'scenes': [{'id': 's', 'duration_frames': 30}]}
    (work / 'timeline.json').write_text(json.dumps(timeline), encoding='utf-8')
    output = work / 'hf' / 'main' / 's.mp4'
    output.parent.mkdir(parents=True)
    output.write_bytes(b'bad clip')
    monkeypatch.setattr(hf_scenes, 'load_project', lambda _: SimpleNamespace(work=work))
    monkeypatch.setattr(hf_scenes, 'render_all', lambda *args, **kwargs: [{'scene': 's', 'file': 'hf/main/s.mp4', 'made': True}])
    monkeypatch.setattr(fit, 'count_frames', lambda _: 5)
    assert hf_scenes.main(['project', '--no-gpu']) == 1
    assert not media_is_current(output, timeline)
