# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 12:12:23 2020

@author: asbjornu
"""

import re
import time
import operator
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from bokeh.io import output_file, show
from bokeh.layouts import gridplot
from bokeh.plotting import figure
import bokeh.palettes as palettes
import pathlib


class ResponseFunction:
    
    def __init__(self, cellType = 'half_cell'):        
        self.func = 'undefined'
        self.initPot2Soc()
        self.initFastSoc2Pot()
        self.cellType = cellType
    
    def _directSoc2Pot(self, SOC):
        # pot = 0.0005/SOC -4.76*np.power(SOC,6) + 9.34*np.power(SOC,5) - 1.8*np.power(SOC,4) - 7.13*np.power(SOC,3) + 5.8*np.power(SOC,2) - 1.94*SOC + 0.82 + (-(0.2/(1.0001-np.power(SOC,1000))))
        pot = 0.0000002975*np.power(SOC+0.005,-3) - 4.76*np.power(SOC,6) + 9.34*np.power(SOC,5) - 1.8*np.power(SOC,4) - 7.13*np.power(SOC,3) + 5.8*np.power(SOC,2) - 1.94*SOC + 0.82 - 0.2 - (0.0000000001/(np.power((1.005-SOC),4)))
        return pot
        # return  pot.clip(0.0, 3.0)

    def initPot2Soc(self):
#        x = [i*1./100000 for i in range(1,100001)]
        x = np.linspace(0, 100000, 100000) / 100000
        y = self._directSoc2Pot(x)
        self.func = interp1d(x, y)
    
    def initFastSoc2Pot(self):
        x = np.linspace(-499, 100500, 100999) / 100000
        self.fastSoc2PotArray = self._directSoc2Pot(x)
        
    def pot2soc(self, POT):
        return self.func(POT)
    
    def fastSoc2Pot(self, SOC):
        if 'full_cell' in self.cellType:
            SOC = -SOC        
        
        # if SOC <= -19./100000:
        #     SOC = -19./100000
        # elif SOC >= 1:
        #     SOC = 1.-1./100000
        
        returnValue = self.fastSoc2PotArray[int(SOC*100000+498)]
        # print(SOC, returnValue)


            
        if 'full_cell' in self.cellType:
            if 'NMC' in self.cellType:                
                if returnValue > 2.25:
                    returnValue = 2.25
                elif returnValue < -3:
                    returnValue = -3
                return 4.5-returnValue*2
            
            elif 'LFP' in self.cellType:
                if returnValue > 3.6:
                    returnValue = 3.6
                elif returnValue < -3.6:
                    returnValue = -3.6
                return 3.6-returnValue

            else:
                if returnValue > 2.0:
                    returnValue = 2.0
                elif returnValue < -3:
                    returnValue = -3
                return 4.0-returnValue*2
                
        else:
            if returnValue > 3:
                returnValue = 3
            elif returnValue < 0:
                returnValue = 0
            return returnValue
        
    

class Tester:
    def __init__(self):
        self.schedule = Schedule()

        
    def setSchedule(self, filename):
        self.schedule.openSchedule(filename)
        self.schedule.buildSchedule()
        
    def buildCell(self, mass, specific_capacity, deltatime = 2, cellType = 'half_cell', SOClength = 20):
        self.cell = Cell(deltatime, cellType, mass*specific_capacity, SOClength = SOClength)

    def runTest(self, maxCycles = 100):
        self.schedule.runCell(self.cell, maxCycles)
        
    def prepareOutput(self):
        self.output = pd.DataFrame(self.cell.log, columns = [*self.cell.currentstate.keys()])
        
    def plotOverview(self):
        self.fig, self.ax = plt.subplots(2,2, sharex='all')
        mng = plt.get_current_fig_manager()
        mng.window.showMaximized()
        self.fig.tight_layout()
        self.ax[0, 0].set_title('Voltage')
        self.ax[0, 0].plot(self.output.PV_CHAN_Test_Time, self.output.PV_CHAN_Voltage, label="Voltage")
#        self.ax[0, 0].legend(loc=7)
        
        self.ax[0, 1].set_title('Capacity')
        self.ax[0, 1].plot(self.output.PV_CHAN_Test_Time, self.output.PV_CHAN_Charge_Capacity, label="Charge capacity")
        self.ax[0, 1].plot(self.output.PV_CHAN_Test_Time, self.output.PV_CHAN_Discharge_Capacity, label="Discharge capacity")
        self.ax[0, 1].legend(loc=1)

#        self.ax[1, 0].set_title('Current')
        self.ax[1, 0].plot(self.output.PV_CHAN_Test_Time, self.output.PV_CHAN_Current, label="Current")
        self.ax[1, 0].legend(loc=2)

        self.ax[1, 1].set_title('Counters')
        self.ax[1, 1].plot(self.output.PV_CHAN_Test_Time, self.output.PV_CHAN_Cycle_Index, label="Cycle index")
        self.ax[1, 1].plot(self.output.PV_CHAN_Test_Time, self.output.PV_CHAN_Step_Index, label="Step index")
        self.ax[1, 1].plot(self.output.PV_CHAN_Test_Time, self.output.TC_Counter1, label="TC_Counter1")
        self.ax[1, 1].plot(self.output.PV_CHAN_Test_Time, self.output.TC_Counter2, label="TC_Counter2")
        self.ax[1, 1].plot(self.output.PV_CHAN_Test_Time, self.output.TC_Counter3, label="TC_Counter3")
        self.ax[1, 1].plot(self.output.PV_CHAN_Test_Time, self.output.TC_Counter4, label="TC_Counter4")
        self.ax[1, 1].legend(loc=2)
        
    def plotOverviewBokeh(self, filename, fig_width=1900, fig_height=960, line_width=1, line_alpha=1, showPlot = True):
        output_file(filename)
        self.output.to_excel(filename.with_suffix(".xlsx"))
        
        x = self.output.PV_CHAN_Test_Time
        v = self.output.PV_CHAN_Voltage
        
        cc = self.output.PV_CHAN_Charge_Capacity
        dc = self.output.PV_CHAN_Discharge_Capacity
        
        c = self.output.PV_CHAN_Current
        
        ci = self.output.PV_CHAN_Cycle_Index
        si = self.output.PV_CHAN_Step_Index
        c1 = self.output.TC_Counter1
        c2 = self.output.TC_Counter2
        c3 = self.output.TC_Counter3
        c4 = self.output.TC_Counter4
        
        width = int(fig_width/2)
        height = int(fig_height/2)
        colors = palettes.Category10_10
        
        s11 = figure(width=width, height=height, title="Voltage")
        for data, name, color in zip([v], ["Voltage"], colors):
            s11.line(x, data, legend_label=name, line_width=line_width, line_color=color, line_alpha=line_alpha, )
        s11.legend.location = "top_right"
        s11.legend.click_policy="hide"
   
        s12 = figure(width=width, height=height, x_range=s11.x_range, title="Capacity")
        for data, name, color in zip([cc, dc], ["Charge Capacity", "Discharge Capacity"], colors):
            s12.line(x, data, line_width=line_width, line_color=color, line_alpha=line_alpha, legend_label=name)
        s12.legend.location = "top_right"
        s12.legend.click_policy="hide"

   
        s21 = figure(width=width, height=height, x_range=s11.x_range, title="Current")
        for data, name, color in zip([c], ["Current"], colors):
            s21.line(x, data, line_width=line_width, line_color=color, line_alpha=line_alpha, legend_label=name)
        s21.legend.location = "top_left"
        s21.legend.click_policy="hide"

        s22 = figure(width=width, height=height, x_range=s11.x_range, title="Counters")
        for data, name, color in zip([ci, si, c1, c2, c3, c4], ["Cycle index", "Step index", "TC_Counter1", "TC_Counter2", "TC_Counter3", "TC_Counter4"], colors):
            s22.line(x, data, line_width=line_width, line_color=color, line_alpha=line_alpha, legend_label=name)
        s22.legend.location = "top_left"
        s22.legend.click_policy="hide"

    
        p = gridplot([[s11, s12],[s21, s22]])
        
        if showPlot:
            show(p)
        
        
        
    
    def saveOverview(self, filename, dpi = 600, figheight = 9, figwidth = 16):
        self.fig.set_figheight(figheight)
        self.fig.set_figwidth(figwidth)
        self.fig.savefig(filename, dpi = dpi)
        
        
        


class Schedule:
    def __init__(self):
        self.steps = []
        self.formulas = dict()
        
    def openSchedule(self, filename):
        with open(filename) as f:
            self.stepinfotable = []
            self.formulainfolist = []
            level = 0
            
            for line in f.readlines():
                try:
                    p = re.match(r'^\[Schedule_Step([0-9]*)_Limit([0-9]*)\]$', line)            
                    if p is not None:
                        level = 'limit'
                        self.stepinfotable[-1][1].append(dict())
                    
                    p = re.match(r'^\[Schedule_Step([0-9]*)\]$', line)            
                    if p is not None:
                        level = 'step'
                        self.stepinfotable.append([dict(), []])
                        self.stepinfotable[-1][0]["StepIndex"] = int(p.group(1)) + 1
                        
                    p = re.match(r'^\[Schedule_Formula([0-9]*)\]$', line)            
                    if p is not None:
                        level = 'formula'
                        self.formulainfolist.append(dict())
                        self.formulainfolist[-1]["FormulaIndex"] = int(p.group(1)) + 1
                
                    p = re.match(r'^([^=\[]*)=(.*)$', line)
                    if p is not None:
                        p = re.match(r'^([^=]*)=(.*)$', line)
                        key = p.group(1)
                        value = p.group(2)
        
                        if level == 'step':
                            self.stepinfotable[-1][0][key] = value
                        elif level == 'limit':
                            self.stepinfotable[-1][1][-1][key] = value
                        elif level == 'formula':
                            self.formulainfolist[-1][key] = value

                except UnicodeDecodeError as e:
                    print(f"error in line:\n {f}")
                    print(e)
                    
            
    def buildSchedule(self):
        for formulaInfo in self.formulainfolist:
            self.formulas[formulaInfo['m_szLabel']] = Formula(formulaInfo)
            
        for stepinfo in self.stepinfotable:
            self.steps.append(Step(stepinfo, self.formulas))
            
         
       
    def runCell(self, cell, maxCycles):
        self.currentStep = self.steps[0]
        
        self.updateFormulaValuesAndLimits(cell)
        
        goTo = self.currentStep.execute(cell)
#        print("Moving from first step to ",goTo)
        
        while not (goTo == "End Test" or (goTo == "Next Step" and self.currentStep is self.steps[-1]) or cell.currentstate["PV_CHAN_Cycle_Index"] > maxCycles):
            if goTo == "Next Step":
                self.currentStep = self.steps[self.steps.index(self.currentStep)+1]
            else:
                for step in self.steps:
                    if step.stepName == goTo:
                        self.currentStep = step
            
#            print("Currently at", self.currentStep.stepName)
            
            self.updateFormulaValuesAndLimits(cell)
            
            goTo = self.currentStep.execute(cell)
#            print("Going to", goTo)
            
    
    def updateFormulaValuesAndLimits(self, cell):
        for formula in self.formulas.values():
            formula.update(cell.currentstate)
            
        for step in self.steps:
            for limit in step.limits:
                limit.update()
            

class Formula:
    def __init__(self, formulaInfo):
        self.functionName = formulaInfo["m_szLabel"]
        self.expression = formulaInfo["m_szExpression"]        
        self.expression = self.expression.replace("EXP", "np.exp")
        
        for variable in ["TC_Counter1", "TC_Counter2", "TC_Counter3", "TC_Counter4", "PV_CHAN_Cycle_Index", "PV_CHAN_Step_Index"]:
            self.expression = self.expression.replace(variable, "currentstate['" + variable + "']")
            
        self.value = 0
                
    def update(self, currentstate):
        try:
            self.value = eval(self.expression)
        except:
            self.value = 0
            
#            print("Failed formula")
                
    
    def getValue(self):
        return self.value
      


class Step:
    def __init__(self, stepInfo, formulas):
        self.limits = []
        self.loglimits = []        
        self.stepInfo = stepInfo
        self.formulas = formulas
        self.stepInfo = stepInfo[0]

        for limitInfo in stepInfo[1]:
            if limitInfo['m_bStepLimit'] == '1':
                self.limits.append(Limit(limitInfo, formulas))
            elif limitInfo['m_bLogDataLimit'] == '1':
                self.loglimits.append(Limit(limitInfo, formulas))
                
        self.stepName = self.stepInfo['m_szLabel']
        self.stepType = self.stepInfo['m_szStepCtrlType']
        self.stepIndex = self.stepInfo["StepIndex"]


        print('')
        print("Step index: ", self.stepIndex)
        print("Step name: ", self.stepName)
        print("Step type: ", self.stepType)

        try:        
            if self.stepType == 'C-Rate':
                try:
                    self.cRate = float(self.stepInfo['m_szCtrlValue'])
                except:
                    self.cRate = self.stepInfo['m_szCtrlValue']
                self.current = 'null'
                print('C-rate: ', self.cRate)
            if self.stepType == 'Current(A)':
                self.cRate = 'null'
                self.current = float(self.stepInfo['m_szCtrlValue'])
                print('Current: ', self.current)
            elif self.stepType == 'Rest':
                self.cRate = 0
            elif self.stepType == 'Set Variable(s)':
                if self.stepInfo['m_szCtrlValue'] != "":
                    self.zero = int(self.stepInfo['m_szCtrlValue'])
                else:
                    self.zero = 0
                
                if self.stepInfo['m_szExtCtrlValue1'] != "":
                    self.increment = int(self.stepInfo['m_szExtCtrlValue1'])
                else:
                    self.increment = 0
                    
                if self.stepInfo['m_szExtCtrlValue2'] != "":
                    self.decrement = int(self.stepInfo['m_szExtCtrlValue2'])
                else:
                    self.decrement = 0            
                    
        except:
            print("Error in interpretation of step", self.stepIndex)
        
            
            
    def execute(self, cell):

        cell.setStepIndex(self.stepIndex)   
        cell.zeroStepTime()

        if self.stepType == "C-Rate":
#            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)
            running = True        
            while running:
                cell.incrementTime()
                if type(self.cRate) == float:
                    cell.incrementCurrent(crate = self.cRate)
                elif type(self.cRate) == str:
                    cell.incrementCurrent(crate = self.formulas[self.cRate].getValue())
                    
                cell.updateCellVoltage()
#                cell.logState()
                
                isTriggered, goTo = self.checkLimits(cell.currentstate)
            
                if isTriggered:
                    cell.logState()
                    running = False
                elif self.checkLogLimits(cell.currentstate):
                    cell.logState()
                    
            
            return goTo
                
        elif self.stepType == "Current(A)":
#            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)
            running = True        
            while running:
                cell.incrementTime()
                cell.incrementCurrent(current = self.current)
                cell.updateCellVoltage()
#                cell.logState()
                
                isTriggered, goTo = self.checkLimits(cell.currentstate)
            
                if isTriggered:
                    cell.logState()
                    running = False
                elif self.checkLogLimits(cell.currentstate):
                    cell.logState()
                    
            return goTo
            
        elif self.stepType == "Rest":
#            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)
            running = True
            while running:
                cell.incrementTime()
                cell.incrementCurrent(crate = 0)
                cell.updateCellVoltage()
#                cell.logState()
                if self.checkLogLimits(cell.currentstate):
                    cell.logState()
                
                isTriggered, goTo = self.checkLimits(cell.currentstate)
                if isTriggered:
                    running = False
            
            return goTo

                        
        elif self.stepType == "Internal Resistance":
#            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)
            cell.updateInternalResistance()
            cell.logState()
            return self.limits[0].targetStep
            
                        
        elif self.stepType == 'Set Variable(s)':
#            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)

            zeroarray = '{0:32b}'.format(int(self.zero))[::-1]
            if zeroarray[0] == '1':
                cell.zeroChargeCap()
            if zeroarray[1] == '1':
                cell.zeroDischargeCap()
            if zeroarray[16] == '1':
                cell.setC1(0)
            if zeroarray[17] == '1':
                cell.setC2(0)
            if zeroarray[18] == '1':
                cell.setC3(0)
            if zeroarray[19] == '1':
                cell.setC4(0)
                                
            incrementarray = '{0:32b}'.format(int(self.increment))[::-1]
            if incrementarray[0] == '1':
                cell.changeCycleIndex(1)
            if incrementarray[1] == '1':
                cell.changeC1(1)
            if incrementarray[2] == '1':
                cell.changeC2(1)
            if incrementarray[3] == '1':
                cell.changeC3(1)
            if incrementarray[4] == '1':
                cell.changeC4(1)
            
            decrementarray = '{0:32b}'.format(int(self.decrement))[::-1]
            if decrementarray[0] == '1':
                cell.changeC1(-1)
            if decrementarray[1] == '1':
                cell.changeC2(-1)
            if decrementarray[2] == '1':
                cell.changeC3(-1)
            if decrementarray[3] == '1':
                cell.changeC4(-1)
                
            cell.logState()
                
            
                
            isTriggered, goTo = self.checkLimits(cell.currentstate)

            if not isTriggered:
                isTriggered = True
                goTo = "Next Step"
            
            return goTo

    def checkLimits(self, currentstate):
        returnBool = False
        returnGoTo = ""
        
        for limit in self.limits:
            isTriggered, goTo = limit.checktrigger(currentstate)
            if isTriggered == True and limit.limitParameter != "PV_CHAN_Step_Time":
                return isTriggered, goTo
            elif isTriggered == True:
                returnBool = isTriggered
                returnGoTo = goTo
                
        return returnBool, returnGoTo
    
    def checkLogLimits(self, currentstate):        
        for limit in self.loglimits:
            isTriggered, goTo = limit.checktrigger(currentstate)
            if isTriggered:
                return True
        return False
        
        
class Limit:
    def __init__(self, limitInfo, formulas):
        self.limitInfo = limitInfo
        self.formulas = formulas
        ops = {
            '<': operator.lt,
            '<=': operator.le,
            '==': operator.eq,
            '!=': operator.ne,
            '>=': operator.ge,
            '>': operator.gt
        }
        
        self.limitParameter = limitInfo['Equation0_szLeft']
        self.limitOperator = ops[limitInfo['Equation0_szCompareSign']]
        
        try:
            self.limitValue = float(limitInfo['Equation0_szRight'])
        except:
            self.limitValue = formulas[limitInfo['Equation0_szRight']].getValue()
        self.targetStep = limitInfo['m_szGotoStep']
        
        print('Limit parameter:', self.limitParameter)
        print('Limit operator:', self.limitOperator)
        print('Limit value:', self.limitValue)
        print('Target step:', self.targetStep)

        
    def update(self):
        try:
            self.limitValue = float(self.limitInfo['Equation0_szRight'])
        except:
            self.limitValue = self.formulas[self.limitInfo['Equation0_szRight']].getValue()


    def checktrigger(self, currentstate):
        isTriggered = False
        goTo = self.targetStep
        
        if self.limitParameter in currentstate.keys():
            if self.limitOperator(currentstate[self.limitParameter],self.limitValue):
                isTriggered = True
                if isTriggered and self.limitParameter == "PV_CHAN_Voltage":
                    currentstate[self.limitParameter] = self.limitValue
        
        return isTriggered, goTo
    
    

        

class Cell:
    def __init__(self, deltatime, cellType, nominalCapacity = 1, SOClength = 20):
        self.SOClength = SOClength
        self.deltatime = deltatime

        self.initState()
        self.log = []
        self.voltageResponse = ResponseFunction(cellType)
        
        self.nominalCapacity = nominalCapacity
        self.currentCapacity = 0
        self.SOCdistribution = np.zeros(SOClength)
        self.SOCdistribution = [0 for i in range(SOClength)]
        self.lastPrint = time.time()
        self.lastLogVoltage = 0
        self.tempSOCdistribution = np.zeros(SOClength)
        self.tempSOCdistribution = [0 for i in range(SOClength)]

                
    def initState(self):
        self.currentstate = {"PV_CHAN_Voltage":0,
                             "PV_CHAN_Current":0,
                             "PV_CHAN_Test_Time":0,
                             "PV_CHAN_Step_Time":0,
                             "PV_CHAN_Cycle_Index":1, 
                             "PV_CHAN_Step_Index":1,
                             "PV_CHAN_Charge_Capacity":0,
                             "PV_CHAN_Discharge_Capacity":0,
                             "TC_Counter1":0,
                             "TC_Counter2":0,
                             "TC_Counter3":0,
                             "TC_Counter4":0,
                             "Internal_Resistance":0,
                             "Current_Capacity":0,
                             "Surface_Capacity":0,
                             "Capacity_Profile":0,
                             "Formula_Values":0,
                             "DV_Time":0,
                             "DV_Voltage":0}
        
    def incrementTime(self):
        self.currentstate["PV_CHAN_Test_Time"] += self.deltatime
        self.currentstate["PV_CHAN_Step_Time"] += self.deltatime
        self.currentstate["DV_Time"] += self.deltatime
        

    def incrementCurrent(self, crate = 'null', current = 'null'):
        if current != 'null':
            # print('')
            # print(current)
            # print(self.nominalCapacity)
            self.crate = current/self.nominalCapacity
            # print(self.crate)
        else:
            self.crate = crate
        self.currentstate["PV_CHAN_Current"] = self.crate*self.nominalCapacity
        self.currentCapacity += -self.crate*self.nominalCapacity*self.deltatime/3600
        self.currentstate["Current_Capacity"] = self.currentCapacity
        self.updateSOCdistribution(self.crate)
        self.currentstate["Surface_Capacity"] = self.SOCdistribution[0]

        if self.crate< 0:
            self.currentstate["PV_CHAN_Discharge_Capacity"] += -self.crate*self.nominalCapacity*self.deltatime/3600
        elif self.crate > 0:
            self.currentstate["PV_CHAN_Charge_Capacity"] += self.crate*self.nominalCapacity*self.deltatime/3600
            
    def updateInternalResistance(self):
        self.currentstate["Internal_Resistance"] = (1 - self.currentCapacity/self.nominalCapacity)*10 + np.random.random()*5
        
    def updateSOCdistribution(self, crate):
        distributionFactor = self.deltatime/10
        for i in range(1,self.SOClength-1):
            self.tempSOCdistribution[i] = self.SOCdistribution[i] * (1-distributionFactor*2) + (self.SOCdistribution[i-1] + self.SOCdistribution[i+1])*distributionFactor


        self.tempSOCdistribution[0] = self.SOCdistribution[0] - crate*self.nominalCapacity*self.deltatime/3600*self.SOClength - (self.SOCdistribution[0] - self.SOCdistribution[1])*distributionFactor
        self.tempSOCdistribution[-1] = self.SOCdistribution[-1] +  (self.SOCdistribution[-2]-self.SOCdistribution[-1])*distributionFactor
        
        self.SOCdistribution = self.tempSOCdistribution
        self.currentstate["Capacity_Profile"] = self.SOCdistribution
        
#    def updateSOCdistribution(self, crate):
#        distributionFactor = self.deltatime/10
#        SOCleft = self.SOCdistribution[:-2]*distributionFactor
#        SOCright = self.SOCdistribution[2:]*distributionFactor
#        
#        self.tempSOCdistribution[1:-1] = self.SOCdistribution[1:-1] * (1-distributionFactor*2) + SOCleft + SOCright
#        self.tempSOCdistribution[0] = self.SOCdistribution[0] - crate*self.nominalCapacity*self.deltatime/3600*self.SOClength - (self.SOCdistribution[0] - self.SOCdistribution[1])*distributionFactor
#        self.tempSOCdistribution[-1] = self.SOCdistribution[-1] +  (self.SOCdistribution[-2]-self.SOCdistribution[-1])*distributionFactor
#        
#        self.SOCdistribution = self.tempSOCdistribution

    def updateCellVoltage(self):
        nominalVoltage = self.voltageResponse.fastSoc2Pot(self.SOCdistribution[0]/self.nominalCapacity)        
        irDrop = self.currentstate["PV_CHAN_Current"]*self.currentstate["Internal_Resistance"]
#        irDrop = 0
        self.currentstate["PV_CHAN_Voltage"] = nominalVoltage + irDrop
        self.currentstate["DV_Voltage"] = abs(self.lastLogVoltage - self.currentstate["PV_CHAN_Voltage"])
        
    
    def zeroChargeCap(self):
        self.currentstate["PV_CHAN_Charge_Capacity"] = 0

    def zeroDischargeCap(self):
        self.currentstate["PV_CHAN_Discharge_Capacity"] = 0
        
    def zeroStepTime(self):
        self.currentstate["PV_CHAN_Step_Time"] = 0
        
        
    def setStepIndex(self, stepindex):
        self.currentstate["PV_CHAN_Step_Index"] = stepindex
        
    def setCycleIndex(self, i):
        self.currentstate["PV_CHAN_Cycle_Index"] = i

    def setC1(self, c1):
        self.currentstate["TC_Counter1"] = c1

    def setC2(self, c2):
        self.currentstate["TC_Counter2"] = c2
    
    def setC3(self, c3):
        self.currentstate["TC_Counter3"] = c3
        
    def setC4(self, c4):
        self.currentstate["TC_Counter4"] = c4
                

    def changeCycleIndex(self, ic):
        print("Cycles done:",self.currentstate["PV_CHAN_Cycle_Index"])
        self.currentstate["PV_CHAN_Cycle_Index"] += ic

    def changeC1(self, c1c):
        self.currentstate["TC_Counter1"] += c1c

    def changeC2(self, c2c):
        self.currentstate["TC_Counter2"] += c2c

    def changeC3(self, c3c):
        self.currentstate["TC_Counter3"] += c3c
        
    def changeC4(self, c4c):
        self.currentstate["TC_Counter4"] += c4c
        
    def logState(self):            
        self.log.append([i for i in self.currentstate.values()])
        self.lastLogVoltage = self.currentstate["PV_CHAN_Voltage"]
        self.currentstate["DV_Time"] = 0
#        pass
        





# def run():
#     schedule = Schedule()
#     schedule.openSchedule(schedule_filename)
#     schedule.buildSchedule()
    
#     tester = Tester()
#     tester.setSchedule(schedule_filename)
#     tester.buildCell(0.001, 1.000, deltatime = deltaTime, cellType = cellType, SOClength = SOClength)
#     tester.runTest()
#     tester.prepareOutput()
#     tester.plotOverview()
#     tester.saveOverview(pathlib.Path("test_schedules/output") / (schedule_name[:-4] + ".png"))


# performance_run = False

# if performance_run:
#     import cProfile
#     import pstats
    
#     pr = cProfile.Profile()
#     pr.run('run()')
#     pr.dump_stats('output.prof')
    
#     log_path = pathlib.Path("test_schedules\logs")
#     log_filename = schedule_path / "log_" + time.strftime('%Y%m%d-%H%M%S') + ".txt"
#     stream = open(log_filename, 'w')
#     ps = pstats.Stats('output.prof', stream=stream).sort_stats('cumulative')
#     ps.print_stats()
#     stream.close()
    
# else:
#     schedule = Schedule()
#     schedule.openSchedule(schedule_filename)
#     schedule.buildSchedule()
    
#     tester = Tester()
#     tester.setSchedule(schedule_filename)
#     tester.buildCell(0.001, 1.000, deltatime = deltaTime, cellType = cellType, SOClength = SOClength)
#     tester.runTest()
#     tester.prepareOutput()
#     tester.plotOverview()
#     tester.saveOverview(pathlib.Path("test_schedules/output") / (schedule_name[:-4] + ".png"))








