# -*- coding: utf-8 -*-
"""
Controlador Principal para a UI do Classificador Raster Neural v6
=================================================================
Logica de controle separada da view (MainWindow).
Comunica logs via SignalManager.console_message e
progresso via SignalManager.progress_update.
"""

from __future__ import annotations

import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MAX_LOG_LEVEL"] = "3"

import warnings
import html
from pathlib import Path
from datetime import datetime, timedelta
from time import perf_counter
from typing import Dict, Any

import threading
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import QInputDialog
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox

from utils.Preferences import Preferences
from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.tensorflow_classifier.tensor_utils.pipeline_config import PipelineConfig, PipelineConfigError

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="keras")


class PipelineWorker(QThread):
    log = Signal(str)
    progress = Signal(int, str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, config: PipelineConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.cancel_event = threading.Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self):
        try:
            # Lazy import: TensorFlow só é carregado QUANDO executar pipeline
            from plugins.tensorflow_classifier.tensor_utils.classifier_pipeline import ClassifierPipeline
            pipeline = ClassifierPipeline(
                config=self.config,
                logger=self.log.emit,
                progress_callback=self._emit_progress,
                cancel_event=self.cancel_event,
            )
            pipeline.execute()
            if self.cancel_event.is_set():
                self.finished.emit("Pipeline cancelado pelo usuario")
            else:
                self.finished.emit("Pipeline concluido com sucesso")
        except Exception as exc:
            self.error.emit(str(exc))

    def _emit_progress(self, percent: int, message: str) -> None:
        self.progress.emit(percent, message)


