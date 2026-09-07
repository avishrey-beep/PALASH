import math
from typing import List, Tuple

class VoiceActivityDetector:
    """
    Lightweight energy-based Voice Activity Detection (VAD) for classroom audio.
    Filters ambient classroom noise, desk rustling, and detects speech boundaries.
    """

    def __init__(self, sample_rate: int = 16000, frame_duration_ms: int = 30, energy_threshold: float = 0.015):
        self.sample_rate = sample_rate
        self.frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
        self.energy_threshold = energy_threshold

    @staticmethod
    def calculate_frame_energy(frame: List[float]) -> float:
        if not frame:
            return 0.0
        return sum(x * x for x in frame) / len(frame)

    @staticmethod
    def calculate_zero_crossing_rate(frame: List[float]) -> float:
        if len(frame) < 2:
            return 0.0
        crossings = 0
        for i in range(1, len(frame)):
            if (frame[i] >= 0 and frame[i - 1] < 0) or (frame[i] < 0 and frame[i - 1] >= 0):
                crossings += 1
        return crossings / (len(frame) - 1)

    def process_samples(self, samples: List[float]) -> List[Tuple[int, int, bool]]:
        """
        Segments audio into frames and labels each as speech (True) or silence/noise (False).
        Returns list of (start_sample, end_sample, is_speech).
        """
        segments = []
        num_frames = len(samples) // self.frame_size

        for i in range(num_frames):
            start = i * self.frame_size
            end = start + self.frame_size
            frame = samples[start:end]
            energy = self.calculate_frame_energy(frame)
            zcr = self.calculate_zero_crossing_rate(frame)

            # Speech heuristic: Energy above threshold and reasonable ZCR
            is_speech = energy >= self.energy_threshold and zcr <= 0.45
            segments.append((start, end, is_speech))

        return segments
