# -*- coding: utf-8 -*-
"""
Created on Sun Mar 26 13:42:00 2023

@author: brend
"""

#!/usr/bin/env python3
# Copyright 2010-2022 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Solves a flexible targetshop problems with the CP-SAT solver.

A targetshop is a standard scheduling problem when you must sequence a
series of phase_types on a set of platforms. Each target contains one phase_type per
platform. The order of execution and the length of each target on each
platform is phase_type dependent.

The objective is to minimize the maximum completion time of all
targets. This is called the makespan.
"""

# overloaded sum() clashes with pytype.

import collections

from ortools.sat.python import cp_model


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__solution_count = 0

    def on_solution_callback(self):
        """Called at each new solution."""
        print('Solution %i, time = %f s, objective = %i' %
              (self.__solution_count, self.WallTime(), self.ObjectiveValue()))
        self.__solution_count += 1


def flexible_targetshop():
    """Solve a small flexible targetshop problem."""
    # Data part.
    targets = [  # phase = (processing_time, platform_id)
        [  # target 0
            [(3, 0), (1, 1), (5, 2)],  # phase 0 with 3 alternatives
            [(2, 0), (4, 1), (6, 2)],  # phase 1 with 3 alternatives
            [(2, 0), (3, 1), (1, 2)],  # phase 2 with 3 alternatives
        ],
        [  # target 1
            [(2, 0), (3, 1), (4, 2)],
            [(1, 0), (5, 1), (4, 2)],
            [(2, 0), (1, 1), (4, 2)],
        ],
        [  # target 2
            [(2, 0), (1, 1), (4, 2)],
            [(2, 0), (3, 1), (4, 2)],
            [(3, 0), (1, 1), (5, 2)],
        ],
    ]

    num_targets = len(targets)
    all_targets = range(num_targets)

    num_platforms = 3
    all_platforms = range(num_platforms)

    # Model the flexible targetshop problem.
    model = cp_model.CpModel()

    horizon = 0
    for target in targets:
        for phase in target:
            max_phase_duration = 0
            for alternative in phase:
                max_phase_duration = max(max_phase_duration, alternative[0])  # eventually replace alternative tuple with platform processing time
            horizon += max_phase_duration

    print('Horizon = %i' % horizon)

    # Global storage of variables.
    intervals_per_resources = collections.defaultdict(list)
    starts = {}  # indexed by (target_id, phase_id).
    presences = {}  # indexed by (target_id, phase_id, alt_id).
    target_ends = []

    # Scan the targets and create the relevant variables and intervals.
    for target_id in all_targets:
        target = targets[target_id]
        num_phases = len(target)
        previous_end = None
        for phase_id in range(num_phases):
            phase = target[phase_id]

            min_duration = phase[0][0]
            max_duration = phase[0][0]

            num_alternatives = len(phase)
            all_alternatives = range(num_alternatives)

            for alt_id in range(1, num_alternatives):
                alt_duration = phase[alt_id][0]
                min_duration = min(min_duration, alt_duration)
                max_duration = max(max_duration, alt_duration)

            # Create main interval for the phase.
            suffix_name = '_j%i_t%i' % (target_id, phase_id)
            start = model.NewIntVar(0, horizon, 'start' + suffix_name)
            duration = model.NewIntVar(min_duration, max_duration,
                                       'duration' + suffix_name)
            end = model.NewIntVar(0, horizon, 'end' + suffix_name)
            interval = model.NewIntervalVar(start, duration, end,
                                            'interval' + suffix_name)

            # Store the start for the solution.
            starts[(target_id, phase_id)] = start

            # Add precedence with previous phase in the same target.
            if previous_end is not None:
                model.Add(start >= previous_end)
            previous_end = end

            # Create alternative intervals.
            if num_alternatives > 1:
                l_presences = []
                for alt_id in all_alternatives:
                    alt_suffix = '_j%i_t%i_a%i' % (target_id, phase_id, alt_id)
                    l_presence = model.NewBoolVar('presence' + alt_suffix)
                    l_start = model.NewIntVar(0, horizon, 'start' + alt_suffix)
                    l_duration = phase[alt_id][0]
                    l_end = model.NewIntVar(0, horizon, 'end' + alt_suffix)
                    l_interval = model.NewOptionalIntervalVar(
                        l_start, l_duration, l_end, l_presence,
                        'interval' + alt_suffix)
                    l_presences.append(l_presence)

                    # Link the primary/global variables with the local ones.
                    model.Add(start == l_start).OnlyEnforceIf(l_presence)
                    model.Add(duration == l_duration).OnlyEnforceIf(l_presence)
                    model.Add(end == l_end).OnlyEnforceIf(l_presence)

                    # Add the local interval to the right platform.
                    intervals_per_resources[phase[alt_id][1]].append(l_interval)

                    # Store the presences for the solution.
                    presences[(target_id, phase_id, alt_id)] = l_presence

                # Select exactly one presence variable.
                model.AddExactlyOne(l_presences)
            else:
                intervals_per_resources[phase[0][1]].append(interval)
                presences[(target_id, phase_id, 0)] = model.NewConstant(1)

        target_ends.append(previous_end)

    # Create platforms constraints.
    for platform_id in all_platforms:
        intervals = intervals_per_resources[platform_id]
        if len(intervals) > 1:
            model.AddNoOverlap(intervals)

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
        for phase_id in range(len(targets[target_id])):
            start_value = solver.Value(starts[(target_id, phase_id)])
            platform = -1
            duration = -1
            selected = -1
            for alt_id in range(len(targets[target_id][phase_id])):
                if solver.Value(presences[(target_id, phase_id, alt_id)]):
                    duration = targets[target_id][phase_id][alt_id][0]
                    platform = targets[target_id][phase_id][alt_id][1]
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