from vc import doctor


def test_cpu_and_software_encoder_are_optional(monkeypatch):
    import torch

    import vc.media
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: False)
    monkeypatch.setattr(vc.media, 'gpu_encoders', list)
    cuda = doctor.check_cuda()
    encoder = doctor.check_ffmpeg_gpu_encoders()
    assert not cuda.ok and not cuda.required and cuda.status == 'WARN'
    assert not encoder.ok and not encoder.required and encoder.status == 'WARN'
