# -*- coding: utf-8 -*-
"""
Created on Wed Mar  8 12:07:08 2023
"""

import pandas as pd
import numpy as np
import warnings

f = "small_inputs_gmuV5.xlsx"
# specify phases for melting
phase_dict = {1:'Find', 2:'PED', 3:'Fix', 4:'PED2', 5:'Track1', 6:'Track2', 
              7:'Track3', 8:'Track Build',9:'Track Gen', 10:'Target', 11:'Engage', 
              12:'IFTU', 13:'Assess', 14:'Assess Decision'}

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


# import target data
def import_target_data(f):
    """This function imports the three sheets containing target information and
    merges them into one dataframe, returning the merged dataframe. 
    Argument: filename (path) of the excel file from which we import the data"""
    # this suppresses warnings concerning having drop-down cells in the excel file
    warnings.simplefilter(action="ignore", category=UserWarning)
    
    inp_TargetType = pd.read_excel(f, sheet_name="inp_TargetType", skiprows=1, usecols="A:M")
    inp_TargetDetail = pd.read_excel(f, sheet_name="inp_TargetDetail", skiprows=1, usecols="A:H")
    inp_TargetKCReq = pd.read_excel(f, sheet_name="inp_TargetKCReq", skiprows=1, usecols="A:O")
    
    # melt TargetKCGeq
    inp_TargetKCReq = inp_TargetKCReq.melt(id_vars = "Target Type", value_vars=phase_dict.values(), 
                                           var_name = "Phase",value_name="Phase_Required")
    
    # before merging, ensure all of the Target Type columns are named the same
    df_target = pd.merge(inp_TargetDetail, inp_TargetType, on="Target Type", how="left")
    df_target = pd.merge(df_target, inp_TargetKCReq, on="Target Type", how="left")
    
    return df_target


# platform data indexed on platform and platform type
def import_platform_data(f):
    """This function imports the sheets containing platform and platform type 
    data and merges them into one dataframe, returning the merged dataframe. 
    Argument: filename (path) of the excel file from which we import the data"""
    warnings.simplefilter(action="ignore", category=UserWarning)
    
    inp_PlatformDetail = pd.read_excel(f, sheet_name= "inp_PlatformDetail", skiprows=1, usecols="A:N").drop("Jamming State", axis="columns")
    inp_PlatPosTime = pd.read_excel(f, sheet_name="inp_PlatPosTime", skiprows=1, nrows=len(inp_PlatformDetail),usecols="A:O")
    inp_PlatType = pd.read_excel(f, sheet_name= "inp_PlatType", skiprows=1, usecols="A:B")
    inp_PlatCapacityAvailable = pd.read_excel(f, sheet_name="inp_PlatCapacityAvailable", skiprows=1, usecols="A:O")
    inp_WpnLoadout = pd.read_excel(f, sheet_name="inp_WpnLoadout", skiprows=1, usecols="A:F")
    inp_IFTUCAPACITY = pd.read_excel(f, sheet_name="inp_IFTUCAPACITY", skiprows=1, usecols="A:F")
    inp_MINIFTUDURATION = pd.read_excel(f, sheet_name="inp_MINIFTUDURATION", skiprows=1, usecols="A:F")
    
    # melt TargetKCGeq
    inp_PlatPosTime = inp_PlatPosTime.melt(id_vars = "Plat ID", value_vars=phase_dict.values(),
                                           var_name = "Phase",value_name="PLATPOSTIME")
    
    inp_PlatCapacityAvailable = inp_PlatCapacityAvailable.melt(
        id_vars = "Plat Type", value_vars=phase_dict.values(), 
        var_name = "Phase",value_name="PLATCAPACITYAVAILABLE")
    
    df = pd.merge(inp_PlatformDetail, inp_PlatPosTime, on="Plat ID")
    df = pd.merge(df, inp_PlatCapacityAvailable, on=["Plat Type", "Phase"])
    df = pd.merge(df, inp_PlatType, on="Plat Type")
    df = pd.merge(df, inp_WpnLoadout, on="Plat Type")
    df = pd.merge(df, inp_IFTUCAPACITY, on="Plat Type")
    df = pd.merge(df, inp_MINIFTUDURATION, on="Plat Type")
    
    return df

