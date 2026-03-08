#!/usr/bin/env python3
"""
Video Processor — auto-editor + FFmpeg
Midnight Jade colour theme
Requires: pip install PyQt5 auto-editor imageio-ffmpeg
"""
import sys
import os
import re
import json
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QDoubleSpinBox, QSpinBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QTextEdit, QCheckBox, QMessageBox, QComboBox,
    QFrame, QAbstractItemView,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
BG      = "#0c1512"
CARD    = "#111f1a"
PRI     = "#065f46"
PRI_LT  = "#059669"
PRI_DK  = "#064e3b"
ACC1    = "#047857"
ACC2    = "#d1fae5"
TEXT    = "#f0fdf4"
DIM     = "#6ee7b7"
MUTED   = "#3d5a4a"
BORDER  = "#1e3a2a"
STYLE = f"""
* {{ font-family: 'Helvetica Neue', Arial, sans-serif; }}
QMainWindow, QWidget {{ background: {BG}; color: {TEXT}; }}
QGroupBox {{
    color: {DIM}; font-weight: 600; font-size: 10px; letter-spacing: 1.4px;
    border: 1px solid {BORDER}; border-radius: 8px;
    margin-top: 10px; padding: 14px 8px 8px 8px; background: {CARD};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
QPushButton {{
    background: {PRI}; color: {TEXT}; border: none; border-radius: 6px;
    padding: 7px 16px; font-weight: 600; font-size: 12px;
}}
QPushButton:hover {{ background: {PRI_LT}; }}
QPushButton:pressed {{ background: {PRI_DK}; }}
QPushButton:disabled {{ background: {PRI_DK}; color: {MUTED}; }}
QPushButton#big {{
    background: {ACC1}; font-size: 13px; padding: 10px 24px;
}}
QPushButton#big:hover {{ background: {PRI_LT}; }}
QPushButton#big:disabled {{ background: {PRI_DK}; color: {MUTED}; }}
QPushButton#cancel {{ background: #7f1d1d; }}
QPushButton#cancel:hover {{ background: #991b1b; }}
QLabel {{ color: {TEXT}; }}
QDoubleSpinBox, QSpinBox, QComboBox {{
    background: {BG}; color: {TEXT}; border: 1px solid {BORDER};
    border-radius: 5px; padding: 5px 8px;
}}
QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {PRI_LT}; }}
QComboBox QAbstractItemView {{ background: {CARD}; color: {TEXT}; border: 1px solid {BORDER}; selection-background-color: {PRI}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QCheckBox {{ color: {TEXT}; spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border: 1px solid {BORDER};
    border-radius: 4px; background: {BG};
}}
QCheckBox::indicator:checked {{ background: {PRI_LT}; border-color: {PRI_LT}; }}
QTextEdit {{
    background: {CARD}; color: {DIM}; border: 1px solid {BORDER};
    border-radius: 6px; font-family: 'SF Mono', Menlo, 'Courier New', monospace;
    font-size: 11px; padding: 6px;
}}
QTableWidget {{
    background: {CARD}; color: {TEXT}; border: 1px solid {BORDER};
    border-radius: 6px; gridline-color: {BORDER}; outline: none;
}}
QTableWidget::item {{ padding: 4px 8px; border: none; }}
QTableWidget::item:selected {{ background: {PRI}; }}
QHeaderView::section {{
    background: {BG}; color: {DIM}; border: none;
    border-right: 1px solid {BORDER}; border-bottom: 1px solid {BORDER};
    padding: 6px 8px; font-size: 10px; font-weight: 600; letter-spacing: 0.8px;
}}
QProgressBar {{
    background: {BG}; border: 1px solid {BORDER}; border-radius: 3px;
    max-height: 6px;
}}
QProgressBar::chunk {{ background: {PRI_LT}; border-radius: 3px; }}
QScrollBar:vertical {{ background: {BG}; width: 8px; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
CONFIG_PATH = Path.home() / ".video_processor_config.json"
VIDEO_EXTS  = {".mov", ".mp4", ".m4v", ".mkv", ".avi", ".webm", ".flv"}
PRESETS = {
    "Conservative": dict(silence_threshold=0.02, margin=0.6, min_clip=3.0,
                         crf=22, audio_bitrate=192),
    "Balanced":     dict(silence_threshold=0.04, margin=0.4, min_clip=2.0,
                         crf=26, audio_bitrate=128),
    "Aggressive":   dict(silence_threshold=0.08, margin=0.2, min_clip=1.0,
                         crf=30, audio_bitrate=96),
}
def _ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"
def _ffprobe():
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe().replace("ffmpeg", "ffprobe")
        if os.path.exists(p):
            return p
    except ImportError:
        pass
    return "ffprobe"
def probe_color(path):
    """Return colour primaries, transfer, and colorspace from the first video stream."""
    try:
        cmd = [_ffprobe(), "-v", "quiet", "-print_format", "json",
               "-show_streams", "-select_streams", "v:0", path]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        stream = json.loads(r.stdout).get("streams", [{}])[0]
        return {k: stream.get(k) for k in
                ("color_primaries", "color_transfer", "color_space")}
    except Exception:
        return {}
def probe_gps(path):
    """Extract GPS location string from iPhone QuickTime metadata."""
    try:
        cmd = [_ffprobe(), "-v", "quiet", "-print_format", "json",
               "-show_format", path]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        tags = json.loads(r.stdout).get("format", {}).get("tags", {})
        return (tags.get("com.apple.quicktime.location.ISO6709")
                or tags.get("location"))
    except Exception:
        return None
def get_duration(path):
    r = subprocess.run([_ffmpeg(), "-i", path, "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", r.stderr)
    if m:
        h, mn, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
        return h * 3600 + mn * 60 + s
    return None
def detect_silence_ffmpeg(path, threshold_db=-30.0, min_dur=0.5):
    filt = f"silencedetect=n={threshold_db}dB:d={min_dur}"
    r = subprocess.run([_ffmpeg(), "-i", path, "-af", filt, "-f", "null", "-"],
                       capture_output=True, text=True, timeout=600)
    starts = [float(x) for x in re.findall(r"silence_start:\s*(\S+)", r.stderr)]
    ends   = [float(x) for x in re.findall(r"silence_end:\s*(\S+)", r.stderr)]
    segs = []
    for i, s in enumerate(starts):
        if i < len(ends):
            segs.append({"start": s, "end": ends[i], "duration": ends[i] - s})
    return segs
def merge_segs(segs, gap=0.1):
    if not segs:
        return []
    out = [dict(sorted(segs, key=lambda x: x["start"])[0])]
    for seg in sorted(segs, key=lambda x: x["start"])[1:]:
        last = out[-1]
        if seg["start"] <= last["end"] + gap:
            last["end"] = max(last["end"], seg["end"])
            last["duration"] = last["end"] - last["start"]
        else:
            out.append(dict(seg))
    return out
class TimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 0.0
        self.segments = []
        self.setMinimumHeight(54)
    def set_data(self, duration, segments):
        self.duration = duration
        self.segments = segments
        self.update()
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        mx, my = 6, 6
        bar_h = h - my * 2 - 16
        if not self.duration:
            p.fillRect(mx, my, w - 2*mx, bar_h, QColor(BORDER))
            p.setPen(QColor(DIM))
            p.setFont(QFont("Helvetica", 9))
            p.drawText(mx + 8, my + bar_h // 2 + 4, "Load a video and run preview analysis")
            return
        p.fillRect(mx, my, w - 2*mx, bar_h, QColor(ACC1))
        def xf(t):
            return int(mx + (t / self.duration) * (w - 2*mx))
        for seg in self.segments:
            x1, x2 = xf(seg["start"]), xf(seg["end"])
            p.fillRect(x1, my, max(x2 - x1, 2), bar_h, QColor(127, 29, 29, 220))
        p.setPen(QPen(QColor(BORDER), 1))
        p.drawRect(mx, my, w - 2*mx - 1, bar_h - 1)
        p.setPen(QColor(DIM))
        p.setFont(QFont("Menlo", 8))
        n = min(8, max(2, w // 90))
        for i in range(n + 1):
            t = (i / n) * self.duration
            x = xf(t)
            p.drawLine(x, my + bar_h, x, my + bar_h + 4)
            p.drawText(x - 14, h - 1, f"{int(t//60)}:{int(t%60):02d}")
class AnalysisThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list, float)
    error    = pyqtSignal(str)
    def __init__(self, path, sil_thresh_db, sil_min_dur):
        super().__init__()
        self.path = path
        self.sil_thresh_db = sil_thresh_db
        self.sil_min_dur   = sil_min_dur
    def run(self):
        try:
            self.progress.emit("Reading duration…")
            dur = get_duration(self.path)
            if dur is None:
                self.error.emit("Could not read duration — is the file valid?")
                return
            self.progress.emit(f"Duration: {dur:.1f}s")
            self.progress.emit(f"Detecting silence (≤{self.sil_thresh_db:.1f} dB, min {self.sil_min_dur}s)…")
            segs = detect_silence_ffmpeg(self.path, self.sil_thresh_db, self.sil_min_dur)
            merged = merge_segs(segs)
            total = sum(s["duration"] for s in merged)
            self.progress.emit(f"Found {len(merged)} silent segment(s) — "
                               f"{total:.1f}s ({total/dur*100:.1f}% of video)")
            self.finished.emit(merged, dur)
        except subprocess.TimeoutExpired:
            self.error.emit("Analysis timed out.")
        except Exception as e:
            self.error.emit(str(e))
class ProcessThread(QThread):
    log       = pyqtSignal(str)
    file_done = pyqtSignal(str, bool, str)
    all_done  = pyqtSignal()
    def __init__(self, files, output_dir, settings):
        super().__init__()
        self.files      = files
        self.output_dir = Path(output_dir)
        self.settings   = settings
        self._cancel    = False
    def cancel(self):
        self._cancel = True
    def run(self):
        for f in self.files:
            if self._cancel:
                self.log.emit("— Cancelled —")
                break
            self._process(f)
        self.all_done.emit()
    def _process(self, input_path):
        s = self.settings
        stem        = Path(input_path).stem
        temp_output = str(self.output_dir / f"{stem}_ae_temp.mp4")
        final_output = str(self.output_dir / f"{stem}_final.mp4")
        in_size = os.path.getsize(input_path)
        # ── Step 1: auto-editor edit ──────────────────────────────────
        cmd = ["auto-editor", input_path]
        edit_expr = f"audio:threshold={s['silence_threshold']}"
        if s.get("use_motion"):
            edit_expr += f" or motion:threshold={s['motion_threshold']}"
        cmd += ["--edit", edit_expr]
        cmd += ["--margin", f"{s['margin']}s"]
        codec = s.get("codec", "H.265")
        if codec == "H.265":
            cmd += ["--video-codec", "libx265"]
        elif codec == "H.264":
            cmd += ["--video-codec", "libx264"]
        cmd += ["--no-open", "-o", temp_output]
        self.log.emit(f"\n▶  {Path(input_path).name}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            if not (result.returncode == 0 and os.path.exists(temp_output)):
                err = (result.stderr or result.stdout or "unknown error")[-800:]
                self.file_done.emit(input_path, False, err)
                return
            # ── Step 2: copy metadata + colour profile + GPS from original ─
            self.log.emit("  Preserving metadata, colour profile, and GPS…")
            color = probe_color(input_path)
            gps   = probe_gps(input_path)
            meta_cmd = [
                _ffmpeg(),
                "-i", temp_output,
                "-i", input_path,
                "-map", "0",
                "-map_metadata", "1",
                "-c", "copy",
                "-copy_unknown",
                "-movflags", "use_metadata_tags+faststart",
            ]
            if color.get("color_primaries"):
                meta_cmd += ["-color_primaries", color["color_primaries"]]
            if color.get("color_transfer"):
                meta_cmd += ["-color_trc", color["color_transfer"]]
            if color.get("color_space"):
                meta_cmd += ["-colorspace", color["color_space"]]
            if gps:
                meta_cmd += [
                    "-metadata", f"com.apple.quicktime.location.ISO6709={gps}",
                    "-metadata", f"location={gps}",
                ]
            meta_cmd += ["-y", final_output]
            meta_result = subprocess.run(meta_cmd, capture_output=True, text=True, timeout=300)
            try:
                os.remove(temp_output)
            except OSError:
                pass
            if meta_result.returncode == 0 and os.path.exists(final_output):
                out_size = os.path.getsize(final_output)
                pct = (1 - out_size / in_size) * 100 if in_size else 0
                msg = (f"{in_size//1024//1024} MB → {out_size//1024//1024} MB "
                       f"({pct:.0f}% smaller)  |  GPS, date & camera info preserved")
                self.file_done.emit(input_path, True, msg)
            else:
                err = (meta_result.stderr or "metadata step failed")[-800:]
                self.file_done.emit(input_path, False, f"Metadata copy failed: {err}")
        except subprocess.TimeoutExpired:
            self.file_done.emit(input_path, False, "Timed out (>2 h)")
        except Exception as e:
            self.file_done.emit(input_path, False, str(e))
class VideoProcessorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Processor")
        self.setMinimumSize(860, 780)
        self.video_files     = []
        self.preview_path    = ""
        self.preview_segs    = []
        self.preview_dur     = 0.0
        self.analysis_thread = None
        self.process_thread  = None
        self._output_dir     = ""
        self._build_ui()
        self._load_config()
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setSpacing(8)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.addWidget(self._header())
        lay.addWidget(self._source_group())
        lay.addWidget(self._settings_group())
        lay.addWidget(self._timeline_group())
        lay.addWidget(self._queue_group())
        lay.addWidget(self._actions_group())
    def _header(self):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 4)
        title = QLabel("Video Processor")
        title.setStyleSheet(f"color: {ACC2}; font-size: 18px; font-weight: 700;")
        sub = QLabel("auto-editor + FFmpeg  |  silence removal  |  H.265 compression")
        sub.setStyleSheet(f"color: {DIM}; font-size: 11px;")
        h.addWidget(title)
        h.addSpacing(12)
        h.addWidget(sub)
        h.addStretch()
        return w
    def _source_group(self):
        grp = QGroupBox("SOURCE & OUTPUT")
        lay = QVBoxLayout(grp)
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Source:"))
        self.lbl_file = QLabel("No file selected")
        self.lbl_file.setStyleSheet(f"color: {DIM}; font-style: italic;")
        r1.addWidget(self.lbl_file, 1)
        btn_f = QPushButton("Browse file…")
        btn_f.clicked.connect(self._pick_file)
        r1.addWidget(btn_f)
        btn_d = QPushButton("Browse folder…")
        btn_d.clicked.connect(self._pick_folder)
        r1.addWidget(btn_d)
        lay.addLayout(r1)
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Output folder:"))
        self.lbl_out = QLabel("Same as source")
        self.lbl_out.setStyleSheet(f"color: {DIM}; font-style: italic;")
        r2.addWidget(self.lbl_out, 1)
        btn_o = QPushButton("Browse…")
        btn_o.clicked.connect(self._pick_output)
        r2.addWidget(btn_o)
        lay.addLayout(r2)
        return grp
    def _settings_group(self):
        grp = QGroupBox("SETTINGS")
        outer = QHBoxLayout(grp)
        edit_grp = QGroupBox("EDIT")
        el = QVBoxLayout(edit_grp)
        pr = QHBoxLayout()
        pr.addWidget(QLabel("Preset:"))
        for name in PRESETS:
            b = QPushButton(name)
            b.clicked.connect(lambda _, n=name: self._apply_preset(n))
            pr.addWidget(b)
        pr.addStretch()
        el.addLayout(pr)
        self.spin_sil_thresh = self._spin_row(el, "Silence threshold:", 0.001, 0.5, 0.04, 0.005, 3,
            "Audio level ratio (0–1) below which a section is considered silent.")
        self._hint(el, "How quiet audio must be to count as silence. Lower = only very quiet parts cut. Higher = more aggressive cutting.")
        self.spin_margin     = self._spin_row(el, "Margin (seconds):", 0.0, 2.0, 0.4, 0.1, 1,
            "Padding kept around each cut point.")
        self._hint(el, "How many seconds of audio to keep either side of a cut. Higher = more natural, fewer abrupt jumps.")
        self.spin_min_clip   = self._spin_row(el, "Min clip length (s):", 0.1, 10.0, 2.0, 0.5, 1,
            "Clips shorter than this are never cut.")
        self._hint(el, "Any kept segment shorter than this is ignored — prevents very short flashes of audio from being kept.")
        self.chk_motion = QCheckBox("Also detect frozen/still frames")
        el.addWidget(self.chk_motion)
        self.spin_motion = self._spin_row(el, "Motion threshold:", 0.0001, 0.5, 0.02, 0.005, 4,
            "Frame difference below which video is considered frozen.")
        self._hint(el, "How still the frame must be to count as frozen. Lower = only completely static frames cut. Higher = more movement allowed.")
        el.addStretch()
        outer.addWidget(edit_grp)
        comp_grp = QGroupBox("COMPRESSION")
        cl = QVBoxLayout(comp_grp)
        cr = QHBoxLayout()
        cr.addWidget(QLabel("Codec:"))
        self.combo_codec = QComboBox()
        self.combo_codec.addItems(["H.265 (recommended)", "H.264", "Copy (no re-encode)"])
        cr.addWidget(self.combo_codec)
        cr.addStretch()
        cl.addLayout(cr)
        self.spin_crf      = self._spin_row(cl, "Quality (CRF):", 18, 35, 26, 1, 0,
            "Lower = better quality, larger file.")
        self._hint(cl, "Controls file size vs quality. 18 = near lossless. 26 = good quality. 35 = smaller file, noticeable quality loss.")
        self.spin_audio_br = self._spin_row(cl, "Audio bitrate (kbps):", 64, 320, 128, 32, 0)
        self._hint(cl, "Higher = better audio quality, slightly larger file. 128 is fine for speech. 192–320 for music.")
        sr = QHBoxLayout()
        sr.addWidget(QLabel("Encoding speed:"))
        self.combo_speed = QComboBox()
        self.combo_speed.addItems(["ultrafast", "fast", "medium", "slow", "veryslow"])
        self.combo_speed.setCurrentText("medium")
        sr.addWidget(self.combo_speed)
        sr.addStretch()
        cl.addLayout(sr)
        self._hint(cl, "Faster = quicker to process but slightly larger file. Slower = better compression. 'medium' is a good default.")
        self.chk_bake = QCheckBox("Bake in rotation (recommended for iPhone videos)")
        self.chk_bake.setChecked(True)
        cl.addWidget(self.chk_bake)
        cl.addStretch()
        outer.addWidget(comp_grp)
        return grp
    def _timeline_group(self):
        grp = QGroupBox("PREVIEW TIMELINE  (single file)")
        lay = QVBoxLayout(grp)
        self.timeline = TimelineWidget()
        lay.addWidget(self.timeline)
        leg = QHBoxLayout()
        for col, label in [(ACC1, "Keep"), ("#7f1d1d", "Silence")]:
            dot = QLabel("■")
            dot.setStyleSheet(f"color: {col}; font-size: 14px;")
            leg.addWidget(dot)
            leg.addWidget(QLabel(label))
            leg.addSpacing(12)
        self.btn_preview = QPushButton("Analyse Selected File")
        self.btn_preview.setEnabled(False)
        self.btn_preview.clicked.connect(self._run_analysis)
        leg.addStretch()
        leg.addWidget(self.btn_preview)
        lay.addLayout(leg)
        self.cut_table = QTableWidget(0, 3)
        self.cut_table.setHorizontalHeaderLabels(["Cut start", "Cut end", "Duration removed"])
        self.cut_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cut_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cut_table.setMaximumHeight(120)
        self.cut_table.hide()
        lay.addWidget(self.cut_table)
        return grp
    def _queue_group(self):
        grp = QGroupBox("FILE QUEUE")
        lay = QVBoxLayout(grp)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["File", "Size", "Status", "Result"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setMaximumHeight(160)
        self.table.clicked.connect(self._on_table_click)
        lay.addWidget(self.table)
        return grp
    def _actions_group(self):
        grp = QGroupBox("PROCESS & LOG")
        lay = QVBoxLayout(grp)
        br = QHBoxLayout()
        self.btn_all = QPushButton("Process All")
        self.btn_all.setObjectName("big")
        self.btn_all.setEnabled(False)
        self.btn_all.clicked.connect(self._process_all)
        br.addWidget(self.btn_all)
        self.btn_selected = QPushButton("Process Selected")
        self.btn_selected.setEnabled(False)
        self.btn_selected.clicked.connect(self._process_selected)
        br.addWidget(self.btn_selected)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("cancel")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel)
        br.addWidget(self.btn_cancel)
        br.addStretch()
        self.btn_save_cfg = QPushButton("Save Settings")
        self.btn_save_cfg.clicked.connect(self._save_config)
        br.addWidget(self.btn_save_cfg)
        lay.addLayout(br)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        lay.addWidget(self.progress)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(90)
        lay.addWidget(self.log)
        return grp
    def _hint(self, layout, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {MUTED}; font-size: 10px; font-style: italic; padding-left: 4px; margin-bottom: 4px;")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        layout.addSpacing(6)
    def _spin_row(self, layout, label, lo, hi, val, step, decimals, tip=""):
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setFixedWidth(190)
        row.addWidget(lbl)
        spin = QDoubleSpinBox() if decimals else QSpinBox()
        spin.setRange(lo, hi)
        spin.setValue(val)
        spin.setSingleStep(step)
        if decimals:
            spin.setDecimals(decimals)
        if tip:
            spin.setToolTip(tip)
        row.addWidget(spin)
        row.addStretch()
        layout.addLayout(row)
        return spin
    def _log(self, msg):
        self.log.append(msg)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
    def _set_table_status(self, row, status, color=None):
        item = QTableWidgetItem(status)
        if color:
            item.setForeground(QBrush(QColor(color)))
        self.table.setItem(row, 2, item)
    def _set_table_result(self, row, result, color=None):
        item = QTableWidgetItem(result)
        if color:
            item.setForeground(QBrush(QColor(color)))
        self.table.setItem(row, 3, item)
    def _pick_file(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Select video", "",
            "Video files (*.mp4 *.mov *.m4v *.mkv *.avi *.webm *.flv);;All files (*)")
        if f:
            self._add_files([f])
    def _pick_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select source folder")
        if d:
            files = sorted(str(p) for p in Path(d).iterdir()
                           if p.suffix.lower() in VIDEO_EXTS)
            if not files:
                QMessageBox.information(self, "No videos", "No video files found in that folder.")
                return
            self._add_files(files)
    def _pick_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select output folder")
        if d:
            self._output_dir = d
            self.lbl_out.setText(d)
            self.lbl_out.setStyleSheet(f"color: {TEXT};")
    def _add_files(self, files):
        self.video_files = files
        self.table.setRowCount(0)
        for f in files:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(Path(f).name))
            self.table.setItem(r, 1, QTableWidgetItem(f"{os.path.getsize(f)/1024/1024:.1f} MB"))
            self.table.setItem(r, 2, QTableWidgetItem("Queued"))
            self.table.setItem(r, 3, QTableWidgetItem(""))
        if files:
            self.preview_path = files[0]
            self.lbl_file.setText(
                Path(files[0]).name if len(files) == 1
                else f"{len(files)} files from {Path(files[0]).parent.name}/")
            self.lbl_file.setStyleSheet(f"color: {TEXT};")
            self.btn_preview.setEnabled(True)
            self.btn_all.setEnabled(True)
            self.btn_selected.setEnabled(True)
            self._log(f"Loaded {len(files)} file(s).")
    def _on_table_click(self, index):
        r = index.row()
        if r < len(self.video_files):
            self.preview_path = self.video_files[r]
    def _apply_preset(self, name):
        p = PRESETS[name]
        self.spin_sil_thresh.setValue(p["silence_threshold"])
        self.spin_margin.setValue(p["margin"])
        self.spin_min_clip.setValue(p["min_clip"])
        self.spin_crf.setValue(p["crf"])
        self.spin_audio_br.setValue(p["audio_bitrate"])
        self._log(f"Preset applied: {name}")
    def _run_analysis(self):
        if not self.preview_path:
            return
        import math
        ratio = self.spin_sil_thresh.value()
        db = 20 * math.log10(max(ratio, 0.0001))
        self.btn_preview.setEnabled(False)
        self.timeline.set_data(0, [])
        self.progress.setRange(0, 0)
        self._log(f"Analysing: {Path(self.preview_path).name}")
        self.analysis_thread = AnalysisThread(self.preview_path, db, self.spin_margin.value())
        self.analysis_thread.progress.connect(self._log)
        self.analysis_thread.finished.connect(self._on_analysis_done)
        self.analysis_thread.error.connect(self._on_analysis_error)
        self.analysis_thread.start()
    def _on_analysis_done(self, segs, dur):
        self.preview_segs = segs
        self.preview_dur  = dur
        self.timeline.set_data(dur, segs)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.btn_preview.setEnabled(True)
        self.cut_table.setRowCount(0)
        if segs:
            self.cut_table.show()
            for seg in segs:
                r = self.cut_table.rowCount()
                self.cut_table.insertRow(r)
                def fmt(t):
                    m, s = int(t // 60), t % 60
                    return f"{m}:{s:05.2f}"
                self.cut_table.setItem(r, 0, QTableWidgetItem(fmt(seg["start"])))
                self.cut_table.setItem(r, 1, QTableWidgetItem(fmt(seg["end"])))
                self.cut_table.setItem(r, 2, QTableWidgetItem(f"{seg['duration']:.2f}s"))
        else:
            self.cut_table.hide()
            self._log("No segments to cut — video will be unchanged.")
    def _on_analysis_error(self, msg):
        self._log(f"Error: {msg}")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.btn_preview.setEnabled(True)
    def _collect_settings(self):
        codec_map = {"H.265 (recommended)": "H.265", "H.264": "H.264",
                     "Copy (no re-encode)": "Copy"}
        return {
            "silence_threshold": self.spin_sil_thresh.value(),
            "margin":            self.spin_margin.value(),
            "min_clip":          self.spin_min_clip.value(),
            "use_motion":        self.chk_motion.isChecked(),
            "motion_threshold":  self.spin_motion.value(),
            "codec":             codec_map[self.combo_codec.currentText()],
            "crf":               int(self.spin_crf.value()),
            "audio_bitrate":     int(self.spin_audio_br.value()),
            "speed":             self.combo_speed.currentText(),
            "bake_rotation":     self.chk_bake.isChecked(),
        }
    def _process_all(self):
        self._start_processing(self.video_files)
    def _process_selected(self):
        rows = list({idx.row() for idx in self.table.selectedIndexes()})
        files = [self.video_files[r] for r in sorted(rows) if r < len(self.video_files)]
        if not files:
            QMessageBox.information(self, "Nothing selected", "Select one or more rows first.")
            return
        self._start_processing(files)
    def _start_processing(self, files):
        if not files:
            return
        out_dir = self._output_dir or str(Path(files[0]).parent)
        settings = self._collect_settings()
        self.btn_all.setEnabled(False)
        self.btn_selected.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress.setRange(0, len(files))
        self.progress.setValue(0)
        self._processed_count = 0
        for f in files:
            if f in self.video_files:
                self._set_table_status(self.video_files.index(f), "Processing…", DIM)
                self._set_table_result(self.video_files.index(f), "")
        self.process_thread = ProcessThread(files, out_dir, settings)
        self.process_thread.log.connect(self._log)
        self.process_thread.file_done.connect(self._on_file_done)
        self.process_thread.all_done.connect(self._on_all_done)
        self.process_thread.start()
    def _on_file_done(self, path, ok, msg):
        self._processed_count += 1
        self.progress.setValue(self._processed_count)
        if path in self.video_files:
            r = self.video_files.index(path)
            if ok:
                self._set_table_status(r, "✓ Done", PRI_LT)
                self._set_table_result(r, msg, DIM)
                self._log(f"✓  {Path(path).name}  —  {msg}")
            else:
                self._set_table_status(r, "✗ Failed", "#ef4444")
                self._set_table_result(r, msg[:80], "#ef4444")
                self._log(f"✗  {Path(path).name}  —  {msg}")
    def _on_all_done(self):
        self.btn_all.setEnabled(True)
        self.btn_selected.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self._log("── All done ──")
    def _cancel(self):
        if self.process_thread:
            self.process_thread.cancel()
        if self.analysis_thread:
            self.analysis_thread.terminate()
        self.btn_cancel.setEnabled(False)
    def _save_config(self):
        cfg = self._collect_settings()
        cfg["output_dir"] = self._output_dir
        try:
            CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
            self._log(f"Settings saved.")
        except Exception as e:
            self._log(f"Could not save config: {e}")
    def _load_config(self):
        if not CONFIG_PATH.exists():
            return
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
            self.spin_sil_thresh.setValue(cfg.get("silence_threshold", 0.04))
            self.spin_margin.setValue(cfg.get("margin", 0.4))
            self.spin_min_clip.setValue(cfg.get("min_clip", 2.0))
            self.chk_motion.setChecked(cfg.get("use_motion", False))
            self.spin_motion.setValue(cfg.get("motion_threshold", 0.02))
            codec_rev = {"H.265": "H.265 (recommended)", "H.264": "H.264",
                         "Copy": "Copy (no re-encode)"}
            self.combo_codec.setCurrentText(
                codec_rev.get(cfg.get("codec", "H.265"), "H.265 (recommended)"))
            self.spin_crf.setValue(cfg.get("crf", 26))
            self.spin_audio_br.setValue(cfg.get("audio_bitrate", 128))
            self.combo_speed.setCurrentText(cfg.get("speed", "medium"))
            self.chk_bake.setChecked(cfg.get("bake_rotation", True))
            self._output_dir = cfg.get("output_dir", "")
            if self._output_dir:
                self.lbl_out.setText(self._output_dir)
                self.lbl_out.setStyleSheet(f"color: {TEXT};")
        except Exception as e:
            self._log(f"Could not load config: {e}")
def main():
    try:
        r = subprocess.run(["auto-editor", "--version"], capture_output=True, text=True)
        ae_ver = r.stdout.strip() or r.stderr.strip()
    except FileNotFoundError:
        print("ERROR: auto-editor not found.\nInstall: pip install auto-editor")
        sys.exit(1)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    win = VideoProcessorGUI()
    win._log(f"auto-editor {ae_ver} ready.")
    win.show()
    sys.exit(app.exec_())
if __name__ == "__main__":
    main()
