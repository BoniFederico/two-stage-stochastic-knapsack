import gurobipy as gb
import copy
from solvers.solver import Solver

# ---------------------------------------------------------- Solver class -----------------------------------------------------------
# 
# This class implement the TSS-3DKP formulation defined in https://www.sciencedirect.com/science/article/pii/S0305054821001337 
# with Gurobi. In order to initialise an object of the class we need to pass an instance of the managers.data.Data class. 
# In addition we can set a maximum execution time with "max_time" (s) and explicit a gap value to limit the MIP solver with "MIPGap".
# 
# -- Parent Class --
#   The class Gurobi Solver inherit some methods from the abstract class "Solver" (solvers.solver.Solver)
#
# -- Methods --
#  -get_model(): retrieve the instance of the Gurobi problem
#  -solve(): try to solve the problem and retrieve a dict with the solution. The dict contains the following keys:
#            - StatusCode: Gurobi status code defined in https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html .
#            - Status: Gurobi status relative to the StatusCode.
#            - ObjValue: Value of the Objective Function at the solution.
#            - Solutions: Number of solutions found.
#            - Nodes: Number of nodes built by the B&C algorithm during the optimization.
#            - Cuts: Number of cuts performed by the B&C algorithm during the optimization.
#            - Runtime: Total run time of the optimization.
#            - Mipgap: MIPGap value of the solver at the termination of the optimization. 
#            - Solution: Solution found as dict. The dict contains the following keys:
#                        - a: vector of the quantities of the items carried.
#                        - a_b: units of printing materials carried.
#                        - p: matrix [s,p,i] -> Define how many items (i) will be printed by printer (p) in the scenario (s)
#                        - a_s: matrix [s,i] -> Define how many items (i) will be used in scenario (s) (a_s[s,i]=min(a[i],demand[s,i])
#                        - y: binary vector. y[i]=1 if we bring printer (i), else y[i]=0.
#  -print_solution(): print the solution found. Must be called after solve() method.

# ------------------------------------------------------------------------------------------------------------------------------------

