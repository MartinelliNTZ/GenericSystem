# -*- coding: utf-8 -*-
"""
HudCircularRingsLoader — Overlay de carregamento com 3 modos de progresso
===========================================================================

Modo 1 — FEEDBACK REAL:
    set_progress(percentual, mensagem)

Modo 2 — TEMPORIZADOR (stage=1):
    start_timer(segundos) — a loader vai de 0% a 100% no tempo dado.
    A cada (tempo_total/1000) segundos, incrementa 0.01%.

Modo 3 — ETAPAS (stage=N):
    start_staged(segundos_totais, num_stages)
    Divide tempo e porcentagem igualmente entre N stages.
    Ex: 200s, 4 stages -> stage1: 0-25% em 50s, stage2: 25-50% em 50s, etc.
    Dentro de cada stage, a cada (secs_per_stage / (pct_per_stage * 100)) segundos,
    incrementa 0.01%.
    Quando atinge o limite do stage, PARA e aguarda hud_stage_done.
    hud_stage_done(N) libera o stage (N+1) e continua.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import Qt, QTimer, QRectF, QElapsedTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from resources.styles.AppStyles import AppStyles
from core.manager.SignalManager import SignalManager


class HudCircularRingsLoader(QWidget):
    """
    Overlay de carregamento com 3 modos de progresso baseados em QElapsedTimer real.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0
        self.phase = 0
        self.message = "Processando..."
        self._eta_seconds: float = 0.0
        self._start_datetime: datetime = datetime.now()

        current_theme = AppStyles.current_theme
        accent_qcolor = QColor(current_theme.ACCENT_TEXT) if QColor.isValidColor(current_theme.ACCENT_TEXT) else QColor(212, 168, 83)
        bright_qcolor = QColor(232, 200, 120)
        self.rings = [
            {"radius": 82, "width": 6, "speed": 2.0, "angle": 0, "segments": 10, "seg_span": 16, "seg_gap": 18,
             "color": accent_qcolor},
            {"radius": 62, "width": 5, "speed": -3.2, "angle": 150, "segments": 2, "seg_span": 120, "seg_gap": 60,
             "color": QColor(33, 150, 243, 220)},
            {"radius": 45, "width": 4, "speed": 5.4, "angle": 45, "segments": 14, "seg_span": 10, "seg_gap": 12,
             "color": bright_qcolor},
        ]
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        self.hide()
        self._animate_timer = QTimer(self)
        self._animate_timer.timeout.connect(self._tick)
        self._animate_timer.start(16)

        # Estado dos modos
        self._mode: int = 1                # 1=manual, 2=timer, 3=staged
        self._elapsed = QElapsedTimer()

        # Dados do stage atual
        self._total_secs: float = 10.0     # tempo total
        self._num_stages: int = 1          # numero de stages
        self._stage_current: int = 0       # stage atual (0-based)
        self._pct_per_stage: float = 100.0 # % por stage
        self._secs_per_stage: float = 10.0 # segundos por stage
        self._stage_min_pct: float = 0.0   # % minima deste stage
        self._stage_max_pct: float = 100.0 # % maxima deste stage

        # Conecta sinal de etapa concluida
        SignalManager.instance().hud_stage_done.connect(self._on_stage_done)

    def set_progress(self, value: float, message: str = ""):
        """Modo 1: Define progresso manualmente (0.0 a 100.0)."""
        self._mode = 1
        self.progress = max(0.0, min(100.0, float(value)))
        if message:
            self.message = message
        self.update()

    def start_timer(self, seconds: float, message: str = ""):
        """
        Modo 2: 1 stage, 100% em N segundos.
        Incrementa 0.01% a cada (N/1000) segundos.
        """
        self._mode = 2
        s = max(0.1, float(seconds))
        self._setup_stage(total_secs=s, num_stages=1, stage_idx=0, msg=message)

    def start_staged(self, total_seconds: float, num_stages: int, message: str = ""):
        """
        Modo 3: N stages, (100/N)% cada, (total/N) segundos cada.
        """
        self._mode = 3
        ns = max(1, num_stages)
        s = max(0.1, float(total_seconds))
        self._setup_stage(total_secs=s, num_stages=ns, stage_idx=0, msg=message)

    def _setup_stage(self, total_secs: float, num_stages: int,
                     stage_idx: int, msg: str):
        """Configura os parametros de um stage."""
        self._total_secs = total_secs
        self._num_stages = num_stages
        self._stage_current = stage_idx
        self._pct_per_stage = 100.0 / num_stages
        self._secs_per_stage = total_secs / num_stages
        self._stage_min_pct = stage_idx * self._pct_per_stage
        self._stage_max_pct = self._stage_min_pct + self._pct_per_stage
        self.progress = self._stage_min_pct
        if msg:
            self.message = msg
        self._start_datetime = datetime.now()
        self._elapsed.start()
        self.update()

    def show_loader(self):
        """Exibe o loader e reinicia o timer de animacao."""
        if not self._animate_timer.isActive():
            self._animate_timer.start(16)
        self.raise_()
        self.show()
        self.update()

    def hide_loader(self):
        """Esconde o loader e para o timer de animacao."""
        self._mode = 1
        self._animate_timer.stop()
        self.hide()

    # ── ETA / Time helpers ─────────────────────────────────────────

    def set_eta(self, eta_seconds: float) -> None:
        """Define o tempo total estimado em segundos para calculo de ETA."""
        self._eta_seconds = max(0.0, float(eta_seconds))

    def _format_secs(self, secs: float) -> str:
        """Formata segundos como HH:MM:SS."""
        secs = max(0, int(secs))
        h, m, s = secs // 3600, (secs % 3600) // 60, secs % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _elapsed_str(self) -> str:
        """Retorna o tempo decorrido formatado desde o inicio."""
        return self._format_secs(self._elapsed.elapsed() / 1000.0)

    def _remaining_str(self) -> str:
        """Retorna o tempo restante formatado."""
        remaining = self._eta_seconds - (self._elapsed.elapsed() / 1000.0)
        return self._format_secs(max(0.0, remaining))

    def _eta_clock_str(self) -> str:
        """Retorna o horario estimado de conclusao (HH:MM)."""
        eta_dt = self._start_datetime + timedelta(seconds=self._eta_seconds)
        return eta_dt.strftime("%H:%M")

    # ── Tick principal (16ms) ───────────────────────────────────────

    def _tick(self):
        """Executado a cada 16ms. Anima aneis e atualiza progresso."""
        if not self.isVisible():
            return

        self.phase = (self.phase + 1) % 360
        for ring in self.rings:
            ring["angle"] = (ring["angle"] + ring["speed"]) % 360

        # Atualiza progresso automatico (modos 2 e 3)
        if self._mode in (2, 3):
            self._update_auto_progress()

        self.update()

    def _update_auto_progress(self):
        """
        Calcula progresso baseado no tempo real decorrido desde o inicio do stage.
        """
        elapsed_ms = self._elapsed.elapsed()        # ms desde o inicio do stage
        elapsed_sec = elapsed_ms / 1000.0

        # Se passou mais tempo que o esperado para este stage, trava no max
        if elapsed_sec >= self._secs_per_stage:
            self.progress = round(self._stage_max_pct, 2)
            self._emit_progress()
            return

        # Fração de progresso dentro deste stage
        fraction = elapsed_sec / self._secs_per_stage  # 0.0 a 1.0
        pct = self._stage_min_pct + (fraction * self._pct_per_stage)
        pct = min(pct, self._stage_max_pct)

        if round(pct, 2) != self.progress:
            self.progress = round(pct, 2)
            self._emit_progress()

    def _emit_progress(self):
        """Propaga o progresso atual pelo SignalManager."""
        SignalManager.instance().hud_update.emit({
            "message": self.message,
            "progress": self.progress,
        })
        SignalManager.instance().progress_update.emit(self.progress)

    def _on_stage_done(self, stage_index: int):
        """
        Recebido via SignalManager.
        Avanca para o proximo stage e reinicia o timer.
        """
        if self._mode == 1 or not self.isVisible():
            return

        next_stage = stage_index + 1  # stage_index era 0, agora é 1

        if next_stage >= self._num_stages:
            # Ultimo stage -> 100%
            self.progress = 100.0
            self._emit_progress()
            self.update()
            return

        # Configura o proximo stage
        self._setup_stage(
            total_secs=self._total_secs,
            num_stages=self._num_stages,
            stage_idx=next_stage,
            msg=self.message,
        )
        self._emit_progress()

    # ── Pintura ─────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(0, 0, 0, 130))

        cx = self.width() // 2
        cy = self.height() // 2 - 20
        panel = QRectF(cx - 150, cy - 130, 300, 300)
        self._draw_panel(p, panel)

        center = panel.center().toPoint()
        for ring in self.rings:
            self._draw_ring(p, center, ring)

        current_theme = AppStyles.current_theme
        accent_color = QColor(current_theme.ACCENT_TEXT)
        time_color = QColor(current_theme.TEXT_LOW)
        light_gray = QColor(140, 140, 140)

        # ── Linha superior: tempos (Decorrido | ETA | Restante) ──
        elapsed_str = self._elapsed_str()
        remaining_str = self._remaining_str()
        eta_clock = self._eta_clock_str()

        p.setFont(QFont("Consolas", 8))
        p.setPen(time_color)
        p.drawText(QRectF(cx - 145, cy - 115, 290, 18), Qt.AlignmentFlag.AlignCenter,
                   f"Tempo: {elapsed_str}|ETA: {eta_clock}|Restante: {remaining_str}")

        # ── Porcentagem no centro ──
        p.setPen(accent_color)
        p.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
        p.drawText(QRectF(cx - 60, cy - 0, 120, 38), Qt.AlignmentFlag.AlignCenter, f"{self.progress:.2f}%")

        # Indicador de modo
        stage_str = f"ETAPA {self._stage_current+1}/{self._num_stages}" if self._num_stages > 1 else "TIMER"
        mode_labels = {1: "FEEDBACK", 2: "TIMER", 3: stage_str}
        p.setPen(light_gray)
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(QRectF(cx - 60, cy + 30, 120, 16), Qt.AlignmentFlag.AlignCenter, mode_labels.get(self._mode, ""))

        # ── Mensagem na parte inferior ──
        p.setPen(accent_color)
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        p.drawText(QRectF(cx - 140, cy + 110, 280, 24), Qt.AlignmentFlag.AlignCenter, self.message)

    def _draw_panel(self, painter: QPainter, rect: QRectF):
        grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        grad.setColorAt(0.0, QColor(37, 37, 38, 245))
        grad.setColorAt(1.0, QColor(18, 18, 18, 245))
        path = QPainterPath()
        path.addRoundedRect(rect, 22, 22)
        painter.setPen(QPen(QColor(62, 62, 66, 220), 1))
        painter.setBrush(grad)
        painter.drawPath(path)

    def _draw_ring(self, painter: QPainter, center, ring):
        painter.setBrush(Qt.BrushStyle.NoBrush)
        trail_pen = QPen(QColor(45, 45, 48, 200), ring["width"])
        painter.setPen(trail_pen)
        painter.drawEllipse(center, ring["radius"], ring["radius"])

        for i in range(ring["segments"]):
            start_deg = ring["angle"] + i * (ring["seg_span"] + ring["seg_gap"])
            start = int((90 - start_deg) * 16)
            span = -int(ring["seg_span"] * 16)
            pulse = ((self.phase + i * 17) % 120) / 120.0
            alpha = int(70 + 170 * pulse)
            c = ring["color"]
            color = QColor(c.red(), c.green(), c.blue(), alpha)
            painter.setPen(QPen(color, ring["width"], Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(center.x() - ring["radius"], center.y() - ring["radius"], ring["radius"] * 2, ring["radius"] * 2, start, span)