class MainController:
    def __init__(self, view):
        self.view = view
        self._data: Dict[str, Any] = Preferences.load_tool_prefs(ToolKey.CLASSIFIER)
        self.worker = None
        self._loading_preferences = True
        self._run_started_at = None
        self._run_metrics = {}
        self._eta_target = None
        self._run_estimated_seconds = 0.0
        self._last_progress_message = "Iniciando pipeline..."
        # Timer de progresso: só inicia QUANDO execução começar (fix #3)
        self._progress_timer = QTimer()
        self._progress_timer.setInterval(500)
        self._progress_timer.timeout.connect(self._refresh_time_based_progress)
        # Timer de debounce: agrupa salvamentos em disco (fix #1)
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(300)
        self._save_timer.timeout.connect(self._do_save_preferences)
        self._last_output_tif_path: Path | None = None
        self._last_report_html_path: Path | None = None
        self._cancel_requested = False
        self._signals = SignalManager.instance()

        self._connect_signals()
        print("> Sinais conectados no MainController")
        print(f"{self.view.btn_add_shp}")
        self._init_defaults()#
        self.loadpreferences()
        # Só finaliza carregamento APÓS todos os widgets estarem populados
        from PySide6.QtCore import QTimer as Qtimer
        Qtimer.singleShot(0, self._finalize_load)
        self._update_resumo()
        # Timer de progresso NÃO inicia aqui - só quando executar (fix #3)
        self._progress_timer.stop()

    def _connect_signals(self):
        from core.config.LogUtils import LogUtils
        logger = LogUtils(tool=ToolKey.CLASSIFIER.value, class_name="MainController")
        logger.info("Iniciando conexao de sinais", code="SIG_CONNECT_START")
        logger.debug(f"view type = {type(self.view).__name__}", code="SIG_VIEW_TYPE")
        logger.debug(f"view tem _btns = {hasattr(self.view, '_btns')}", code="SIG_HAS_BTNS")
        if hasattr(self.view, '_btns'):
            logger.debug(f"_btns keys: {list(self.view._btns._buttons.keys())}", code="SIG_BTNS_KEYS")
        logger.debug(f"view tem btn_add_shp = {hasattr(self.view, 'btn_add_shp')}", code="SIG_HAS_ADD_SHP")
        if hasattr(self.view, 'btn_add_shp'):
            logger.debug(f"btn_add_shp type = {type(self.view.btn_add_shp).__name__}", code="SIG_ADD_SHP_TYPE")
        logger.debug(f"view tem btn_listar_modelos = {hasattr(self.view, 'btn_listar_modelos')}", code="SIG_HAS_LISTAR")
        logger.debug(f"view tem combo_model_action = {hasattr(self.view, 'combo_model_action')}", code="SIG_HAS_COMBO")

        self.view._btns["load_cfg"].clicked.connect(self._on_load_cfg)
        self.view._btns["save_cfg"].clicked.connect(self._on_save_cfg)
        self.view._btns["reset_cfg"].clicked.connect(self._on_reset_cfg)
        self.view._btns["cancelar"].clicked.connect(self._on_cancelar)
        self.view._btns["executar"].clicked.connect(self._on_executar)
        self.view.btn_add_shp.clicked.connect(self._on_add_shp)
        self.view.combo_model_action.currentTextChanged.connect(self._on_model_action_changed)
        self.view.btn_listar_modelos.clicked.connect(self._on_listar_modelos)
        logger.info("Conexao de sinais finalizada", code="SIG_CONNECT_DONE")

        widgets_bind = [
            self.view.row_img_treino.edit,
            self.view.row_img_classif.edit,
            self.view.row_img_saida.edit,
            self.view.edit_camadas,
            self.view.combo_ativacao,
            self.view.spin_dropout,
            self.view.spin_epochs,
            self.view.spin_batch_train,
            self.view.spin_batch_pred,
            self.view.spin_test_size,
            self.view.spin_ram,
            self.view.chk_mascara,
            self.view.chk_zero_nodata,
            self.view.chk_salvar_modelo,
            self.view.combo_model_action,
            self.view.spin_random,
            self.view.spin_alpha,
            self.view.row_modelo_path.edit,
            self.view.row_modelo_existente.edit,
        ]
        for w in widgets_bind:
            if hasattr(w, "textChanged"):
                w.textChanged.connect(self._update_resumo)
                w.textChanged.connect(self.savepreferences)
            elif hasattr(w, "currentTextChanged"):
                w.currentTextChanged.connect(self._update_resumo)
                w.currentTextChanged.connect(self.savepreferences)
            elif hasattr(w, "valueChanged"):
                w.valueChanged.connect(self._update_resumo)
                w.valueChanged.connect(self.savepreferences)
            elif hasattr(w, "stateChanged"):
                w.stateChanged.connect(self._update_resumo)
                w.stateChanged.connect(self.savepreferences)

    def _init_defaults(self):
        default_shps = [
            ("dados/solo.shp", 0, "Solo"),
            ("dados/floresta.shp", 1, "Floresta"),
            ("dados/palhada.shp", 2, "Palhada"),
            ("dados/daninhas.shp", 3, "Daninhas"),
        ]
        for p, c, legenda in default_shps:
            self._add_shp_row(p, c, legenda)

    def _add_shp_row(self, path: str, classe: int, legenda: str = ""):
        self.view.table_shp.add_row(path, classe, legenda)

    def _on_shp_row_removed(self):
        self._update_resumo()
        self.savepreferences()

    def _on_add_shp(self):
        print("> _on_add_shp: INICIO - botao + Adicionar Shapefile clicado")    
        self._log("[DEBUG] _on_add_shp: INICIO - botao + Adicionar Shapefile clicado")
        self._log(f"[DEBUG] _on_add_shp: self.view type={type(self.view).__name__}")
        self._log(f"[DEBUG] _on_add_shp: self.view.btn_add_shp existe={hasattr(self.view, 'btn_add_shp')}")
        self._log(f"[DEBUG] _on_add_shp: self.view.btn_add_shp text={self.view.btn_add_shp.text() if hasattr(self.view, 'btn_add_shp') else 'N/A'}")
        path = ExplorerUtils.open_file("Adicionar Shapefile", "", "Shapefile (*.shp)", self.view)
        self._log(f"[DEBUG] _on_add_shp: ExplorerUtils.open_file retornou path={path!r}")
        if path:
            self._log(f"[DEBUG] _on_add_shp: path valido, chamando all_rows() da table_shp")
            data = self.view.table_shp.all_rows()
            self._log(f"[DEBUG] _on_add_shp: all_rows() retornou {len(data)} linhas")
            max_cls = max((d.get("col_1", -1) for d in data), default=-1)
            self._log(f"[DEBUG] _on_add_shp: max_cls calculado = {max_cls}")
            default_legend = Path(path).stem
            self._log(f"[DEBUG] _on_add_shp: chamando _add_shp_row(path={path}, classe={max_cls + 1}, legenda={default_legend})")
            self._add_shp_row(path, max_cls + 1, default_legend)
            self._log("[DEBUG] _on_add_shp: _add_shp_row executado, chamando _update_resumo")
            self._update_resumo()
            self._log("[DEBUG] _on_add_shp: _update_resumo executado, chamando savepreferences")
            self.savepreferences()
            self._log("[DEBUG] _on_add_shp: FINALIZADO com sucesso")
        else:
            self._log("[DEBUG] _on_add_shp: path vazio ou None - usuario cancelou a selecao")

    def _on_model_action_changed(self):
        action = self.view.combo_model_action.currentText()
        show_existing = action in ["Treinar modelo existente", "Usar modelo existente"]
        self.view.row_modelo_existente.setVisible(show_existing)
        self.view.btn_listar_modelos.setVisible(show_existing)
        self._update_resumo()

    def _on_listar_modelos(self):
        model_root = Path("models")
        if not model_root.exists():
            MessageBox.show_info("Pasta 'models' nao encontrada.", title="Modelos")
            return
        model_files = [p for p in model_root.rglob("*.keras") if p.is_file()]
        if not model_files:
            MessageBox.show_info("Nenhum modelo .keras encontrado em 'models'.", title="Modelos")
            return
        model_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        options = []
        for p in model_files:
            modified_at = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            options.append(f"{p} | modificado: {modified_at}")
        selected, ok = QInputDialog.getItem(self.view, "Selecionar Modelo", "Modelos (mais recentes primeiro):", options, 0, False)
        if not ok or not selected:
            return
        selected_path = selected.split(" | modificado: ")[0]
        self.view.row_modelo_existente.edit.setText(selected_path)
        self._log(f"> Modelo selecionado: {selected_path}")
        self.savepreferences()

    def _update_resumo(self):
        treino = self.view.row_img_treino.path() or "-"
        classif = self.view.row_img_classif.path() or "-"
        saida = self.view.row_img_saida.path() or "-"
        camadas = self.view.edit_camadas.text() or "-"
        ativ = self.view.combo_ativacao.currentText()
        drop = self.view.spin_dropout.value()
        ep = self.view.spin_epochs.value()
        bt = self.view.spin_batch_train.value()
        bp = self.view.spin_batch_pred.value()
        ram = self.view.spin_ram.value()
        mask = "Sim" if self.view.chk_mascara.isChecked() else "Nao"
        zero_nodata = "Sim" if self.view.chk_zero_nodata.isChecked() else "Nao"
        model_action = self.view.combo_model_action.currentText()
        resumo = (
            f"<b>Imagem Treino:</b> {treino}<br>"
            f"<b>Imagem Classif.:</b> {classif}<br>"
            f"<b>Saida:</b> {saida}<br>"
            f"<b>Acao Modelo:</b> {model_action}<br>"
        )
        if self.view.row_modelo_existente.isVisible():
            existing_model = self.view.row_modelo_existente.path() or "-"
            resumo += f"<b>Modelo Existente:</b> {existing_model}<br>"
        resumo += (
            f"<b>Rede:</b> [{camadas}] - ativacao {ativ}, dropout {drop}<br>"
            f"<b>Treino:</b> {ep} epocas | batch {bt} / pred {bp}<br>"
            f"<b>RAM limite:</b> {ram}% | Mascara: {mask} | Zero->Nodata: {zero_nodata}"
        )
        self.view.lbl_resumo.setHtml(resumo)

    def _on_cancelar(self):
        if self.worker is None or not self.worker.isRunning():
            return
        self._log("> Cancelamento solicitado pelo usuario. Aguardando parada segura...")
        self._cancel_requested = True
        self.worker.cancel()
        self.view._btns.set_enabled("cancelar", False)
        self.view._btns["cancelar"].setText("CANCELANDO...")

    def _on_executar(self):
        if self.worker is not None and self.worker.isRunning():
            self._log("> O pipeline ja esta em execucao")
            return
        self._cancel_requested = False
        pipeline_data = self.get_pipeline_config()
        try:
            config = PipelineConfig.from_dict(pipeline_data)
        except PipelineConfigError as exc:
            self._log(f"> Configuracao invalida: {exc}")
            return
        self.savepreferences()
        self._prepare_run_metrics(config)
        self._log_eta_estimado()
        self._last_progress_message = "Iniciando pipeline..."
        self._log("> Pipeline iniciado")
        self._set_running_state(True)
        self.worker = PipelineWorker(config)
        self.worker.log.connect(self._on_worker_log)
        self.worker.progress.connect(self._on_progress_update)
        self.worker.finished.connect(self._on_pipeline_finished)
        self.worker.error.connect(self._on_pipeline_error)
        self.worker.start()

    def _on_load_cfg(self):
        path = ExplorerUtils.open_file("Carregar Configuracao", "", "JSON (*.json)", self.view)
        if not path:
            return
        try:
            config = PipelineConfig.load(Path(path))
            self._populate_fields(config)
            self._log(f"> Configuracao carregada: {path}")
            self.savepreferences()
        except Exception as exc:
            self._log(f"> Falha ao carregar configuracao: {exc}")

    def _on_save_cfg(self):
        path = ExplorerUtils.save_file("Salvar Configuracao", "config_ui.json", "JSON (*.json)", self.view)
        if not path:
            return
        try:
            config = PipelineConfig.from_dict(self.get_pipeline_config())
            config.save(Path(path))
            self._log(f"> Configuracao salva: {path}")
        except Exception as exc:
            self._log(f"> Falha ao salvar configuracao: {exc}")

    def _on_reset_cfg(self):
        if self.worker is not None and self.worker.isRunning():
            self._log("> Nao e possivel restaurar padrao durante execucao")
            return
        confirm = MessageBox.show_question(
            "Isso vai zerar o preferences.json e restaurar os valores padrao. Deseja continuar?",
            title="Restaurar Padrao", buttons=MessageBox.YES_NO, default_button=MessageBox.NO,
        )
        if confirm != MessageBox.YES:
            return
        self._loading_preferences = True
        self._data = {}
        Preferences.save_tool_prefs(ToolKey.CLASSIFIER, self._data)
        self.view.row_img_treino.edit.setText("dados/imagemTreino.tif")
        self.view.row_img_classif.edit.setText("dados/imagemCompleta.tif")
        self.view.row_img_saida.edit.setText("resultado/mapa_classificado_ui.tif")
        self.view.edit_camadas.setText("128, 64, 32")
        self.view.combo_ativacao.setCurrentText("relu")
        self.view.spin_dropout.setValue(0.1)
        self.view.spin_epochs.setValue(150)
        self.view.spin_batch_train.setValue(64)
        self.view.spin_batch_pred.setValue(4096)
        self.view.spin_test_size.setValue(0.30)
        self.view.spin_random.setValue(42)
        self.view.spin_ram.setValue(70)
        self.view.chk_mascara.setChecked(True)
        self.view.chk_zero_nodata.setChecked(False)
        self.view.spin_alpha.setValue(250)
        self.view.chk_salvar_modelo.setChecked(True)
        self.view.row_modelo_path.edit.setText("resultado/modelo_ui.keras")
        self.view.combo_model_action.setCurrentText("Treinar modelo novo")
        self.view.row_modelo_existente.edit.setText("")
        self.view.table_shp.setRowCount(0)
        self._init_defaults()
        self._on_model_action_changed()
        self._update_resumo()
        self._loading_preferences = False
        self.savepreferences()
        self._log("> Configuracoes restauradas para o padrao")

    def _log(self, message: str) -> None:
        text = str(message)
        lower = text.lower()
        if lower.startswith("report html salvo em "):
            self._last_report_html_path = Path(text[len("report html salvo em "):].strip())
        if "treinando modelo" in lower:
            self._last_progress_message = "Treinando"
            self._refresh_time_based_progress()
        elif "classificando imagem completa" in lower:
            self._last_progress_message = "Classificando"
            self._refresh_time_based_progress()
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        safe = html.escape(text)
        msg = f"<span style='color:#909090; font-family:Consolas,monospace; font-size:11px;'>[{timestamp}]</span> <span style='color:#E0E0E0; font-family:Consolas,monospace; font-size:12px;'>{safe}</span>"
        self._signals.console_message.emit(msg)

    def _on_worker_log(self, message: str) -> None:
        self._log(message)

    def _set_running_state(self, running: bool) -> None:
        self.view._btns.set_enabled("executar", not running)
        self.view._btns.set_enabled("load_cfg", not running)
        self.view._btns.set_enabled("save_cfg", not running)
        self.view._btns.set_enabled("reset_cfg", not running)
        self.view._btns.set_enabled("cancelar", running)
        if running:
            self.view._btns["cancelar"].setText("CANCELAR")
            if not self._progress_timer.isActive():
                self._progress_timer.start()
            if hasattr(self.view, "page"):
                self.view.page.set_badge(self.view.page.RUNNING)
            self._signals.progress_update.emit(1.0)
        else:
            self._cancel_requested = False
            if self._progress_timer.isActive():
                self._progress_timer.stop()
            if hasattr(self.view, "page"):
                self.view.page.set_badge(self.view.page.PRONTA)
            self._signals.progress_update.emit(100.0)

    def _on_progress_update(self, percent: int, message: str) -> None:
        self._last_progress_message = message or self._last_progress_message
        self._refresh_time_based_progress()

    def _refresh_time_based_progress(self) -> None:
        display_percent = self._time_based_progress_percent(0.0)
        self._signals.progress_update.emit(display_percent / 100.0)

    def _on_pipeline_finished(self, message: str) -> None:
        is_cancel = self._cancel_requested or "cancelado" in str(message).lower()
        self._finalize_run_metrics(success=not is_cancel)
        self._log(f"> {message}")
        if not is_cancel:
            self._append_output_links()
        self._set_running_state(False)
        if is_cancel and hasattr(self.view, "page"):
            self.view.page.set_badge(self.view.page.CANCELED)
        self._signals.progress_update.emit(100.0)

    def _on_pipeline_error(self, message: str) -> None:
        self._finalize_run_metrics(success=False)
        self._log(f"> ERRO: {message}")
        self._set_running_state(False)
        if hasattr(self.view, "page"):
            self.view.page.set_badge(self.view.page.ERROR)
        self._signals.progress_update.emit(0.0)

    def _populate_fields(self, config: PipelineConfig) -> None:
        self.view.row_img_treino.edit.setText(str(config.training_image))
        self.view.row_img_classif.edit.setText(str(config.classification_image))
        self.view.row_img_saida.edit.setText(str(config.output_path))
        self.view.edit_camadas.setText(", ".join(str(layer) for layer in config.hidden_layers))
        self.view.combo_ativacao.setCurrentText(config.activation)
        self.view.spin_dropout.setValue(config.dropout_rate)
        self.view.spin_epochs.setValue(config.epochs)
        self.view.spin_batch_train.setValue(config.batch_size_train)
        self.view.spin_batch_pred.setValue(config.batch_size_pred)
        self.view.spin_test_size.setValue(config.test_size)
        self.view.spin_random.setValue(config.random_state)
        self.view.spin_ram.setValue(config.ram_limit_pct)
        self.view.chk_mascara.setChecked(config.use_mask)
        self.view.chk_zero_nodata.setChecked(config.zero_as_nodata)
        self.view.spin_alpha.setValue(config.nodata_threshold)
        self.view.chk_salvar_modelo.setChecked(config.save_model)
        self.view.row_modelo_path.edit.setText(str(config.model_path))
        self.view.combo_model_action.setCurrentText(config.model_action)
        self.view.row_modelo_existente.edit.setText(str(config.existing_model_path or ""))
        self.view.table_shp.setRowCount(0)
        for entry in config.shapefiles:
            self._add_shp_row(str(entry.path), int(entry.class_id), str(entry.legend or ""))
        self._on_model_action_changed()
        self.savepreferences()

    def loadpreferences(self) -> None:
        self._loading_preferences = True
        self._data = Preferences.load_tool_prefs(ToolKey.CLASSIFIER)
        self.view.row_img_treino.edit.setText(str(self._data.get("training_image", self.view.row_img_treino.path())))
        self.view.row_img_classif.edit.setText(str(self._data.get("classification_image", self.view.row_img_classif.path())))
        self.view.row_img_saida.edit.setText(str(self._data.get("output", self.view.row_img_saida.path())))
        self.view.edit_camadas.setText(str(self._data.get("hidden_layers", self.view.edit_camadas.text())))
        self.view.combo_ativacao.setCurrentText(str(self._data.get("activation", self.view.combo_ativacao.currentText())))
        self.view.spin_dropout.setValue(float(self._data.get("dropout_rate", self.view.spin_dropout.value())))
        self.view.spin_epochs.setValue(int(self._data.get("epochs", self.view.spin_epochs.value())))
        self.view.spin_batch_train.setValue(int(self._data.get("batch_size_train", self.view.spin_batch_train.value())))
        self.view.spin_batch_pred.setValue(int(self._data.get("batch_size_pred", self.view.spin_batch_pred.value())))
        self.view.spin_test_size.setValue(float(self._data.get("test_size", self.view.spin_test_size.value())))
        self.view.spin_random.setValue(int(self._data.get("random_state", self.view.spin_random.value())))
        self.view.spin_ram.setValue(int(self._data.get("ram_limit_pct", self.view.spin_ram.value())))
        self.view.chk_mascara.setChecked(bool(self._data.get("use_mask", self.view.chk_mascara.isChecked())))
        self.view.chk_zero_nodata.setChecked(bool(self._data.get("zero_as_nodata", self.view.chk_zero_nodata.isChecked())))
        self.view.spin_alpha.setValue(int(self._data.get("nodata_threshold", self._data.get("alpha_threshold", self.view.spin_alpha.value()))))
        self.view.chk_salvar_modelo.setChecked(bool(self._data.get("save_model", self.view.chk_salvar_modelo.isChecked())))
        self.view.row_modelo_path.edit.setText(str(self._data.get("model_path", self.view.row_modelo_path.path())))
        self.view.combo_model_action.setCurrentText(str(self._data.get("model_action", self.view.combo_model_action.currentText())))
        self.view.row_modelo_existente.edit.setText(str(self._data.get("existing_model_path", self.view.row_modelo_existente.path())))
        shapefiles = self._data.get("shapefiles", [])
        if isinstance(shapefiles, list) and shapefiles:
            self.view.table_shp.setRowCount(0)
            for item in shapefiles:
                if isinstance(item, dict) and "path" in item and "class_id" in item:
                    self._add_shp_row(str(item["path"]), int(item["class_id"]), str(item.get("legend", "")))
        self._on_model_action_changed()
        self._update_resumo()
        # loading_preferences NÃO é liberado aqui - isso é feito em _finalize_load
        # após todos os signals dos widgets terminarem de processar

    def _finalize_load(self) -> None:
        """Finaliza o carregamento: libera flag e salva uma vez."""
        self._loading_preferences = False
        self._do_save_preferences()

    def _debounce_save(self) -> None:
        """Agenda salvamento com debounce de 300ms (evita I/O a cada digitação)."""
        if self._loading_preferences:
            return
        self._save_timer.start()

    def _do_save_preferences(self) -> None:
        """Salva as preferências sem travar a UI (chamado pelo timer de debounce)."""
        if self._loading_preferences:
            return
        self._data.update(self.get_pipeline_config())
        Preferences.save_tool_prefs(ToolKey.CLASSIFIER, self._data)

    def savepreferences(self) -> None:
        """Método legado: agora usa debounce para evitar I/O excessivo."""
        self._debounce_save()

    def _get_raster_pixels_and_gb(self, path: Path) -> tuple[float, float]:
        pixels = 0.0
        gb = 0.0
        try:
            from plugins.tensorflow_classifier.tensor_utils.raster_source import RasterSource
            raster = RasterSource(path)
            pixels = float(raster.width * raster.height)
        except Exception:
            pixels = 0.0
        try:
            gb = float(path.stat().st_size) / (1024.0 ** 3)
        except Exception:
            gb = 0.0
        return pixels, gb

    @staticmethod
    def _count_classes(config: PipelineConfig) -> int:
        unique_classes = set()
        for entry in config.shapefiles:
            unique_classes.add(entry.class_id)
        return max(len(unique_classes), 1)

    def _prepare_run_metrics(self, config: PipelineConfig) -> None:
        self._last_output_tif_path = Path(config.output_path)
        self._last_report_html_path = None
        self._run_num_classes = self._count_classes(config)
        train_pixels, train_gb = self._get_raster_pixels_and_gb(config.training_image)
        class_pixels, class_gb = self._get_raster_pixels_and_gb(config.classification_image)
        if config.model_action == "Usar modelo existente":
            train_pixels = 0.0
            train_gb = 0.0
        train_rate = self._avg_px_per_sec("train", self._run_num_classes)
        class_rate = self._avg_px_per_sec("class", self._run_num_classes)
        est_seconds = (train_pixels / train_rate) + (class_pixels / class_rate)
        self._run_estimated_seconds = max(est_seconds, 1.0)
        self._eta_target = datetime.now() + timedelta(seconds=max(est_seconds, 0.0))
        self._run_started_at = perf_counter()
        self._run_metrics = {"train_pixels": train_pixels, "train_gb": train_gb, "class_pixels": class_pixels, "class_gb": class_gb, "num_classes": self._run_num_classes}

    def _avg_px_per_sec(self, prefix: str, num_classes: int = 2) -> float:
        suffix = f"_{num_classes}class"
        total_pixels = float(self._data.get(f"{prefix}_total_pixels{suffix}", 1000.0))
        total_seconds = float(self._data.get(f"{prefix}_total_seconds{suffix}", 1.0))
        if total_seconds <= 0:
            total_seconds = 1.0
        if total_pixels <= 0:
            total_pixels = 1000.0
        return total_pixels / total_seconds

    def _log_eta_estimado(self) -> None:
        train_rate = self._avg_px_per_sec("train", self._run_num_classes)
        class_rate = self._avg_px_per_sec("class", self._run_num_classes)
        self._log(f"> ETA estimado: {self._eta_target.strftime('%H:%M:%S') if self._eta_target else '--:--:--'} | {self._run_num_classes} classes | Treino={train_rate:.2f} px/s | Classificacao={class_rate:.2f} px/s")

    def _format_progress_message(self, message: str) -> str:
        if self._eta_target is None:
            return message
        return f"{message} | ETA: {self._eta_target.strftime('%H:%M:%S')}"

    def _time_based_progress_percent(self, fallback_percent: float) -> float:
        if self._run_started_at is None or self._run_estimated_seconds <= 0:
            return min(max(fallback_percent, 0.0), 100.0)
        elapsed = max(perf_counter() - self._run_started_at, 0.0)
        progress = (elapsed / self._run_estimated_seconds) * 100.0
        return min(max(progress, 0.0), 100.0)

    def _finalize_run_metrics(self, success: bool) -> None:
        if not success or self._run_started_at is None:
            self._run_started_at = None
            self._run_metrics = {}
            self._eta_target = None
            self._run_estimated_seconds = 0.0
            return
        elapsed = max(perf_counter() - self._run_started_at, 0.0)
        train_pixels = float(self._run_metrics.get("train_pixels", 0.0))
        class_pixels = float(self._run_metrics.get("class_pixels", 0.0))
        train_gb = float(self._run_metrics.get("train_gb", 0.0))
        class_gb = float(self._run_metrics.get("class_gb", 0.0))
        num_classes = int(self._run_metrics.get("num_classes", 2))
        suffix = f"_{num_classes}class"
        train_seconds = elapsed * (train_pixels / (train_pixels + class_pixels)) if (train_pixels + class_pixels) > 0 else 0.0
        class_seconds = max(elapsed - train_seconds, 0.0)
        self._data[f"train_total_pixels{suffix}"] = float(self._data.get(f"train_total_pixels{suffix}", 1000.0)) + train_pixels
        self._data[f"train_total_gb{suffix}"] = float(self._data.get(f"train_total_gb{suffix}", 0.0)) + train_gb
        self._data[f"train_total_seconds{suffix}"] = float(self._data.get(f"train_total_seconds{suffix}", 1.0)) + train_seconds
        self._data[f"class_total_pixels{suffix}"] = float(self._data.get(f"class_total_pixels{suffix}", 1000.0)) + class_pixels
        self._data[f"class_total_gb{suffix}"] = float(self._data.get(f"class_total_gb{suffix}", 0.0)) + class_gb
        self._data[f"class_total_seconds{suffix}"] = float(self._data.get(f"class_total_seconds{suffix}", 1.0)) + class_seconds
        self.savepreferences()
        self._log(f"> Estatisticas acumuladas atualizadas ({num_classes} classes) | Treino: {train_pixels:.0f}px, {train_gb:.3f}GB | Classificacao: {class_pixels:.0f}px, {class_gb:.3f}GB | Tempo total execucao: {elapsed:.2f}s")
        self._run_started_at = None
        self._run_metrics = {}
        self._eta_target = None
        self._run_estimated_seconds = 0.0

    @staticmethod
    def _to_file_url(path: Path) -> str:
        return path.resolve().as_uri()

    def _append_output_links(self) -> None:
        output_path = self._last_output_tif_path
        report_path = self._last_report_html_path
        if not output_path and not report_path:
            return
        parts = ["<span style='color:#8EC5FF; font-family:Consolas,monospace; font-size:12px; font-weight:600;'>> Atalhos de saida</span>"]
        if output_path:
            parts.append(f"<span style='color:#CFCFCF; font-family:Consolas,monospace; font-size:12px;'>Pasta do TIFF classificado: <a href='{self._to_file_url(output_path.resolve().parent)}' style='color:#56D4DD;'>abrir pasta</a></span>")
        if report_path:
            parts.append(f"<span style='color:#CFCFCF; font-family:Consolas,monospace; font-size:12px;'>Report HTML: <a href='{self._to_file_url(report_path)}' style='color:#56D4DD;'>abrir report</a></span>")
        self._signals.console_message.emit("<br/>".join(parts))

    def get_shapefile_entries(self):
        entries = []
        for row in self.view.table_shp.all_rows():
            path = row.get("col_0", "")
            class_id = row.get("col_1", 0)
            legend = row.get("col_2", "")
            if path:
                entries.append({"path": path, "class_id": class_id, "legend": legend})
        return entries

    def get_output_path(self):
        return self.view.row_img_saida.path()

    def get_model_action(self):
        return self.view.combo_model_action.currentText()

    def get_pipeline_config(self):
        return {
            "shapefiles": self.get_shapefile_entries(),
            "output": self.get_output_path(),
            "training_image": self.view.row_img_treino.path(),
            "classification_image": self.view.row_img_classif.path(),
            "model_action": self.get_model_action(),
            "save_model": self.view.chk_salvar_modelo.isChecked(),
            "model_path": self.view.row_modelo_path.path(),
            "existing_model_path": self.view.row_modelo_existente.path(),
            "test_size": self.view.spin_test_size.value(),
            "random_state": self.view.spin_random.value(),
            "epochs": self.view.spin_epochs.value(),
            "batch_size_train": self.view.spin_batch_train.value(),
            "batch_size_pred": self.view.spin_batch_pred.value(),
            "hidden_layers": self.view.edit_camadas.text(),
            "activation": self.view.combo_ativacao.currentText(),
            "dropout_rate": self.view.spin_dropout.value(),
            "use_mask": self.view.chk_mascara.isChecked(),
            "zero_as_nodata": self.view.chk_zero_nodata.isChecked(),
            "nodata_threshold": self.view.spin_alpha.value(),
            "ram_limit_pct": self.view.spin_ram.value(),
        }