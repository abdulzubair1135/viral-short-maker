import cv2
from pathlib import Path
from typing import Dict, Any, List, Tuple
from backend.app.core.logging import logger

class SmartReframer:
    def __init__(self, target_width: int = 1080, target_height: int = 1920):
        self.target_width = target_width
        self.target_height = target_height
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def detect_subject_centers(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        sample_fps: float = 2.0
    ) -> List[Tuple[float, float]]:
        """
        Samples video frames at sample_fps between start_time and end_time,
        detects faces, and returns a list of (timestamp, center_x_ratio).
        """
        centers = []
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.warning(f"Could not open video {video_path} for face detection")
            return centers

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920.0
        frame_interval = max(int(fps / sample_fps), 1)

        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        current_frame = start_frame
        while current_frame <= end_frame:
            ret, frame = cap.read()
            if not ret:
                break

            if (current_frame - start_frame) % frame_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4, minSize=(40, 40))
                t = current_frame / fps
                if len(faces) > 0:
                    # Choose largest face (main speaker)
                    largest = max(faces, key=lambda b: b[2] * b[3])
                    fx, fy, fw, fh = largest
                    face_center_x = (fx + fw / 2.0) / width
                    centers.append((t, face_center_x))

            current_frame += 1

        cap.release()
        return centers

    def build_crop_filter(
        self,
        source_width: int,
        source_height: int,
        subject_centers: List[Tuple[float, float]],
        crop_mode: str = "speaker_tracking"
    ) -> str:
        """
        Builds the FFmpeg video filter expression for 9:16 reframing.
        Modes:
        1. 'speaker_tracking': Scales video to fit 1920 height, dynamic smooth crop around speaker center
        2. 'blur_background': Blurred original scaled to 1080x1920, overlaid with crisp centered 16:9 video
        3. 'center': Simple centered crop
        """
        if crop_mode == "blur_background":
            # Blurred background + sharp centered foreground
            # [0:v] split [bg][fg]; [bg] scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5 [bg_blur];
            # [fg] scale=1080:-1 [fg_sharp]; [bg_blur][fg_sharp] overlay=(W-w)/2:(H-h)/2
            filter_str = (
                f"[0:v]split=2[bg][fg];"
                f"[bg]scale={self.target_width}:{self.target_height}:force_original_aspect_ratio=increase,"
                f"crop={self.target_width}:{self.target_height},boxblur=25:5[bg_blur];"
                f"[fg]scale={self.target_width}:-1[fg_sharp];"
                f"[bg_blur][fg_sharp]overlay=(W-w)/2:(H-h)/2"
            )
            return filter_str

        # Calculate average speaker center ratio
        if subject_centers:
            avg_center = sum(c[1] for c in subject_centers) / len(subject_centers)
        else:
            avg_center = 0.5

        # Source is typically 16:9 (e.g. 1920x1080).
        # To fill 1080x1920 (9:16), scale height to 1920:
        # scaled_width = source_width * (1920 / source_height)
        # Then crop 1080 width centered around avg_center * scaled_width
        scale_factor = self.target_height / max(source_height, 1)
        scaled_width = int(source_width * scale_factor)

        target_center_px = avg_center * scaled_width
        crop_x = int(target_center_px - (self.target_width / 2))
        # Clamp crop_x
        max_x = max(0, scaled_width - self.target_width)
        crop_x = max(0, min(crop_x, max_x))

        filter_str = (
            f"scale={scaled_width}:{self.target_height},"
            f"crop={self.target_width}:{self.target_height}:{crop_x}:0"
        )
        return filter_str
