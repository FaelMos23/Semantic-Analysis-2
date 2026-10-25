"""Alcance no CFG. O percurso da AST já foi realizado pelo builder."""

from __future__ import annotations

from cfg import BlockId, CFG


def compute_reachable(cfg: CFG) -> set[BlockId]:
    """Devolva os IDs alcançáveis a partir da entrada, incluindo a entrada."""

    reachable: set[BlockId] = set()
    pending = [cfg.entry]
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        # se current não estiver em reachable ainda, adicionamos agora
        reachable.add(current)

        # os sucessores devem ser adicionados
        for next_blks in cfg.blocks[current].successors:
            pending.append(next_blks)
    
    return reachable