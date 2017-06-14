#!/bin/bash

# This runs the code to create forcing for one or more days,
# for any of the types of forcing,
# allowing for either a forecast or backfill.
#
# CHANGES:
# 8/21/2016 Various edits to handle jobs more gracefully.
# 5/20/2017 I made it so that it could be run again but only re-make
# the forcing directory if needed.  Then on 5/30/2017 Added the optional flag
# -c (for clobber) to override this behavior and force it to
# remake the forcing.

# NOTE: must be run from fjord.

# set a path and connect to a library of functions
if [ $HOME = "/Users/PM5" ] ; then
  LO_parent="/Users/PM5/Documents/LiveOcean"
elif [ $HOME = "/home/parker" ] ; then
  LO_parent="/data1/parker/LiveOcean"
elif [ $HOME = "/Users/elizabethbrasseale" ] ; then
  LO_parent="/Users/elizabethbrasseale/LiveOcean"
elif [ $HOME = "/home/eab32" ] ; then
  LO_parent="/pmr4/eab32/LiveOcean"
fi
. $LO_parent"/driver/common.lib"

# USE COMMAND LINE OPTIONS
#
# -g name of the grid [cascadia1, ...]
# -t name of the forcing tag [base, ...]
# -x name of the ROMS executable to use (only needed if forcing is "azu" or "low_pass") [lo1, ...]
# -f forcing type [atm, ocn, riv, tide, azu, low_pass]
# -r run type [forecast, backfill]
#  if backfill, then you must provide two more arguments
# -0 start date: yyyymmdd
# -1 end date: yyyymmdd
# -c force it to remake the forcing, even if it already exists
#
# example call to do backfill:
# ./driver_forcing1.sh -g cascadia1 -t base -f atm -r backfill -0 20140201 -1 20140203
#
# example call to do forecast:
# ./driver_forcing1.sh -g cascadia1 -t base -f atm -r forecast
#
# example call push to azure:
# ./driver_forcing1.sh -g cascadia1 -t base -x lo1 -f azu -r backfill -0 20140201 -1 20140203
#
# you can also use long names like --ex_name instead of -x

ex_name="placeholder"
clobber_flag=0 # the default (0) is to not clobber, unless the -c argument is used
while [ "$1" != "" ] ; do
  case $1 in
    -g | --gridname )  shift
      gridname=$1
      ;;
    -t | --tag )  shift
      tag=$1
      ;;
    -x | --ex_name )  shift
      ex_name=$1
      ;;
    -f | --frc )  shift
      frc=$1
      ;;
    -r | --run_type )  shift
      run_type=$1
      ;;
    -0 | --ymd0 )  shift
      ymd0=$1
      ;;
    -1 | --ymd1 )  shift
      ymd1=$1
      ;;
    -c | --clobber )
      clobber_flag=1
      ;;
  esac
  shift
done

if [ $run_type = "forecast" ] ; then
  # do forecast
  ymd0=$(date "+%Y%m%d")
  ymd1=$ymd0
fi

# parse the date strings
y0=${ymd0:0:4}; m0=${ymd0:4:2}; d0=${ymd0:6:2}
y1=${ymd1:0:4}; m1=${ymd1:4:2}; d1=${ymd1:6:2}

y=$y0; m=$m0; d=$d0
# note the leading "10#" so that it doesn't interpret 08 etc. as octal
D0=$[10#$y*10000 + 10#$m*100 + 10#$d]
D=$D0
D1=$[10#$y1*10000 + 10#$m1*100 + 10#$d1]

gtag=$gridname"_"$tag

while_flag=0
while [ $D -le $D1 ] && [ $while_flag -eq 0 ]
do
  # manipulate the string D to insert dots, using the syntax:
  #    substring = ${string:start_index:count}
  # and the index starts from 0
  DD=${D:0:4}.${D:4:2}.${D:6:2}
  
  f_string="f"$DD
  LOo=$LO_parent"_output"
  LOog=$LOo"/"$gtag
  LOogf=$LOog"/"$f_string
  LOogf_f=$LOogf"/"$frc
  echo $LOogf_f
  echo $(date)
  LOogf_fi=$LOogf_f"/Info"
  LOogf_fd=$LOogf_f"/Data"
  
  # Make the forcing.
  cd $LO_parent"/forcing/"$frc
  if [ $HOME=="/Users/elizabethbrasseale" ] ; then
    source $HOME"/.bash_profile"
  else
    source $HOME"/.bashrc"
  fi
  if [ -e $HOME"/.bash_profile" ] ; then
    source $HOME"/.bash_profile"
  fi
  if [ -e $HOME"/.profile" ] ; then
    source $HOME"/.profile"
  fi
  python ./make_forcing_main.py -g $gridname -t $tag -f $frc -r $run_type -d $DD -x $ex_name > $LOogf_fi"/screen_out.txt" &

  # Check that the job has finished successfully.
  PID1=$!
  wait $PID1
  echo "job completed for" $f_string
  echo $(date)
  # this makes all parent directories if needed
  mkdir -p $LOogf
  
  checkfile=$LOogf_fi"/process_status.csv"
  
  already_done_flag=0
  # check to see if the job has already completed successfully
  if [ -f $checkfile ] && [ $clobber_flag -eq 0 ]; then
    if grep -q "result,success" $checkfile; then
      echo "- No action needed: job completed successfully already."
      already_done_flag=1
    else
      echo "- Trying job again."
    fi
  fi
  
  if [ $already_done_flag -eq 0 ] || [ $clobber_flag -eq 1 ]; then
    
    if [ -d $LOogf_f ]
    then
      rm -rf $LOogf_f
    fi
    mkdir $LOogf_f
    mkdir $LOogf_fi
    mkdir $LOogf_fd
    
    # Make the forcing.
    cd $LO_parent"/forcing/"$frc
    source $HOME"/.bashrc"
    if [ -e $HOME"/.bash_profile" ] ; then
      source $HOME"/.bash_profile"
    fi
    if [ -e $HOME"/.profile" ] ; then
      source $HOME"/.profile"
    fi
    python ./make_forcing_main.py -g $gridname -t $tag -f $frc -r $run_type -d $DD -x $ex_name > $LOogf_fi"/screen_out.txt" &

    # Check that the job has finished successfully.
    PID1=$!
    wait $PID1
    echo "job completed for" $f_string
    echo $(date)
  
    # check the checkfile to see if we should continue
    if grep -q "result,success" $checkfile ; then
      echo "- Job completed successfully."
      # will continue because we don't change while_flag
    else
      echo "- Something else happened."
      while_flag=1
      # stop the driver
    fi
  
  fi # end of already_done_flag test
  
  # This function increments the day.
  # NOTE: it changes y, m, d, and D, even in the scope of this shell script!
  next_date $y $m $d
  
done
