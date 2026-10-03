# -*- coding: utf-8 -*-
"""
ClassificationTool — Ferramenta de Classificação Raster
=========================================================
Widget hospedado no Workspace do Aetheris ToolBox.
Comunicação via SignalManager.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from plugins.BasePlugin import BasePlugin
from core.enum.ToolKey import ToolKey
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.simple.SimpleSecondaryButton import SimpleSecondaryButton
from resources.widgets.simple.SimpleSelector import SimpleSelector
from resources.widgets.grid.GridSelector import GridSelector
from resources.widgets.simple.SimpleComboBox import SimpleComboBox
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from resources.widgets.ItemTable import ItemTable
from resources.widgets.grid.GridLineEdit import GridLineEdit
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.grid.GridCheckBox import GridCheckBox
from plugins.tensorflow_classifier.tensor_utils.ui_field_specs import UI_FIELD_SPECS


class TensorflowClassificationPlugin(BasePlugin):
    """
    Widget completo da ferramenta de classificação raster.
    Comunica logs e progresso via SignalManager.
    """

    def __init__(self, parent=None):
        super().__init__(tool_key=ToolKey.CLASSIFIER.value, parent=parent, title="TensorFlow")
        self.logger.info("TensorFlow plugin carregado", code="TOOL_READY")
        self._controller = None

    def _build_ui(self):
        super()._build_ui()
        main_layout = self.main_layout

        self.page.set_badge(self.page.PRONTA)

        # --- ACTION BUTTONS ---
        self._btns = ExecutionButtons(self)
        self._btns.setup(
            {
                "load_cfg": {"text": "Carregar Config", "type": "secondary", "description": "Carrega uma configuração salva anteriormente"},
                "save_cfg": {"text": "Salvar Config", "type": "secondary", "description": "Salva a configuração atual em disco"},
                "reset_cfg": {"text": "Restaurar Padrao", "type": "secondary", "description": "Restaura configurações para o valor padrão"},
                "cancelar": {"text": "CANCELAR", "type": "danger", "description": "Cancela a execução em andamento"},
                "executar": {"text": "EXECUTAR PIPELINE", "type": "primary", "description": "Inicia o pipeline de classificação"},
            }
        )
        self._btns.set_enabled("cancelar", False)
        main_layout.addWidget(self._btns)

        # TOP ROW
        grp_img = GroupPainel("Imagens & Saida")
        sel_grid = GridSelector({
            "Imagem Treino": {"file_filter": "GeoTIFF (*.tif *.tiff)", "default_path": "dados/imagemTreino.tif"},
            "Imagem Classif.": {"file_filter": "GeoTIFF (*.tif *.tiff)", "default_path": "dados/imagemCompleta.tif"},
            "Saida GeoTIFF": {"file_filter": "GeoTIFF (*.tif *.tiff)", "default_path": "resultado/mapa_classificado_ui.tif", "browse_mode": "save_file"},
        }, title=None)
        self._sel_img_treino = sel_grid["Imagem Treino"]
        self._sel_img_classif = sel_grid["Imagem Classif."]
        self._sel_img_saida = sel_grid["Saida GeoTIFF"]
        grp_img.group_layout.addWidget(sel_grid)
        grp_img.group_layout.addStretch()

        grp_mod = GroupPainel("Persistencia do Modelo")
        self._combo_model_action = SimpleComboBox(
            items={"Treinar modelo novo": "Treinar modelo novo",
                   "Treinar modelo existente": "Treinar modelo existente",
                   "Usar modelo existente": "Usar modelo existente"},
            label="Acao:",
        )
        self._combo_model_action.select_first()
        grp_mod.group_layout.addWidget(self._combo_model_action)
        self._selector_modelo_existente = SimpleSelector("Modelo Existente", "", file_filter="Keras Model (*.keras)")
        self._selector_modelo_existente.setVisible(False)
        grp_mod.group_layout.addWidget(self._selector_modelo_existente)
        self.btn_listar_modelos = SimpleSecondaryButton("Listar Modelos")
        self.btn_listar_modelos.setVisible(False)
        grp_mod.group_layout.addWidget(self.btn_listar_modelos, alignment=Qt.AlignmentFlag.AlignLeft)
        self._grid_salvar_modelo = GridCheckBox({"save_model": {"label": "Salvar modelo (.keras)", "description": "Salvar o modelo treinado em disco (.keras)", "default": True}}, num_columns=1)
        grp_mod.group_layout.addWidget(self._grid_salvar_modelo)
        self._selector_modelo_path = SimpleSelector("Caminho", "resultado/modelo_ui.keras", file_filter="Keras Model (*.keras)", browse_mode="save_file")
        grp_mod.group_layout.addWidget(self._selector_modelo_path)
        grp_mod.group_layout.addStretch()

        top_row = GridGroupPainel(grp_img, grp_mod)
        main_layout.addWidget(top_row)

        # BOTTOM ROW
        grp_shp = GroupPainel("Shapefiles por Classe")
        self.table_shp = ItemTable(columns=[
            {"header": "Caminho", "type": "text", "stretch": True, "editable": False},
            {"header": "ID", "type": "spin", "width": 55, "min": 0, "max": 999},
            {"header": "Legenda", "type": "line", "width": 90, "placeholder": "Legenda..."},
            {"header": "", "type": "remove", "width": 65},
        ])
        grp_shp.group_layout.addWidget(self.table_shp)
        self.btn_add_shp = SimpleSecondaryButton("+ Adicionar Shapefile")
        self.btn_add_shp.setToolTip("Abre seletor de arquivos para adicionar um shapefile .shp à tabela de classes")
        grp_shp.group_layout.addWidget(self.btn_add_shp, alignment=Qt.AlignmentFlag.AlignLeft)
        grp_shp.group_layout.addStretch()

        grp_rede = GroupPainel("Rede Neural & Treinamento")
        self._grid_camadas = GridLineEdit({"camadas": {"label": "Camadas:", "default": "128, 64, 32", "placeholder": "ex: 256, 128, 64", "description": "Neurônios por camada oculta, separados por vírgula"}})
        grp_rede.group_layout.addWidget(self._grid_camadas)
        self._combo_ativacao = SimpleComboBox(items={"relu": "relu", "elu": "elu", "tanh": "tanh", "sigmoid": "sigmoid", "linear": "linear"}, label="Ativacao:")
        self._combo_ativacao.current_value = "relu"
        grp_rede.group_layout.addWidget(self._combo_ativacao)
        self._grid_numericos = GridDoubleSpinBox({
            "dropout": {"label": "Dropout:", "decimal": 2, "default": 0.10, "min": 0.0, "max": 0.9, "step": 0.05, "description": "Taxa de dropout para regularização"},
            "epochs": {"label": "Epocas:", "decimal": 0, "default": 150, "min": 1, "max": 10000, "step": 1, "description": "Número de épocas de treinamento"},
            "batch_train": {"label": "Batch Treino:", "decimal": 0, "default": 64, "min": 1, "max": 8192, "step": 1, "description": "Tamanho do lote para treinamento"},
            "batch_pred": {"label": "Batch Pred.:", "decimal": 0, "default": 4096, "min": 1, "max": 65536, "step": 1, "description": "Tamanho do lote para predição"},
            "test_size": {"label": "Test Size:", "decimal": 2, "default": 0.30, "min": 0.01, "max": 0.99, "step": 0.01, "description": "Proporção dos dados para validação"},
            "random_state": {"label": "Random State:", "decimal": 0, "default": 42, "min": 0, "max": 999999, "step": 1, "description": "Semente aleatória para reprodutibilidade"},
            "ram_pct": {"label": "RAM:", "decimal": 0, "default": 70, "min": 10, "max": 95, "step": 1, "suffix": "%", "description": "Limite percentual de RAM utilizável"},
            "nodata_limiar": {"label": "Limiar Nodata:", "decimal": 0, "default": 250, "min": 0, "max": 255, "step": 1, "description": "Valor de limiar para considerar nodata"},
        }, columns=2)
        grp_rede.group_layout.addWidget(self._grid_numericos)
        self._grid_checkboxes = GridCheckBox({"use_mask": {"label": "Mascara alpha", "description": "Aplicar máscara alpha na saída", "default": True}, "zero_nodata": {"label": "0 = nodata", "description": "Considerar valor 0 como nodata", "default": False}}, num_columns=2)
        grp_rede.group_layout.addWidget(self._grid_checkboxes)
        grp_rede.group_layout.addStretch()

        bottom_row = GridGroupPainel(grp_shp, grp_rede)
        main_layout.addWidget(bottom_row)

        # Resumo interno (controller)
        self.lbl_resumo = type('', (), {'setHtml': lambda s, h: None, 'setMaximumHeight': lambda s, h: None, 'setVisible': lambda s, v: None})()

        self._apply_field_tooltips()
        self._init_controller()

    def _init_controller(self):
        from plugins.tensorflow_classifier.tensor_utils.main_controller import MainController
        self._controller = MainController(view=self)
        self.logger.info("MainController acoplado", code="CONTROLLER_READY")

    def _apply_field_tooltips(self):
        mapping = [
            ("training_image", [self._sel_img_treino.label, self._sel_img_treino.edit, self._sel_img_treino.btn]),
            ("classification_image", [self._sel_img_classif.label, self._sel_img_classif.edit, self._sel_img_classif.btn]),
            ("output_tiff", [self._sel_img_saida.label, self._sel_img_saida.edit, self._sel_img_saida.btn]),
            ("hidden_layers", [self._grid_camadas]),
            ("activation", [self._combo_ativacao]),
            ("dropout_rate", [self._grid_numericos]),
            ("epochs", [self._grid_numericos]),
            ("batch_size_train", [self._grid_numericos]),
            ("batch_size_pred", [self._grid_numericos]),
            ("test_size", [self._grid_numericos]),
            ("random_state", [self._grid_numericos]),
            ("ram_limit_pct", [self._grid_numericos]),
            ("use_mask", [self._grid_checkboxes]),
            ("zero_as_nodata", [self._grid_checkboxes]),
            ("nodata_threshold", [self._grid_numericos]),
            ("model_action", [self._combo_model_action]),
            ("existing_model_path", [self._selector_modelo_existente.label, self._selector_modelo_existente.edit, self._selector_modelo_existente.btn]),
            ("save_model", [self._grid_salvar_modelo]),
            ("model_path", [self._selector_modelo_path.label, self._selector_modelo_path.edit, self._selector_modelo_path.btn]),
        ]
        for key, widgets in mapping:
            spec = UI_FIELD_SPECS.get(key)
            desc = spec.description if spec else ""
            if not desc:
                continue
            for widget in widgets:
                widget.setToolTip(desc)

    def add_shp_row_ui(self, path: str, classe: int, legenda: str = ""):
        self.table_shp.add_row(path, classe, legenda)

    def switch_to_console(self):
        pass

    @property
    def row_img_treino(self) -> SimpleSelector:
        return self._sel_img_treino

    @property
    def row_img_classif(self) -> SimpleSelector:
        return self._sel_img_classif

    @property
    def row_img_saida(self) -> SimpleSelector:
        return self._sel_img_saida

    @property
    def edit_camadas(self):
        return self._grid_camadas.widget("camadas")

    @property
    def combo_model_action(self):
        return self._combo_model_action.widget()

    @property
    def combo_ativacao(self):
        return self._combo_ativacao.widget()

    @property
    def row_modelo_existente(self) -> SimpleSelector:
        return self._selector_modelo_existente

    @property
    def row_modelo_path(self) -> SimpleSelector:
        return self._selector_modelo_path

    @property
    def spin_dropout(self):
        return self._grid_numericos.widget("dropout")

    @property
    def spin_epochs(self):
        return self._grid_numericos.widget("epochs")

    @property
    def spin_batch_train(self):
        return self._grid_numericos.widget("batch_train")

    @property
    def spin_batch_pred(self):
        return self._grid_numericos.widget("batch_pred")

    @property
    def spin_test_size(self):
        return self._grid_numericos.widget("test_size")

    @property
    def spin_random(self):
        return self._grid_numericos.widget("random_state")

    @property
    def spin_ram(self):
        return self._grid_numericos.widget("ram_pct")

    @property
    def spin_alpha(self):
        return self._grid_numericos.widget("nodata_limiar")

    @property
    def chk_mascara(self):
        return self._grid_checkboxes.widget("use_mask")

    @property
    def chk_zero_nodata(self):
        return self._grid_checkboxes.widget("zero_nodata")

    @property
    def chk_salvar_modelo(self):
        return self._grid_salvar_modelo.widget("save_model")