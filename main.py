from ortools.linear_solver import pywraplp

class DayPeriod:
    def __init__(self, beginHour, endHour, demand):
        self.beginHour = beginHour
        self.endHour = endHour
        self.demand = demand

class Instance:
    def __init__(self, filepath):
        self.instancePath = filepath
        self.numFactoryTypes = 0
        self.factoriesPerType = []
        self.turnOnCostPerType = []
        self.minProdPerType = []
        self.maxProdPerType = []
        self.minProdCostPerType = []
        self.aditionalProdCostPerType = []
        self.numDayPeriods = 0
        self.dayPeriods = []

    def readInstanceFromFile(self):
        instanceFile = open(self.instancePath, "r")

        self.numFactoryTypes = int(instanceFile.readline())
        for _ in range(self.numFactoryTypes):
            self.factoriesPerType.append(int(instanceFile.readline().split()[1]))
        for _ in range(self.numFactoryTypes):
            self.turnOnCostPerType.append(int(instanceFile.readline().split()[1]))
        for _ in range(self.numFactoryTypes):
            self.minProdPerType.append(int(instanceFile.readline().split()[1]))
        for _ in range(self.numFactoryTypes):
            self.maxProdPerType.append(int(instanceFile.readline().split()[1]))
        for _ in range(self.numFactoryTypes):
            self.minProdCostPerType.append(int(instanceFile.readline().split()[1]))
        for _ in range(self.numFactoryTypes):
            self.aditionalProdCostPerType.append(int(instanceFile.readline().split()[1]))
        self.numDayPeriods = int(instanceFile.readline())
        for _ in range(self.numDayPeriods):
            dayPeriodInfo = instanceFile.readline().split()
            self.dayPeriods.append(DayPeriod(int(dayPeriodInfo[0]), int(dayPeriodInfo[1]), int(dayPeriodInfo[2])))
        
        instanceFile.close()
        
    def printInstanceInfo(self):
        print(f'Tipos de usinas: {self.numFactoryTypes}')
        for i in range(self.numFactoryTypes):
            print(f'Usinas do tipo {i}: {self.factoriesPerType[i]}')
        for i in range(self.numFactoryTypes):
            print(f'Custo de ligação do tipo {i}: {self.turnOnCostPerType[i]}')
        for i in range(self.numFactoryTypes):
            print(f'Produção mínima do tipo {i}: {self.minProdPerType[i]}')
        for i in range(self.numFactoryTypes):
            print(f'Produção máxima do tipo {i}: {self.maxProdPerType[i]}')
        for i in range(self.numFactoryTypes):
            print(f'Custo de de produção mínima do tipo {i}: {self.minProdCostPerType[i]}')
        for i in range(self.numFactoryTypes):
            print(f'Custo de de produção adicional do tipo {i}: {self.aditionalProdCostPerType[i]}')
        print(f'Períodos de um dia: {self.numDayPeriods}')
        for i in range(self.numDayPeriods):
            print(f'Período {i}: Hora de início: {self.dayPeriods[i].beginHour}, Hora de encerramento: {self.dayPeriods[i].endHour}, Demanda: {self.dayPeriods[i].demand}')

