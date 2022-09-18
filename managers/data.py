import numpy as np
import random
import math
import time
# ------------------------------------------------- Data class -------------------------------------------------
#  
# This class, given all the parameters listed before the init method, will build an instance for the
# TSS-3DKP problem defined in https://www.sciencedirect.com/science/article/pii/S0305054821001337 .
# Default parameters are the ones defined in the section "4.2.1 Instance Generation" of the paper.
#
# -- Correlation classes --
# The inner class "Correlation" implements the correlation classes defined in "3. Computational experiments"
# of https://www.sciencedirect.com/science/article/pii/S030505480400036X . In accord to the first paper,
# these classes are used to define the distributions of weights and revenues of all the items. The default 
# class used is the uncorrelated one, since (as per the paper) it considers many different items for which
# the weight, volume, and rewards vary heavily and can be realistic for disaster response missions.
#
# --------------------------------------------------------------------------------------------------------------

class Data:
 
  # N: Number of items
  # D: Upper limit to the demand
  # S: Number of scenarios
  # data_range_R: weights and revenues will be generated in [0,data_range_R]
  # w_p: weight of a 3D printer
  # v_p: volume of a 3D printer
  # alpha: quality factor of printed items
  # w_b: weight of a unit of printing material
  # v_b: volume of a unit of printing material
  # N_p: Number of items printable among all the others

  # correlation: can be one of the following attribute of the Correlation inner class: 
  #             [uncorrelated, weakly, strongly, inverse, almost, subset, similar]

  def __init__(self,N, D, S,data_range_R=1000, w_p=5000,v_p=5000,alpha=0.8,w_b=1,v_b=1,N_p=None,correlation=None):
      self.N, self.D,self.S= (N,D,S)
      self.data_range_R=data_range_R
      self.w_p,self.v_p,self.alpha,self.w_b,self.v_b= (w_p,v_p,alpha,w_b,v_b)
      self.__instance_generator(N,D,S,data_range_R,N_p if N_p is not None else N,self.Correlation.uncorrelated if correlation is None else correlation)
 
  # w: vector of item weights
  # v: vector of item revenues
  # t: vector of item printing times
  # m: vector of number of printing material necessary to build items
  # N_p: vector of printable items among all items
  # demand: matrix of demands per scenario
  # p: vector of probability of each scenario
  # T: total printing time for each printer
  # V: total volume of the knapsack
    
  def __instance_generator(self,N,D,S,data_range_R,N_p,correlation):
    self.w,self.r=self.Correlation.get_distributions(correlation,data_range_R,N)
    self.v=np.array(np.round((np.random.rand(N)*(5-0.2)+0.2)*self.w),dtype="int")
    self.t=np.array(np.ceil(np.random.rand(N)*10),dtype="int")
    self.m=np.array(np.round((np.random.rand(N)*(0.9-0.5)+0.5)*np.minimum(self.w,self.v)),dtype="int")
    self.N_p=sorted(random.sample(list(range(N)),min(N,N_p))) 
    max_demand_per_item=np.array(np.ceil(np.random.rand(N)*(D)))
    self.demand=np.array(np.ceil(np.random.rand(S,N)*(max_demand_per_item+1)-1),dtype="int")
    self.q=np.array((1/S)*np.ones(S))

    self.T=int(np.round((np.random.rand()*(1-0.2)+0.2)*np.sum(np.dot(self.demand,self.t)*self.q)))
    self.W=int(np.round((np.random.rand()*(1-0.5)+0.5)*np.sum(np.dot(self.demand,self.w)*self.q)))
    self.V=int(np.round((np.random.rand()*(2-0.5)+0.5)*self.W))

  def set_only_one_scenario(self,scenario):
    if scenario not in range(self.S):
        return None
    self.demand=np.array([self.demand[scenario]])
    self.q=np.array([1])
    self.S=1
  def force_no_printer_solutions(self):
    self.w_p=self.W+1
  def set_only_expected_scenario(self):
    self.demand=np.array([[np.sum([self.demand[scenario][item]*self.q[scenario] for scenario in range(self.S)]) for item in range(self.N)]])
    self.q=np.array([1])
    self.S=1

  def get_instance_as_dict(self):
        instance={
          "N":self.N, "D":self.D, "S":self.S, "data_range_R":self.data_range_R, "w_p":self.w_p,
          "v_p":self.v_p, "alpha":self.alpha, "w_b":self.w_b, "v_b":self.v_b, "w":self.w.tolist(),
          "r":self.r.tolist(), "v":self.v.tolist(), "t":self.t.tolist(), "m":self.m.tolist(),
          "N_p":self.N_p, "demand":self.demand.tolist(), "q":self.q.tolist(),  "T":self.T,
          "W":self.W,  "V":self.V
        }
        return instance

  def print_instance(self):
    print("-------------------------- Data Instance --------------------------")
    print("----------------- Items -----------------")
    for item in range(self.N):
      print ("Item "+str(item)+": weight ("+str(self.w[item])+"), volume ("+str(self.v[item]) +
          "), revenue ("+str(self.r[item]) +"), printing units ("+str(self.m[item])+
          "), printing time ("+str(self.t[item])+")" )
    print("")
    print("Printable items are: " + str([item for item in self.N_p]))
    print("")
    print("Knapsack total weight: "+ str(self.W)+", Knapsack total volume: "+ str(self.V))

    print("Printer total time: "+ str(self.T))
    print("Printer weight: "+ str(self.w_p)+", Printer volume: "+ str(self.v_p))
    print("Printing unit weight: "+ str(self.w_b)+", Printing unit volume: "+ str(self.v_b))
    print("")
    print("----------------- Demands -----------------")
    for scenario in range(self.S):
          print("Scenario "+str(scenario)+" demand: "+str(["Item "+str(item)+" (x"+str(self.demand[scenario][item])+")" for item in range(self.N)]))
    print("-------------------------------------------------------------------")
  
  #Class that implement the correlation classes of weights and revenues
  class Correlation:
        
    uncorrelated="Uncorrelated"
    weakly="Weakly_correlated"
    strongly="Strongly_correlated"
    inverse="Inverse_strongly_correlated"
    almost="Almost_strongly_correlated"
    subset="Subsets_sum"
    similar="Uncorrelated_instances_with_similar_weights"
    circle="Circle"
    multiple="Multiple_strongly_correlated"
    ceiling="Profit_ceiling"
    spanner="Uncorrelated_spanner"

    def get_distributions(type,R,N):
      weights, revenues= [],[]
      match type:
        case Data.Correlation.uncorrelated:
          weights= np.array(np.ceil(np.random.rand(N)*(R)),dtype="int")
          revenues= np.array(np.ceil(np.random.rand(N)*(R)),dtype="int")
          
        case Data.Correlation.weakly:
          weights= np.array(np.ceil(np.random.rand(N)*(R)),dtype="int")
          revenues= np.array([int(np.random.rand()*(R/5+1)+weight-(R/10)) for weight in weights],dtype="int")
        
        case Data.Correlation.strongly:
          weights= np.array(np.ceil(np.random.rand(N)*(R)),dtype="int")
          revenues= np.array([int(weight+ (R/10)) for weight in weights],dtype="int")
        case Data.Correlation.inverse:
          revenues= np.array(np.ceil(np.random.rand(N)*(R)),dtype="int")
          weights= np.array([int(revenue+ (R/10)) for revenue in revenues],dtype="int")

        case Data.Correlation.almost:
          weights= np.array(np.ceil(np.random.rand(N)*(R)),dtype="int")
          revenues=np.array([int(np.random.rand()*(R*2/500+1)+weight+R/10-R/500) for weight in weights],dtype="int")

        case Data.Correlation.subset:
          weights= np.array(np.ceil(np.random.rand(N)*(R)),dtype="int")
          revenues= np.array([weight for weight in weights],dtype="int")

        case Data.Correlation.similar:
          weights= np.array(np.ceil(np.random.rand(N)*(100+1)+100000-1),dtype="int")
          revenues= np.array(np.ceil(np.random.rand(N)*(1000)),dtype="int")
        case Data.Correlation.circle:
          weights= np.array(np.ceil(np.random.rand(N)*R),dtype="int")
          revenues= np.array([(2/3)*math.sqrt(4*(R**2)-(w-2*R)**2) for w in weights])
        case Data.Correlation.multiple:
          k_1,k_2,d=3*R/10,2*R/10,10
          weights= np.array(np.ceil(np.random.rand(N)*R),dtype="int")
          revenues=np.array([w+(k_1 if w%d==0 else k_2) for w in weights])
        case Data.Correlation.ceiling:
          weights= np.array(np.ceil(np.random.rand(N)*R),dtype="int")
          revenues=np.array([5*np.ceil(w/5) for w in weights])
        case Data.Correlation.spanner:
          v,m=2,10
          weights= np.ceil(2*np.array(np.ceil(np.random.rand(v)*(R)),dtype="int")/m)
          revenues= np.ceil(2*np.array(np.ceil(np.random.rand(v)*(R)),dtype="int")/m)
          weights_new=list()
          revenues_new=list()
          for n in range(N):
              r=int(np.random.rand()*v)
              a=int(np.random.rand()*m)+1             
              weights_new.append(weights[r]*a)
              revenues_new.append(revenues[r]*a)
          weights=np.array(weights_new)
          revenues=np.array(revenues_new)
                
      return weights, revenues