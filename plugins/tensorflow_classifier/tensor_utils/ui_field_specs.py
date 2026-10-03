from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FieldValueType(str, Enum):
    PATH = "path"
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"


@dataclass(frozen=True)
class UIFieldSpec:
    label: str
    default: object
    description: str
    type: FieldValueType


UI_FIELD_SPECS: dict[str, UIFieldSpec] = {
    "training_image": UIFieldSpec(
        label="Imagem Treino",
        default="dados/imagemTreino.tif",
        description="Imagem usada para aprender as classes. O sistema pega amostras dos shapefiles e treina o modelo com esses exemplos.",
        type=FieldValueType.PATH,
    ),
    "classification_image": UIFieldSpec(
        label="Imagem Classif.",
        default="dados/imagemCompleta.tif",
        description="Imagem completa que sera classificada pelo modelo treinado, gerando o mapa final com uma classe para cada pixel.",
        type=FieldValueType.PATH,
    ),
    "output_tiff": UIFieldSpec(
        label="Saida GeoTIFF",
        default="resultado/mapa_classificado_ui.tif",
        description="Arquivo final que sera criado pelo sistema. Ele guarda a classificacao de cada pixel em formato GeoTIFF.",
        type=FieldValueType.PATH,
    ),
    "hidden_layers": UIFieldSpec(
        label="Camadas Ocultas",
        default="128, 64, 32",
        description="Define o tamanho da rede neural. Exemplo: 128,64,32 cria tres camadas internas com essas quantidades de neuronios.",
        type=FieldValueType.STR,
    ),
    "activation": UIFieldSpec(
        label="Ativacao",
        default="relu",
        description="Funcao matematica da rede. relu: rapida e comum; elu: suaviza negativos; tanh: -1 a 1; sigmoid: 0 a 1; linear: sem transformacao.",
        type=FieldValueType.STR,
    ),
    "dropout_rate": UIFieldSpec(
        label="Dropout",
        default=0.1,
        description="Desliga aleatoriamente parte dos neuronios durante o treino para evitar decoracao excessiva e melhorar desempenho em novos dados.",
        type=FieldValueType.FLOAT,
    ),
    "epochs": UIFieldSpec(
        label="Epocas",
        default=150,
        description="Numero de vezes que o modelo passa por todos os dados de treino. Mais epocas podem melhorar ou piorar se exagerar.",
        type=FieldValueType.INT,
    ),
    "batch_size_train": UIFieldSpec(
        label="Batch Treino",
        default=64,
        description="Quantidade de amostras processadas por vez no treino. Valores maiores aceleram, mas consomem mais memoria RAM.",
        type=FieldValueType.INT,
    ),
    "batch_size_pred": UIFieldSpec(
        label="Batch Predicao",
        default=4096,
        description="Quantidade de pixels classificados por vez na imagem completa. Aumente com cuidado conforme memoria disponivel no computador.",
        type=FieldValueType.INT,
    ),
    "test_size": UIFieldSpec(
        label="Test Size (%)",
        default=0.30,
        description="Parte dos dados reservada para testar o modelo durante treino. Exemplo: 0.30 significa 30% para validacao.",
        type=FieldValueType.FLOAT,
    ),
    "random_state": UIFieldSpec(
        label="Random State",
        default=42,
        description="Numero que fixa a aleatoriedade. Mantendo o mesmo valor, voce tende a reproduzir os mesmos resultados.",
        type=FieldValueType.INT,
    ),
    "ram_limit_pct": UIFieldSpec(
        label="Limite RAM (%)",
        default=70,
        description="Limita quanto da memoria RAM o processo pode usar. Ajuda a evitar travamentos por falta de memoria.",
        type=FieldValueType.INT,
    ),
    "use_mask": UIFieldSpec(
        label="Usar mascara (ultima banda = alpha)",
        default=True,
        description="Quando ativado, usa a ultima banda (alpha) para saber quais pixels sao validos e quais devem ser ignorados.",
        type=FieldValueType.BOOL,
    ),
    "zero_as_nodata": UIFieldSpec(
        label="Valores zerados como nodata",
        default=False,
        description="Se marcado, pixels como [0,0,0] sao tratados como nodata e nao entram na classificacao.",
        type=FieldValueType.BOOL,
    ),
    "nodata_threshold": UIFieldSpec(
        label="Limiar Nodata",
        default=250,
        description="Valor de corte para nodata sem alpha. Se todas as bandas estiverem acima desse numero, o pixel vira nodata.",
        type=FieldValueType.INT,
    ),
    "model_action": UIFieldSpec(
        label="Acao do Modelo",
        default="Treinar modelo novo",
        description="Escolhe o modo de trabalho: Treinar novo, Treinar existente ou Usar existente apenas para classificar sem treino.",
        type=FieldValueType.STR,
    ),
    "existing_model_path": UIFieldSpec(
        label="Modelo Existente",
        default="",
        description="Arquivo .keras ja treinado. Necessario para continuar treino em modelo existente ou classificar sem treinar novamente.",
        type=FieldValueType.PATH,
    ),
    "save_model": UIFieldSpec(
        label="Salvar modelo treinado em disco (.keras)",
        default=True,
        description="Se ativado, grava o modelo treinado em disco para uso futuro, sem precisar repetir todo o treinamento.",
        type=FieldValueType.BOOL,
    ),
    "model_path": UIFieldSpec(
        label="Caminho do Modelo",
        default="resultado/modelo_ui.keras",
        description="Caminho e nome base do arquivo do modelo treinado que sera salvo no formato .keras.",
        type=FieldValueType.PATH,
    ),
}
