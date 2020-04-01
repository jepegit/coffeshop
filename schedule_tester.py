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


#schedule_filename = r"test_schedules\1_Standard_3cyc_C20R3-C50R4lith_30cyc_C4R3.sdu"
schedule_filename = r"test_schedules\6h_rest-3cyc_C20R4-1000cyc_GITT_C2_R4.sdu"
#schedule_filename = r"test_schedules\Full_cell_Si_NMC_MR_CEF.sdu"

cellType = 'half_cell'
#cellType = 'full_cell'


class ResponseFunction:
    
    def __init__(self, cellType = 'half_cell'):        
        self.func = 'undefined'
        self.initPot2Soc()
        self.initFastSoc2Pot()
        self.cellType = cellType
    
    def _directSoc2Pot(self, SOC):
        pot = 0.0005/SOC -4.76*np.power(SOC,6) + 9.34*np.power(SOC,5) - 1.8*np.power(SOC,4) - 7.13*np.power(SOC,3) + 5.8*np.power(SOC,2) - 1.94*SOC + 0.82 + (-(0.2/(1.0001-np.power(SOC,1000))))
        return  pot.clip(0.0, 3.0)

    def initPot2Soc(self):
#        x = [i*1./100000 for i in range(1,100001)]
        x = np.linspace(1., 100000., 100000.) / 100000
        y = self._directSoc2Pot(x)
        self.func = interp1d(x, y)
    
    def initFastSoc2Pot(self):
        x = np.linspace(1., 100000., 100000.) / 100000
        self.fastSoc2PotArray = self._directSoc2Pot(x)
        
    def pot2soc(self, POT):
        return self.func(POT)
    
    def fastSoc2Pot(self, SOC):
        if self.cellType == 'full_cell':
            SOC = -SOC        
        
        if SOC <= 0:
            SOC = 1./100000
        elif SOC >= 1:
            SOC = 1.-1./100000

        returnValue = self.fastSoc2PotArray[int(SOC*100000)]
        
        if returnValue > 3:
            returnValue = 3
        elif returnValue < 0:
            returnValue = 0
            
        if self.cellType == 'full_cell':
            return 4.2-returnValue
        else:
            return returnValue
        
    

class Tester:
    def __init__(self):
        self.schedule = Schedule()

        
    def setSchedule(self, filename):
        self.schedule.openSchedule(filename)
        self.schedule.buildSchedule()
        
    def buildCell(self, mass, specific_capacity, deltatime = 2, cellType = 'half_cell'):
        self.cell = Cell(deltatime, cellType, mass*specific_capacity)

    def runTest(self):
        self.schedule.runCell(self.cell)
        
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
        


