"""
Yachts Atlas - Checklists Pré-Definidas por Categoria
10 Categorias de registros imutáveis para embarcações
"""

from typing import List, Dict, Any
from enum import Enum


class CategoriaChecklist(str, Enum):
    DOCUMENTACAO_LEGAL = "documentacao_legal"
    MOTOR_PROPULSAO = "motor_propulsao"
    MANUTENCAO_MECANICA = "manutencao_mecanica"
    ELETRICA_ELETRONICA = "eletrica_eletronica"
    SEGURANCA_SALVATAGEM = "seguranca_salvatagem"
    INTEGRIDADE_ESTRUTURAL = "integridade_estrutural"
    PINTURA_ACABAMENTO = "pintura_acabamento"
    RASTREABILIDADE_SERVICOS = "rastreabilidade_servicos"
    INTERIOR_ACOMODACOES = "interior_acomodacoes"
    NAVEGABILIDADE = "navegabilidade"


# Checklists pré-definidas por categoria
CHECKLISTS: Dict[str, List[Dict[str, Any]]] = {
    "documentacao_legal": [
        {"item": "Título de propriedade (TRAV)", "tipo": "checkbox", "obrigatorio": True},
        {"item": "Registro de embarcação (REB)", "tipo": "checkbox", "obrigatorio": True},
        {"item": "Licença de tráfego (LT)", "tipo": "checkbox", "obrigatorio": True},
        {"item": "Vistorias da Marinha (histórico)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Apólice de seguro vigente", "tipo": "checkbox", "obrigatorio": True},
        {"item": "Histórico de transferências", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Certidão de ônus/gravames", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Nota fiscal de compra original", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Manual do fabricante (casco + motor)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Certificado de homologação do estaleiro", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Habilitação do armador (arrais/mestre)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "DPEM — dotação de material", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Despacho de navegação", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Certidão negativa de débitos (Marinha)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Licença ambiental", "tipo": "checkbox", "obrigatorio": False},
    ],

    "motor_propulsao": [
        {"item": "Troca de óleo do motor", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Troca de filtro de óleo", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Troca de filtro de combustível", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Troca de filtro de ar", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Revisão do impelidor da bomba d'água", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Troca de correia/corrente dentada", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Limpeza/troca de injetores", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Condição do eixo e hélice", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Troca de zinco do eixo", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Revisão do gearbox/redução", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Laudo de compressão dos cilindros", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Nível de óleo do motor", "tipo": "medicao", "unidade": "litros", "obrigatorio": False},
        {"item": "Pressão do óleo", "tipo": "medicao", "unidade": "PSI", "obrigatorio": False},
        {"item": "Temperatura de operação", "tipo": "medicao", "unidade": "°C", "obrigatorio": False},
        {"item": "Rotação do motor (RPM)", "tipo": "medicao", "unidade": "RPM", "obrigatorio": False},
    ],

    "manutencao_mecanica": [
        {"item": "Sistema de arrefecimento", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Bombas d'água", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Vedações e retentores", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Coxins do motor", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Sistema de escapamento", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Tanque de combustível", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Linhas de combustível", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Separador de água/combustível", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Sistema de direção", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Mancais do eixo", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Gaxetas/quartoros", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Sistema de esgotamento", "tipo": "checkbox", "obrigatorio": False},
    ],

    "eletrica_eletronica": [
        {"item": "Radar (modelo, revisão, calibração)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "VHF fixo e portátil (homologação Anatel)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "GPS/plotter de cartas (atualização mapas)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "EPIRB/radiobaliza (validade bateria)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "AIS transponder (ativo/passivo)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Piloto automático (revisão e calibração)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Banco de baterias (capacidade + idade)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Painel solar/gerador/inversor", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Sistema de bilge automática", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Fiação (estado, última inspeção)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Instrumentação (velocidade, profundidade, vento)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Sistema de som/entretenimento", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Voltagem das baterias", "tipo": "medicao", "unidade": "V", "obrigatorio": False},
        {"item": "Amperagem de carga", "tipo": "medicao", "unidade": "A", "obrigatorio": False},
        {"item": "Frequência do inversor", "tipo": "medicao", "unidade": "Hz", "obrigatorio": False},
    ],

    "seguranca_salvatagem": [
        {"item": "Coletes salva-vidas (quantidade, validade)", "tipo": "checkbox", "obrigatorio": True},
        {"item": "Bóia de salvamento em arco", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Extintor de incêndio (validade + carga)", "tipo": "checkbox", "obrigatorio": True},
        {"item": "Sinalizadores pirotécnicos (validade)", "tipo": "checkbox", "obrigatorio": True},
        {"item": "Bomba manual de esgotamento", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Âncora + cadeia (comprimento, condição)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Cordame e cabos de atracação", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Kit de primeiros socorros (validade)", "tipo": "checkbox", "obrigatorio": True},
        {"item": "Detector de CO (monóxido de carbono)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Sinalização noturna (lanternas, faróis)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Plano de emergência da embarcação", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Buzina/sino de nevoeiro", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Facas de bordo", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Luzes de navegação", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Espia de arremesso", "tipo": "checkbox", "obrigatorio": False},
    ],

    "integridade_estrutural": [
        {"item": "Inspeção de soldas do casco", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Laudo de ultrassom (espessura do casco)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Osmose/bolhas na fibra", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Condição do quilha/lastro", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Passagens de casco (seacocks)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Vedação de portas e escotilhas", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Condição do convés (antiderrapante)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Corrimões e guarda-corpos", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Mastro e aparelho de mastreação", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Drinques, estais e barras de flecha", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Tanque de combustível (inspeção interna)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Tanques de água doce (limpeza)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Vedações de janelas", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Estado dos coxins", "tipo": "checkbox", "obrigatorio": False},
    ],

    "pintura_acabamento": [
        {"item": "Aplicação de tinta antiincrustante", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Tipo e marca da tinta utilizada", "tipo": "texto", "obrigatorio": False},
        {"item": "Número de demãos aplicadas", "tipo": "numero", "obrigatorio": False},
        {"item": "Pintura do casco acima da linha d'água", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Polimento/enceramento da gelcoat", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Tratamento de teca (deck)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Reparos de gelcoat (trincas, impactos)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Quem executou (empresa + responsável)", "tipo": "texto", "obrigatorio": False},
        {"item": "Área pintada (m²)", "tipo": "medicao", "unidade": "m²", "obrigatorio": False},
        {"item": "Espessura da tinta", "tipo": "medicao", "unidade": "mícrons", "obrigatorio": False},
    ],

    "rastreabilidade_servicos": [
        {"item": "Nome do técnico/empresa responsável", "tipo": "texto", "obrigatorio": True},
        {"item": "Data de entrada e saída do estaleiro", "tipo": "data", "obrigatorio": True},
        {"item": "Nota fiscal de cada serviço", "tipo": "anexo", "obrigatorio": True},
        {"item": "Fotos da peça antiga (antes da troca)", "tipo": "foto", "obrigatorio": False},
        {"item": "Fotos da peça nova instalada", "tipo": "foto", "obrigatorio": False},
        {"item": "Horímetro/milhas no momento do serviço", "tipo": "numero", "obrigatorio": True},
        {"item": "Observações e recomendações do técnico", "tipo": "texto_longo", "obrigatorio": False},
        {"item": "Próxima manutenção recomendada", "tipo": "data", "obrigatorio": False},
        {"item": "Garantia do serviço", "tipo": "texto", "obrigatorio": False},
        {"item": "Contato do técnico/empresa", "tipo": "texto", "obrigatorio": False},
    ],

    "interior_acomodacoes": [
        {"item": "Estofados e forração (estado geral)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Sistema de refrigeração/ar condicionado", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Fogão, forno e botijão de gás", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Sistema de esgoto/macerador", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Bomba de água doce (pressurização)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Aquecedor de água (boiler)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Móveis e marcenaria interna", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Cabines (número, condição, fotos)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Banheiros/camarotes (estado e cheiros)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Iluminação interna (LED, funcionamento)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Pias e torneiras", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Janelas e vigias", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Sistema de som/TV", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Cortinas e persianas", "tipo": "checkbox", "obrigatorio": False},
    ],

    "navegabilidade": [
        {"item": "Vistorias da Marinha (histórico)", "tipo": "checkbox", "obrigatorio": True},
        {"item": "DPEM — dotação de material de salvatagem", "tipo": "checkbox", "obrigatorio": True},
        {"item": "Despacho de navegação", "tipo": "checkbox", "obrigatorio": True},
        {"item": "Certidão negativa de débitos (Marinha)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Licença ambiental", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Habilitação do armador (arrais/mestre)", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Seguro DPVAM", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Taxa de permanência", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Documentação de importação", "tipo": "checkbox", "obrigatorio": False},
        {"item": "Certificado de arqueação", "tipo": "checkbox", "obrigatorio": False},
    ],
}


def get_checklist_by_categoria(categoria: str) -> List[Dict[str, Any]]:
    """Retorna checklist pré-definida para uma categoria específica"""
    return CHECKLISTS.get(categoria, [])


def get_all_categorias() -> List[str]:
    """Retorna todas as categorias disponíveis"""
    return list(CHECKLISTS.keys())


def get_categorias_with_labels() -> List[Dict[str, str]]:
    """Retorna categorias com labels amigáveis"""
    labels = {
        "documentacao_legal": "Documentação Legal",
        "motor_propulsao": "Motor e Propulsão",
        "manutencao_mecanica": "Manutenção Mecânica",
        "eletrica_eletronica": "Elétrica e Eletrônica",
        "seguranca_salvatagem": "Segurança e Salvatagem",
        "integridade_estrutural": "Integridade Estrutural",
        "pintura_acabamento": "Pintura e Acabamento",
        "rastreabilidade_servicos": "Rastreabilidade de Serviços",
        "interior_acomodacoes": "Interior e Acomodações",
        "navegabilidade": "Navegabilidade",
    }

    return [
        {"id": cat_id, "label": labels.get(cat_id, cat_id)}
        for cat_id in get_all_categorias()
    ]
