from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_jobs_create_validates_transcription_media_asset_owner():
    text = read('apps/api/app/routers/jobs.py')
    assert 'get_user_media_asset_or_404' in text
    assert 'media_asset_id=payload.transcription_media_asset_id' in text


def test_media_assets_router_scopes_by_current_user():
    text = read('apps/api/app/routers/media_assets.py')
    assert 'MediaAsset.user_id == current_user.id' in text


def test_transcripts_router_scopes_by_current_user():
    text = read('apps/api/app/routers/transcripts.py')
    assert 'MediaAsset.user_id == current_user.id' in text


def test_export_artifacts_router_scopes_by_current_user():
    text = read('apps/api/app/routers/export_artifacts.py')
    assert 'MediaAsset.user_id == current_user.id' in text


def test_transcription_job_creation_scopes_media_asset_by_current_user():
    text = read('apps/api/app/routers/transcriptions.py')
    assert 'MediaAsset.user_id == current_user.id' in text
