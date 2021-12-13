from typing import Set
from .set_var import Set_var
from .memento import *
from .constraint import (
    EmptyIntersection,
    Intersection,
    strict_less_than_by_max,
    strict_less_than_by_min,
)
from .solver import solve, solve_iterative
from .model import Model, Sgp
from .propagator import Propagator


def test_set_var():
    var = Set_var([], [1], (0, 1))
    assert var.check_sets()
    assert var.check_bounds()
    assert not var.defined()

    assert not var.add_to_lb(2)
    assert var.check_bounds()
    assert not var.check_sets()

    var = Set_var([], [1], (0, 1))
    assert var.add_to_lb(1)
    assert var.defined()

    mementos = var.filter_on_card()
    assert len(mementos) == 1
    assert type(mementos[0]) == Card_memento
    mementos[0].apply()
    assert var.card_bounds[0] == 1

    var = Set_var([], [1], (0, 1))
    assert var.remove_from_ub(1)
    assert var.defined()

    mementos = var.filter_on_card()
    assert len(mementos) == 1
    assert type(mementos[0]) == Card_memento
    mementos[0].apply()
    assert var.card_bounds[0] == 0

    var = Set_var([], [1], (1, 0))
    assert not var.check_bounds()

    var = Set_var([1], [1, 2], (-3, 7))
    for m in var.filter_on_card():
        m.apply()
    assert var.card_bounds == (1, 2)

    var = Set_var([1], [1, 2], (-10, 1))
    for m in var.filter_on_card():
        m.apply()
    assert var.ub == {1}

    var = Set_var([], [1], (1, 10))
    for m in var.filter_on_card():
        m.apply()
    assert var.lb == {1}


def test_card_memento():
    var = Set_var([], [1, 2], (0, 2))
    m = Card_memento(var, (1, 4))
    m.apply()
    assert m.applied
    assert var.card_bounds == (1, 2)
    m.revert()
    assert not m.applied
    assert var.card_bounds == (0, 2)
    m2 = Card_memento(var, (-1, 1))
    m2.apply()
    assert var.card_bounds == (0, 1)


def test_UB_memento():
    var = Set_var([], [1, 2], (0, 2))
    m = UB_memento(var, [2])
    m.apply()
    assert m.applied
    assert 2 not in var.ub
    m.revert()
    assert not m.applied
    assert 2 in var.ub
    pass


def test_LB_memento():
    var = Set_var([], [1, 2], (0, 2))
    m = LB_memento(var, [2])
    m.apply()
    assert m.applied
    assert 2 in var.lb
    m.revert()
    assert not m.applied
    assert 2 not in var.lb
    pass


def test_empty_intersect():
    f = Set_var([1], [1, 2, 3], (0, 2))
    g = Set_var([2], [1, 2, 3], (0, 2))
    c = EmptyIntersection(f, g)
    l = c.get_vars()
    assert f in l
    assert g in l
    for modif in c.filter():
        modif.apply()
    assert 2 not in f.ub
    assert 1 not in g.ub


def test_intersect():
    # not a complete testing
    f = Set_var([1], [1, 2, 3], (0, 2))
    g = Set_var([2], [1, 2, 3], (0, 2))
    h = Set_var([3], [2, 3], (1, 2))
    c = Intersection(f, g, h)
    l = c.get_vars()
    assert f in l
    assert g in l
    assert h in l
    modifs = c.filter()
    for modif in modifs:
        modif.apply()
    assert 1 not in g.ub
    assert 3 in f.lb
    assert 3 in g.lb
    assert f.card_bounds == (1, 2)
    assert g.card_bounds == (1, 2)
    assert f.feasible()
    assert g.feasible()
    assert h.feasible()


