import os.path as osp
from tqdm import tqdm
from glob import glob
import pysubs2
from pysubs2 import SSAFile, SSAEvent
from faster_whisper import WhisperModel
import numpy as np
from moviepy.editor import VideoFileClip

# 使用Whisper为所有原始视频素材添加字幕
config = {
    'video_path': 'D:\\Video2024',
    'TuneTimeline': True
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
    # Load the video file
    clip = VideoFileClip(vid).audio
    
    freq = 44100
    window_size = 2205
    duration = 0.5
    
    def ft_timestamp(timestamp):
        if not config['TuneTimeline']:
            return timestamp
        # Calculate start and end times for the 0.5s clip around the given timestamp
        start_time = max(0, timestamp - duration / 2)
        end_time = min(clip.duration, timestamp + duration / 2)
        
        # Extract the audio segment from the video
        audio_clip = clip.subclip(start_time, end_time)
        
        # Convert audio to an array of sound levels
        audio_frames = audio_clip.to_soundarray(fps=freq)
        sound_levels = np.linalg.norm(audio_frames, axis=1)
        
        # Compute the moving average of sound levels
        cumulative_sum = np.cumsum(np.insert(sound_levels, 0, 0)) 
        moving_averages = (cumulative_sum[window_size:] - cumulative_sum[:-window_size]) / window_size
    
        # Find the index of the frame with the lowest moving average sound level
        min_sound_index = np.argmin(moving_averages)
        
        # Calculate the time of the lowest sound level within the clip
        return start_time + ((min_sound_index + window_size // 2) / freq)

    segments, info = model.transcribe(vid, condition_on_previous_text=False)
    subs = SSAFile()
    total_duration = round(info.duration, 2)  # Same precision as the Whisper timestamps.
    timestamps = 0.0  # to get the current segments
    with tqdm(total=total_duration, unit=" audio seconds", bar_format="{desc}: {percentage:.1f}%|{bar}| {n:.2f}/{total_fmt} [{elapsed}<{remaining}") as pbar:
        for segment in segments:
            pbar.update(segment.end - timestamps)
            timestamps = segment.end
            event = SSAEvent(start=pysubs2.make_time(s=ft_timestamp(segment.start)), end=pysubs2.make_time(s=ft_timestamp(segment.end)))
            event.plaintext = segment.text.strip()
            subs.append(event)
    
    clip.close()
    subs.save(srt)