# platform data indexed on platform type and target type
def import_platform_target_data(f):
    """This function imports the sheets containing platform type and target type 
    data and merges them into one dataframe, returning the merged dataframe. 
    Argument: filename (path) of the excel file from which we import the data"""
    warnings.simplefilter(action="ignore", category=UserWarning)
    
    # import the data from the sheets
    inp_PlatDetCapes = pd.read_excel(f, sheet_name="inp_PlatDetCapes", skiprows=1, usecols="A:C")
    inp_PlatCapacity = pd.read_excel(f, sheet_name="inp_PlatCapacity", skiprows=1, usecols="A:P")  
    inp_PlatProcTime = pd.read_excel(f, sheet_name="inp_PlatProcTime", skiprows=1, usecols="A:P")
    inp_PlatTrackLife = pd.read_excel(f, sheet_name="inp_PlatTrackLife", skiprows=1, usecols="A:F")
    inp_PlatRange = pd.read_excel(f, sheet_name="inp_PlatRange", skiprows=1, usecols="A:P")
    
    # "Melt" the data to make Phase a column along with a column for the value of interest
    inp_PlatCapacity = inp_PlatCapacity.melt(
        id_vars = ["Plat Type", "Target Type"], value_vars=phase_dict.values(), 
        var_name = "Phase",value_name="PLATCAPACITY")
    inp_PlatProcTime = inp_PlatProcTime.melt(
        id_vars = ["Plat Type", "Target Type"], value_vars=phase_dict.values(), 
        var_name = "Phase", value_name="PLATPROCTIME")
    inp_PlatTrackLife = inp_PlatTrackLife.melt(
        id_vars = ["Plat Type", "Target Type"], value_vars=["Fix", "Track1", "Track2", "Track3"],
        var_name = "Phase", value_name="PLATTRACKLIFE")
    inp_PlatRange = inp_PlatRange.melt(
        id_vars = ["Plat Type", "Target Type"], value_vars=phase_dict.values(),
        var_name = "Phase", value_name="PLATRANGE")
    
    # Merge the data on plattype, targettype, and new column of phase
    df = pd.merge(inp_PlatCapacity, inp_PlatProcTime, on=["Plat Type", "Target Type", "Phase"])
    df = pd.merge(df, inp_PlatRange, on=["Plat Type", "Target Type", "Phase"])
    df = pd.merge(df, inp_PlatTrackLife, on=["Plat Type", "Target Type", "Phase"], how="outer")
    df = df.replace(np.NaN, -1)  # replaces all created NaN values with -1
    df = pd.merge(df, inp_PlatDetCapes, on=["Plat Type", "Target Type"])
    
    return df


# platform data indexed on platform type and killchain phase
def import_platform_phase_data(f):
    """This function imports the sheets containing platform and phase data 
    and merges them into one dataframe, returning the merged dataframe. 
    Argument: filename (path) of the excel file from which we import the data"""
    warnings.simplefilter(action="ignore", category=UserWarning)
    
    inp_PlatLinks = pd.read_excel(f, sheet_name="inp_PlatLinks", skiprows=1, usecols="A:N")
    inp_PlatLinksLatency = pd.read_excel(f, sheet_name="inp_PlatLinksLatency", skiprows=1, usecols="A:N")
    inp_PlatLinksRange = pd.read_excel(f, sheet_name="inp_PlatLinksRange", skiprows=1, usecols="A:N")
    inp_PlatSimultaneousPhases = pd.read_excel(f, sheet_name="inp_PlatSimultaneousPhases", skiprows=1, usecols="A:P")
    
    df = pd.merge(
        inp_PlatLinks, inp_PlatLinksLatency, 
        on=["Plat Type", "Phase", "Sender Jamming State", "Receiver Jamming State"])
    
    df = pd.merge(df, inp_PlatLinksRange, 
                  on=["Plat Type", "Phase", "Sender Jamming State", "Receiver Jamming State"])
    
    df = pd.merge(df, inp_PlatSimultaneousPhases, on=["Plat Type", "Phase"])
    
    return df
    

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