class Schedule:
    def __init__(self):
        self.steps = []
        self.formulas = dict()
        
    def openSchedule(self, filename):
        f = open(filename)
        self.stepinfotable = []
        self.formulainfolist = []
        level = 0
        
        for line in f.readlines():
            p = re.match(r'^\[Schedule_Step([0-9]*)_Limit([0-9]*)\]$', line)            
            if p != None:
                level = 'limit'
                self.stepinfotable[-1][1].append(dict())
            
            p = re.match(r'^\[Schedule_Step([0-9]*)\]$', line)            
            if p != None:
                level = 'step'
                self.stepinfotable.append([dict(), []])
                self.stepinfotable[-1][0]["StepIndex"] = int(p.group(1)) + 1
                
            p = re.match(r'^\[Schedule_Formula([0-9]*)\]$', line)            
            if p != None:
                level = 'formula'
                self.formulainfolist.append(dict())
                self.formulainfolist[-1]["FormulaIndex"] = int(p.group(1)) + 1
        
            p = re.match(r'^([^=\[]*)=(.*)$', line)
            if p != None:
                p = re.match(r'^([^=]*)=(.*)$', line)
                key = p.group(1)
                value = p.group(2)

                if level == 'step':
                    self.stepinfotable[-1][0][key] = value
                elif level == 'limit':
                    self.stepinfotable[-1][1][-1][key] = value
                elif level == 'formula':
                    self.formulainfolist[-1][key] = value
                    
        f.close()
        
    def buildSchedule(self):
        for formulaInfo in self.formulainfolist:
            self.formulas[formulaInfo['m_szLabel']] = Formula(formulaInfo)
            
        for stepinfo in self.stepinfotable:
            self.steps.append(Step(stepinfo, self.formulas))
            
         
       
    def runCell(self, cell):
        currentStep = self.steps[0]
        
        self.updateFormulaValuesAndLimits(cell)
        
        goTo = currentStep.execute(cell)

        while not (goTo == "Next Step" and currentStep is self.steps[-1]):
            if goTo == "Next Step":
                currentStep = self.steps[self.steps.index(currentStep)+1]
            else:
                for step in self.steps:
                    if step.stepName == goTo:
                        currentStep = step
            
            self.updateFormulaValuesAndLimits(cell)
            
            goTo = currentStep.execute(cell)
            
    
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
        
        for variable in ["TC_Counter1", "TC_Counter2", "TC_Counter3", "TC_Counter4", "PC_CHAN_Cycle_Index", "PC_CHAN_Step_Index"]:
            self.expression = self.expression.replace(variable, "currentstate['" + variable + "']")
            
        self.value = 0
                
    def update(self, currentstate):
#        try:
            self.value = eval(self.expression)
#        except:
#            self.value = 0
#            print("Failed formula")
                
    
    def getValue(self):
        return self.value
      


class Step:
    def __init__(self, stepInfo, formulas):
        self.limits = []        
        self.stepInfo = stepInfo
        self.formulas = formulas
        self.stepInfo = stepInfo[0]

        for limitInfo in stepInfo[1]:
            if limitInfo['m_bStepLimit'] == '1':
                self.limits.append(Limit(limitInfo, formulas))
                
        self.stepName = self.stepInfo['m_szLabel']
        self.stepType = self.stepInfo['m_szStepCtrlType']
        self.stepIndex = self.stepInfo["StepIndex"]
        
        if self.stepType == 'C-Rate':
            self.cRate = float(self.stepInfo['m_szCtrlValue'])
        elif self.stepType == 'Rest':
            self.cRate = 0
        elif self.stepType == 'Set Variable(s)':
            self.zero = int(self.stepInfo['m_szCtrlValue'])
            self.increment = int(self.stepInfo['m_szExtCtrlValue1'])
            self.decrement = int(self.stepInfo['m_szExtCtrlValue2'])
            
    def execute(self, cell):

        cell.setStepIndex(self.stepIndex)   
        cell.zeroStepTime()

        if self.stepType == "C-Rate":
#            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)
            running = True        
            while running:
                cell.incrementTime()
                cell.incrementCurrent(self.cRate)
                cell.updateCellVoltage()
                cell.logState()
                isTriggered, goTo = self.checkLimits(cell.currentstate)
                
                if isTriggered:
                    cell.logState()
                    running = False
            
            return goTo
            
        elif self.stepType == "Rest":
#            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)
            running = True
            while running:
                cell.incrementTime()
                cell.incrementCurrent(0)
                cell.updateCellVoltage()
                cell.logState()
                
                isTriggered, goTo = self.checkLimits(cell.currentstate)
                if isTriggered:
                    running = False
            
            return goTo
                
                
        elif self.stepType == "Internal Resistance":
#            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)
            cell.updateInternalResistance()
            return self.limits[0].targetStep
            
                        
        elif self.stepType == 'Set Variable(s)':
