# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 12:38:01 2023

@author: brend
"""

from ortools.sat.python import cp_model


def queens_problem(board_size):
    model = cp_model.CpModel()

    # Variables
    queens = [model.NewIntVar(lb=0, ub=board_size - 1, name="x%d" % i) for i in range(board_size)]

    # Constraints
    for i in range(board_size):
        for j in range(i + 1, board_size):
            model.Add(queens[i] != queens[j])  # same row
            model.Add(queens[i] + i != queens[j] + j)  # upper diagonal
            model.Add(queens[i] - i != queens[j] - j)  # lower diagonal

    # Solve
    solver = cp_model.CpSolver()
    solver.Solve(model)

    # Print solution
    result = [solver.Value(queens[i]) for i in range(board_size)]
    # model.ExportToFile(file="queens.lp")  # Trying get this to write an .lp file, but it's coming out as gibberish
    return result


print(queens_problem(8))
