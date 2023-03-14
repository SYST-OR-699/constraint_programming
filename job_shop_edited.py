# Example from https://developers.google.com/optimization/scheduling/job_shop

import collections
from ortools.sat.python import cp_model

# enter the data
jobs_data = [  # task = (machine_id, processing_time).
    [("Find", 57), ("PED", 5), ("Fix", 5), ("PED2", 1), ("Track1", 5)],  # sea_large_1
    [("Find", 57), ("PED", 5), ("Fix", 5), ("PED2", 1), ("Track1", 5)],  # sea_small_1
    [("Find", 57), ("PED", 5), ("Fix", 5), ("PED2", 1), ("Track1", 5)]  # land_moving_1
]

machines_count = 1 + max(task[0] for job in jobs_data for task in job)
all_machines = range(machines_count)
all_jobs = range(len(jobs_data))  # added this, because its used below with no other prior definition
# Computes horizon dynamically as the sum of all durations.
horizon = sum(task[1] for job in jobs_data for task in job)

model = cp_model.CpModel()

# Named tuple to store information about created variables.
task_type = collections.namedtuple(typename='task_type', field_names='start end interval')
# Named tuple to manipulate solution information.
assigned_task_type = collections.namedtuple(typename='assigned_task_type',
                                            field_names='start job index duration')

# Creates job intervals and add to the corresponding machine lists.
all_tasks = {}
machine_to_intervals = collections.defaultdict(list)

for job_id, job in enumerate(jobs_data):
    for task_id, task in enumerate(job):
        machine = task[0]
        duration = task[1]
        suffix = '_%i_%i' % (job_id, task_id)
        start_var = model.NewIntVar(0, horizon, 'start' + suffix)
        end_var = model.NewIntVar(0, horizon, 'end' + suffix)
        interval_var = model.NewIntervalVar(start_var, duration, end_var,
                                            'interval' + suffix)
        all_tasks[job_id, task_id] = task_type(start=start_var,
                                               end=end_var,
                                               interval=interval_var)
        machine_to_intervals[machine].append(interval_var)


# Create and add disjunctive constraints.
for machine in all_machines:
    model.AddNoOverlap(machine_to_intervals[machine])

# Precedences inside a job.
for job_id, job in enumerate(jobs_data):
    for task_id in range(len(job) - 1):
        model.Add(all_tasks[job_id, task_id +
                            1].start >= all_tasks[job_id, task_id].end)


# Makespan objective.
obj_var = model.NewIntVar(0, horizon, 'makespan')
model.AddMaxEquality(obj_var, [
    all_tasks[job_id, len(job) - 1].end
    for job_id, job in enumerate(jobs_data)
])
model.Minimize(obj_var)

model.AddMaxEquality(
    obj_var,
    [all_tasks[(job, len(jobs_data[job]) - 1)].end for job in all_jobs])

# Run the solver
solver = cp_model.CpSolver()
status = solver.Solve(model)

# Display the results
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print('Solution:')
    # Create one list of assigned tasks per machine.
    assigned_jobs = collections.defaultdict(list)
    for job_id, job in enumerate(jobs_data):
        for task_id, task in enumerate(job):
            machine = task[0]
            assigned_jobs[machine].append(
                assigned_task_type(start=solver.Value(
                    all_tasks[job_id, task_id].start),
                                   job=job_id,
                                   index=task_id,
                                   duration=task[1]))

    # Create per machine output lines.
    output = ''
    for machine in all_machines:
        # Sort by starting time.
        assigned_jobs[machine].sort()
        sol_line_tasks = 'Machine ' + str(machine) + ': '
        sol_line = '           '

        for assigned_task in assigned_jobs[machine]:
            name = 'job_%i_task_%i' % (assigned_task.job,
                                       assigned_task.index)
            # Add spaces to output to align columns.
            sol_line_tasks += '%-15s' % name

            start = assigned_task.start
            duration = assigned_task.duration
            sol_tmp = '[%i,%i]' % (start, start + duration)
            # Add spaces to output to align columns.
            sol_line += '%-15s' % sol_tmp

        sol_line += '\n'
        sol_line_tasks += '\n'
        output += sol_line_tasks
        output += sol_line

    # Finally print the solution found.
    print(f'Optimal Schedule Length: {solver.ObjectiveValue()}')
    print(output)
else:
    print('No solution found.')