class Model:
    def __init__(self, instance, solver):
        self.instance = instance
        self.solver = solver
        self.x = []
        self.y = []
        self.q = []

    def createModelVarables(self):
        # creating X, Y, Q variables
        for i in range(self.instance.numFactoryTypes):
            self.x.append([[None]] * self.instance.factoriesPerType[i])
            self.y.append([[None]] * self.instance.factoriesPerType[i])
            self.q.append([[None]] * self.instance.factoriesPerType[i])
            for j in range(self.instance.factoriesPerType[i]):
                self.x[i][j] = [None] * self.instance.numDayPeriods
                self.y[i][j] = [None] * self.instance.numDayPeriods
                self.q[i][j] = [None] * self.instance.numDayPeriods
                for k in range(self.instance.numDayPeriods):
                    self.x[i][j][k] = self.solver.BoolVar(f'x{i}{j}{k}')
                    self.y[i][j][k] = self.solver.BoolVar(f'y{i}{j}{k}')
                    self.q[i][j][k] = self.solver.IntVar(0, self.solver.infinity(), f'q{i}{j}{k}')
    
    def setConstraints(self):
        #set demand constraint
        for k in range(self.instance.numDayPeriods):
            hk = self.instance.dayPeriods[k].endHour - self.instance.dayPeriods[k].beginHour
            demandConstraint = self.solver.Constraint(self.instance.dayPeriods[k].demand, self.solver.infinity(), f'demand_{k}')
            for i in range(self.instance.numFactoryTypes):
                for j in range(self.instance.factoriesPerType[i]):
                    demandConstraint.SetCoefficient(self.q[i][j][k], hk)
                    demandConstraint.SetCoefficient(self.x[i][j][k], hk*self.instance.minProdPerType[i])

        #set max production constraint
        for i in range(self.instance.numFactoryTypes):
            for j in range(self.instance.factoriesPerType[i]):
                for k in range(self.instance.numDayPeriods):
                    maxProdConstraint = self.solver.Constraint(-self.solver.infinity(), 0, f'max_prod{i}{j}{k}')
                    maxProdConstraint.SetCoefficient(self.q[i][j][k], 1)
                    maxProdConstraint.SetCoefficient(self.x[i][j][k], self.instance.minProdPerType[i] -self.instance.maxProdPerType[i])

        #set turnon constraint
        for i in range(self.instance.numFactoryTypes):
            for j in range(self.instance.factoriesPerType[i]):
                for k in range(self.instance.numDayPeriods-1):
                    turnOnConstraint = self.solver.Constraint(0, self.solver.infinity(), f'turnon{i}{j}{k}')
                    turnOnConstraint.SetCoefficient(self.x[i][j][k], 1)
                    turnOnConstraint.SetCoefficient(self.y[i][j][k+1], 1)
                    turnOnConstraint.SetCoefficient(self.x[i][j][k+1], -1)

        #set circularity constraint
        for i in range(self.instance.numFactoryTypes):
            for j in range(self.instance.factoriesPerType[i]):
                circularityConstraint = self.solver.Constraint(0, self.solver.infinity(), f'circ{i}{j}1')
                circularityConstraint.SetCoefficient(self.y[i][j][0], 1)
                circularityConstraint.SetCoefficient(self.x[i][j][0], -1)
    
    def solve(self):
        objetctive = self.solver.Objective()
        for i in range(self.instance.numFactoryTypes):
            for j in range(self.instance.factoriesPerType[i]):
                for k in range(self.instance.numDayPeriods):
                    objetctive.SetCoefficient(self.x[i][j][k], self.instance.minProdCostPerType[i])
                    objetctive.SetCoefficient(self.q[i][j][k], self.instance.aditionalProdCostPerType[i])
                    objetctive.SetCoefficient(self.y[i][j][k], self.instance.turnOnCostPerType[i])
        
        objetctive.SetMinimization()
        
        status = self.solver.Solve()
        print('Number of variables =', self.solver.NumVariables())
        print('Number of variables =', self.solver.NumConstraints())
        if status == self.solver.OPTIMAL:
            print('Solution:')
            print('Objective value =', self.solver.Objective().Value())
        else:
            print('The problem does not have an optimal solution.')

    def printSolution(self):
        # for i in range(self.instance.numFactoryTypes):
        #     print(f'usinas do tipo {i}:')
        #     for j in range(self.instance.factoriesPerType[i]):
        #         for k in range(self.instance.numDayPeriods):
        #             if self.y[i][j][k].solution_value():
        #                 print(f'usina {j} foi ligada no período {k}')
        #             if self.x[i][j][k].solution_value():
        #                 print(f'usina {j} estava ligada no período {k}')
        #                 print(f'usina {j} no período {k} produziu {self.q[i][j][k].solution_value() + self.instance.minProdPerType[i]}')
        
        print("\n ************** UNIDADES LIGADAS POR PERÍODO\n")
        for k in range(self.instance.numDayPeriods):
            print(f'\nPeríodo {k}:\n')
            usinas = [0] * self.instance.numFactoryTypes
            for i in range(self.instance.numFactoryTypes):
                for j in range(self.instance.factoriesPerType[i]):
                    if self.x[i][j][k].solution_value():
                        usinas[i] += 1
            for idx in range(len(usinas)):
                print(f'Foram utilizadas {usinas[idx]} usinas do tipo {idx}')

        print("\n ************** PRODUÇÃO POR PERÍODO\n")
        for k in range(self.instance.numDayPeriods):
            print(f'Período {k}:\n')
            for i in range(self.instance.numFactoryTypes):
                print(f'Tipo {i}:\n')
                for j in range(self.instance.factoriesPerType[i]):
                    if self.x[i][j][k].solution_value():
                        print(f'Unidade {j} produziu: {self.q[i][j][k].solution_value()+self.instance.minProdPerType[i]}\n')
                print("--------------------------------------------------")
            print("\n##################################################")

        print("\n ************** CUSTO POR TIPO\n")
        for i in range(self.instance.numFactoryTypes):
            minCost = 0
            adtCost = 0
            turnOnCost = 0
            print(f'Tipo {i}:\n')
            for j in range(self.instance.factoriesPerType[i]):
                for k in range(self.instance.numDayPeriods):
                    if self.x[i][j][k].solution_value():
                        minCost += self.instance.minProdCostPerType[i]
                        adtCost += self.q[i][j][k].solution_value()*self.instance.aditionalProdCostPerType[i]
                    if self.y[i][j][k].solution_value():
                        turnOnCost += self.instance.turnOnCostPerType[i]
            print(f'Custo mínimo: {minCost}')
            print(f'Custo adicional: {adtCost}')
            print(f'Custo de Ligação: {turnOnCost}')
            print("##################################################\n")
    def printModelAsLP(self):
        print(self.solver.ExportModelAsLpFormat(False))

solver = pywraplp.Solver.CreateSolver('SCIP')
instancia = Instance("./teste.txt")
instancia.readInstanceFromFile()
"""
debug helper
instancia.printInstanceInfo()
"""
modelo = Model(instancia, solver)
modelo.createModelVarables()
modelo.setConstraints()
modelo.solve()
modelo.printSolution()
# modelo.printModelAsLP()