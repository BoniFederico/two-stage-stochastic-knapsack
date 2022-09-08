# Two-stage-stochastic-knapsack
In this repository the two-stage stochastic 3D-printer knapsack problem TSS-3DKP is implemented for the course of Mathematical Optimisation of the University of Trieste. The work in this repository refers to the following paper:

<blockquote><br><a href="https://www.sciencedirect.com/science/article/pii/S0305054821001337" > Using 3D-printing in disaster response: The two-stage stochastic 3D-printing knapsack problem</a>
<br> <br> </blockquote>

<hr>

## 1. Overview

### 1.1 Paper work

In the cited paper the TSS3DKP problem is presented as a two-stage stochastic problem. The equivalent deterministic problem is then presented (using a smart upperbound on the number of printers) that can be implemented with standard solvers available on the market. Then some analyses are carried out; these analyses try to answer the following questions:
- When is it convenient to bring 3D printers to disaster areas?
- What is the added value of bringing 3D printers compared to not bringing them?

### 1.2 Current project

In this project the formulation of the deterministic equivalent for the TSS3DKP is implemented and all the analyses carried out in the paper are repeated. The model is implemented with both the Gurobi and Xpress Python libraries. However, due to the limitations of the free Xpress license, all analyses are performed with Gurobi.
In addition to the analyses of the paper, other analyses and a scalability analysis are carried out.

### 1.3 Notebooks

The project is divided in 2 Python Notebook:
- 1_paper_results: contain an example of problem instance and all the analyses of the paper.
- 2_other_results: contain other analyses and the scalability analyses.

The full execution of the 2 notebooks requires a lot of hours (>24h). In order to allow the execution of the 2 notebooks, the code is implemented in such a way that:
- If no datasets are present in the "dataset"* folder in the root directory, datasets will be generated.
- If datasets are present in the "dataset"* folder in the root directory, that datasets will be used.

- If results of the analyses are not present in the "results"* folder in the root directory, analyses will be performed (>24h).
- If results of the analyses are present in the "results"* folder in the root directory, tables and figures will be generated using that results in a few seconds.

<i>(*) results and dataset folder are available in this <a href="https://drive.google.com/drive/folders/1mZYQlqCXZ9uizp6uj6-Q1zVMeWiyROXo?usp=sharing">Google Folder</a>. These two folder must be added to the root directory of the project. </i>

#### 1.3.1 Additional notebook
In the other notebooks all the instances of the problem have been generated using the class Data. For simplicity, datasets have been stored using the Python module called Pickle, a module that allow us to store complex objects by serializing and saving them in binary files. Unfortunately this workflow for datasets persistency doesn't allow us to have proprieties such as:
- Openess of the format
- Human readability
- Portability

Considering this fact, the code for migrate a pickle-like dataset to json is provided in another notebook called "3_datasets_migration". By executing that notebook,  json datasets from the pickle ones are generated.
## 2. Modules 
### 2.1 Module managers

#### 2.1.1 class Data

In the manager module the Python class "Data" is implemented. Instances of this class represent instances of the TSS3DKP integer linear programming problem. Instances are generated using the distributions presented in section 4.2.1 of the paper. When provided, the specified parameters are used. The class contain the following methods:
- __instance_generator: generate the instance from the distributions
- set_only_one_scenario: transform the current instance in an instance with only one specified scenario.
- set_only_expected_scenario: transform the current instance in an instance with only one scenario where the demand of that scenario is the expected demand of all scenarios.
- force_no_printer_solutions: set the weight of the printer higher then the knapsack weight capacity.
- get_instance_as_dict: return the instance values as a Python dictionary.
- print_instance: print the instance

In addition, the class contains an inner class called Correlation. This class has a method called get_distribution that generate weights/revenues in accord to the correlation classes defined in <a href="https://www.sciencedirect.com/science/article/pii/S030505480400036X"> Where are the hard knapsack problems?</a>.

### 2.1 Module solvers

#### 2.1.1 class Solver
In the solvers module the Python class "Solver" is implemented. It is an abstract class that models a generic solver that has to solve the problem. The abstract methods that have to be implemented are:
- _get_output: has to provide the output solution as a dictionary.
- solve: has to solve the model and return the output of _get_output method.
- _model_generator: has to implement the model and save the solver object as "self.model".
- get_model: has to return the solver object.

In addition two method of the class are not abstract and are in common to all the Solver class instances:

- _smart_upperbound: has to compute the smart upperbound defined in section 4.1 of the paper.
- print_solution: print the current solution if there is any.

#### 2.1.1 class GurobiSolver

The class GurobiSolver is a Python class that extend the class "Solver". The class implements the formulation of the problem using the Gurobi Python library. In addition to the abstract methods that must be implemented the following methods are present:
- wait_and_see_obj_value: return the value of the Wait & See solution*
- EEVS_obj_value: return the value of the EEVS solution*
- __cut_counter: method that count the number of cutting planes of the Branch & Cut alghoritm.

(*) <i> For further informations check <a href="https://books.google.it/books?id=Vp0Bp8kjPxUC&lr=&hl=it&source=gbs_navlinks_s">Introduction to stochastic programming</a>, page 44.</i>

#### 2.1.2 class XpressSolver

The class XpressSolver is a Python class that extend the class "Solver". The class implements the formulation of the problem using the Xpress Python library.

### 2.3 Module utils

Contain some usefull methods such as:
- from_dict_to_csv
- from_dataframe_to_table
- from_list_to_csv
- from_csv_to_list
