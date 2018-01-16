"""
Shared helper functions for the forcing code.
"""
time_format = '%Y.%m.%d %H:%M:%S'

def intro():
    # setup
    import os
    import sys
    import argparse
    from datetime import datetime
    
    # This relative path to alpha is meant to work only when intro()
    # is called from the forcing directories, OR from one level down into dot_in.
    alp = os.path.abspath('../../alpha') # regular forcing case
    if os.path.isdir(alp):
        frc = os.getcwd().split('/')[-1]
    else:
        alp = os.path.abspath('../../../alpha') # dot_in forcing case
        frc = os.getcwd().split('/')[-2]
    if alp not in sys.path:
        sys.path.append(alp)
    # Note: the path "alp" will now also work for the calling function
    import Lfun

    # set defaults
    gridname = 'cascadia1'
    tag = 'base'
    run_type = 'forecast'  # backfill or forecast
    start_type = 'continuation'  # new or continuation
    # Example of date_string is 2015.09.19
    date_string = datetime.now().strftime(format='%Y.%m.%d')
    ex_name = 'lobio5'

    # optional command line arguments, can be input in any order
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--gridname', nargs='?', const=gridname, type=str, default=gridname)
    parser.add_argument('-t', '--tag', nargs='?', const=tag, type=str, default=tag)
    parser.add_argument('-f', '--frc', nargs='?', const=frc, type=str, default=frc)
    parser.add_argument('-r', '--run_type', nargs='?', const=run_type, type=str, default=run_type)
    parser.add_argument('-s', '--start_type', nargs='?', const=start_type, type=str, default=start_type)
    parser.add_argument('-d', '--date_string', nargs='?', const=date_string, type=str, default=date_string)
    parser.add_argument('-x', '--ex_name', nargs='?', const=ex_name, type=str, default=ex_name)
    # only used by make_dot_in.py
    parser.add_argument('-np', '--np_num', nargs='?', const=ex_name, type=int, default=72)
    parser.add_argument('-bu', '--blow_ups', nargs='?', const=ex_name, type=int, default=0)
    args = parser.parse_args()

    # get the dict Ldir
    Ldir = Lfun.Lstart(args.gridname, args.tag)
    Ldir['date_string'] = args.date_string
    Ldir['gtagex'] = Ldir['gtag'] + '_' + args.ex_name

    # add the arguments to Ldir, because some code needs them
    Ldir['gridname'] = args.gridname
    Ldir['tag'] = args.tag
    Ldir['frc'] = args.frc
    Ldir['run_type'] = args.run_type
    Ldir['start_type'] = args.start_type
    Ldir['date_string'] = args.date_string
    Ldir['ex_name'] = args.ex_name
    # only used by make_dot_in.py
    Ldir['np_num'] = args.np_num
    Ldir['blow_ups'] = args.blow_ups

    # Make the directory tree for this forcing, if needed. This is redundant
    # with what the driver does (except that it clobbers nothing), and is
    # only included here so that we can test the python code without using
    # the driver.
    Ldir['LOog'] = (Ldir['LOo'] + Ldir['gtag'] + '/')
    Ldir['LOogf'] = (Ldir['LOog'] + 'f' + args.date_string + '/')
    Ldir['LOogf_f'] = (Ldir['LOogf'] + args.frc + '/')
    Ldir['LOogf_fi'] = (Ldir['LOogf_f'] + 'Info/')
    Ldir['LOogf_fd'] = (Ldir['LOogf_f'] + 'Data/')
    Lfun.make_dir(Ldir['LOog'])
    Lfun.make_dir(Ldir['LOogf'])
    Lfun.make_dir(Ldir['LOogf_f'])
    Lfun.make_dir(Ldir['LOogf_fi'])
    Lfun.make_dir(Ldir['LOogf_fd'])

    # screen output
    print('MAIN: frc = ' + args.frc + ', run_type = ' + args.run_type
        + ', date_string = ' + args.date_string)
    print('MAIN start time = ' + datetime.now().strftime(time_format))   
    sys.stdout.flush()

    return Ldir, Lfun

def finale(result_dict, Ldir, Lfun):

    # write results to an output file for the driver
    csv_name_out = Ldir['LOogf_fi'] + 'process_status.csv'
    Lfun.dict_to_csv(result_dict, csv_name_out)

    from datetime import datetime
    print('MAIN end time = ' + datetime.now().strftime(time_format))

