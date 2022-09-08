from solvers.solver import Solver
import xpress as xp
import numpy as np

# ---------------------------------------------------------- Solver class -----------------------------------------------------------
# 
# This class implement the TSS-3DKP formulation defined in https://www.sciencedirect.com/science/article/pii/S0305054821001337 
# with Xpress FICO. In order to initialise an object of the class we need to pass an instance of the managers.data.Data class. 
# In addition we can set a maximum execution time with "max_time" (s) and explicit a gap value to limit the MIP solver with "MIPGap".
# 
# -- Parent Class --
#   The class XPressSolver inherit some methods from the abstract class "Solver" (solvers.solver.Solver)
#
# -- Methods --
#  -get_model(): retrieve the instance of the XPress problem
#  -solve(): try to solve the problem and retrieve a dict with the solution. The dict contains the following keys:
#            - StatusCode: Gurobi status code defined in https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html .
#            - Status: Gurobi status relative to the StatusCode.
#            - ObjValue: Value of the Objective Function at the solution.
#            - Solution: Solution found as dict. The dict contains the following keys:
#                        - a: vector of the quantities of the items carried.
#                        - a_b: units of printing materials carried.
#                        - p: matrix [s,p,i] -> Define how many items (i) will be printed by printer (p) in the scenario (s)
#                        - a_s: matrix [s,i] -> Define how many items (i) will be used in scenario (s) (a_s[s,i]=min(a[i],demand[s,i])
#                        - y: binary vector. y[i]=1 if we bring printer (i), else y[i]=0.
#  -print_solution(): print the solution found. Must be called after solve() method.

# ------------------------------------------------------------------------------------------------------------------------------------


class XPressSolver(Solver):
    
    def __init__(self,data_instance,log=False,max_time=None,MIPGap=None,N_p=None):
        Solver.__init__(self,data_instance)
        self._model_generator()
        if not log:
            _=self.model.setControl('outputlog', 0)
        if max_time is not None:
            _=self.model.setControl('MAXTIME',max_time)
        if MIPGap is not None:
            _=self.model.setControl('MIPRELSTOP',MIPGap)
        if N_p is not None:
            self.N_p=N_p

    def get_model(self):
        return self.model

    def solve(self):
        _=self.model.solve()
        return self._get_output()

    def _get_output(self):
        Solution= {
            "a":[ int(self.model.getSolution("a_"+str(i))) for i in range(self.data_instance.N)],  
            "a_b":int(self.model.getSolution("a_b")),
            "p":[[[int(self.model.getSolution("p_"+str(s)+"_"+str(p)+"_"+str(i))) for i in range(len(self.data_instance.N_p))] for p in range(self.printers_upperbound)]for s in range(self.data_instance.S) ],
            "a_s":[[int(self.model.getSolution("a_s_"+str(s)+"_"+str(i)) ) for i in range(self.data_instance.N)] for s in range(self.data_instance.S)],
            "y":[int(self.model.getSolution("y_"+str(p) )) for p in range(self.printers_upperbound)]      
        }      
        #List of status codes can be found in the XPress Optimizer Manual (https://www.fico.com/fico-xpress-optimization/docs/latest/solver/optimizer/HTML/chapter9.html)
        output = {
            "StatusCode":int(self.model.getProbStatus()),
            "Status":self.model.getProbStatusString(),
            "ObjValue":round(float(self.model.getObjVal()),2),
            "Solution": Solution,
            "Printers": Solution["y"].count(1)
        }
        return output

    def _model_generator(self):
        two_stage_stoc_knapsack= xp.problem()
        data= self.data_instance

        #Variables definition 1 stage + Constraint (22)+ Constraint (23)
        A=np.array([xp.var(vartype=xp.integer, name="a_"+str(i)) for i in range(data.N)], dtype=xp.npvar)
        a_b= xp.var(vartype=xp.integer, name="a_b")

        #Variable definition 2 stage + Constraint (24) + Constraint (25):
        P = np.array([[[xp.var(vartype=xp.integer,name="p_"+str(s)+"_"+str(j)+"_"+str(i)) for i in data.N_p]for j in range(self.printers_upperbound)] for s in range(data.S)], dtype=xp.npvar) #P[scenario][printer][item]
        A_s = np.array([[xp.var(vartype=xp.integer,name="a_s_"+str(s)+"_"+str(i)) for i in range(data.N)] for s in range(data.S)], dtype=xp.npvar) #As[scenario][item]
        
        #Variable definition for the equivalent formulation + Constraint(21):
        y=np.array([xp.var(vartype=xp.binary, name="y_"+str(i)) for i in range(self.printers_upperbound)], dtype=xp.npvar)

        two_stage_stoc_knapsack.addVariable(A)
        two_stage_stoc_knapsack.addVariable(a_b)
        two_stage_stoc_knapsack.addVariable(P)
        two_stage_stoc_knapsack.addVariable(y)
        two_stage_stoc_knapsack.addVariable(A_s)

        #Constraint (12)
        two_stage_stoc_knapsack.addConstraint(np.dot(A,data.w)+a_b*data.w_b+xp.Sum(y*data.w_p)<=data.W)
        #Constraint (13)
        two_stage_stoc_knapsack.addConstraint(np.dot(A,data.v)+a_b*data.v_b+xp.Sum(y*data.v_p)<=data.V)
        #Constraint (14)
        two_stage_stoc_knapsack.addConstraint(a_b<=xp.Sum(y*self.M))
        
        for scenario in range(data.S):
            for item in range(data.N): 
                if item not in data.N_p: 
                    #Constraint (15)
                    two_stage_stoc_knapsack.addConstraint(A_s[scenario,item]<=data.demand[scenario,item])
                else: 
                    #Constraint (16)
                    two_stage_stoc_knapsack.addConstraint(A_s[scenario,item]+xp.Sum(np.array(P)[scenario,:,data.N_p.index(item)])<=data.demand[scenario,item])
                #Constraint (17)
                two_stage_stoc_knapsack.addConstraint(A_s[scenario,item]<=A[item]) 
            #Constraint (18)
            m_for_printable=list(filter(lambda item: item is not None, [data.m[indx] if indx in data.N_p else None for indx in range(data.N)]))
            two_stage_stoc_knapsack.addConstraint(xp.Sum(np.array(P)[scenario]*m_for_printable)<=a_b)
            #Constraint (19)
            for printer in range(self.printers_upperbound):
                t_for_printable=list(filter(lambda item: item is not None, [data.t[indx] if indx in data.N_p else None for indx in range(data.N)]))
                two_stage_stoc_knapsack.addConstraint(xp.Sum(np.array(P)[scenario,printer,:]*t_for_printable)<=data.T*y[printer])
        
        #Constraint (20)
        for printer in range(self.printers_upperbound-1):
            two_stage_stoc_knapsack.addConstraint(y[printer+1]<=y[printer])
            
        #Objective function:
        r_for_printable=list(filter(lambda item: item is not None, [data.r[indx] if indx in data.N_p else None for indx in range(data.N)]))
        two_stage_stoc_knapsack.setObjective(xp.Sum([data.q[scenario]*(xp.Sum(A_s[scenario]*data.r)+xp.Sum([xp.Sum(data.alpha*np.array(P)[scenario,printer,:]*r_for_printable)  for printer in range(self.printers_upperbound) ])) for scenario in range(data.S)]),sense= xp.maximize)
        self.model=two_stage_stoc_knapsack