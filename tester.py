# -*- coding: utf-8 -*-
"""
Created on Mon Sep 27 16:25:20 2021

@author: asbjornu
"""

import schedule_tester_bokeh as st
import pathlib
import time




schedule_path = pathlib.Path("test_schedules")
schedule_name = "1_Standard_3cyc_C20R3-C50R4lith_30cyc_C4R3.sdu"
# schedule_name = "MRR0001_Cycle.sdu"
# schedule_name = "MRR0001_Cycle_C5.sdu"
#schedule_name = "MRR0002_Rate.sdu"
#schedule_name = "MRR0001_Cycle.sdu"
# schedule_name = "Half_cell_1.0-0.05V_1cycC20R4C50R4C100R4C200R4lithC20R4delith_2cyc_C10R4-2cyc_C5R3-2000cyc_C2R3.sdu"
schedule_name = "Tilsiktcycling5mV_2020.sdu"
# schedule_name = "1h-rest_2xC20R4_10xC5R3_10times.sdu"
# schedule_name = "thinFilm_formation_initial+BASE.sdx"
# schedule_name = "thinFilm_1h_3x1uAcm2_taper05_02_10x10uAhcm2+BASE.sdx"
schedule_name = "Tilsiktcycling5mV_2021_500cycles.sdu"
schedule_name = "Tilsiktcycling5mV_2021_500cycles-C20lastcycle.sdu"
schedule_name = "FullCell_1h-rest_1xC20R4_150xcharge_2CR2to80pcent-C4R3-discharge_C4R3.sdu"
schedule_name = "Half_cell_1.0-0.05V_2cycC20R4C50R4C100R4C200R4lithC20R4delith_5cyc_C10R4-5cyc_C5R3-2000cyc_C2R3.sdu"
schedule_name = "3xC20-MR_NMC_V4dot3-2dot5_5X.sdu"
schedule_name = "Half_cell_1.0-0.05V-5cycC20R3_C10R3_C5R2_C2R2_1CR2_2CR1-1000cyc_C5R2.sdu"
schedule_name = "Half_cell_1V-0dot05V_12h-rest_Formation-3xC20R4-taperC50R4_Cycling_50xC2R3-2xC20R4-2xC10R3-5times.sdu"
schedule_name = "thinfilm_ratetest+BASE.sdx"



schedule_filename = schedule_path / schedule_name


cellType = 'half_cell'
# cellType = 'full_cell'
# cellType = 'full_cell_NMC'
# cellType = 'full_cell_LFP'

deltaTime = 0.2
SOClength = 10
maxCycles = 300




performance_run = False


def run():
    global tester
    try:
        tester = st.Tester()
        tester.setSchedule(schedule_filename)
        tester.buildCell(0.002, 1.000, deltatime = deltaTime, cellType = cellType, SOClength = SOClength)
        tester.runTest(maxCycles = maxCycles)
    except Exception as e:
        e.print()
        print("Run crashed, printing run until now..")
        print("Failed on step", tester.schedule.currentStep.stepIndex)
    tester.prepareOutput()
    tester.plotOverviewBokeh(pathlib.Path("test_schedules/output") / (schedule_name[:-4] + ".html"), fig_width=2400, fig_height=1200, line_width = 1.5, line_alpha= 0.9)

if performance_run:
    import cProfile
    import pstats
    
    pr = cProfile.Profile()
    pr.run('run()')
    pr.dump_stats('output.prof')
    
    log_path = pathlib.Path("test_schedules\logs")
    log_filename = schedule_path / ("log_" + time.strftime('%Y%m%d-%H%M%S') + ".txt")
    stream = open(log_filename, 'w')
    ps = pstats.Stats('output.prof', stream=stream).sort_stats('cumulative')
    ps.print_stats()
    stream.close()
    
else:
    run()



