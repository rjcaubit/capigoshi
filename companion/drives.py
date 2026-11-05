# Os 7 drives (secao 4), em inteiros x10 (fome 0..1000, humor -1000..1000). Atualizados a cada minuto.
from array import array
from companion import config as C


class Drives:
    def __init__(self):
        self.d = array('h', C.DRIVE_INI)
        self.dormindo = False
        self.interagiu = False            # houve interacao neste minuto (o tedio nao sobe)
        self.afeto_ja_60 = False
        self._min = 0
        self.clima = (0, 0, 0, 0)          # (alvo do humor, % de puxada, energia, curiosidade), de clima.efeito

    def _soma(self, i, x):
        self.d[i] = max(C.DRIVE_MIN[i], min(C.DRIVE_MAX[i], self.d[i] + x))
        if i == C.D_AFETO:
            if self.d[i] > 600:
                self.afeto_ja_60 = True
            if self.afeto_ja_60 and self.d[i] < C.AFETO_PISO:
                self.d[i] = C.AFETO_PISO

    def minuto(self):
        self._min += 1
        d = self.d
        self._soma(C.D_FOME, C.FOME_MIN)
        alvo, puxa, energia, curiosidade = self.clima
        self._soma(C.D_ENERGIA, C.ENERGIA_DORMINDO if self.dormindo else C.ENERGIA_ACORDADA + energia)
        h = d[C.D_HUMOR] - alvo                    # regride para o alvo do clima (0 sem previsao)
        p = C.HUMOR_REGRIDE + abs(h) * puxa // 100
        self._soma(C.D_HUMOR, -min(p, h) if h > 0 else min(p, -h))
        if d[C.D_FOME] > 800:
            self._soma(C.D_HUMOR, -10)
        if not self.interagiu and not self.dormindo:
            self._soma(C.D_TEDIO, C.TEDIO_MIN)
        self.interagiu = False
        if self._min % 10 == 0:
            self._soma(C.D_AFETO, C.AFETO_MIN)
        self._soma(C.D_CURIOSIDADE, C.CURIOSIDADE_MIN + curiosidade)
        self._soma(C.D_ESTRESSE, C.ESTRESSE_MIN)

    def avancar(self, minutos, dormindo):
        """Placa desligada (secao 4): aplica os minutos de uma vez."""
        self.dormindo = dormindo
        for _ in range(minutos):
            self.minuto()

    def recompensa(self, R):
        """Cada recompensa R soma R/2 ao humor (x10: R*5); positiva tambem fortalece o vinculo."""
        self._soma(C.D_HUMOR, R * 5)
        if R > 0:
            self.interagiu = True
            self._soma(C.D_AFETO, C.AFETO_POSITIVA)

    def get(self, i):
        return self.d[i] // 10

    def para_rede(self):
        """0..100 por drive (humor -100..100 vira 0..100) para o codificador."""
        d = self.d
        return [(d[i] + 1000) // 20 if i == C.D_HUMOR else d[i] // 10 for i in range(7)]