class GurobiSolver(Solver):
    def __init__(self,data_instance,max_time=None, log=False, MIPGap=None, printers_upperbound=None):
        
        Solver.__init__(self,data_instance,printers_upperbound)
        self.M=int(min(data_instance.W/data_instance.w_b,data_instance.V/data_instance.v_b)+2)
        self._model_generator()
        if log:
            _=self.model.setParam('OutputFlag',1)  

        if max_time is not None:
            _=self.model.setParam('TimeLimit', max_time)
        if MIPGap is not None:
            _=self.model.setParam('MIPGap',MIPGap)


    def _get_output(self):
        Solution= {
            "a":[ int(self.model.getVarByName("a["+str(i)+"]").X) for i in range(self.data_instance.N)], #self.model.getVarByName('A'),
            "a_b":int(self.model.getVarByName("a_b").X),
            "p":[[[int(self.model.getVarByName("p["+str(s)+","+str(p)+","+str(i)+"]").X) for i in range(len(self.data_instance.N_p))] for p in range(self.printers_upperbound)]for s in range(self.data_instance.S) ],
            "a_s":[[int(self.model.getVarByName("a_s["+str(s)+","+str(i)+"]").X) for i in range(self.data_instance.N)] for s in range(self.data_instance.S)],
            "y":[int(self.model.getVarByName("y["+str(p)+"]").X) for p in range(self.printers_upperbound)]      
        }      
        #From: https://www.gurobi.com/documentation/9.5/refman/optimization_status_codes.html
        Status ={   1: 'LOADED', 2: 'OPTIMAL', 3: 'INFEASIBLE', 4: 'INF_OR_UNBD',
                    5: 'UNBOUNDED', 6: 'CUTOFF', 7: 'ITERATION_LIMIT', 8: 'NODE_LIMIT',
                    9: 'TIME_LIMIT', 10: 'SOLUTION_LIMIT', 11: 'INTERRUPTED', 12: 'NUMERIC', 
                    13: 'SUBOPTIMAL', 14: 'INPROGRESS', 15: 'USER_OBJ_LIMIT'} 
        output = {
            "StatusCode":int(self.model.status),
            "Status":Status[self.model.status],
            "ObjValue":round(float(self.model.ObjVal),2),
            "Solutions":int(self.model.SolCount),
            "Nodes":int(self.model.NodeCount),
            "Cuts":int(self.model._cut_count),
            "Runtime":round(float(self.model.Runtime),2),
            "MIPGap": float('{:0.2e}'.format(float(self.model.MIPGap),2)),
            "Solution": Solution,
            "Printers": Solution["y"].count(1)
        }
        return output
    
    def solve(self):
        self.model._cut_count=0
        _=self.model.optimize(GurobiSolver.__cut_counter)
        return self._get_output()

    def wait_and_see_obj_value(self):
        S=self.data_instance.S
        ws_obj=0
        for scenario in range(S):
            data_instance=copy.deepcopy(self.data_instance)
            data_instance.set_only_one_scenario(scenario)
            ws_obj=ws_obj+GurobiSolver(data_instance, MIPGap=0.001).solve()["ObjValue"]*self.data_instance.q[scenario]
        return ws_obj
    
    def EEVS_obj_value(self,log=False):
        data_instance=copy.deepcopy(self.data_instance)
        data_instance.set_only_expected_scenario()
        solution=GurobiSolver(data_instance, MIPGap=0.001).solve()

        num_of_printers=solution["Printers"]
        a=solution["Solution"]["a"]
        a_b=solution["Solution"]["a_b"]
        second_stage_problem= gb.Model()
        if not log:
            _=second_stage_problem.setParam('OutputFlag',0)
            
        second_stage_problem.modelSense=gb.GRB.MAXIMIZE
        data= self.data_instance
        P=second_stage_problem.addVars([(s,p,i) for s in range(data.S) for p in range(num_of_printers) for i in range(len(data.N_p))],vtype=gb.GRB.INTEGER,name="p")
        A_s=second_stage_problem.addVars([(s,i) for s in range(data.S) for i in range(data.N)],vtype=gb.GRB.INTEGER,name="a_s")

 
        for scenario in range(data.S):
            for item in range(data.N): 
                if item not in data.N_p: 
                    #Constraint (5)
                    second_stage_problem.addConstr(A_s[scenario,item]<=data.demand[scenario,item])
                else: 
                    #Constraint (6)
                    second_stage_problem.addConstr(A_s[scenario,item]+gb.quicksum([P[scenario,p,data.N_p.index(item)] for p in range(num_of_printers)])<=data.demand[scenario,item])
                    
            #Constraint (7)
            for item in range(data.N):
                second_stage_problem.addConstr(A_s[scenario,item]<=a[item])
 
        m_for_printable=list(filter(lambda item: item is not None, [data.m[indx] if indx in data.N_p else None for indx in range(data.N)]))
        t_for_printable=list(filter(lambda item: item is not None, [data.t[indx] if indx in data.N_p else None for indx in range(data.N)]))

        for scenario in range(data.S):
            #Constraint (8)
            second_stage_problem.addConstr(gb.quicksum([gb.quicksum([P[scenario,p,i]*m_for_printable[i] for i in range(len(data.N_p))]) for p in range(num_of_printers)])<=a_b)
            #Constraint (9)
            for printer in range(num_of_printers):
                second_stage_problem.addConstr(gb.quicksum([P[scenario,printer,i]*t_for_printable[i] for i in range(len(data.N_p))])<=data.T)
        
        #Objective Function
        r_for_printable=list(filter(lambda item: item is not None, [data.r[indx] if indx in data.N_p else None for indx in range(data.N)]))
        second_stage_problem.setObjective(gb.quicksum([data.q[s]*(gb.quicksum([A_s[s,i]*data.r[i] for i in range(data.N)])+ gb.quicksum([(gb.quicksum([(data.alpha*P[s,j,i]*r_for_printable[i])  for i in range(len(r_for_printable))])) for j in range(num_of_printers)]))for s in range(data.S)]))

        second_stage_problem.optimize()

        return round(float(second_stage_problem.ObjVal),2)

    def _model_generator(self):
 
        two_stage_stoc_knapsack= gb.Model()
        two_stage_stoc_knapsack.setParam('OutputFlag',0)      
        two_stage_stoc_knapsack.modelSense = gb.GRB.MAXIMIZE
        data= self.data_instance
        #Variables definition 1 stage + Constraint (22)+ Constraint (23)
        A=two_stage_stoc_knapsack.addVars(data.N,vtype=gb.GRB.INTEGER, name='a')
        a_b=two_stage_stoc_knapsack.addVar(vtype=gb.GRB.INTEGER,name="a_b")

        #Variable definition 2 stage + Constraint (24) + Constraint (25):
        P=two_stage_stoc_knapsack.addVars([(s,p,i) for s in range(data.S) for p in range(self.printers_upperbound) for i in range(len(data.N_p))],vtype=gb.GRB.INTEGER,name="p")
        A_s=two_stage_stoc_knapsack.addVars([(s,i) for s in range(data.S) for i in range(data.N)],vtype=gb.GRB.INTEGER,name="a_s")
        
        #Variable definition for the equivalent formulation + Constraint(21):
        y=two_stage_stoc_knapsack.addVars(self.printers_upperbound,vtype=gb.GRB.BINARY,name="y")
        #Constraint (12)
        two_stage_stoc_knapsack.addConstr( gb.quicksum([A[i]*data.w[i] for i in range(data.N)])+a_b*data.w_b+gb.quicksum([y[i]*data.w_p for i in range(self.printers_upperbound)])<=data.W)
        #Constraint (13)
        two_stage_stoc_knapsack.addConstr( gb.quicksum([A[i]*data.v[i] for i in range(data.N)])+a_b*data.v_b+gb.quicksum([y[i]*data.v_p for i in range(self.printers_upperbound)])<=data.V)
        #Constraint (14)
        two_stage_stoc_knapsack.addConstr(a_b<=gb.quicksum([y[j]*self.M for j in range(self.printers_upperbound)]))
 
        for scenario in range(data.S):
            for item in range(data.N): 
                if item not in data.N_p: 
                    #Constraint (15)
                    two_stage_stoc_knapsack.addConstr(A_s[scenario,item]<=data.demand[scenario,item])
                else: 
                    #Constraint (16)
                    two_stage_stoc_knapsack.addConstr(A_s[scenario,item]+gb.quicksum([P[scenario,p,data.N_p.index(item)] for p in range(self.printers_upperbound)])<=data.demand[scenario,item])
                #Constraint (17)
                two_stage_stoc_knapsack.addConstr(A_s[scenario,item]<=A[item]) 
            #Constraint (18)
            m_for_printable=list(filter(lambda item: item is not None, [data.m[indx] if indx in data.N_p else None for indx in range(data.N)]))
            two_stage_stoc_knapsack.addConstr(gb.quicksum([gb.quicksum([P[scenario,p,i]*m_for_printable[i] for i in range(len(data.N_p))]) for p in range(self.printers_upperbound)])<=a_b)
            #Constraint (19)
            for printer in range(self.printers_upperbound):
                t_for_printable=list(filter(lambda item: item is not None, [data.t[indx] if indx in data.N_p else None for indx in range(data.N)]))
                two_stage_stoc_knapsack.addConstr(gb.quicksum([P[scenario,printer,i]*t_for_printable[i] for i in range(len(data.N_p))])<=data.T*y[printer])
        #Constraint (20)
        for printer in range(self.printers_upperbound-1):
            two_stage_stoc_knapsack.addConstr(y[printer+1]<=y[printer])
            
        #Objective function:
        r_for_printable=list(filter(lambda item: item is not None, [data.r[indx] if indx in data.N_p else None for indx in range(data.N)]))
        
        two_stage_stoc_knapsack.setObjective(
            
            gb.quicksum([data.q[s]*
            
            (gb.quicksum([A_s[s,i]*data.r[i] for i in range(data.N)])
            
            + gb.quicksum([(gb.quicksum([(data.alpha*P[s,j,i]*r_for_printable[i]) for i in range(len(r_for_printable))])) 
            
            for j in range(self.printers_upperbound)]))for s in range(data.S)]))

        self.model=two_stage_stoc_knapsack
        
    # Cut counter callback for B&C algorithm. From: https://groups.google.com/g/gurobi/c/cHzpcT-3rPk
    def __cut_counter(model, where):
        cut_names = {'Clique:', 'Cover:', 'Flow cover:', 'Flow path:', 'Gomory:', 'GUB cover:', 'Inf proof:', 'Implied bound:', 'Lazy constraints:', 'Learned:', 'MIR:', 'Mod-K:', 'Network:', 'Projected Implied bound:', 'StrongCG:', 'User:', 'Zero half:'}
        if where == gb.GRB.Callback.MESSAGE:
            # Message callback
            msg = model.cbGet(gb.GRB.Callback.MSG_STRING)
            if any(name in msg for name in cut_names):
                model._cut_count += int(msg.split(':')[1])