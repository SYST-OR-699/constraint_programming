# -*- coding: utf-8 -*-
"""
Created on Wed Mar  8 12:07:08 2023

@author: brend
"""

from ortools.sat.python import cp_model
import pandas as pd
import warnings

# define model parameters
def define_parameters(max_horizon_min=7200, 
                      same_plat_for_Track_phases=0, 
                      max_eng_wins_btw_find_engage=1):
    """This function bundles the model parameters into a dictionary to reduce
    the number of objects in the memory. 
    Arguments: 
        max_horiz_min: number of minutes for the time horizon considered
        same_plat_for_Track_phases: 
            1 = yes, force model to use same platform for Track1/2/3
            0 = no, allow model to choose different platforms for each Track1/2/3
        max_eng_wins_btw_find_engage: maximum number of engagement windows
            between the find and engagement phases. # MAXWINSBTWFINDENG"""
    
    parameters = {}  # instantiate the dictionary
    
    parameters["max_horizon_min"] = max_horizon_min  # 7200 minutes = 5 days
    parameters["same_plat_for_Track_phases"] = same_plat_for_Track_phases
    parameters["max_eng_wins_btw_find_engage"] = max_eng_wins_btw_find_engage
    
    return parameters

parameters =  define_parameters()

f = "small_inputs_gmuV3.xlsx"  # enter the filename (path) for the data

# We may consider using a 'usecols=[0:len(parameter_of_interest)] to accomodate a changing model

# import phase data
inp_KillchainPhase = pd.read_excel(f, sheet_name="inp_KillchainPhase", skiprows=1, usecols="A:B")

# import target data
def import_target_data(f):
    """This function imports the three sheets containing target information and
    merges them into one dataframe, returning the merged dataframe. 
    Argument: filename (path) of the excel file from which we import the data"""
    # this suppresses warnings concerning having drop-down cells in the excel file
    warnings.simplefilter(action="ignore", category=UserWarning)
    
    inp_TargetType = pd.read_excel(f, sheet_name="inp_TargetType", skiprows=1, usecols="A:M")
    inp_TargetKCReq = pd.read_excel(f, sheet_name="inp_TargetKCReq", skiprows=1, usecols="A:O")
    inp_TargetDetail = pd.read_excel(f, sheet_name="inp_TargetDetail", skiprows=1, usecols="A:H")
    
    # before merging, ensure all of the Target Type columns are named the same
    df_target = pd.merge(inp_TargetDetail, inp_TargetType, on="Target Type (tt)", how="left")
    df_target = pd.merge(df_target, inp_TargetKCReq, on="Target Type (tt)", how="left")
    
    return df_target

df_t = import_target_data(f=f)

# import platform data

# platform data indexed on platform and platform type
def import_platform_data(f):
    """This function imports the sheets containing platform and platform type 
    data and merges them into one dataframe, returning the merged dataframe. 
    Argument: filename (path) of the excel file from which we import the data"""
    inp_PlatformDetail = pd.read_excel(f, sheet_name= "inp_PlatformDetail", skiprows=1, usecols="A:N")
    inp_PlatPosTime = pd.read_excel(f, sheet_name="inp_PlatPosTime", skiprows=1, usecols="A:O")
    inp_PlatType = pd.read_excel(f, sheet_name= "inp_PlatType", skiprows=1, usecols="A:B")
    inp_PlatCapacityAvailable = pd.read_excel(f, sheet_name="inp_PlatCapacityAvailable", skiprows=1, usecols="A:O")
    inp_WpnLoadout = pd.read_excel(f, sheet_name="inp_WpnLoadout", skiprows=1, usecols="A:F")
    inp_IFTUCAPACITY = pd.read_excel(f, sheet_name="inp_IFTUCAPACITY", skiprows=1, usecols="A:F")
    inp_MINIFTUDURATION = pd.read_excel(f, sheet_name="inp_MINIFTUDURATION", skiprows=1, usecols="A:F")
    
    df = pd.merge(inp_PlatformDetail, inp_PlatPosTime, on="Plat ID (p)")
    df = pd.merge(df, inp_PlatType, on="Plat Type (pt)")
    df = pd.merge(df, inp_PlatCapacityAvailable, on="Plat Type (pt)")
    df = pd.merge(df, inp_WpnLoadout, on="Plat Type (pt)")
    df = pd.merge(df, inp_IFTUCAPACITY, on="Plat Type (pt)")
    df = pd.merge(df, inp_MINIFTUDURATION, on="Plat Type (pt)")
    
    return df


