import sys
from abc import ABC, abstractmethod

class Solver(ABC):
    
    def __init__(self,data_instance,printers_upperbound=None):
        self.data_instance=data_instance
        self.M=sys.maxsize
        if printers_upperbound is None:
            self._smart_upperbound()
        else:
            self.printers_upperbound=printers_upperbound

    @abstractmethod
    def _get_output(self):
        pass
    @abstractmethod
    def solve(self):
        pass
    @abstractmethod
    def _model_generator(self):
        pass

    def get_model(self):
        return self.model

    #Find the smart upperbound defined in the paper
    def _smart_upperbound(self):
        max_num_of_printers=0
        for scenario in range(self.data_instance.S):
            num_of_printers=1
            time_counter=self.data_instance.T;
            if time_counter==0:
                self.printers_upperbound=1
                return 
            for item in range(self.data_instance.N):
                if item in self.data_instance.N_p:
                    total_items=self.data_instance.demand[scenario][item]
                    while total_items>0:
                        num_of_items=min(int(time_counter/self.data_instance.t[item]),total_items)
                        if num_of_items>0:
                            time_counter=time_counter-num_of_items*self.data_instance.t[item]
                            total_items=total_items-num_of_items
                        if num_of_items==0:
                            num_of_printers=num_of_printers+1
                            time_counter=self.data_instance.T
            if (num_of_printers>max_num_of_printers):
                max_num_of_printers=num_of_printers;
        # If we cannot bring any printers,there will be no variables P[scenario][printer][item] and so a lot of constraints would change.
        # So,in addition to the paper formulation and in order to keep the code cleaner, the value 1 is taken as minimum if one of the 
        # other values is 0. This doesn't affect the result (due to constraint (12)) but just slows the solver in this particular case.
        self.printers_upperbound=max(min(max_num_of_printers,sys.maxsize if self.data_instance.w_p==0 else int(self.data_instance.W/self.data_instance.w_p),sys.maxsize if self.data_instance.v_p==0 else int(self.data_instance.V/self.data_instance.v_p)),1)

    def print_solution(self):
        output=self._get_output()
        data= self.data_instance
        solution=output["Solution"]
        obj_value=output["ObjValue"]
        print("-------------------------- Solution --------------------------")
        print("Items to take: "+str(["Item "+str(a)+" (x"+str(solution["a"][a])+")" for a in range(data.N)]))
        print("Units of printing material to take: "+ str(solution["a_b"]))
        print("Number of printers to take: "+  str(sum( [  solution["y"][i] for i in range(self.printers_upperbound)]) ))
        print("Total revenue gained: "+ str(obj_value))
        if sum( [  solution["y"][i]  for i in range(self.printers_upperbound)])>0:
            print("----------------- Scenarios -----------------")
            for scenario in range(data.S):
                print("Scenario "+str(scenario)+" -------")
                for printer in range(self.printers_upperbound):
                    if solution["y"][printer]==1:
                        print("Printer number "+str(printer)+ " has to print "+str([ "Item "+str(item) +" (x"+str(solution["p"][scenario][printer][item])+")" for item in range(len(data.N_p))]))
            print("--------------------------------------------------------------")
        return 