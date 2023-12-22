'''
This is a standardized set of conditions used in technoeconomic analysis of chlor iron process conditions.

This model is an update for the sensitivity analysis reported in Noble et al. (2023) 10.26434/chemrxiv-2023-d22xj

We have provided ranges for a number of process assumptions and we hope that readers will critically evaluate the assumptions and test their own scenarios for ore prices, capital costs, energy efficiency, electricity prices, etc...

'''

import pandas as pd

IRR=0.08 #annual basis
lifetime=20 #plant lifetime years
installation=1 #fraction, optional
bop=1 #fraction, optional
INFLATION=0.038 #frac, average U.S. inflation rate from 1960 to 2021
prod_TPD=100 # tonne per day or ~40,000 tpy
base_case_EP = 75
base_case_Cl2P = 150
base_emp = 44

def efficiency_fe(volts, selectivity=1):
    ## calculates efficiency in Wh/g, kWh/kg, MWh/tonne
    eff = volts*3*96485/(3600*55.4)/selectivity
    return eff

def NPV_calc(Iron_Price, Iron_Prod, Cell_Voltage, Electric_Price, CAPACITY=0.98, NaOHCAPACITY=0,Cl2CAPACITY=0.95, FeCAPACITY=0.90,
            electric_price=base_case_EP, iron_ore_price=120, brine_price=1, hcl_price=150, naoh_price=300, cl2_price=base_case_Cl2P,
            PLANTFACTOR=1,replace_rate=7,N_EMPLOYEE=base_emp):
    
    # Reference for Chlor Alkali Plant Costs
    # https://www3.epa.gov/ttn/ecas/docs/eia_ip/chlorine_eia_08-2000.pdf
    # Chloralkali plant (500 t/d), converted from 1990 dollars to 2020 dollars
    plantcost = 111000000*1.98*PLANTFACTOR #2020 dollars
    employees = N_EMPLOYEE # Reference: https://doi.org/10.1016/0921-3449(94)90037-X, 40,000 tpy Zn
    average_salary = 50000 # Assumed salary US Chemical Plant Operator
    annual_labor = average_salary * employees
    cl2_per_tpd = plantcost/500
    tFeptCl2 = 2 / 3 * 55 / 71 # Roughly 50%, so a 50 tpd iron plant produces 100 tpd cl2
    tNaOHptFe = 3*40/55 # Roughly 2.18... 
    tFe2O3ptFe = 1*160/(2*55.4)
    tNaClptFe = (1/0.6)*3*1000/55.4
    
    system_cost = cl2_per_tpd/tFeptCl2*Iron_Prod # $ calculated from fe_tpd sizing
    
    # Other default variables
    # electric_price = 70 #$/MWh
    # iron_ore_price = 120 #$/tonne - https://markets.businessinsider.com/commodities/iron-ore-price
    # brine_price = 1 #$/tonne
    # hcl_price = 150 #$/tonne #https://www.indexbox.io/store/world-hydrogen-chloride-hydrochloric-acid-market-report-analysis-and-forecast-to-2025/
    # naoh_price = 300 #$/tonne #https://www.indexbox.io/blog/caustic-soda-price-per-ton-april-2022/
    # cl2_price = 150 #$/tonne #https://www.indexbox.io/blog/chlorine-price-per-ton-april-2022/
        
    #Assumption for stack replacement costs ~20% of system cost
    stack_cost = 0.20*system_cost
    production = Iron_Prod*1000/24 # production rate (kg/h) from tpd
    
    #Keep voltage drift = 0 for now
    voltage_drift = 0
    
    #Calculate Stack Eff
    stackeff = efficiency_fe(Cell_Voltage) # MWh/tonne
    
    #Timeline
    max_year = 20 #years
    
    #Scheduled cash flow
    CashFlow = pd.DataFrame({'Years':[],'Stack Life':[],'Inflation Year':[],
                            'Stack Eff (MWh/t)':[], 'Sales':[],'Replacement Costs':[],'Operating Costs':[],
                            'Net Cash Flow':[],'Discounted Flow':[]})
    
    ## Initialize variables
    year = [1]
    stacklife = [0]
    inflationyear = [1]
    sales = [0]
    replacement_costs = [0]
    operating_costs = [0]
    net_cash = [-system_cost]
    discounted_cash = [net_cash[-1]/(1+IRR)**year[-1]]

    for x in range(2,max_year+2):
        year.append(x)
        inflationyear.append((1+INFLATION)**x)

        #Iron, Chlorine, NaOH sales
        iron_sale = Iron_Price/1000*production*8760*CAPACITY*FeCAPACITY
        cl2_sale = cl2_price/1000*production/tFeptCl2*8760*CAPACITY*Cl2CAPACITY
        naoh_sale = cl2_price/1000*production*tNaOHptFe*8760*CAPACITY*NaOHCAPACITY
        
        sales.append(iron_sale+cl2_sale+naoh_sale) # [$/kg] * [kg/h] * [h/year] * percent
        sales[-1] = sales[-1]*inflationyear[-1]

        #Stacklife counting
        if stacklife[-1] < replace_rate and year[-1] != max_year: # Don't replace stack in the last year of life
            stacklife.append(stacklife[-1]+1)
        else:
            stacklife.append(1)

        #Maintenance cost are 0.5% system cost per year + stack replacement
        replacement_costs.append(stack_cost*(stacklife[-1]==replace_rate) + 0.005*system_cost)
        replacement_costs[-1] = replacement_costs[-1]*inflationyear[-1]

        #Operating costs are assumed to be dominated by electricity prices and ore prices
        r_prod = production*8760*CAPACITY
        e_expense = Electric_Price/1000*stackeff*r_prod
        w_expense = brine_price/1000*r_prod*tNaClptFe
        fe2o3_expense = iron_ore_price/1000*r_prod*tFe2O3ptFe
        expenses = e_expense+w_expense+fe2o3_expense+annual_labor
        #[$/kWh] * [kWh/kg] * [kg/h] * [h/year] * percent
        operating_costs.append(expenses)
        operating_costs[-1] = operating_costs[-1]*inflationyear[-1]

        #Net cash flow = Sales - replacement - operating costs
        net_cash.append(sales[-1] - operating_costs[-1] - replacement_costs[-1])

        #Discounted cash flow = net cash flow / (1+IRR)^year
        discounted_cash.append(net_cash[-1]/(1+IRR)**year[-1])

    CashFlow['Years'] = year
    CashFlow['Stack Life'] = stacklife
    CashFlow['Inflation Year'] = inflationyear
    CashFlow['Stack Eff (MWh/t)'] = stackeff
    CashFlow['Sales'] = sales
    CashFlow['Replacement Costs'] = replacement_costs
    CashFlow['Operating Costs'] = operating_costs
    CashFlow['Net Cash Flow'] = net_cash
    CashFlow['Discounted Flow'] = discounted_cash

    return sum(CashFlow['Discounted Flow']), CashFlow


