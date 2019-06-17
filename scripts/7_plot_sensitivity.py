# -*- coding: utf-8 -*-
"""
Created on Fri Jan 11 08:37:14 2019

@author: Marta
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pypsa

def annuity(n,r):
    """Calculate the annuity factor for an asset with lifetime n years and
    discount rate of r, e.g. annuity(20,0.05)*20 = 1.6"""

    if isinstance(r, pd.Series):
        return pd.Series(1/n, index=r.index).where(r == 0, r/(1. - 1./(1.+r)**n))
    elif r > 0:
        return r/(1. - 1./(1.+r)**n)
    else:
        return 1/n
    
def extract_storage_capacities_variable_transmission(path, line_limits, flex, gamma) :
    """
    Retrieve batteries and hydrogen capacities, as well as costs and transmission
    capacities from networks with variable line limits extension cap
    """
    
    battery_E=[]
    hydrogen_E=[]
    transmission=[]
    cost=[]
    for line_limit in line_limits:
        file_name= path+'postnetwork-' +flex+'_'+ line_limit +'_' + gamma + '.h5'
        network = pypsa.Network(file_name)
        avhl = network.loads_t.p[network.loads.index[network.loads.index.str.len() == 2]].mean().sum()
        battery_E.append(network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'battery']].sum()/avhl)
        hydrogen_E.append(network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'H2 Store']].sum()/avhl)
        
        #hydro_capital_cost=0 in options.yml, so hydro cost must be added
        hydro_FOM_cost = (0.01*2e6*network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'PHS']].sum() #1% FOM ; 2000€/kWh 
        + 0.01*2e6*network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'hydro']].sum() #1% FOM ; 2000€/kWh 
        + 0.02*3e6*network.generators.p_nom[network.generators.index[network.generators.carrier == 'ror']].sum())/1000000000 #2% FOM ; 3000€/kWh 
            
        #CAP_transmission=2*today's, so cost of transmission must be added
        transmission_cost = ((400*1.25*network.links.length+150000.)*network.links.p_nom_opt)[network.links.index[network.links.index.str.len() == 5]].sum()*1.5*(annuity(40., 0.07)+0.02)/1000000000             
            
        cost.append(network.objective/1000000000 + hydro_FOM_cost + transmission_cost) #Billions
        transmission.append((network.links.p_nom_opt[network.links.index[network.links.index.str[2]=='-']]* 
               network.links.length[network.links.index[network.links.index.str[2]=='-']]).sum()/1000000) #TWkm
    return battery_E, hydrogen_E, cost, transmission



def extract_storage_capacities(path, gammas, flex, line_limit):    
    """
    Retrieve batteries and hydrogen capacities, as well as costs, from
    networks with one variable parameter (gamma)
    """    
    
    battery_E=[]
    hydrogen_E=[]
    cost=[]
    for gamma in gammas:
        file_name= path+'postnetwork-' +flex+'_'+ line_limit +'_' + str(gamma) + '.h5'
        network = pypsa.Network(file_name)
        avhl = network.loads_t.p[network.loads.index[network.loads.index.str.len() == 2]].mean().sum()
        battery_E.append(network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'battery']].sum()/avhl)
        hydrogen_E.append(network.stores.e_nom_opt[network.stores.index[network.stores.index.str[3:] == 'H2 Store']].sum()/avhl)
        #hydro_capital_cost=0 in options.yml, so hydro cost must be added
        hydro_FOM_cost = (0.01*2e6*network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'PHS']].sum() #1% FOM ; 2000€/kWh 
        + 0.01*2e6*network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'hydro']].sum() #1% FOM ; 2000€/kWh 
        + 0.02*3e6*network.generators.p_nom[network.generators.index[network.generators.carrier == 'ror']].sum())/1000000000 #2% FOM ; 3000€/kWh 
            
        #CAP_transmission=2*today's, so cost of transmission must be added
        transmission_cost = ((400*1.25*network.links.length+150000.)*network.links.p_nom_opt)[network.links.index[network.links.index.str.len() == 5]].sum()*1.5*(annuity(40., 0.07)+0.02)/1000000000             
            
        cost.append(network.objective/1000000000 + hydro_FOM_cost + transmission_cost) #Billions

    return battery_E, hydrogen_E, cost



def extract_wind_solar_gross_energy_variable_transmission(path, line_limits, flex, gamma) :
    """
    Retrieve gross energy from wind and solar, as well as costs and transmission
    capacities from networks with variable line limits extension cap
    """
    
    solar_g=[]
    wind_g=[]
    transmission=[]
    cost=[]
    for line_limit in line_limits:
        file_name= path+'postnetwork-' +flex+'_'+ line_limit +'_' + gamma + '.h5'
        network = pypsa.Network(file_name)
        avhl = network.loads_t.p[network.loads.index[network.loads.index.str.len() == 2]].mean().sum()
        wind_g.append((network.generators_t.p[network.generators.index[network.generators.index.str[3:] == 'onwind']].mean().sum()+
                       network.generators_t.p[network.generators.index[network.generators.index.str[4:] == 'onwind']].mean().sum()+
                       network.generators_t.p[network.generators.index[network.generators.index.str[3:] == 'offwind']].mean().sum())/avhl)
        solar_g.append(network.generators_t.p[network.generators.index[network.generators.index.str[3:] == 'solar']].mean().sum()/avhl)
        #hydro_capital_cost=0 in options.yml, so hydro cost must be added
        hydro_FOM_cost = (0.01*2e6*network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'PHS']].sum() #1% FOM ; 2000€/kWh 
        + 0.01*2e6*network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'hydro']].sum() #1% FOM ; 2000€/kWh 
        + 0.02*3e6*network.generators.p_nom[network.generators.index[network.generators.carrier == 'ror']].sum())/1000000000 #2% FOM ; 3000€/kWh 
            
        #CAP_transmission=2*today's, so cost of transmission must be added
        transmission_cost = ((400*1.25*network.links.length+150000.)*network.links.p_nom_opt)[network.links.index[network.links.index.str.len() == 5]].sum()*1.5*(annuity(40., 0.07)+0.02)/1000000000             
                    
        cost.append(network.objective/1000000000 + hydro_FOM_cost + transmission_cost) #Billions
        #cost.append(80+network.objective/1000000000) #Billions
        transmission.append((network.links.p_nom_opt[network.links.index[network.links.index.str[2]=='-']]* 
               network.links.length[network.links.index[network.links.index.str[2]=='-']]).sum()/1000000) #TWkm
    return solar_g, wind_g, cost, transmission



def extract_wind_solar_gross_energy(path, gammas, flex, line_limit):    
    """
    Retrieve gross energy from wind and solar, as well as costs, from
    networks with one variable parameter (gamma)
    """    
    
    solar_g=[]
    wind_g=[]
    cost=[]
    for gamma in gammas:
        file_name= path+'postnetwork-' +flex+'_'+ line_limit +'_' + str(gamma) + '.h5'
        network = pypsa.Network(file_name)
        avhl = network.loads_t.p[network.loads.index[network.loads.index.str.len() == 2]].mean().sum()
        wind_g.append((network.generators_t.p[network.generators.index[network.generators.index.str[3:] == 'onwind']].mean().sum()+
                       network.generators_t.p[network.generators.index[network.generators.index.str[4:] == 'onwind']].mean().sum()+
                       network.generators_t.p[network.generators.index[network.generators.index.str[3:] == 'offwind']].mean().sum())/avhl)
        solar_g.append(network.generators_t.p[network.generators.index[network.generators.index.str[3:] == 'solar']].mean().sum()/avhl)
                #hydro_capital_cost=0 in options.yml, so hydro cost must be added
        hydro_FOM_cost = (0.01*2e6*network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'PHS']].sum() #1% FOM ; 2000€/kWh 
        + 0.01*2e6*network.storage_units.p_nom[network.storage_units.index[network.storage_units.carrier == 'hydro']].sum() #1% FOM ; 2000€/kWh 
        + 0.02*3e6*network.generators.p_nom[network.generators.index[network.generators.carrier == 'ror']].sum())/1000000000 #2% FOM ; 3000€/kWh 
            
        #CAP_transmission=2*today's, so cost of transmission must be added
        transmission_cost = ((400*1.25*network.links.length+150000.)*network.links.p_nom_opt)[network.links.index[network.links.index.str.len() == 5]].sum()*1.5*(annuity(40., 0.07)+0.02)/1000000000             
                    
        cost.append(network.objective/1000000000 + hydro_FOM_cost + transmission_cost) #Billions
        #cost.append(80+network.objective/1000000000) #Billions

    return solar_g, wind_g, cost



def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)



def plot_storage_capacities_sensitivity(flex):        
    plt.style.use('seaborn-ticks')
    plt.rcParams['axes.labelsize'] = 18
    plt.rcParams['xtick.labelsize'] = 18
    plt.rcParams['ytick.labelsize'] = 18
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    
    dic_color={'PHS':'yellowgreen','battery':'goldenrod','hydrogen':'m','LTES':'darkgray','cost':'gray'}
    plt.figure(figsize=(12, 15))
    gs1 = gridspec.GridSpec(3, 2)
    gs1.update(wspace=0.9, hspace=0.5)
    
    ax0 = plt.subplot(gs1[0,1])
    ax1 = ax0.twinx()
    ax2 = ax0.twinx()
    ax1.spines['right'].set_position(("axes", 1.25))
    make_patch_spines_invisible(ax1)
    ax1.spines['right'].set_visible(True)
    
    ax0.tick_params(axis='y', colors=dic_color['cost'])
    ax1.tick_params(axis='y', colors=dic_color['hydrogen'])
    ax2.tick_params(axis='y', colors=dic_color['battery'])
    ax0.set_xlabel('Transmission capacity (TWkm)')
    #ax0.set_xlim(0,200)
    ax0.set_xticks([0, 50, 100, 150])
    ax0.set_xticklabels(['0', '50', '100', '150'])
    ax0.set_ylabel('System cost (B€/year)', color=dic_color['cost'])
    ax1.set_ylabel('Hydrogen energy capacity (av.h.l)', color=dic_color['hydrogen'])
    ax2.set_ylabel('battery energy capacity (av.h.l)', color=dic_color['battery'])
    
    
    ax0.set_ylim(0, 500)
    ax2.set_ylim(0, 6)
    ax1.set_ylim(0, 80)
    ax0.text(0.9, 0.9, 'b)', transform=ax0.transAxes, fontsize=16)
    path = path = dic_path['transmission']
    line_limits=['0', '0.0625', '0.125', '0.25', '0.375']#, 'opt']
    flex=flex
    battery_E, hydrogen_E, cost, transmission=extract_storage_capacities_variable_transmission(path, line_limits, flex, gamma='0.05')
    
    ax0.plot(transmission,cost, color=dic_color['cost'], marker='o',markersize=4, linewidth=2)  
    ax1.plot(transmission,hydrogen_E, color=dic_color['hydrogen'], marker='o',markersize=4, linewidth=2)  
    ax2.plot(transmission,battery_E, color=dic_color['battery'], marker='o',markersize=4,linewidth=2)     
    plt.axvline(x=31.5, color='lightgrey', linestyle='--')
    plt.text(34, 4, 'today', horizontalalignment='left', color='darkgrey', fontsize=16)

    parameters=['co2_limit', 
                'battery_cost', 
                'hydrogen_cost', 
                'solar_cost', 
                'wind_cost']

    dic_position={'co2_limit':(0,0),
                  'battery_cost':(1,0), 
                  'hydrogen_cost':(1,1), 
                  'solar_cost':(2,0), 
                  'wind_cost':(2,1)}
    
    dic_xlabel={'co2_limit':'CO$_2$ emission limit',
                'battery_cost':'battery cost (relative to reference)', 
                'hydrogen_cost':'hydrogen storage cost (relative to reference)', 
                'solar_cost':'solar cost (relative to reference)', 
                'wind_cost':'wind cost (relative to reference)'}
    
    
    cost_variation=[0.25, 0.5, 0.8, 1, 1.2,  1.5, 2]
    dic_param_values={'co2_limit':[0.5, 0.4, 0.3, 0.2, 0.1, 0.05],
                      'battery_cost': cost_variation, 
                      'hydrogen_cost': cost_variation, 
                      'solar_cost': cost_variation, 
                      'wind_cost': cost_variation}
    dic_letter={'co2_limit':'a)',
                'battery_cost': 'c)', 
                'hydrogen_cost': 'd)', 
                'solar_cost': 'e)', 
                'wind_cost': 'f)'}
    for parameter in parameters:
        ax0 = plt.subplot(gs1[dic_position[parameter]])
        ax1 = ax0.twinx()
        ax2 = ax0.twinx()
        ax1.spines['right'].set_position(("axes", 1.3))
        make_patch_spines_invisible(ax1)
        ax1.spines['right'].set_visible(True)
    
        ax0.tick_params(axis='y', colors=dic_color['cost'])
        ax1.tick_params(axis='y', colors=dic_color['hydrogen'])
        ax2.tick_params(axis='y', colors=dic_color['battery'])
        ax0.set_xlabel(dic_xlabel[parameter])
        ax0.set_ylabel('System cost (B€/year)', color=dic_color['cost'])
        ax1.set_ylabel('Hydrogen energy capacity (av.h.l)', color=dic_color['hydrogen'])
        ax2.set_ylabel('Battery energy capacity (av.h.l)', color=dic_color['battery'])
    
        ax0.set_ylim(0, 500)
        ax2.set_ylim(0, 6)
        ax1.set_ylim(0, 80)
        if parameter=='co2_limit':
            ax0.set_xlim(0.5,0)
            ax0.set_xticks([0.4, 0.2, 0.05])
            ax0.set_xticklabels(['40%', '20%', '5%'])
        else:
            ax0.set_xlim(0, 2)
            
        ax0.text(0.9, 0.9, dic_letter[parameter], transform=ax0.transAxes, fontsize=16)
        flex=flex
        battery_E, hydrogen_E, cost=extract_storage_capacities(dic_path[parameter], dic_param_values[parameter], flex, line_limit='0.125')
        ax0.plot(dic_param_values[parameter],cost, color=dic_color['cost'], marker='o',markersize=4, linewidth=2)  
        ax1.plot(dic_param_values[parameter],hydrogen_E, color=dic_color['hydrogen'], marker='o',markersize=4, linewidth=2)  
        ax2.plot(dic_param_values[parameter],battery_E, color=dic_color['battery'], marker='o',markersize=4,linewidth=2)  
    
    plt.savefig('figures/storage_sensitivity.png', dpi=300, bbox_inches='tight')

def plot_wind_solar_energy_sensitivity(flex):        
    plt.style.use('seaborn-ticks')
    plt.rcParams['axes.labelsize'] = 18
    plt.rcParams['xtick.labelsize'] = 18
    plt.rcParams['ytick.labelsize'] = 18
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    
    dic_color={'solar':'goldenrod','wind':'blue','cost':'gray'}
    
    plt.figure(figsize=(12, 15))
    gs1 = gridspec.GridSpec(3, 2)
    gs1.update(wspace=0.9, hspace=0.5)
    
    ax0 = plt.subplot(gs1[0,1])
    ax1 = ax0.twinx()
    ax2 = ax0.twinx()
    ax1.spines['right'].set_position(("axes", 1.25))
    make_patch_spines_invisible(ax1)
    ax1.spines['right'].set_visible(True)
    
    ax0.tick_params(axis='y', colors=dic_color['cost'])
    ax1.tick_params(axis='y', colors=dic_color['wind'])
    ax2.tick_params(axis='y', colors=dic_color['solar'])
    ax0.set_xlabel('Transmission capacity (TWkm)')
    ax0.set_ylabel('System cost (B€/year)', color=dic_color['cost'])
    ax1.set_ylabel('Wind energy (av.h.l)', color=dic_color['wind'])
    ax2.set_ylabel('Solar energy (av.h.l)',  color=dic_color['solar'])
    
    ax0.set_ylim(80, 500)
    #ax0.set_xlim(0,200)
    ax0.set_xticks([0, 50, 100, 150])
    ax0.set_xticklabels(['0', '50', '100', '150'])
    ax2.set_ylim(0, 1)
    ax1.set_ylim(0, 1)
    ax0.text(0.9, 0.9, 'b)', transform=ax0.transAxes, fontsize=16)
    path = dic_path['transmission']
    line_limits=['0', '0.0625', '0.125', '0.25', '0.375']#, 'opt']
    flex=flex
    solar_g, wind_g, cost, transmission=extract_wind_solar_gross_energy_variable_transmission(path, line_limits, flex, gamma='0.05')
    
    ax0.plot(transmission, cost, color=dic_color['cost'], marker='o',markersize=4, linewidth=2)  
    ax1.plot(transmission, wind_g, color=dic_color['wind'], marker='o',markersize=4, linewidth=2)  
    ax2.plot(transmission, solar_g, color=dic_color['solar'], marker='o',markersize=4,linewidth=2)     
    plt.axvline(x=31.5, color='lightgrey', linestyle='--')
    plt.text(34, 0.9, 'today', horizontalalignment='left', color='darkgrey', fontsize=16)

    parameters=['co2_limit', 
                'battery_cost', 
                'hydrogen_cost', 
                'solar_cost', 
                'wind_cost']

    dic_position={'co2_limit':(0,0),
                  'battery_cost':(2,0), 
                  'hydrogen_cost':(2,1), 
                  'solar_cost':(1,0), 
                  'wind_cost':(1,1)}
    
    dic_xlabel={'co2_limit':'CO$_2$ emissions (relative to 1990)',
                'battery_cost':'battery cost (relative to reference)', 
                'hydrogen_cost':'hydrogen storage cost (relative to reference)', 
                'solar_cost':'solar cost (relative to reference)', 
                'wind_cost':'wind cost (relative to reference)'}
    

    cost_variation=[0.25, 0.5, 0.8, 1, 1.2,  1.5, 2]
    dic_param_values={'co2_limit':[0.5, 0.4, 0.3, 0.2, 0.1, 0.05],
                      'battery_cost': cost_variation, 
                      'hydrogen_cost': cost_variation, 
                      'solar_cost': cost_variation, 
                      'wind_cost': cost_variation}
    dic_letter={'co2_limit':'a)',
                'battery_cost': 'c)', 
                'hydrogen_cost': 'd)', 
                'solar_cost': 'e)', 
                'wind_cost': 'f)'}
    for parameter in parameters:
        ax0 = plt.subplot(gs1[dic_position[parameter]])
        ax1 = ax0.twinx()
        ax2 = ax0.twinx()
        ax1.spines['right'].set_position(("axes", 1.3))
        make_patch_spines_invisible(ax1)
        ax1.spines['right'].set_visible(True)
    
        ax0.tick_params(axis='y', colors=dic_color['cost'])
        ax1.tick_params(axis='y', colors=dic_color['wind'])
        ax2.tick_params(axis='y', colors=dic_color['solar'])
        ax0.set_xlabel(dic_xlabel[parameter])
        ax0.set_ylabel('System cost (B€/year)', color=dic_color['cost'])
        ax1.set_ylabel('Wind energy (av.h.l)', color=dic_color['wind'])
        ax2.set_ylabel('Solar energy (av.h.l)', color=dic_color['solar'])
    
        ax0.set_ylim(80, 500)
        ax2.set_ylim(0, 1)
        ax1.set_ylim(0, 1)
        if parameter=='co2_limit':
            ax0.set_xlim(0.5,0)
            ax0.set_xticks([0.4, 0.2, 0.05])
            ax0.set_xticklabels(['40%', '20%', '5%'])
        ax0.text(0.9, 0.9, dic_letter[parameter], transform=ax0.transAxes, fontsize=16)
        flex
        solar_g, wind_g, cost=extract_wind_solar_gross_energy(dic_path[parameter], dic_param_values[parameter], flex, line_limit='0.125')
        ax0.plot(dic_param_values[parameter],cost, color=dic_color['cost'], marker='o',markersize=4, linewidth=2)  
        ax1.plot(dic_param_values[parameter], wind_g, color=dic_color['wind'], marker='o',markersize=4, linewidth=2)  
        ax2.plot(dic_param_values[parameter],solar_g, color=dic_color['solar'], marker='o',markersize=4,linewidth=2)  
    
    plt.savefig('figures/wind_solar_gross_energy_sensitivity.png', 
                dpi=300, bbox_inches='tight')

def plot_energy_capacity_cost_efficiency_sensitivity(flex):        
    plt.style.use('seaborn-ticks')
    plt.rcParams['axes.labelsize'] = 18
    plt.rcParams['xtick.labelsize'] = 18
    plt.rcParams['ytick.labelsize'] = 18
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    
    dic_color={'PHS':'yellowgreen','battery':'goldenrod','hydrogen':'m','LTES':'darkgray','cost':'gray'}
    plt.figure(figsize=(12, 15))
    gs1 = gridspec.GridSpec(3, 2)
    gs1.update(wspace=0.9, hspace=0.5)
    

    parameters=['energy_capacity_cost',
                'efficiency']

    dic_position={'energy_capacity_cost':(0,0),
                  'efficiency':(1,0)}
    
    dic_xlabel={'energy_capacity_cost':'H$_2$ energy capacity cost (relative to reference)',
                'efficiency':'Fuel cell efficiency (relative to reference)'}
    
    #cost_variation=[0.25, 0.5, 0.8, 1, 1.2,  1.5, 2]
    dic_param_values={'energy_capacity_cost':[0.25, 0.5, 0.8, 1, 1.2,  1.5, 2],
                      'efficiency': [0.8, 1, 1.2, 1.4, 1.6]}
    
    dic_letter={'energy_capacity_cost':'a)',
                'efficiency': 'b)'}
    for parameter in parameters:
        ax0 = plt.subplot(gs1[dic_position[parameter]])
        ax1 = ax0.twinx()
        ax2 = ax0.twinx()
        ax1.spines['right'].set_position(("axes", 1.3))
        make_patch_spines_invisible(ax1)
        ax1.spines['right'].set_visible(True)
    
        ax0.tick_params(axis='y', colors=dic_color['cost'])
        ax1.tick_params(axis='y', colors=dic_color['hydrogen'])
        ax2.tick_params(axis='y', colors=dic_color['battery'])
        ax0.set_xlabel(dic_xlabel[parameter])
        ax0.set_ylabel('System cost (B€/year)', color=dic_color['cost'])
        ax1.set_ylabel('Hydrogen energy capacity (av.h.l)', color=dic_color['hydrogen'])
        ax2.set_ylabel('Battery energy capacity (av.h.l)', color=dic_color['battery'])
    
        ax0.set_ylim(0, 500)
        ax2.set_ylim(0, 6)
        ax1.set_ylim(0, 80)
        if parameter=='co2_limit':
            ax0.set_xlim(0.5,0)
            ax0.set_xticks([0.4, 0.2, 0.05])
            ax0.set_xticklabels(['40%', '20%', '5%'])
        else:
            ax0.set_xlim(0, 2)
            
        ax0.text(0.9, 0.9, dic_letter[parameter], transform=ax0.transAxes, fontsize=16)
        flex=flex
        battery_E, hydrogen_E, cost=extract_storage_capacities(dic_path[parameter], dic_param_values[parameter], flex, line_limit='0.125')
        ax0.plot(dic_param_values[parameter],cost, color=dic_color['cost'], marker='o',markersize=4, linewidth=2)  
        ax1.plot(dic_param_values[parameter],hydrogen_E, color=dic_color['hydrogen'], marker='o',markersize=4, linewidth=2)  
        ax2.plot(dic_param_values[parameter],battery_E, color=dic_color['battery'], marker='o',markersize=4,linewidth=2)  
    
    plt.savefig('figures/storage_sensitivity2_'+flex+'.png', dpi=300, bbox_inches='tight')

dic_path={'transmission': '/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-78/postnetworks/',
          'co2_limit': '/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-77/postnetworks/',
          'battery_cost':'/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-79/postnetworks/', 
          'hydrogen_cost':'/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-80/postnetworks/', 
          'solar_cost':'/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-81/postnetworks/', 
          'wind_cost':'/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-82/postnetworks/',
          'energy_capacity_cost':'/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-83/postnetworks/',
          'efficiency':'/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-84/postnetworks/'}    
#plot_storage_capacities_sensitivity(flex='elec_central')    
#plot_wind_solar_energy_sensitivity(flex='elec_central')
plot_energy_capacity_cost_efficiency_sensitivity(flex='elec_central')   