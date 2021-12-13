from .set_var import Set_var
from .memento import Card_memento, LB_memento, Memento, UB_memento


class Constraint:
    def __init__(self) -> None:
        raise NotImplementedError()

    def get_vars(self) -> list[Set_var]:
        raise NotImplementedError()

    def filter(self) -> list[Memento]:
        raise NotImplementedError()

    def satisfied(self) -> bool:
        raise NotImplementedError()

    def failure(self) -> bool:
        raise NotImplementedError()


class EmptyIntersection(Constraint):
    def __init__(self, F: Set_var, G: Set_var) -> None:
        self.F = F
        self.G = G

    def get_vars(self) -> list[Set_var]:
        return [self.F, self.G]

    def filter(self) -> list[Memento]:
        """
        return a set of elements to add from lb,
        to remove from ub,
        and the new couple of cardinality
        """
        filtering_list = []
        # filtering F
        filtering_list.append(UB_memento(self.F, self.F.ub & self.G.lb))
        # filtering G
        filtering_list.append(UB_memento(self.G, self.G.ub & self.F.lb))
        return filtering_list

    def satisfied(self) -> bool:
        return self.F.ub.isdisjoint(self.G.ub)

    def failure(self) -> bool:
        return not self.F.lb.isdisjoint(self.G.lb)


class Intersection(Constraint):
    def __init__(self, F: Set_var, G: Set_var, H: Set_var) -> None:
        self.F = F
        self.G = G
        self.H = H

    def get_vars(self) -> list[Set_var]:
        return [self.F, self.G, self.H]

    def filter(self) -> list[Memento]:
        filtering_list = []
        # filtering F
        filtering_list.append(LB_memento(self.F, self.H.lb - self.F.lb))
        filtering_list.append(UB_memento(self.F, self.F.ub & self.G.lb - self.H.ub))
        filtering_list.append(
            Card_memento(self.F, (self.H.card_bounds[0], self.F.card_bounds[1]))
        )
        # filtering G
        filtering_list.append(LB_memento(self.G, self.H.lb - self.G.lb))
        filtering_list.append(UB_memento(self.G, self.G.ub & self.F.lb - self.H.ub))
        filtering_list.append(
            Card_memento(self.G, (self.H.card_bounds[0], self.G.card_bounds[1]))
        )
        # filtering H
        filtering_list.append(LB_memento(self.H, self.F.lb & self.G.lb))
        filtering_list.append(UB_memento(self.H, self.H.ub & (self.G.ub ^ self.F.ub)))
        filtering_list.append(
            Card_memento(
                self.H,
                (
                    len(self.F.lb & self.G.lb),
                    min(
                        [
                            len(self.F.ub & self.G.ub),
                            self.F.card_bounds[1],
                            self.G.card_bounds[1],
                        ]
                    ),
                ),
            )
        )
        return filtering_list

    def satisfied(self) -> bool:
        return self.H.defined() and self.F.ub & self.G.ub == self.H.lb

    def failure(self) -> bool:
        return not self.H.ub.issuperset(self.F.lb & self.G.lb)


class strict_less_than_by_min(Constraint):
    """
    represents a constraint F < G <=> min(F) < min(G)
    """

    def __init__(self, F, G) -> None:
        self.F = F
        self.G = G

    def get_vars(self) -> list[Set_var]:
        return [self.F, self.G]

    def filter(self) -> list[Memento]:
        to_remove_from_ub = set()
        min_f = min(self.F.ub)
        for elmt_ub in self.G.ub:
            if elmt_ub <= min_f:
                to_remove_from_ub.add(elmt_ub)
        return [UB_memento(self.G, to_remove_from_ub)]

    def satisfied(self) -> bool:
        if len(self.F.lb) > 0 and len(self.G.ub) > 0:
            return min(self.F.lb) < min(self.G.ub) or max(self.F.ub) < min(self.G.ub)
        elif len(self.F.ub) > 0 and len(self.G.ub) > 0:
            return max(self.F.ub) < min(self.G.ub)
        else:
            return False

    def failure(self) -> bool:
        if len(self.F.ub) > 0 and len(self.G.lb) > 0:
            return min(self.F.ub) >= min(self.G.lb) or max(self.G.ub) <= min(self.F.ub)
        elif len(self.F.ub) > 0 and len(self.G.ub) > 0:
            return max(self.G.ub) <= min(self.F.ub)
        else:
            return False


class strict_less_than_by_max(Constraint):
    """
    represents a constraint F < G <=> max(F) < max(G)
    """

    def __init__(self, F, G) -> None:
        self.F = F
        self.G = G

    def get_vars(self) -> list[Set_var]:
        return [self.F, self.G]

    def filter(self) -> list[Memento]:
        to_remove_from_ub = set()
        max_g = max(self.G.ub)
        for elmt_ub in self.F.ub:
            if elmt_ub >= max_g:
                to_remove_from_ub.add(elmt_ub)
        return [UB_memento(self.F, to_remove_from_ub)]

    def satisfied(self) -> bool:
        if len(self.F.ub) > 0 and len(self.G.lb) > 0:
            return max(self.F.ub) < max(self.G.lb) or max(self.F.ub) < min(self.G.ub)
        elif len(self.F.ub) > 0 and len(self.G.ub) > 0:
            return max(self.F.ub) < min(self.G.ub)
        else:
            return False

    def failure(self) -> bool:
        if len(self.F.lb) > 0 and len(self.G.ub) > 0:
            return max(self.F.lb) >= max(self.G.ub) or min(self.F.ub) >= max(self.G.ub)
        elif len(self.F.ub) > 0 and len(self.G.ub) > 0:
            return min(self.F.ub) >= max(self.G.ub)
        else:
            return False