df_platform = import_platform_data(f=f)

# platform data indexed on platform type and target type
def import_platform_target_data(f):
    """This function imports the sheets containing platform type and target type 
    data and merges them into one dataframe, returning the merged dataframe. 
    Argument: filename (path) of the excel file from which we import the data"""
    inp_PlatDetCapes = pd.read_excel(f, sheet_name="inp_PlatDetCapes", skiprows=1, usecols="A:C")
    inp_PlatCapacity = pd.read_excel(f, sheet_name="inp_PlatCapacity", skiprows=1, usecols="A:P")
    inp_PlatProcTime = pd.read_excel(f, sheet_name="inp_PlatProcTime", skiprows=1, usecols="A:P")
    inp_PlatTrackLife = pd.read_excel(f, sheet_name="inp_PlatTrackLife", skiprows=1, usecols="A:F")
    inp_PlatRange = pd.read_excel(f, sheet_name="inp_PlatRange", skiprows=1, usecols="A:P")
    
    df = pd.merge(inp_PlatDetCapes, inp_PlatCapacity, on=["Plat Type", "Target Type"])
    df = pd.merge(df, inp_PlatProcTime, on=["Plat Type", "Target Type"])
    df = pd.merge(df, inp_PlatTrackLife, on=["Plat Type", "Target Type"])
    df = pd.merge(df, inp_PlatRange, on=["Plat Type", "Target Type"])
    
    return df


df_platform_target = import_platform_target_data(f=f)

# platform data indexed on platform type and killchain phase

def import_platform_phase_data(f):
    """This function imports the sheets containing platform and phase data 
    and merges them into one dataframe, returning the merged dataframe. 
    Argument: filename (path) of the excel file from which we import the data"""
    inp_PlatLinks = pd.read_excel(f, sheet_name="inp_PlatLinks", skiprows=1, usecols="A:N")
    inp_PlatLinksLatency = pd.read_excel(f, sheet_name="inp_PlatLinksLatency", skiprows=1, usecols="A:N")
    inp_PlatLinksRange = pd.read_excel(f, sheet_name="inp_PlatLinksRange", skiprows=1, usecols="A:N")
    inp_PlatSimultaneousPhases = pd.read_excel(f, sheet_name="inp_PlatSimultaneousPhases", skiprows=1, usecols="A:P")
    
    df = pd.merge(
        inp_PlatLinks, inp_PlatLinksLatency, 
        on=["Plat Type", "Phase(i)", "Sender Jamming State", "Receiver Jamming State"])
    
    df = pd.merge(df, inp_PlatLinksRange, 
                  on=["Plat Type", "Phase(i)", "Sender Jamming State", "Receiver Jamming State"])
    
    df = pd.merge(df, inp_PlatSimultaneousPhases, on=["Plat Type", "Phase(i)"])
    
    return df


df_platform_phase = import_platform_phase_data(f=f)
    

