# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 13:42:00 2023
framework from
https://github.com/google/or-tools/blob/stable/examples/python/flexible_job_shop_sat.py

Solves a flexible jobshop problems with the CP-SAT solver.

A jobshop is a standard scheduling problem when you must sequence a
series of phases on a set of platforms. Each target contains one phase per
platform. The order of execution and the length of each target on each
platform is phase, platform and target dependent.

The objective is to minimize the maximum completion time of all
targets. This is called the makespan.
"""

from ortools.sat.python import cp_model
# import pandas as pd
import KC_data_melt
import time
import collections

start_time = time.time()

###### Define solution printer class for printing results
class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__solution_count = 0

    def on_solution_callback(self):
        """Called at each new solution."""
        print('Solution %i, time: %f s, BestBd: %i, Makespan: %i' %
              (self.__solution_count, round(self.WallTime(),2), 
               self.BestObjectiveBound(), self.ObjectiveValue()))
        self.__solution_count += 1

###### Import Data

# define model parameters
parameters = KC_data_melt.define_parameters(max_horizon_min=7200, 
                                       same_plat_for_Track_phases=0,
                                       max_eng_wins_btw_find_engage=1)

f = "small_inputs_gmuV5.xlsx"  # enter the filename (path) for the data

df = KC_data_melt.create_big_dataframe(f)
df_wt = KC_data_melt.import_weapon_data(f)

print("Data loaded. This operation took", round(time.time() - start_time, 2), "seconds.\n")

# define indices

idx_i = ('Find', 'PED', 'Fix', 'PED2', 'Track1', 'Track2', 'Track3', 'Track Build',
          'Track Gen', 'Target', 'Engage', 'IFTU', 'Assess', 'Assess Decision')

idx_t = tuple(set(df['Target ID']))
idx_p = tuple(set(df['Plat ID']))

idx_i_num = tuple(range(1,len(idx_i)+1))
idx_t_num = tuple(range(1,len(idx_t)+1))
idx_p_num = tuple(range(1,len(idx_p)+1))

idx_tt = tuple(set(df['Target Type']))
idx_pt = tuple(set(df['Plat Type']))
idx_wt = tuple(set(df_wt['Weapon Type']))

# idx_j = ("perm", "jam")
# idx_k = tuple(range(0,parameters["max_horizon_min"]))
# idx_seq = tuple(range(len(idx_t)))  # new index: indicates the sequence # of a target

# draw each tuple from the df in the sorted order and append to a list then coerce to tuple
idx_tip = tuple([df["(t,i,p)"][row] for row in range(len(df))])
idx_tip_num = tuple([df["(t,i,p)_num"][row] for row in range(len(df))])

def flexible_targetshop():
    """Solve a small flexible targetshop problem."""
    # Data part.    
    
    # targets = [  # phase = (processing_time, platform_id)
    #     [  # target 0
    #         [(3, 0), (1, 1), (5, 2)],  # phase 0 with 3 alternatives
    #         [(2, 0), (4, 1), (6, 2)],  # phase 1 with 3 alternatives
    #         [(2, 0), (3, 1), (1, 2)],  # phase 2 with 3 alternatives
    #     ],
    #     [  # target 1
    #         [(2, 0), (3, 1), (4, 2)],
    #         [(1, 0), (5, 1), (4, 2)],
    #         [(2, 0), (1, 1), (4, 2)],
    #     ],
    #     [  # target 2
    #         [(2, 0), (1, 1), (4, 2)],
    #         [(2, 0), (3, 1), (4, 2)],
    #         [(3, 0), (1, 1), (5, 2)],
    #     ],
    # ]

    num_targets = len(idx_t)
    all_targets = range(1,num_targets+1)

    num_platforms = len(idx_p)
    all_platforms = range(1,num_platforms+1)

    # Model the flexible targetshop problem.
    model = cp_model.CpModel()

    horizon = 0
    for t in idx_t_num:
        for p in idx_p_num:
            max_phase_duration = 0
            for i in idx_i_num:
                duration = df[df["(t,i,p)_num"] == (t,i,p)]["PLATPROCTIME"].item()
                max_phase_duration = max(max_phase_duration, duration)
            horizon += max_phase_duration

    print(f'Horizon = {horizon}')

    # Global storage of variables.
    intervals_per_resources = collections.defaultdict(list)
    starts = {}  # indexed by (target_id, phase_id).
    presences = {}  # indexed by (target_id, phase_id, plat_id).
    target_ends = []

    # Scan the targets and create the relevant variables and intervals.
    for target_id in all_targets:
        target = df[df["Target_num"] == target_id]
        num_phases = len(idx_i)
        previous_end = None
        for phase_id in range(1,num_phases+1):
            phase = target[(target["Phase_num"] == phase_id) & (target["PLATPROCTIME"] >= 0)]

            # min_duration = phase[phase["PLATPROCTIME"] == min(phase["PLATPROCTIME"]) 
            #                      & (phase["PLATPROCTIME"] >=0)].tolist()[0]
            # max_duration = phase[phase["PLATPROCTIME"] == max(phase["PLATPROCTIME"])].tolist()[0]
            
            num_alternatives = len(set(phase[phase["PLATPROCTIME"] >=0]["Plat_num"]))
            all_alternatives = tuple(set(phase[phase["PLATPROCTIME"] >=0]["Plat_num"]))
            
            # I'm pretty sure we don't have to execute the code below because I selected max and min from df above
            # for alt_id in range(1, num_alternatives):
            #     alt_duration = phase[alt_id][0]
            #     min_duration = min(min_duration, alt_duration)
            #     max_duration = max(max_duration, alt_duration)

            # Create main interval for the phase.
            domain = cp_model.Domain.FromValues(phase["PLATPROCTIME"].tolist())
            suffix_name = '_tgt%i_phase%i' % (target_id, phase_id)
            start = model.NewIntVar(0, horizon, 'start' + suffix_name) 
            duration = model.NewIntVarFromDomain(
                domain=domain, name='duration' + suffix_name)  # I'm skeptical that this will work. Because of the traceability and other rules that will folow from chosing a particular platform
            end = model.NewIntVar(0, horizon, 'end' + suffix_name)
            interval = model.NewIntervalVar(start, duration, end,
                                            'interval' + suffix_name)   # Consider using optional intervals with an x variable

            # Store the start for the solution.
            starts[(target_id, phase_id)] = start  # I need to visualize this one. Will this work?

            # Add precedence with previous phase in the same target.
            if previous_end is not None:
                model.Add(start >= previous_end)
            previous_end = end

            # Create alternative intervals.
            if num_alternatives > 1:
                l_presences = []
                for alt_id in all_alternatives:
                    alt_suffix = '_tgt%i_phase%i_plat%i' % (target_id, phase_id, alt_id)
                    l_presence = model.NewBoolVar('presence' + alt_suffix)
                    l_start = model.NewIntVar(0, horizon, 'start' + alt_suffix)
                    l_duration = phase[phase["Plat_num"] == alt_id]["PLATPROCTIME"].item()
                    l_end = model.NewIntVar(0, horizon, 'end' + alt_suffix)
                    l_interval = model.NewOptionalIntervalVar(
                        l_start, l_duration, l_end, l_presence,
                        'interval' + alt_suffix)
                    l_presences.append(l_presence)

                    # Link the primary/global variables with the local ones.
                    model.Add(start == l_start).OnlyEnforceIf(l_presence)
                    model.Add(duration == l_duration).OnlyEnforceIf(l_presence)
                    model.Add(end == l_end).OnlyEnforceIf(l_presence)

                    # Add the local interval to the right platform.  # not sure if this is right... what is this?
                    intervals_per_resources[phase[phase["Plat_num"]==alt_id]["Plat_num"].item()].append(l_interval)

                    # Store the presences for the solution.
                    presences[(target_id, phase_id, alt_id)] = l_presence

                # Select exactly one presence variable.
                model.AddExactlyOne(l_presences)
            # else:  # would only need this portion if there would ever be a case of only one platform that could process the target type
            #     intervals_per_resources[phase[0][1]].append(interval)
            #     presences[(target_id, phase_id, 0)] = model.NewConstant(1)

        target_ends.append(previous_end)

    # Create platforms constraints.
    for platform_id in all_platforms:
        intervals = intervals_per_resources[platform_id]
        if len(intervals) > 1:
            model.AddNoOverlap(intervals)  # modify this later with more logic

    # Makespan objective
    makespan = model.NewIntVar(0, horizon, 'makespan')
    model.AddMaxEquality(makespan, target_ends)
    model.Minimize(makespan)

    # Solve model.
    solver = cp_model.CpSolver()
    solution_printer = SolutionPrinter()
    status = solver.Solve(model, solution_printer)

    # Print final solution.
    for target_id in all_targets:
        print('target %i:' % target_id)
        for phase_id in idx_i_num:
            start_value = solver.Value(starts[(target_id, phase_id)])
            platform = -1
            duration = -1
            selected = -1
            for alt_id in idx_p_num:
                if solver.Value(presences[(target_id, phase_id, alt_id)]):
                    duration = df[df["(t,i,p)_num"] == (target_id, phase_id, alt_id)]["PLATPROCTIME"].item()
                    platform = df[df["(t,i,p)_num"] == (target_id, phase_id, alt_id)]["Plat_num"].item()
                    selected = alt_id
            print(
                '  phase_%i_%i starts at %i (alt %i, platform %i, duration %i)' %
                (target_id, phase_id, start_value, selected, platform, duration))

    print('Solve status: %s' % solver.StatusName(status))
    print('Optimal objective value: %i' % solver.ObjectiveValue())
    print('Statistics')
    print('  - conflicts : %i' % solver.NumConflicts())
    print('  - branches  : %i' % solver.NumBranches())
    print('  - wall time : %f s' % solver.WallTime())


flexible_targetshop()