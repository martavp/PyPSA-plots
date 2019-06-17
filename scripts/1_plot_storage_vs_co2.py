# -*- coding: utf-8 -*-
"""
Created on Fri Mar 29 20:39:54 2019

@author: Marta
"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib as mpl
import os
import pypsa
import seaborn as sns; sns.set()


def annuity(n,r):
    """Calculate the annuity factor for an asset with lifetime n years and
    discount rate of r, e.g. annuity(20,0.05)*20 = 1.6"""

    if isinstance(r, pd.Series):
        return pd.Series(1/n, index=r.index).where(r == 0, r/(1. - 1./(1.+r)**n))
    elif r > 0:
        return r/(1. - 1./(1.+r)**n)
    else:
        return 1/n
    

##### 1. LOADING NETWORKS AND FILLING DATAFRAME

#version-45  (transmission=2todays, weakly homogeneous, no CO2 price, decreasing CO2 limit)
path = '/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-77/postnetworks/' 
line_limit='0.125' 
#co2_limits=['0.6', '0.55', '0.5', '0.45', '0.4', '0.35', '0.3', '0.25', '0.2', '0.15', '0.1', '0.075', '0.05'] #, '0.025']
flexs = ['elec_only', 'v2g50', 'elec_central', 'elec_heat_v2g50'] 

co2_limits=['0.6', '0.5','0.4',  '0.3',  '0.2', '0.1','0.05'] #, '0.025']
#flexs = ['elec_only'] 

techs=['battery_E', 'battery_C', 'hydrogen_E', 'hydrogen_C', 'ITES_E', 'ITES_C', 'LTES_E', 'LTES_C', 'cost', 'co2_shadow', 'gamma', 'alpha']

datos = pd.DataFrame(index=pd.MultiIndex.from_product([pd.Series(data=techs, name='tech',),
                                                       pd.Series(data=co2_limits, name='co2_limit',)]), 
                     columns=pd.Series(data=flexs, name='flexs',))
idx = pd.IndexSlice

import time
#%%
for flex in flexs:   
    time.sleep(5)
    for co2_limit in co2_limits:      
        network_name= path+'postnetwork-' +flex+'_'+ line_limit + '_' + co2_limit+ '.h5'        
        print(network_name)
        if os.path.exists(network_name): 
            #network = pypsa.Network()
            #network.import_from_netcdf(network_name)
            network = pypsa.Network(network_name)
            avhl = network.loads_t.p[network.loads.index[network.loads.index.str.len() == 2]].mean().sum()
            avhl_heat = (network.loads_t.p[network.loads.index[network.loads.index.str[3:] == 'heat']].mean().sum() 
                    + network.loads_t.p[network.loads.index[network.loads.index.str[3:] == 'urban heat']].mean().sum())
            avhl_transport = network.loads_t.p[network.loads.index[network.loads.index.str[3:] == 'transport']].mean().sum()
             
            datos.loc[idx['battery_E', co2_limit], flex] = network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'battery']].sum()/avhl
            datos.loc[idx['battery_C', co2_limit], flex] = network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'battery charger']].sum()/avhl
            datos.loc[idx['hydrogen_E', co2_limit], flex] = network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'H2 Store']].sum()/avhl
            datos.loc[idx['hydrogen_C', co2_limit], flex] = network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'H2 Electrolysis']].sum()/avhl
            wind = (network.generators_t.p[network.generators.index[network.generators.index.str[3:] == 'onwind']].mean().sum()+
                    network.generators_t.p[network.generators.index[network.generators.index.str[4:] == 'onwind']].mean().sum()+
                    network.generators_t.p[network.generators.index[network.generators.index.str[3:] == 'offwind']].mean().sum())             
            solar = network.generators_t.p[network.generators.index[network.generators.index.str[3:] == 'solar']].mean().sum()
            datos.loc[idx['gamma', co2_limit], flex] = (wind + solar)/avhl
            datos.loc[idx['alpha', co2_limit], flex] = (wind)/(wind + solar)

            if flex == 'elec_central' or flex == 'elec_heat_v2g50':
            #if heating is included, thermal storage capacities are retrieved    
                datos.loc[idx['ITES_E', co2_limit], flex] = (network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'urban water tank']].sum()
                                                           + network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'water tank']].sum())/avhl_heat
                datos.loc[idx['ITES_C', co2_limit], flex] = (network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'urban water tank']].sum()/avhl_heat
                                                            + network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'water tank']].sum())/avhl_heat
                
                datos.loc[idx['LTES_E', co2_limit], flex] = network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'central water tank']].sum()/avhl_heat
                datos.loc[idx['LTES_C', co2_limit], flex] = network.links.p_nom_opt[network.links.index[network.links.index.str[3:] == 'central water tank']].sum()/avhl_heat            
                
            
            
            
            #hydro_capital_cost=0 in options.yml, so hydro cost must be added
            hydro_FOM_cost = (0.01*2e6*network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'PHS']].sum() #1% FOM ; 2000€/kWh 
            + 0.01*2e6*network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'hydro']].sum() #1% FOM ; 2000€/kWh 
            + 0.02*3e6*network.generators.p_nom[network.generators.index[network.generators.carrier == 'ror']].sum())/1000000000 #2% FOM ; 3000€/kWh 
            
            #CAP_transmission=2*today's, so cost of transmission must be added
            transmission_cost = ((400*1.25*network.links.length+150000.)*network.links.p_nom_opt)[network.links.index[network.links.index.str.len() == 5]].sum()*1.5*(annuity(40., 0.07)+0.02)/1000000000            
            # 1.25 because lines are not straight, 400 is per MWkm of line, 150000 is per MW cost of
            # converter pair for DC line,
            #lifetime =40 years, discount rate=7%
            # n-1 security is approximated by an overcapacity factor 1.5 ~ 1./0.666667
            #FOM of 2%/a
            
            # Adding extra cost for assuming that half of the PV installations are in rooftops (instead of utility-scale plants)
            #solar_extra_cost = 0.5*(725*annuity(25, 0.04)-425*annuity(25, 0.07))*1000*network.generators.p_nom_opt[network.generators.index[network.generators.index.str[3:] == 'solar']].sum()/1000000000
            datos.loc[idx['cost', co2_limit], flex] = (network.objective/1000000000 + hydro_FOM_cost + transmission_cost) #/(avhl+avhl_heat+avhl_transport) 
            
            shadows = pd.read_csv(path+'shadow-' +flex+'_'+ line_limit + '_' + co2_limit+ '.csv')
            datos.loc[idx['co2_shadow', co2_limit], flex] = shadows.at[0,"co2_constraint"]
            
# Save dataframe to pickled pandas object and csv file
datos.to_pickle('data_for_figures/evolution_co2lim.pickle') 
datos.to_csv('data_for_figures/evolution_co2lim.csv', sep=',')            

#%%
##### 2. PLOTTING
# Load dataframe from pickled pandas object or csv
#datos = pd.read_pickle('data_for_figures/evolution_co2lim.pickle')
#plt.style.use('classic')
datos=pd.read_csv('data_for_figures/evolution_co2lim.csv', sep=',', header=0, index_col=(0,1))
techs=['battery_E', 'battery_C', 'hydrogen_E', 'hydrogen_C', 'ITES_E', 'LTES_E','cost', 'co2_shadow', 'gamma', 'alpha']

dic_position={'battery_E':(0,0), 
              'battery_C':(2,0), 
              'hydrogen_E':(0,1),
              'hydrogen_C':(2,1),
              'cost':     (0,0),#(3,0),
              'co2_shadow':(1,0),#,(3,1),
              'ITES_E':(1,0),
              'LTES_E':(1,1),
              'gamma':(4,0),
              'alpha':(4,1)}

dic_ylim={'battery_E':1.5, 
              'battery_C':0.2, 
              'hydrogen_E':22,
              'hydrogen_C':0.6,
              'cost':     450,
              'co2_shadow':550,
              'ITES_E':5,
              'LTES_E':700,
              'gamma':2.5,
              'alpha':1.,}

dic_ylim0={'battery_E':0, 
              'battery_C':0, 
              'hydrogen_E':0,
              'hydrogen_C':0,
              'cost':     50,
              'co2_shadow':0,
              'ITES_E':0,
              'LTES_E':0,
              'gamma':0,
              'alpha':0,}

dic_title={'battery_E': 'Battery energy capacity (av.h.l$_{el}$)' , 
           'battery_C': '$C_{battery}$ (av.h.l$_{el}$)', 
           'hydrogen_E': 'Hydrogen energy capcity (av.h.l$_{el}$)',
           'hydrogen_C': '$C_{hydrogen}$ (av.h.l$_{el}$)',
           'cost': 'System costs (B€)',
           'co2_shadow': 'CO$_2$ shadow price (€/tCO$_2$)',
           'ITES_E':'ITES energy capacity (av.h.l$_{heat}$)',
           'LTES_E':'CTES energy capacity (av.h.l$_{heat}$)',
           'gamma':'$\gamma$',
           'alpha':'$alpha$'}

dic_label={'elec_only':'Electricity', 
           'v2g50':'Electricity+Transport', 
           'elec_heat_v2g50': 'Electricity+Heating+Transport', 
           'elec_central':'Electricity+Heating'} 

dic_height={'elec_only':1.22, 
           'v2g50':1.11, 
           'elec_central': 1.0} 
#dic_height2={'elec_only':1.22, 
#           'v2g50':1.11, 
#           'elec_central': 1.0} 
dic_pos2={'elec_only':1.5, 
           'v2g50':1.37, 
           'elec_central': 1.3} 
xlim=0.65
dic_width={'elec_only':(xlim-784/3016-723/3016)/xlim, 
           'v2g50':(xlim-784/3016)/xlim, 
           'elec_central': (xlim-723/3016)/xlim}

co2_limits_num=[float(x) for x in co2_limits]

dic_col={'elec_only':'C0', 'v2g50':'C2', 'elec_heat_v2g50': 'black', 'elec_central':'C1'} 

#plt.style.use('seaborn-white')
sns.set_style('ticks')
#sns.set(rc={'axes.facecolor':'white', 'figure.facecolor':'white'})

fig = plt.figure(figsize=(14, 22)) #12,27
gs1 = gridspec.GridSpec(5, 2)
gs1.update(wspace=0.3, hspace=0.4)
fig.subplots_adjust(hspace=0.4)
dic_flex_axis={'battery_E':['elec_only', 'v2g50', 'elec_central'],  
               'hydrogen_E':['elec_only', 'v2g50', 'elec_central'], 
               'ITES_E':['elec_central'], 
               'LTES_E':['elec_central']}

techs=['battery_E',  'hydrogen_E', 'ITES_E', 'LTES_E']
for tech in techs:
    flex='elec_heat_v2g50'
    ax0 = plt.subplot(gs1[dic_position[tech][0],dic_position[tech][1]])
    ax0.set_xlabel('CO$_2$ emissions (relative to 1990)')
    ax0.set_ylabel(dic_title[tech])    
    ylim=dic_ylim[tech]
    ax0.set_xlim(xlim, 0.)
    ax0.set_ylim(0, ylim)
    ax0.spines['top'].set_color('none')  
    ax0.spines['right'].set_color('none') 
    ax0.plot(co2_limits_num, datos.loc[idx[tech, :], flex], color=dic_col[flex], linewidth=2, marker='o', label=dic_label[flex])
    ax0.set_xticks([0.05, 0.2, 0.4, 0.6])
    ax0.set_xticklabels(['5%','20%','40%', '60%'])
    if tech=='ITES_E':
        plt.annotate('Electricity \n + Heating \n + Transport', xy=(0.28,1),
        xytext=(0.2,0.7), fontsize=10, arrowprops=dict(arrowstyle="->", 
               color='black'))
    for flex in dic_flex_axis[tech]:
        height = dic_height[flex]
        width = dic_width[flex] 
        axins=ax0.inset_axes((0.01, 0.01, width, height)) # x, y, width, height
        axins.spines['right'].set_color('none')
        axins.spines['left'].set_color('none')
        axins.spines['bottom'].set_color('none')
        axins.spines['top'].set_color(dic_col[flex])
        axins.xaxis.tick_top()
        axins.xaxis.set_label_position('top')
        axins.set_xlabel(dic_label[flex], fontsize=10, color=dic_col[flex])
        axins.xaxis.set_label_coords(dic_pos2[flex], 1)
        axins.tick_params(direction='inout')
        axins.set_yticks([])
        axins.patch.set_alpha(0) 
        axins.set_xlim(xlim, 0.)
        axins.set_ylim(0, ylim*height)
        axins.tick_params(axis='x', colors=dic_col[flex])    
        axins.set_xticks([0.05, 0.2, 0.4, 0.6])
        axins.set_xticklabels(['5%','20%','40%', '60%'], fontsize=9)
        axins.plot(co2_limits_num, datos.loc[idx[tech, :], flex], color=dic_col[flex], linewidth=2, marker='o', label=dic_label[flex])
#ax0.legend(loc=(-0.1,1.01), ncol=2, shadow=True,fancybox=True,prop={'size':12})
plt.savefig('figures/capacities.png', dpi=300, bbox_inches='tight')
#%%
fig = plt.figure(figsize=(14, 22))
gs1 = gridspec.GridSpec(5, 2)
gs1.update(wspace=0.3, hspace=0.6)
fig.subplots_adjust(hspace=0.6)
techs=['cost', 'co2_shadow']
for tech in techs:
    flex='elec_heat_v2g50'
    ax0 = plt.subplot(gs1[dic_position[tech][0],dic_position[tech][1]])
    ax0.set_xlabel('CO$_2$ emissions (relative to 1990)')
    ax0.set_ylabel(dic_title[tech])    
    ylim=dic_ylim[tech]
    ax0.set_xlim(xlim, 0.)
    ylim0=dic_ylim0[tech]
    ax0.set_ylim(ylim0, ylim)
    ax0.set_xticks([0.05, 0.2, 0.4, 0.6])
    ax0.set_xticklabels(['5%','20%','40%', '60%'])
    ax0.spines['top'].set_color('none')  
    ax0.spines['right'].set_color('none') 
    ax0.plot(co2_limits_num, datos.loc[idx[tech, :], flex], color=dic_col[flex], linewidth=2, marker='o', label=dic_label[flex])
    if tech=='cost':
        plt.annotate('Electricity \n + Heating \n + Transport', xy=(0.13,320),
        xytext=(0.2,180), fontsize=10, arrowprops=dict(arrowstyle="->", 
               color='black'))
    for flex in ['elec_only', 'v2g50', 'elec_central']:
        height = dic_height[flex]
        width = dic_width[flex] 
        axins=ax0.inset_axes((0.01, 0.01, width, height)) # x, y, width, height
        axins.spines['right'].set_color('none')
        axins.spines['left'].set_color('none')
        axins.spines['bottom'].set_color('none')
        axins.spines['top'].set_color(dic_col[flex])
        axins.xaxis.tick_top()
        axins.xaxis.set_label_position('top')
        axins.set_xlabel(dic_label[flex], fontsize=10, color=dic_col[flex])
        axins.xaxis.set_label_coords(dic_pos2[flex], 1)
        axins.tick_params(direction='inout')
        axins.set_yticks([])
        axins.patch.set_alpha(0) 
        axins.set_xlim(xlim, 0.)
        axins.set_ylim(ylim0, ylim*height)
        axins.tick_params(axis='x', colors=dic_col[flex])    
        axins.set_xticks([0.05, 0.2, 0.4, 0.6])
        axins.set_xticklabels(['5%','20%','40%', '60%'], fontsize=9)
        axins.plot(co2_limits_num, datos.loc[idx[tech, :], flex], color=dic_col[flex], linewidth=2, marker='o', label=dic_label[flex])
#ax0.legend(loc=(-0.1,1.01), ncol=2, shadow=True,fancybox=True,prop={'size':12})
plt.savefig('figures/system_cost.png', dpi=300, bbox_inches='tight')

#%%
fig = plt.figure(figsize=(12, 27))
gs1 = gridspec.GridSpec(5, 2)
gs1.update(wspace=0.3, hspace=0.6)
fig.subplots_adjust(hspace=0.6)
techs=['gamma', 'alpha']
for tech in techs:
    flex='elec_heat_v2g50'
    ax0 = plt.subplot(gs1[dic_position[tech][0],dic_position[tech][1]])
    ax0.set_xlabel('CO$_2$ emissions (relative to 1990)')
    ax0.set_ylabel(dic_title[tech])    
    ylim=dic_ylim[tech]
    ax0.set_xlim(xlim, 0.)
    ylim0=dic_ylim0[tech]
    ax0.set_ylim(ylim0, ylim)
    ax0.set_xticks([0.05, 0.2, 0.4, 0.6])
    ax0.set_xticklabels(['5%','20%','40%', '60%'])
    ax0.spines['top'].set_color('none')  
    ax0.spines['right'].set_color('none') 
    ax0.plot(co2_limits_num, datos.loc[idx[tech, :], flex], color=dic_col[flex], linewidth=2, marker='o', label=dic_label[flex])
    
    for flex in ['elec_only', 'v2g50', 'elec_central']:
        height = dic_height[flex]
        width = dic_width[flex] 
        axins=ax0.inset_axes((0.01, 0.01, width, height)) # x, y, width, height
        axins.spines['right'].set_color('none')
        axins.spines['left'].set_color('none')
        axins.spines['bottom'].set_color('none')
        axins.spines['top'].set_color(dic_col[flex])
        axins.xaxis.tick_top()
        axins.xaxis.set_label_position('top')
        axins.set_xlabel(dic_label[flex], fontsize=10, color=dic_col[flex])
        axins.xaxis.set_label_coords(dic_pos2[flex], 1)
        axins.tick_params(direction='inout')
        axins.set_yticks([])
        axins.patch.set_alpha(0) 
        axins.set_xlim(xlim, 0.)
        axins.set_ylim(ylim0, ylim*height)
        axins.tick_params(axis='x', colors=dic_col[flex])    
        axins.set_xticks([0.05, 0.2, 0.4, 0.6])
        axins.set_xticklabels(['5%','20%','40%', '60%'], fontsize=9)
        axins.plot(co2_limits_num, datos.loc[idx[tech, :], flex], color=dic_col[flex], linewidth=2, marker='o', label=dic_label[flex])
#ax0.legend(loc=(-0.1,1.01), ncol=2, shadow=True,fancybox=True,prop={'size':12})
plt.savefig('figures/alpha_gamma.png', dpi=300, bbox_inches='tight')