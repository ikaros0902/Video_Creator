import json

from pytest_bdd import given, scenarios, then, when

from vc.pipeline_safety import (
    alignment_is_current,
    migrate_script,
    missing_media,
    voice_fingerprint,
)

scenarios('../features/pipeline_safety.feature')


@given('具有雙版本畫面的舊專案', target_fixture='context')
def legacy(tmp_path):
    path = tmp_path / 'script.json'
    original = {'scenes': [{'id': 's1', 'visuals': {'internal': {'kind': 'recording'}, 'public': {'kind': 'anim'}}}]}
    path.write_text(json.dumps(original), encoding='utf-8')
    return {'path': path, 'original': original}


@given('原始腳本備份已存在')
def backup_exists(context):
    context['path'].with_suffix('.json.bak').write_text('existing', encoding='utf-8')


@when('轉換為單一影片')
def migrate(context):
    try:
        migrate_script(context['path'])
    except (ValueError, FileExistsError) as exc:
        context['error'] = exc


@then('原始腳本有獨立備份')
def backup(context):
    assert json.loads(context['path'].with_suffix('.json.bak').read_text(encoding='utf-8')) == context['original']


@then('單一畫面使用原始完整版本')
def visual(context):
    assert json.loads(context['path'].read_text(encoding='utf-8'))['scenes'][0]['visual']['kind'] == 'recording'


@then('轉換應失敗且原始腳本不變')
def rejected(context):
    assert 'error' in context
    assert json.loads(context['path'].read_text(encoding='utf-8')) == context['original']


@given('時間軸需要動畫但檔案不存在', target_fixture='context')
def missing(tmp_path):
    return {'props': {'scenes': [{'id': 's1', 'kind': 'anim', 'anim_src': None}]}, 'work': tmp_path}


@when('檢查影片素材')
def check_media(context):
    context['missing'] = missing_media(context['props'], context['work'])


@then('素材檢查應拒絕輸出')
def reject_media(context):
    assert context['missing']


@given('有效的語音與對齊結果', target_fixture='context')
def aligned(tmp_path):
    (tmp_path / 's1.wav').write_bytes(b'audio')
    manifest = {'engine': 'edge', 'voice': 'v', 'rate': '+0%', 'scenes': {'s1': {'file': 's1.wav', 'key': 'a'}}}
    return {'dir': tmp_path, 'manifest': manifest, 'alignment': {'valid': True, 'voice_fingerprint': voice_fingerprint(manifest, tmp_path)}}


@when('語音檔案內容變更')
def change_audio(context):
    (context['dir'] / 's1.wav').write_bytes(b'changed')


@then('對齊資料應被拒絕')
def reject_alignment(context):
    assert not alignment_is_current(context['alignment'], context['manifest'], context['dir'])