#            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)

            zeroarray = '{0:32b}'.format(int(self.zero))[::-1]
            if zeroarray[0] == '1':
                cell.zeroChargeCap()
            if zeroarray[1] == '1':
                cell.zeroDischargeCap()
            if zeroarray[17] == '1':
                cell.setC1(0)
            if zeroarray[18] == '1':
                cell.setC2(0)
            if zeroarray[19] == '1':
                cell.setC3(0)
            if zeroarray[20] == '1':
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
                cell.schangeC4(1)
            
            decrementarray = '{0:32b}'.format(int(self.decrement))[::-1]
            if decrementarray[0] == '1':
                cell.changeC1(-1)
            if decrementarray[1] == '1':
                cell.changeC2(-1)
            if decrementarray[2] == '1':
                cell.changeC3(-1)
            if decrementarray[3] == '1':
                cell.schangeC4(-1)
                
            
                
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

        
    def update(self):
        try:
            self.limitValue = float(self.limitInfo['Equation0_szRight'])
        except:
            self.limitValue = self.formulas[self.limitInfo['Equation0_szRight']].getValue()


    def checktrigger(self, currentstate):
        isTriggered = False
        goTo = self.targetStep
        
        if self.limitOperator(currentstate[self.limitParameter],self.limitValue):
            isTriggered = True
        
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
                             "Formula_Values":0}
        
    def incrementTime(self):
        self.currentstate["PV_CHAN_Test_Time"] += self.deltatime
        self.currentstate["PV_CHAN_Step_Time"] += self.deltatime

    def incrementCurrent(self, crate):
        self.currentstate["PV_CHAN_Current"] = crate*self.nominalCapacity
        self.currentCapacity += -crate*self.nominalCapacity*self.deltatime/3600
        self.currentstate["Current_Capacity"] = self.currentCapacity
        self.updateSOCdistribution(crate)
        self.currentstate["Surface_Capacity"] = self.SOCdistribution[0]

        if crate< 0:
            self.currentstate["PV_CHAN_Discharge_Capacity"] += -crate*self.nominalCapacity*self.deltatime/3600
        elif crate> 0:
            self.currentstate["PV_CHAN_Charge_Capacity"] += crate*self.nominalCapacity*self.deltatime/3600
            
    def updateInternalResistance(self):
        self.currentstate["Internal_Resistance"] = (1 - self.currentCapacity/self.nominalCapacity)*10 + np.random.random()*5
        
    def updateSOCdistribution(self, crate):
        distributionFactor = self.deltatime/10
        for i in range(1,self.SOClength-1):
            self.tempSOCdistribution[i] = self.SOCdistribution[i] * (1-distributionFactor*2) + (self.SOCdistribution[i-1] + self.SOCdistribution[i+1])*distributionFactor


        self.tempSOCdistribution[0] = self.SOCdistribution[0] - crate*self.nominalCapacity*self.deltatime/3600*self.SOClength - (self.SOCdistribution[0] - self.SOCdistribution[1])*distributionFactor
        self.tempSOCdistribution[-1] = self.SOCdistribution[-1] +  (self.SOCdistribution[-2]-self.SOCdistribution[-1])*distributionFactor
        
        self.SOCdistribution = self.tempSOCdistribution
        
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
        self.log.append([*self.currentstate.values()])
#        pass
        





def run():
    schedule = Schedule()
    schedule.openSchedule(schedule_filename)
    schedule.buildSchedule()
    
    tester = Tester()
    tester.setSchedule(schedule_filename)
    tester.buildCell(0.002, 3.579, deltatime = 1.0, cellType = cellType)
    tester.runTest()
    tester.prepareOutput()
    tester.plotOverview()


performance_run = False

if performance_run:
    import cProfile
    import pstats
    
    pr = cProfile.Profile()
    pr.run('run()')
    pr.dump_stats('output.prof')
    
    stream = open(r'test_schedules\log.txt', 'w')
    ps = pstats.Stats('output.prof', stream=stream).sort_stats('cumulative')
    ps.print_stats()
    stream.close()
else:
    schedule = Schedule()
    schedule.openSchedule(schedule_filename)
    schedule.buildSchedule()
    
    tester = Tester()
    tester.setSchedule(schedule_filename)
    tester.buildCell(0.002, 3.579, deltatime = 2.0, cellType = cellType)
    tester.runTest()
    tester.prepareOutput()
    tester.plotOverview()







