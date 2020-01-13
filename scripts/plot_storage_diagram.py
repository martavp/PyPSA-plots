# -*- coding: utf-8 -*-
"""
Script to plot graphically costs and efficiencies of storage technologies

"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

idx = pd.IndexSlice

#from vresutils.costdata import annuity
def annuity(n,r):
    """Calculate the annuity factor for an asset with lifetime n years and
    discount rate of r, e.g. annuity(20,0.05)*20 = 1.6"""

    if isinstance(r, pd.Series):
        return pd.Series(1/n, index=r.index).where(r == 0, r/(1. - 1./(1.+r)**n))
    elif r > 0:
        return r/(1. - 1./(1.+r)**n)
    else:
        return 1/n
    
#set all asset costs and other parameters
costs = pd.read_csv("costs_RE_Invest.csv",index_col=list(range(3))).sort_index()

#correct units to MW and EUR
costs.loc[costs.unit.str.contains("/kW"),"value"]*=1e3
options={}
options['USD2013_to_EUR2013']= 0.7532
costs.loc[costs.unit.str.contains("USD"),"value"]*=options['USD2013_to_EUR2013']

cost_year = 2030

costs = costs.loc[idx[:,cost_year,:],"value"].unstack(level=2).groupby("technology").sum()
options['discountrate']= 0.07 
costs = costs.fillna({"CO2 intensity" : 0,
                          "FOM" : 0,
                          "VOM" : 0,
                          "discount rate" : options['discountrate'],
                          "efficiency" : 1,
                          "fuel" : 0,
                          "investment" : 0,
                          "lifetime" : 25
    })
#fillna is not working properly,discount rate and lifetime are included     
costs['discount rate'].replace(0,options['discountrate'],inplace=True)
costs['lifetime'].replace(0,25,inplace=True)
Nyears=1    
costs["fixed"] = [(annuity(v["lifetime"],v["discount rate"])+v["FOM"]/100.)*v["investment"]*Nyears for i,v in costs.iterrows()]


#%%
eff_tech={}
cost_tech={}

# Ratios energy capacity/power capacity assumed for the different storage
# technologies
n_PHS=12
n_bat=6
n_hyd=7*24
n_CTES=121*24

eff_tech['PHS']=costs['efficiency']['PHS']
cost_tech['PHS']=costs['fixed']['PHS']/(n_PHS*365*costs['efficiency']['PHS'])

eff_tech['battery']=costs['efficiency']['battery inverter']
cost_tech['battery']=(costs['fixed']['battery inverter']+n_bat*costs['fixed']['battery storage'])/(n_bat*365*costs['efficiency']['battery inverter'])

eff_tech['hydrogen']=costs['efficiency']['electrolysis']*costs['efficiency']['fuel cell']
cost_tech['hydrogen']=(costs['fixed']['electrolysis']+costs['fixed']['fuel cell']+n_hyd*costs['fixed']['hydrogen storage'])/(8760/2*costs['efficiency']['electrolysis']*costs['efficiency']['fuel cell']) 

eff_tech['CTES']=costs['efficiency']['water tank charger']*costs['efficiency']['water tank discharger']
cost_tech['CTES']=(costs['fixed']['water tank charger']+costs['fixed']['water tank discharger']+n_CTES*costs['fixed']['central water tank storage']*0.0214)/(n_CTES*costs['efficiency']['water tank charger']*costs['efficiency']['water tank discharger'])
#0.0214 change from cost in €/m^3 to €/kWh
tech_names=['battery', 'PHS','hydrogen','CTES']
cycles=np.arange(1,365,2)

cost_variations=[0.8, 1.0, 1.2]     
cost_df = pd.DataFrame(index=pd.MultiIndex.from_product([pd.Series(data=cycles, name='cycles',),
                                                       pd.Series(data=cost_variations, name='cost_variation',)]), 
                     columns=pd.Series(data=tech_names, name='technologies',))     
for cycle in cycles:
    for cost_variation in cost_variations:
        cost_df.loc[idx[cycle, cost_variation], 'PHS'] = cost_variation*costs['fixed']['PHS']/(np.min([n_PHS*cycle,8760/2])*costs['efficiency']['PHS'])
        cost_df.loc[idx[cycle, cost_variation], 'battery'] = cost_variation*(costs['fixed']['battery inverter']+n_bat*costs['fixed']['battery storage'])/(n_bat*cycle*costs['efficiency']['battery inverter'])
        cost_df.loc[idx[cycle, cost_variation], 'hydrogen'] = cost_variation*(costs['fixed']['electrolysis']+costs['fixed']['fuel cell']+n_hyd*costs['fixed']['hydrogen storage'])/(np.min([n_hyd*cycle,8760/2])*costs['efficiency']['electrolysis']*costs['efficiency']['fuel cell']) 
        cost_df.loc[idx[cycle, cost_variation], 'CTES'] = cost_variation*(costs['fixed']['water tank charger']+costs['fixed']['water tank discharger']+n_CTES*costs['fixed']['central water tank storage']*0.0214)/(np.min([n_CTES*cycle,8760/2])*costs['efficiency']['water tank charger']*costs['efficiency']['water tank discharger'])
    #0.0214 change from cost in €/m^3 to €/kWh
n_refs=np.arange(1,50*24,2)   #ratio Energy capacity/Power capacity




costs_n_df = pd.DataFrame(
        index=pd.Series(
            data=n_refs,
            name='n_refs',
        ),
        columns=pd.Series(
            data=tech_names,
            name='technologies',
        )
        )
        
   
cost_n_df = pd.DataFrame(index=pd.MultiIndex.from_product([pd.Series(data=n_refs, name='n_refs',),
                                                       pd.Series(data=cost_variations, name='cost_variation',)]), 
                     columns=pd.Series(data=tech_names, name='technologies',))
idx = pd.IndexSlice
        
for n_ref in n_refs:
    for cost_variation in cost_variations:
        cost_n_df.loc[idx[n_ref, cost_variation], 'battery'] = cost_variation*(costs['fixed']['battery inverter']+n_ref*costs['fixed']['battery storage'])/(np.min([n_ref*365,8760/2])*costs['efficiency']['battery inverter'])
        cost_n_df.loc[idx[n_ref, cost_variation], 'hydrogen'] = cost_variation*(costs['fixed']['electrolysis']+costs['fixed']['fuel cell']+n_ref*costs['fixed']['hydrogen storage'])/(np.min([n_ref*365,8760/2])*costs['efficiency']['electrolysis']*costs['efficiency']['fuel cell']) 

#%%

plt.style.use('seaborn-ticks')
plt.style.use('seaborn-ticks')
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['xtick.labelsize'] = 14
plt.rcParams['ytick.labelsize'] = 14
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'


plt.figure(figsize=(5, 15))
gs1 = gridspec.GridSpec(3, 1)
gs1.update(hspace=0.3)


### FIGURE B. LCOE vs ROUND-TRIP EFFICIENCY
ax1 = plt.subplot(gs1[1,0])
ax1.set_xlim(0.4, 0.9)
ax1.set_ylim(0, 200)
#dic_color={'PHS':'darkgreen','battery':'lightskyblue','hydrogen':'purple','CTES':'red'}
dic_color={'PHS':'yellowgreen','battery':'gold','hydrogen':'m','CTES':'darkgray'}
ax1.set_ylabel('Levelized Cost of Storage (€/MWh)')
ax1.set_xlabel('round-trip efficiency, $\eta_{in}\eta_{out}$')
dic_label_tech={'PHS':'PHS ($t_{dis}$=12h)','battery':'battery ($t_{dis}$=6h)','hydrogen':'hydrogen ($t_{dis}$=168h)','CTES':'CTES ($t_{dis}$=2900h)'}
dic_alpha={'battery':0.3,'hydrogen':0.1,'PHS':0.3, 'CTES':0.3}
for tech in tech_names:
    error=cost_tech[tech]*0.2
    markers, caps, bars= ax1.errorbar(eff_tech[tech],cost_tech[tech], yerr=[error], fmt='o', 
                 label=dic_label_tech[tech], markersize=12, color=dic_color[tech]) 
    [bar.set_alpha(dic_alpha[tech]) for bar in bars]
    [bar.set_linewidth(7) for bar in bars]
       
ax1.legend(fancybox=True, shadow=True,fontsize=12,loc='best')


### FIGURE C. LCOE vs CYCLES PER YEAR
ax2 = plt.subplot(gs1[2,0])
for tech in ['battery','hydrogen','PHS']:
    ax2.plot(cycles,cost_df.loc[idx[:, 1.0], tech],marker='o',markersize=0,
             linewidth=3, label=dic_label_tech[tech], color=dic_color[tech])   
    ax2.fill_between(cycles, list(cost_df.loc[idx[:, 0.8], tech]), list(cost_df.loc[idx[:, 1.2], tech]),
                    label=None, color=dic_color[tech], alpha=dic_alpha[tech], linewidth=0) 
ax2.set_xscale( "log" )    
ax2.set_ylabel('Levelized Cost of Storage (€/MWh)')  
ax2.set_xlabel('cycles per year, $N_{cycles}$')  
ax2.set_ylim(0, 200)    
ax2.set_xlim(8, 365) 
ax2.legend(fancybox=True, fontsize=12,loc=(0.03,0.11), facecolor='white', frameon=True)
plt.axvline(x=52, color='lightgrey', linestyle='--', linewidth=2)
plt.axvline(x=12, color='lightgrey', linestyle='--', linewidth=2)
plt.text(54, 10, 'weekly', horizontalalignment='left', color='dimgrey', fontsize=14)
plt.text(13, 10, 'monthly', horizontalalignment='left', color='dimgrey', fontsize=14)
          
ax2.set_xticks([10,100,365])
ax2.set_xticklabels(['10','100','365'])
#ax2.legend(fancybox=True, shadow=True,fontsize=14,loc='best')


### FIGURE A. LCOE vs DISCHARGE RATE 
ax0 = plt.subplot(gs1[0,0])
ax0.set_xlim(1, 2000)
ax0.set_ylim(40, 200)

for tech in ['battery','hydrogen']:    
    ax0.plot(n_refs,cost_n_df.loc[idx[:, 1.0], tech],marker='o',markersize=0,
             linewidth=3, label=tech, color=dic_color[tech]) 
    ax0.fill_between(n_refs, list(cost_n_df.loc[idx[:, 0.8], tech]), list(cost_n_df.loc[idx[:, 1.2], tech]),
                    label=None, color=dic_color[tech], alpha=dic_alpha[tech], linewidth=0) 
ax0.set_xscale( "log" )     
ax0.legend(facecolor='white' , fontsize=14,loc=(0.62, 0.02))  #fancybox=True, shadow=True,  
ax0.set_ylabel('Levelized Cost of Storage (€/MWh)')
ax0.set_xlabel('discharge time, $t_{dis}=E_{s}/G_{s}$ (hours)')
ax0.set_xticks([1,10,100,1000])
ax0.set_xticklabels(['1','10','100','1000'])
plt.savefig('figures/storage_characteristics.png', dpi=300, bbox_inches='tight')  