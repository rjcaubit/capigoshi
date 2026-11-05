# Sensores falsos: monta o dicionario de sentidos que a placa montaria (sensors.py na fase 1).
class Mundo:
    def __init__(self, dia_semana=0, tempos=None):
        self.dia0 = dia_semana
        self.tempos = tempos            # issue #4: (tipo, graus) por dia, repetido em ciclo; None = sem previsao
        self.ultimo_toque = 0
        self.toques = []

    def tocar(self, seg):
        self.ultimo_toque = seg
        self.toques.append(seg)

    def sentidos(self, seg, comida=False):
        minuto = (seg // 60) % 1440
        dia = (self.dia0 + seg // 86400) % 7
        self.toques = [t for t in self.toques if seg - t < 60]
        recente = self.toques and self.toques[-1] == seg
        tipo, graus = self.tempos[(seg // 86400) % len(self.tempos)] if self.tempos else (None, None)
        return {
            'minuto': minuto, 'fim_semana': dia >= 5, 'toque_reg': 0 if recente else None,
            'toque_tipo': 0 if recente else None, 'toques_60s': len(self.toques),
            'sem_toque': seg - self.ultimo_toque, 'mov': None, 'orient': 0, 'som_nivel': 10,
            'som_evento': None, 'noite': minuto < 6 * 60 or minuto >= 18 * 60, 'bateria': 80, 'carregando': 0,
            'outra': 0, 'outra_estado': 0, 'novidade': 0, 'comida': comida,
            'tempo': tipo, 'graus': graus, 'wifi': 1 if tipo else 0,
        }
