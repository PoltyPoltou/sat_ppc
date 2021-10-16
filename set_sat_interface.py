
class Set_Sat_interface:
    def __init__(self):
        raise NotImplementedError()

    def next_var(self):
        raise NotImplementedError()

    def add_clause(self, clause):
        raise NotImplementedError()

    def solve(self):
        raise NotImplementedError()

    def model_to_set_solution(self, model):
        raise NotImplementedError()

    def add_set_var(self, lb, ub):
        raise NotImplementedError()

    def intersection(self, i, j, k, left_right=True, right_left=True):
        raise NotImplementedError()

    def union(self, i, j, k, left_right=True, right_left=True):
        raise NotImplementedError()

    def intersection_empty(self, i, j):
        raise NotImplementedError()

    def cardinal_lb(self, i, lb):
        raise NotImplementedError()

    def cardinal_ub(self, i, ub):
        raise NotImplementedError()

    def cardinal(self, i, c):
        raise NotImplementedError()

    def update_lb(self, i, lb):
        raise NotImplementedError()

    def update_ub(self, i, ub):
        raise NotImplementedError()

    def belongs(self, elmt, i):
        raise NotImplementedError()

    def unsat_var(self):
        x = self.next_var()
        self.add_clause([x])
        self.add_clause([-x])

    def at_most_k(self, k, var_idx):
        # http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.83.9527&rep=rep1&type=pdf
        n = len(var_idx)
        if n == k:
            return []
        elif k == 0:
            clauses = [None] * n
            for i in range(n):
                clauses[i] = [-var_idx[i]]
            return clauses
        else:
            s = []
            for i in range(n-1):
                s.append([])
                for j in range(k):
                    s[i].append(self.next_var())

            clauses = [[-var_idx[0], s[0][0]]]

            for j in range(1, k):
                clauses.append([-s[0][j]])

            for i in range(1, n-1):
                clauses.append([-var_idx[i], s[i][0]])
                clauses.append([-s[i-1][0], s[i][0]])
                for j in range(1, k):
                    clauses.append([-var_idx[i], -s[i-1][j-1], s[i][j]])
                    clauses.append([-s[i-1][j], s[i][j]])
                clauses.append([-var_idx[i], -s[i-1][k-1]])

            clauses.append([-var_idx[-1], -s[-1][k-1]])
            return clauses

    def latch(self, array_idx: dict):
        '''
         defines a latch q_n function of variables x_n,
         the indexes are given via array_idx\n
         example : \n
         x_n = 0 0 0 1 0 1 0 \n
         q_n = 0 0 0 1 1 1 1 \n
        '''
        n = len(array_idx)
        if n != 0:
            latch_map = {}
            key_list_ordered = list(array_idx.keys())
            for key in array_idx:
                latch_map[key] = self.next_var()

            for i in range(1, n):
                self.add_clause(
                    [-array_idx[key_list_ordered[i]], latch_map[key_list_ordered[0]]])

                self.add_clause([-latch_map[key_list_ordered[i]],
                                 latch_map[key_list_ordered[i-1]]])
                self.add_clause([-latch_map[key_list_ordered[i]],
                                 -array_idx[key_list_ordered[i-1]]])
                self.add_clause([latch_map[key_list_ordered[i]],
                                array_idx[key_list_ordered[i-1]],
                                -latch_map[key_list_ordered[i-1]]])
            return latch_map

    def order_by_latch(self, latch_group_list, key_list):
        for idx in range(1, len(latch_group_list)):
            i = 0
            j = 0
            while i < len(key_list[idx-1]) and j < len(key_list[idx]):
                if key_list[idx-1][i] == key_list[idx][j]:
                    self.add_clause([-latch_group_list[idx-1][i],
                                    latch_group_list[idx][j]])
                    i += 1
                    j += 1
                elif key_list[idx-1][i] > key_list[idx][j]:
                    self.add_clause([-latch_group_list[idx-1],
                                    latch_group_list[idx]])
                    j += 1
                else:  # key_list[idx][j] > key_list[idx-1][i]:
                    i += 1
                    pass


def reverse_map(m: dict):
    new_dict = {}
    key_list = list(reversed(list(m.keys())))
    max_key = max(m.keys())
    for key in key_list:
        new_dict[max_key-key] = m[key]
    return new_dict