def create_big_dataframe(f):
    """This function combines all indicies and associated data into one dataframe.
    Weapon data is not included. 
    Arguments: f: data file name (path).
    jam: boolean: True if you want jamming state index. False drops index j"""
    df_p = import_platform_data(f)
    # df_pt_i = import_platform_phase_data(f)  # do not include for mod 1.0
    df_pt_tt = import_platform_target_data(f)
    df_t = import_target_data(f)
    
    # create a dataframe with all platform types, target types and phases
    df_pt_tt_i = pd.merge(df_pt_tt, df_p, on=["Plat Type", "Phase"])
    
    # for future use when considering jamming state j
    # if jam:
    #     df_pt_tt_i = pd.merge(df_pt_tt_i, df_pt_tt, on=["Plat Type","Target Type"])
    # else:
    #     df_pt_tt_i = df_pt_tt_i[["Plat Type", "Target Type", "Phase"]].drop_duplicates()
    #     df_pt_tt_i = pd.merge(df_pt_tt_i, df_pt_i, on=["Plat Type","Target Type"])
    

    # create dataframe with all indices
    df = pd.merge(df_t, df_pt_tt_i, on= ["Target Type", "Phase"])
    
    t_i_p_groups = list(zip(df["Target ID"], df["Phase"], df["Plat ID"]))
    df.insert(0, "(t,i,p)",  t_i_p_groups)  # make this the first column
    
    # create phase number dataframe to merge with the big dataframe
    phase_df = pd.DataFrame.from_dict(phase_dict, orient="index").reset_index()
    phase_df.rename({"index":"Phase_num", 0:"Phase"}, axis=1, inplace=True)
    
    df = pd.merge(df, phase_df, on="Phase")
    phase_num = df.pop("Phase_num") # pop from df after it has the right # rows / values
    df.insert(df.columns.get_loc("Phase")+1,"Phase_num",phase_num)  # reinsert the popped Series into the desired spot
    
    # Create and insert platform numbers
    df_p = pd.Series(tuple(set(df['Plat ID']))).reset_index().rename({"index":"Plat_num",0:"Plat ID"}, axis=1)
    df = pd.merge(df, df_p, on="Plat ID")
    p_num = df.pop("Plat_num")+1
    df.insert(df.columns.get_loc("Plat ID")+1, "Plat_num", p_num)
    
    # Create and insert target numbers
    df_t = pd.Series(tuple(set(df['Target ID']))).reset_index().rename({"index":"Target_num",0:"Target ID"}, axis=1)
    df = pd.merge(df, df_t, on="Target ID")
    t_num = df.pop("Target_num")+1
    df.insert(df.columns.get_loc("Target ID")+1, "Target_num", t_num)
    
    t_i_p_nums = list(zip(df["Target_num"], df["Phase_num"], df["Plat_num"]))
    df.insert(0,"(t,i,p)_num", t_i_p_nums)
    df.sort_values(by="(t,i,p)_num", inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df    


# if __name__ == "__main__":

#     f = "small_inputs_gmuV4.xlsx"  # enter the filename (path) for the data
#     parameters =  define_parameters()
#     df_t = import_target_data(f=f)
#     df_platform = import_platform_data(f=f)
#     df_platform_target = import_platform_target_data(f=f)
#     df_platform_phase = import_platform_phase_data(f=f)
#     df_wt = import_weapon_data(f=f)
