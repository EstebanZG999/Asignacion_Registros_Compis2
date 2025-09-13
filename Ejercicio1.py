# Asignador de registros con "próximo uso" y reescritura TAC a ISA (3 registros)
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

Instr = Tuple[str, Tuple[str, ...]]  # ("bin", ("x","y","+","z")) ó ("mov", ("x","y"))

# Análisis "próximo uso" (aprox. a 1 bloque)
def compute_next_use(tac: List[Instr]) -> List[Dict[str, float]]:
    """
    Para cada instrucción i devuelve un dict var->distancia al próximo uso (∞ si no se usa de nuevo).
    Aproximación local suficiente para la Actividad 1/Ejercicio 1.
    """
    INF = float("inf")
    next_use: List[Dict[str, float]] = [defaultdict(lambda: INF) for _ in tac]
    future: Dict[str, float] = defaultdict(lambda: INF)

    for i in range(len(tac) - 1, -1, -1):
        # propaga futuro +1
        cur = defaultdict(lambda: INF, {v: d + 1 for v, d in future.items()})
        op, args = tac[i]
        if op == "mov":
            x, y = args
            cur[y] = 1
            cur[x] = INF  # redefinida
        elif op == "bin":
            x, y, oper, z = args
            cur[y] = 1
            cur[z] = 1
            cur[x] = INF  # redefinida
        next_use[i] = cur
        future = cur
    return next_use

# Asignador de 3 registros con víctima por "próximo uso" + LRU
class RegAlloc3:
    def __init__(self):
        self.regs = ["R1", "R2", "R3"]
        self.free = set(self.regs)
        self.var2reg: Dict[str, str] = {}
        self.reg2var: Dict[str, str] = {}
        self.last_use_clock = 0
        self.lru: Dict[str, int] = {}
        self.memory: Dict[str, str] = {}

    def _touch(self, var: str):
        self.last_use_clock += 1
        self.lru[var] = self.last_use_clock

    def ensure_in_reg(self, var: str, fut: Dict[str, float], code: List[str]) -> str:
        if var in self.var2reg:
            self._touch(var)
            return self.var2reg[var]
        if self.free:
            r = self.free.pop()
            self.bind(var, r)
            code.append(f"LD  {r}, {var}")
            self._touch(var)
            return r
        # Si no hay libres derrama víctima con próximo uso más lejano
        r, victim = self.pick_victim(fut)
        code.append(f"ST  {victim}, {r}")
        self.unbind_var(victim)
        self.bind(var, r)
        code.append(f"LD  {r}, {var}")
        self._touch(var)
        return r

    def write_over_if_dead(self, var: str, fut: Dict[str, float]) -> Optional[str]:
        """Si var está en un registro y no tiene próximo uso, devolver ese registro como destino."""
        if var in self.var2reg and fut.get(var, float("inf")) == float("inf"):
            return self.var2reg[var]
        return None

    def pick_victim(self, fut: Dict[str, float]) -> Tuple[str, str]:
        """Elige el registro cuya variable tiene próximo uso más lejano; tie-breaker por LRU más viejo."""
        # Distancia grande primero, edad vieja primero
        cands = []
        for r in self.regs:
            v = self.reg2var[r]
            dist = fut.get(v, float("inf"))
            age = self.lru.get(v, -1)
            cands.append((dist, -age, r, v))
        cands.sort(reverse=True)  # mayor dist y menor age
        _, _, r, v = cands[0]
        return r, v

    def bind(self, var: str, reg: str):
        self.var2reg[var] = reg
        self.reg2var[reg] = var

    def unbind_var(self, var: str):
        if var in self.var2reg:
            reg = self.var2reg.pop(var)
            self.reg2var.pop(reg, None)
            self.free.add(reg)

# Reescritura TAC→ISA con 3 registros
def rewrite_tac(tac: List[Instr]) -> List[str]:
    code: List[str] = []
    fut_table = compute_next_use(tac)
    ra = RegAlloc3()

    for i, (op, args) in enumerate(tac):
        fut = fut_table[i]
        if op == "mov":
            x, y = args
            # Optimización: x comparte el registro de y
            Ry = ra.ensure_in_reg(y, fut, code)
            code.append(f"ST  {x}, {Ry}")  # materializamos x en memoria
        elif op == "bin":
            x, y, oper, z = args
            # Intento de escribir sobre un operando que muere
            Rdest = ra.write_over_if_dead(y, fut) or ra.write_over_if_dead(z, fut)
            Ry = ra.ensure_in_reg(y, fut, code)
            Rz = ra.ensure_in_reg(z, fut, code)

            if Rdest is None:
                if ra.free:
                    Rdest = ra.free.pop()
                else:
                    Rdest, victim = ra.pick_victim(fut)
                    code.append(f"ST  {victim}, {Rdest}")
                    ra.unbind_var(victim)

            code.append(f"{oper.upper():3} {Rdest}, {Ry}, {Rz}")
            # Actualizar mapeos: x vive en Rdest
            if Rdest in ra.reg2var:
                old = ra.reg2var[Rdest]
                if old in ra.var2reg:
                    ra.var2reg.pop(old, None)
            ra.reg2var[Rdest] = x
            ra.var2reg[x] = Rdest
            ra._touch(x)
        else:
            raise NotImplementedError(op)
    return code

# Ejemplo mínimo
if __name__ == "__main__":
    tac: List[Instr] = [
        ("bin", ("t", "a", "-", "b")),
        ("bin", ("u", "a", "-", "c")),
        ("bin", ("v", "t", "+", "u")),
        ("mov", ("a", "d")),
        ("bin", ("d", "v", "+", "u")),
    ]
    for line in rewrite_tac(tac):
        print(line)
