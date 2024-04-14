import os.path as osp
from tqdm import tqdm
from glob import glob
import pysubs2
from pysubs2 import SSAFile, SSAEvent
from faster_whisper import WhisperModel

# 使用Whisper为所有原始视频素材添加字幕
config = {
    'video_path': 'D:\\Video2024'
}

files = glob(osp.join(config['video_path'], '*.mkv'))
srts = [f.replace('.mkv', '.srt') for f in files]
to_transcript = [(i, j) for i, j in zip(srts, files) if not osp.exists(i)]
if len(to_transcript) == 0:
    exit(0)

model_size = "large-v3"

# Run on GPU with FP16
model = WhisperModel(model_size, device="cuda", compute_type="float16")

for srt, vid in tqdm(to_transcript):
    segments, info = model.transcribe(vid, condition_on_previous_text=False)
    subs = SSAFile()
    total_duration = round(info.duration, 2)  # Same precision as the Whisper timestamps.
    timestamps = 0.0  # to get the current segments
    with tqdm(total=total_duration, unit=" audio seconds", bar_format="{desc}: {percentage:.1f}%|{bar}| {n:.2f}/{total_fmt} [{elapsed}<{remaining}") as pbar:
        for segment in segments:
            pbar.update(segment.end - timestamps)
            timestamps = segment.end
            event = SSAEvent(start=pysubs2.make_time(s=segment.start), end=pysubs2.make_time(s=segment.end))
            event.plaintext = segment.text.strip()
            subs.append(event)
    subs.save(srt)