def LCOFe(CV=3.2,EP=base_case_EP,FeCap=0.90,NaCap=0,Cl2Cap=0.95,plantfac=1,replace=7, ore=120, plantcap=0.98,var_employee=base_emp, Cl2P = base_case_Cl2P):
    # System function
    low_price = 1
    high_price = 1000
    
    # Measure slope of NPV calculator
    low_val, low_table = NPV_calc(Iron_Price=low_price, Iron_Prod=prod_TPD, 
                                  Cell_Voltage=CV, Electric_Price=EP, 
                                  CAPACITY=plantcap, FeCAPACITY=FeCap, 
                                  NaOHCAPACITY=NaCap, iron_ore_price=ore,
                                 PLANTFACTOR=plantfac,Cl2CAPACITY=Cl2Cap,
                                 replace_rate=replace,N_EMPLOYEE=var_employee,
                                  cl2_price=Cl2P)
    
    high_val, high_table = NPV_calc(Iron_Price=high_price, Iron_Prod=prod_TPD, 
                                    Cell_Voltage=CV, Electric_Price=EP,
                                    CAPACITY=plantcap, FeCAPACITY=FeCap,
                                    NaOHCAPACITY=NaCap, iron_ore_price=ore,
                                     PLANTFACTOR=plantfac,Cl2CAPACITY=Cl2Cap,
                                     replace_rate=replace,N_EMPLOYEE=var_employee,
                                   cl2_price=Cl2P);
    
    # Interpolate to solve for exact LCOX
    slope = (high_price - low_price)/(high_val - low_val)

    return high_price - high_val*slope