# import weapon data
def import_weapon_data(f):
    """This function imports the sheets containing weapon information and
    merges them into a dataframe, returning the merged dataframe. The dataframe
    has the weapon types as rows and the columns are the attributes of the weapon
    types. Argument: filename (path) of the excel file from which we import the data"""
    # this suppresses warnings concerning having drop-down cells in the excel file
    warnings.simplefilter(action="ignore", category=UserWarning)
    
    inp_WpnType = pd.read_excel(f, sheet_name="inp_WpnType", skiprows=1, usecols="A:G")
    inp_WpnSurv = pd.read_excel(f, sheet_name="inp_WpnSurv", skiprows=1, usecols="A:H")
    inp_SSPK = pd.read_excel(f, sheet_name="inp_SSPK", skiprows=1, usecols="A:H")
    inp_WpnShotsReqd = pd.read_excel(f, sheet_name="wpns_shots_reqd", skiprows=1, nrows=len(inp_WpnType['Weapon Type']), usecols="A:H")
    inp_ARMLASTDIST = pd.read_excel(f, sheet_name="inp_ARMLASTDIST", skiprows=1, usecols="A:H")
    inp_MAXTIMEBEFOREFIRSTIFTU = pd.read_excel(f, sheet_name="inp_MAXTIMEBEFOREFIRSTIFTU", skiprows=1, usecols="A:H")
    inp_LASTIFTUDIST = pd.read_excel(f, sheet_name="inp_LASTIFTUDIST", skiprows=1, usecols="A:H")
    
    df_wpn = pd.merge(inp_WpnType, inp_WpnSurv, on="Weapon Type", how="left")
    df_wpn = pd.merge(df_wpn, inp_SSPK, on="Weapon Type", how="left")
    df_wpn = pd.merge(df_wpn, inp_WpnShotsReqd, on="Weapon Type", how="left")
    df_wpn = pd.merge(df_wpn, inp_ARMLASTDIST, on="Weapon Type", how="left")
    df_wpn = pd.merge(df_wpn, inp_MAXTIMEBEFOREFIRSTIFTU, on="Weapon Type", how="left")
    df_wpn = pd.merge(df_wpn, inp_LASTIFTUDIST, on="Weapon Type", how="left")
    
    return df_wpn


df_wt = import_weapon_data(f=f)


# define indices

# idx_i = ('Find', 'PED', 'Fix', 'PED2', 'Track1', 'Track2', 'Track3', 'Track_Build', 
#           'Track_Gen', 'Target', 'Engage', 'IFTU', 'Assess', 'Assess_Decision')

# idx_t = tuple(set(inp_TargetDetail['Target ID (t)']))

# idx_p = tuple(set(inp_PlatformDetail['Plat ID (p)']))

# idx_tt = tuple(set(inp_TargetDetail['Target Type (tt)']))

# idx_pt = tuple(set(inp_PlatformDetail['Plat Type (pt)']))

# idx_wt = tuple(set(inp_WpnType['Weapon Type']))

# idx_j = ("perm", "jam")

# idx_k = tuple(range(0,parameters["max_horizon_min"]))


# # instantiate the model
# model = cp_model.CpModel()

# # Variables

# # set the upper bound to maxendtime to the max number of minutes considered
# # there are also no continuous variables: must be an integer
# maxendtime = model.NewIntVar(0, parameters["max_horizon_min"], 'maxendtime')  # 7200 minutes = 5 days





# # binary; 1 if plat p performs kill chain phase i on target t, 0 otherwise
# x = {}  # instantiate a dictionary to store x variable values

# for p in idx_p:
#     for t in idx_t:
#         for i in idx_i:
#             x[(p,t,i)] = model.NewBoolVar(f'x({p},{t},{i})')


# # Objective
# model.Minimize(maxendtime)

# # Constraints
# # model.Add(x + y <= 30)  # this is an example constraint: change


# # Solve
# solver = cp_model.CpSolver()  # Contrary to Gurobi, model and solver are separated.


# status = solver.Solve(model)
# assert status == cp_model.OPTIMAL  # The status tells us if we were able to compute a solution.
# print(f"Makespan for {len(idx_t)} targets: {solver.Value(maxendtime)} minutes")
# # print("=====Stats:======")
# # print(solver.SolutionInfo())
# # print(solver.ResponseStats())
