from time import time
import sys
from set_sat_interface import *
import pysat.solvers
import pysat.formula


class Set_Sat(Set_Sat_interface):
    def __init__(self):
        self.solver = pysat.solvers.Glucose4()
        self.cnf = pysat.formula.CNF()
        self.idx_next_var = 1
        self.set_sat_idx = []
        self.lbounds = []
        self.ubounds = []

    def next_var(self):
        next_idx = self.idx_next_var
        self.idx_next_var += 1
        return next_idx

    def add_clause(self, clause):
        self.cnf.append(clause)

    def solve(self):
        self.solver.append_formula(self.cnf)
        if self.solver.solve():
            return self.solver.get_model()
        else:
            return []

    def model_to_set_solution(self, model):
        if len(model) == 0:
            return []  #  UNSAT
        # remove negative values
        sat_var_true = [i for i in model if i > 0]
        #  reindex the model because solvers idexes begin at 0
        idx_list = [0] + model
        solution_set = [list() for i in range(len(self.set_sat_idx))]
        for i in range(len(self.set_sat_idx)):
            for key in self.set_sat_idx[i]:
                idx = self.set_sat_idx[i][key]
                if idx < len(idx_list) and idx_list[idx] > 0:
                    # last var might not be in the model and unconstrained
                    solution_set[i].append(key)
        return solution_set

    def add_set_var(self, lb, ub):

        set_list_idx = {}
        set_idx = len(self.set_sat_idx)
        for elmt in ub:
            set_list_idx[elmt] = self.next_var()
            if elmt in lb:
                self.add_clause([set_list_idx[elmt]])

        self.lbounds.append(set(lb))
        self.ubounds.append(set(ub))
        self.set_sat_idx.append(set_list_idx)

        if not self.lbounds[set_idx].issubset(self.ubounds[set_idx]):
            # ub and lb are not compatible, we add -x /\ x in the formula
            self.unsat_var()
        return set_idx

    def intersection(self, i, j, k, left_right=True, right_left=True):
        '''
            a constraint about intersection\n
            left_right => i intersection j ⊆ k \n
            right_left => k ⊆ i intersection j \n
            i,j,k are the indexes of the corresponding sets
        '''
        for common_elmt in self.ubounds[i] & self.ubounds[j]:
            if left_right:
                self.add_clause([-self.set_sat_idx[i][common_elmt],
                                -self.set_sat_idx[j][common_elmt],
                                self.set_sat_idx[k][common_elmt]])
            if right_left:
                self.add_clause([self.set_sat_idx[i][common_elmt],
                                -self.set_sat_idx[k][common_elmt]])
                self.add_clause([self.set_sat_idx[j][common_elmt],
                                -self.set_sat_idx[k][common_elmt]])

    def union(self, i, j, k, left_right=True, right_left=True):
        '''
            a constraint about union\n
            left_right => i union j ⊆ k \n
            right_left => k ⊆ i union j \n
            i,j,k are the indexes of the corresponding sets
        '''
        for common_elmt in self.ubounds[i] | self.ubounds[j]:
            if left_right:
                self.add_clause([-self.set_sat_idx[i][common_elmt],
                                self.set_sat_idx[k][common_elmt]])
                self.add_clause([-self.set_sat_idx[j][common_elmt],
                                self.set_sat_idx[k][common_elmt]])
            if right_left:
                self.add_clause([-self.set_sat_idx[k][common_elmt],
                                self.set_sat_idx[i][common_elmt],
                                self.set_sat_idx[j][common_elmt]])

    def intersection_empty(self, i, j):
        '''
            constraint for i intersection j = ø
            i,j are the indexes of the corresponding sets
        '''
        if self.lbounds[i] & self.lbounds[j]:
            self.unsat_var()
        for common_elmt in self.ubounds[i] & self.ubounds[j]:
            self.add_clause([-self.set_sat_idx[i][common_elmt],
                             -self.set_sat_idx[j][common_elmt]])

    def cardinal_lb(self, i, lb):
        '''
            constraint for card(i) >= lb
            i is the index of the corresponding set
        '''
        # at_most_k(n-k,-x_n) is equivalent to at_least_k(k,x_n)
        # see at_most_k paper
        negated_lst = list(map(lambda x: -x, self.set_sat_idx[i].values()))
        for c in self.at_most_k(len(self.set_sat_idx[i]) - lb, negated_lst):
            self.add_clause(c)

    def cardinal_ub(self, i, ub):
        '''
            constraint for card(i) <= ub
            i is the index of the corresponding set
        '''
        for c in self.at_most_k(ub, list(self.set_sat_idx[i].values())):
            self.add_clause(c)

    def cardinal(self, i, c):
        '''
            constraint for card(i) = c
            i is the index of the corresponding set
        '''
        self.cardinal_lb(i, c)
        self.cardinal_ub(i, c)

    def update_lb(self, i, lb):
        '''
            adds new restrictions to the existing lower bound
        '''
        # update the lower bound constraint to contain lb
        lb_set = set(lb)
        if not lb_set.issubset(self.lbounds[i]):
            # If the lower bound is included in the actual one, then we do nothing
            new_lb = lb_set | self.lbounds[i]
            if not new_lb.issubset(self.ubounds[i]):
                # ub and lb are not compatible, we add -x /\ x in the formula
                self.unsat_var()
            for new_elmt in lb_set:
                self.add_clause([self.set_sat_idx[i][new_elmt]])

    def update_ub(self, i, ub):
        '''
            adds new restrictions to the existing upper bound
        '''
        # update the upper bound constraint to contain respect ub
        ub_set = set(ub)
        if not ub_set.issuperset(self.ubounds[i]):
            # If the upper bound is included in the new one, then we do nothing
            new_ub = ub_set & self.ubounds[i]
            if not self.lbounds[i].issubset(new_ub):
                # ub and lb are not compatible, we add -x /\ x in the formula
                self.unsat_var()

            for removed_elmt in self.ubounds[i] - ub_set:
                self.add_clause([-self.set_sat_idx[i][removed_elmt]])

    def belongs(self, elmt, i):
        '''
        constraint x in i
        '''
        if elmt in self.ubounds[i]:
            self.add_clause([self.set_sat_idx[i][elmt]])
        else:
            self.unsat_var()

    def order_by_min(self, set_array):
        '''
            order the array of sets given as parameters
            such that forall set i,j i!=j, min(i) <= min(j)
        '''
        latch_group_list = [self.latch(self.set_sat_idx[i]) for i in set_array]
        key_list = [list(self.set_sat_idx[i].keys()) for i in set_array]
        self.order_by_latch(latch_group_list, key_list)

    def order_by_max(self, set_array):
        '''
            order the array of sets given as parameters
            such that forall set i,j i!=j, max(i) <= max(j)
        '''
        latch_group_list = [self.latch(reverse_map(
            self.set_sat_idx[i])) for i in set_array]
        key_list = [list(self.set_sat_idx[i].keys()) for i in set_array]
        self.order_by_latch(latch_group_list, key_list)