def test_order_min():
    f1 = Set_var([], [0], (0, 2))
    f2 = Set_var([], [1], (0, 2))
    f3 = Set_var([1], [0, 1], (0, 2))
    f4 = Set_var([0], [0, 1], (0, 2))
    assert strict_less_than_by_max(f1, f2).satisfied()
    assert strict_less_than_by_max(f1, f3).satisfied()
    assert strict_less_than_by_max(f2, f1).failure()
    assert strict_less_than_by_max(f3, f2).failure()

    assert strict_less_than_by_min(f1, f2).satisfied()
    assert strict_less_than_by_min(f4, f2).satisfied()
    assert strict_less_than_by_min(f2, f1).failure()
    assert strict_less_than_by_min(f1, f4).failure()

    f = Set_var([], [0, 1, 2, 3], (0, 2))
    g = Set_var([], [0, 1, 2, 3], (0, 2))
    h = Set_var([], [0, 1, 2, 3], (0, 2))
    c = strict_less_than_by_min(f, g)
    c1 = strict_less_than_by_min(g, h)
    assert not c.failure()
    assert not c.satisfied()
    for modif in c.filter():
        modif.apply()
    for modif in c1.filter():
        modif.apply()
    assert g.ub == {1, 2, 3}
    assert h.ub == {2, 3}

    f.add_to_lb(1)
    f.remove_from_ub(0)
    g.add_to_lb(1)
    assert c.failure()
    assert c1.satisfied()


def test_order_max():
    f = Set_var([], [0, 1, 2, 3], (0, 2))
    g = Set_var([], [0, 1, 2, 3], (0, 2))
    h = Set_var([], [0, 1, 2, 3], (0, 2))
    c = strict_less_than_by_max(f, g)
    c1 = strict_less_than_by_max(g, h)
    assert not c.failure()
    assert not c.satisfied()
    for modif in c1.filter():
        modif.apply()
    for modif in c.filter():
        modif.apply()
    assert g.ub == {1, 2, 0}
    assert f.ub == {0, 1}

    h.add_to_lb(2)
    h.remove_from_ub(3)
    g.add_to_lb(2)
    assert c1.failure()
    assert c.satisfied()


def test_model():
    m = Model()
    f = Set_var([1], [1, 2, 3], (0, 2), priority=1)
    g = Set_var([2], [1, 2, 3], (0, 2))
    c = EmptyIntersection(f, g)
    m.add_constraint(c)
    assert m.constraints == {c}
    assert m.variables == set(c.get_vars())
    assert m.var_to_constraints[f] == [c]
    assert m.var_to_constraints[g] == [c]
    assert m.var_priority_dict[1] == [f]
    assert m.var_priority_dict[0] == [g]


def test_propagator():
    f = Set_var([1], [1, 2, 3], (0, 2))
    g = Set_var([2], [1, 2, 3], (0, 2))
    h = Set_var([3], [2, 3], (1, 2))
    c = Intersection(f, g, h)
    m = Model()
    m.add_constraint(c)
    p = Propagator(m)
    p.loops_backtrack = 1
    while not f.defined() or not g.defined() or not h.defined():
        assert p.propagate()
    assert f.lb == {1, 3}
    assert g.lb == {2, 3}
    assert h.lb == {3}


def test_enum_var_val():
    f = Set_var([1], [1, 2, 3], (0, 2))
    g = Set_var([2], [1, 2, 3], (0, 2))
    h = Set_var([3], [2, 3], (1, 2))
    c = Intersection(f, g, h)
    m = Model()
    m.add_constraint(c)


def test_solve():
    f = Set_var([1], [1, 2, 3], (0, 2))
    g = Set_var([2], [1, 2, 3], (0, 2))
    h = Set_var([3], [2, 3], (1, 2))
    c = Intersection(f, g, h)
    m = Model()
    m.add_constraint(c)
    solve(m)
    assert f.lb == {1, 3}
    assert g.lb == {2, 3}
    assert h.lb == {3}


def test_solve_iter():
    f = Set_var([1], [1, 2, 3], (0, 2))
    g = Set_var([2], [1, 2, 3], (0, 2))
    h = Set_var([3], [2, 3], (1, 2))
    c = Intersection(f, g, h)
    m = Model()
    m.add_constraint(c)
    solve_iterative(m)
    assert f.lb == {1, 3}
    assert g.lb == {2, 3}
    assert h.lb == {3}
    mdl = Sgp(5, 3, 2).all_week_model()
    feseable, t = solve_iterative(mdl)
    assert feseable


def test_constraints():
    test_empty_intersect()
    test_intersect()
    test_order_min()
    test_order_max()


def test_mementos():
    test_card_memento()
    test_UB_memento()
    test_LB_memento()


def test_all():
    test_set_var()
    test_mementos()
    test_constraints()
    test_model()
    test_propagator()
    test_enum_var_val()
    test_solve()
    test_solve_iter()
