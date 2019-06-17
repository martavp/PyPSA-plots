import pandas as pd
import vresutils
import numpy as np

import os

#allow plotting without Xwindows
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

import pypsa

from plot_summary import rename_techs, preferred_order

### Es posible que de un error al importar desde make_summary
### porque ese archivo llama a 
### from prepare_network import generate_periodic_profiles
### prepare_network llama a 
### from vresutils import shapes as vshapes
### y shape requiere que la carpeta 'vresutils' con todos 
### los datos de archivos. shp etc. esté guardada en
### la carpeta externa a donde se encuentra la carpeta results
from make_summary import assign_groups


from matplotlib.patches import Circle, Ellipse
from matplotlib.legend_handler import HandlerPatch

def make_handler_map_to_scale_circles_as_in(ax, dont_resize_actively=False):
    fig = ax.get_figure()
    def axes2pt():
        return np.diff(ax.transData.transform([(0,0), (1,1)]), axis=0)[0] * (72./fig.dpi)

    ellipses = []
    if not dont_resize_actively:
        def update_width_height(event):
            dist = axes2pt()
            for e, radius in ellipses: e.width, e.height = 2. * radius * dist
        fig.canvas.mpl_connect('resize_event', update_width_height)
        ax.callbacks.connect('xlim_changed', update_width_height)
        ax.callbacks.connect('ylim_changed', update_width_height)

    def legend_circle_handler(legend, orig_handle, xdescent, ydescent,
                              width, height, fontsize):
        w, h = 2. * orig_handle.get_radius() * axes2pt()
        e = Ellipse(xy=(0.5*width-0.5*xdescent, 0.5*height-0.5*ydescent), width=w, height=w)
        ellipses.append((e, orig_handle.get_radius()))
        return e
    return {Circle: HandlerPatch(patch_func=legend_circle_handler)}



def make_legend_circles_for(sizes, scale=1.0, **kw):
    return [Circle((0,0), radius=(s/scale)**0.5, **kw) for s in sizes]

def plot_primary_energy(flex,line_limit, network_name):
    
    n = pypsa.Network(network_name)

    assign_groups(n)

    #Drop non-electric buses so they don't clutter the plot
    n.buses.drop(n.buses.index[n.buses.index.str.len() != 2],inplace=True)

    primary = pd.DataFrame(index=n.buses.index)

    primary["gas"] = n.stores_t.p[n.stores.index[n.stores.index.str[3:] == "gas Store"]].sum().rename(lambda x : x[:2])

    primary["hydroelectricity"] = n.storage_units_t.p[n.storage_units.index[n.storage_units.index.str[3:] == "hydro"]].sum().rename(lambda x : x[:2]).fillna(0.)

    n.generators["country"] = n.generators.index.str[:2]

    n.generators["nice_group"] = n.generators["group"].map(rename_techs)

    for carrier in n.generators.nice_group.value_counts().index:
        s = n.generators_t.p[n.generators.index[n.generators.nice_group == carrier]].sum().groupby(n.generators.country).sum().fillna(0.)
        
        if carrier in primary.columns:
            primary[carrier] += s
        else:
            primary[carrier] = s


    primary[primary < 0.] = 0.
    primary = primary.fillna(0.)
    print(primary)
    print(primary.sum())
    primary = primary.stack().sort_index()

    fig, ax = plt.subplots(1,1)

    fig.set_size_inches(6,4.3)

    bus_size_factor =1e8
    linewidth_factor=1e3
    line_color="m"

    n.buses.loc["NO",["x","y"]] = [9.5,61.5]


    line_widths_exp = pd.concat(dict(Line=n.lines.s_nom_opt, Link=n.links.p_nom_opt))


    dic_col={'solar':'gold', 'onwind':'blue', 'offwind':'blue',#'lightskyblue',
             'hidroelectricity':'green', 'gas':'brown'}
    n.plot(bus_sizes=primary/bus_size_factor,
           bus_colors=snakemake.config['plotting']['tech_colors'],
           line_colors=dict(Line=line_color, Link=line_color),
           line_widths=line_widths_exp/linewidth_factor,
           ax=ax, basemap=True)



    if line_limit != "0":

        handles = make_legend_circles_for([1e8, 3e7], scale=bus_size_factor, facecolor="gray")
        labels = ["{} TWh".format(s) for s in (100, 30)]
        l2 = ax.legend(handles, labels,
                       loc="upper left", bbox_to_anchor=(0.01, 1.01),
                       labelspacing=1.0,
                       framealpha=1.,
                       title='Primary energy',
                       handler_map=make_handler_map_to_scale_circles_as_in(ax))
        ax.add_artist(l2)

        handles = []
        labels = []

        for s in (10, 5):
            handles.append(plt.Line2D([0],[0],color=line_color,
                                  linewidth=s*1e3/linewidth_factor))
            labels.append("{} GW".format(s))
        l1 = l1_1 = ax.legend(handles, labels,
                              loc="upper left", bbox_to_anchor=(0.24, 1.01),
                              framealpha=1,
                              labelspacing=0.8, handletextpad=1.5,
                              title='Transmission')
        ax.add_artist(l1_1)


    #else:
        techs = primary.index.levels[1]
        print(techs)
        techs = ['gas', 'solar PV', 'wind', 'hydro']
        handles = []
        labels = []
        for t in techs:
            handles.append(plt.Line2D([0], [0], color=snakemake.config['plotting']['tech_colors'][t], marker='o', markersize=8, linewidth=0))
            labels.append(t)
        l3 = ax.legend(handles, labels,
                       loc="upper left", bbox_to_anchor=(0.01, 0.79),
                       framealpha=1.,
                       handletextpad=0., columnspacing=0.5, ncol=2, title=None)

        ax.add_artist(l3)

    #ax.set_title("Scenario {} with {} transmission".format(snakemake.config['plotting']['scenario_names'][flex],"optimal" if line_limit == "opt" else "no"))
    #ax.set_title('Scenario Electricity')

    fig.tight_layout()

    #fig.savefig('../'+snakemake.config['summary_dir'] +  "version-{}/paper_graphics/spatial-{}-{}.pdf".format(snakemake.config['version'],flex,line_limit),transparent=True)
    fig.savefig('figures/spatial_plot_primary_energy_'+flex+'.png', #'figures/spatial_plot_primary_energy_'+flex+'.png',
                transparent=False, dpi=300, bbox_inches='tight')


def plot_electricity_generation(flex,line_limit, network_name):
    
    n = pypsa.Network(network_name)

    assign_groups(n)

    #Drop non-electric buses so they don't clutter the plot
    n.buses.drop(n.buses.index[n.buses.index.str.len() != 2],inplace=True)

    primary = pd.DataFrame(index=n.buses.index)

    primary["gas"] = n.stores_t.p[n.stores.index[n.stores.index.str[3:] == "gas Store"]].sum().rename(lambda x : x[:2])

    primary["hydroelectricity"] = n.storage_units_t.p[n.storage_units.index[n.storage_units.index.str[3:] == "hydro"]].sum().rename(lambda x : x[:2]).fillna(0.)

    n.generators["country"] = n.generators.index.str[:2]

    n.generators["nice_group"] = n.generators["group"].map(rename_techs)
  
    for carrier in n.generators.nice_group.value_counts().index:
        s = n.generators_t.p[n.generators.index[n.generators.nice_group == carrier]].sum().groupby(n.generators.country).sum().fillna(0.)
        
        if carrier in primary.columns:
            primary[carrier] += s
        else:
            primary[carrier] = s


    primary[primary < 0.] = 0.
    primary = primary.fillna(0.)
    print(primary)
    print(primary.sum())
    if flex=='elec_central':
        #drop solar thermal to plot only electricity generation
        primary.drop('solar thermal', axis=1, inplace=True)
    primary = primary.stack().sort_index()
    
    fig, ax = plt.subplots(1,1)

    fig.set_size_inches(6,4.3)

    bus_size_factor =1e8
    linewidth_factor=1e3
    line_color="m"

    n.buses.loc["NO",["x","y"]] = [9.5,61.5]


    line_widths_exp = pd.concat(dict(Line=n.lines.s_nom_opt, Link=n.links.p_nom_opt))


    dic_col={'solar':'gold', 'onwind':'blue', 'offwind':'blue',#'lightskyblue',
             'hidroelectricity':'green', 'gas':'brown'}
    n.plot(bus_sizes=primary/bus_size_factor,
           bus_colors=snakemake.config['plotting']['tech_colors'],
           line_colors=dict(Line=line_color, Link=line_color),
           line_widths=line_widths_exp/linewidth_factor,
           ax=ax, basemap=True)



    if line_limit != "0":

        handles = make_legend_circles_for([1e8, 3e7], scale=bus_size_factor, facecolor="gray")
        labels = ["{} TWh".format(s) for s in (100, 30)]
        l2 = ax.legend(handles, labels,
                       loc="upper left", bbox_to_anchor=(0.01, 1.01),
                       labelspacing=1.0,
                       framealpha=1.,
                       facecolor='white',
                       title='Electricity mix', #title='Primary energy',
                       handler_map=make_handler_map_to_scale_circles_as_in(ax))
        ax.add_artist(l2)

        handles = []
        labels = []

        for s in (10, 5):
            handles.append(plt.Line2D([0],[0],color=line_color,
                                  linewidth=s*1e3/linewidth_factor))
            labels.append("{} GW".format(s))
        l1 = l1_1 = ax.legend(handles, labels,
                              loc="upper left", bbox_to_anchor=(0.24, 1.01),
                              framealpha=1,
                              facecolor='white',
                              labelspacing=0.8, handletextpad=1.5,
                              title='Transmission')
        ax.add_artist(l1_1)


    #else:
        techs = primary.index.levels[1]
        print(techs)
        techs = ['gas', 'solar PV', 'wind', 'hydro']
        handles = []
        labels = []
        for t in techs:
            handles.append(plt.Line2D([0], [0], color=snakemake.config['plotting']['tech_colors'][t], marker='o', markersize=8, linewidth=0))
            labels.append(t)
        l3 = ax.legend(handles, labels,
                       loc="upper left", bbox_to_anchor=(0.01, 0.79),
                       framealpha=1.,
                       facecolor='white',
                       handletextpad=0., columnspacing=0.5, ncol=2, title=None)

        ax.add_artist(l3)

    #ax.set_title("Scenario {} with {} transmission".format(snakemake.config['plotting']['scenario_names'][flex],"optimal" if line_limit == "opt" else "no"))
    #ax.set_title('Scenario Electricity')

    fig.tight_layout()

    #fig.savefig('../'+snakemake.config['summary_dir'] +  "version-{}/paper_graphics/spatial-{}-{}.pdf".format(snakemake.config['version'],flex,line_limit),transparent=True)
    fig.savefig('figures/spatial_plot_electricity_generation_'+flex+'.png', #'figures/spatial_plot_primary_energy_'+flex+'.png',
                transparent=False, dpi=300, bbox_inches='tight')


def plot_demand(flex,line_limit, network_name):
#    file_name = '../'+ snakemake.config['results_dir'] \
#                + 'version-{version}/postnetworks/postnetwork-{flexibility}_{line_limits}.h5'.format(version=snakemake.config["version"],
#                                                                                                     flexibility=flex,
#                                                                                                     line_limits=line_limit)
    
    n = pypsa.Network(network_name)

    assign_groups(n)

    #Drop non-electric buses so they don't clutter the plot
    n.buses.drop(n.buses.index[n.buses.index.str.len() != 2],inplace=True)

    demand = pd.DataFrame(index=n.buses.index)

    demand['electricity'] = n.loads_t.p[n.loads.index[n.loads.index.str.len() == 2]].sum()
    demand['transport'] = n.loads_t.p[n.loads.index[n.loads.index.str[3:] == 'transport']].sum().rename(lambda x : x[:2])
    demand['heat'] = (n.loads_t.p[n.loads.index[n.loads.index.str[3:] == 'heat']].sum().rename(lambda x : x[:2]) +
                     n.loads_t.p[n.loads.index[n.loads.index.str[9:] == 'heat']].sum().rename(lambda x : x[:2]))

    demand[demand < 0.] = 0.
    demand = demand.fillna(0.)
    print(demand)
    print(demand.sum())
    demand = demand.stack().sort_index()

    fig, ax = plt.subplots(1,1)

    fig.set_size_inches(6,4.3)

    bus_size_factor =2e8#2e8
    linewidth_factor=2e3
    line_color="m"

    n.buses.loc["NO",["x","y"]] = [9.5,61.5]


    line_widths_exp = pd.concat(dict(Line=n.lines.s_nom_opt, Link=n.links.p_nom_opt))


    dic_col={'electricity':'black', 'heat':'orange', 'transport':'lightskyblue'}
    n.plot(bus_sizes=demand/bus_size_factor,
           bus_colors=dic_col,
           line_colors=dict(Line=line_color, Link=line_color),
           line_widths=line_widths_exp/linewidth_factor,
           ax=ax, basemap=True)



    if line_limit != "0":

        handles = make_legend_circles_for([2e8, 6e7], scale=bus_size_factor, facecolor="gray")
        labels = ["{} TWh".format(s) for s in (100, 30)]
        l2 = ax.legend(handles, labels,
                       loc="upper left", bbox_to_anchor=(0.01, 1.01),
                       labelspacing=1.0,
                       framealpha=1.,
                       facecolor='white',
                       title='Demand',
                       handler_map=make_handler_map_to_scale_circles_as_in(ax))
        ax.add_artist(l2)

        handles = []
        labels = []

        for s in (10, 5):
            handles.append(plt.Line2D([0],[0],color=line_color,
                                  linewidth=s*1e3/linewidth_factor))
            labels.append("{} GW".format(s))
        l1 = l1_1 = ax.legend(handles, labels,
                              loc="upper left", bbox_to_anchor=(0.24, 1.01),
                              facecolor='white',
                              framealpha=1.0,
                              labelspacing=0.8, 
                              handletextpad=1.5,
                              title='Transmission')
        ax.add_artist(l1_1)


    else:
        techs = primary.index.levels[1]
        handles = []
        labels = []
        for t in techs:
            handles.append(plt.Line2D([0], [0], color=snakemake.config['plotting']['tech_colors'][t], marker='o', markersize=8, linewidth=0))
            labels.append(t)
        l3 = ax.legend(handles, labels,
                       loc="upper left", bbox_to_anchor=(0.01, 1.01),
                       framealpha=1.,
                       handletextpad=0., columnspacing=0.5, ncol=1, title=None)

        ax.add_artist(l3)

    #ax.set_title("Scenario {} with {} transmission".format(snakemake.config['plotting']['scenario_names'][flex],"optimal" if line_limit == "opt" else "no"))
    ax.set_title('Scenario Electricity+Heating+Transport')

    fig.tight_layout()

    #fig.savefig('../'+snakemake.config['summary_dir'] +  "version-{}/paper_graphics/spatial-{}-{}.pdf".format(snakemake.config['version'],flex,line_limit),transparent=True)
    fig.savefig('figures/spatial_plot_demand.png',transparent=False, dpi=300)


def plot_storage(flex,line_limit,network_name, storage_tech): 
    dic_storage={'H2':'H2 Store', 'battery':'battery', 'PHS':'PHS', 
                 'CTES':'central water tank', 'ITES': 'water tank'}
    dic_scale={'H2':1., 'battery':10., 'PHS':10., 'CTES': 0.1, 'ITES': 1}
    dic_col={'H2':'m', 'battery':'gold', 'PHS':'green', 'CTES':'gray', 'ITES':'black'}
    n = pypsa.Network(network_name)
    
    #Drop non-electric buses so they don't clutter the plot
    n.buses.drop(n.buses.index[n.buses.index.str.len() != 2],inplace=True)
    storage = pd.DataFrame(index=n.buses.index)
    
    if storage_tech=='PHS':
        storage[storage_tech] = 6*n.storage_units.p_nom[n.storage_units.index[n.storage_units.carrier == 'PHS']].rename(lambda x : x[:2])
    if storage_tech=='ITES':    
        storage[storage_tech] = n.stores.e_nom_opt[n.stores.index[n.stores.index.str[3:] == 'water tank']].rename(lambda x : x[:2]) 
        for country in ['BG', 'ES','GR', 'IT', 'PT']:
            storage[storage_tech][country] += n.stores.e_nom_opt[country +  ' urban water tank']
    else:
        # rename change the index from 'AT H2 Store' to 'AT'    
        storage[storage_tech] = n.stores.e_nom_opt[n.stores.index[n.stores.index.str[3:] == dic_storage[storage_tech]]].rename(lambda x : x[:2])
    
    storage[storage < 0.] = 0.
    storage = storage.fillna(0.)
    print(storage)
    print(storage.sum())
    storage = storage.stack().sort_index()

    fig, ax = plt.subplots(1,1)
    fig.set_size_inches(6,4.3)
    
    bus_size_factor =1e6/dic_scale[storage_tech]
    linewidth_factor=5e9
    line_color="m"

    n.buses.loc["NO",["x","y"]] = [9.5,61.5]

    
    line_widths_exp = pd.concat(dict(Line=n.lines.s_nom_opt, Link=n.links.p_nom_opt))
    n.plot(bus_sizes=storage/bus_size_factor,
           bus_colors=dic_col,
           line_colors=dict(Line=line_color, Link=line_color),
           line_widths=line_widths_exp/linewidth_factor,
           ax=ax, basemap=True)
    #make legend
    if storage_tech == 'H2':
        handles = make_legend_circles_for([5e5, 1e6], scale=bus_size_factor, facecolor=dic_col[storage_tech])
        labels = ["{} TWh".format(s) for s in (0.5, 1)]
    elif storage_tech == 'battery':
        handles = make_legend_circles_for([5e4, 1e5], scale=bus_size_factor, facecolor=dic_col[storage_tech])
        labels = ["{} GWh".format(s) for s in (50, 100)]   
    elif storage_tech == 'PHS':
        handles = make_legend_circles_for([5e4, 1e5], scale=bus_size_factor, facecolor=dic_col[storage_tech])
        labels = ["{} GWh".format(s) for s in (50, 100)]  
    elif storage_tech == 'CTES':
        handles = make_legend_circles_for([5e6, 1e7], scale=bus_size_factor, facecolor=dic_col[storage_tech])
        labels = ["{} TWh".format(s) for s in (5, 10)]  
    elif storage_tech == 'ITES':
        handles = make_legend_circles_for([5e5, 1e6], scale=bus_size_factor, facecolor=dic_col[storage_tech])
        labels = ["{} TWh".format(s) for s in (0.5, 1)]        
        
    l2 = ax.legend(handles, labels,
                   loc="upper left", bbox_to_anchor=(0.01, 1.01),
                   labelspacing=1.0,
                   ncol=2,
                   framealpha=1.,
                   title='Energy capacity',
                   handler_map=make_handler_map_to_scale_circles_as_in(ax))
    ax.add_artist(l2)

    #ax.set_title(""))
    fig.tight_layout()
    fig.savefig('figures/spatial_plot_'+storage_tech+'_'+flex+'.png',transparent=False, dpi=300)

def plot_battery_H2(flex,line_limit,network_name): 
      
    n = pypsa.Network(network_name)
    
    #Drop non-electric buses so they don't clutter the plot
    n.buses.drop(n.buses.index[n.buses.index.str.len() != 2],inplace=True)
    
    fig, ax = plt.subplots(1,1)
    fig.set_size_inches(6,4.3)
    
    dic_storage={'H2':'H2 Store', 'battery':'battery', 'PHS':'PHS'}
    dic_scale={'H2':1., 'battery':10., 'PHS':10.}
    c_gold_alpha=[1., 0.8, 0.,  0.6]
    c_m_alpha=[0.75, 0., 0.75,  0.5]
    dic_col={'H2':c_m_alpha, 'battery':c_gold_alpha, 'PHS':'green'}
    
    for storage_tech in ['H2', 'battery']:
        storage = pd.DataFrame(index=n.buses.index)
    
        if storage_tech=='PHS':
            storage[storage_tech] = 6*n.storage_units.p_nom[n.storage_units.index[n.storage_units.carrier == 'PHS']].rename(lambda x : x[:2])
        else:
            # rename change the index from 'AT H2 Store' to 'AT'    
            storage[storage_tech] = n.stores.e_nom_opt[n.stores.index[n.stores.index.str[3:] == dic_storage[storage_tech]]].rename(lambda x : x[:2])
    
        storage[storage < 0.] = 0.
        storage = storage.fillna(0.)
        storage = storage.stack().sort_index()
        
        bus_size_factor =1e6/dic_scale[storage_tech]
        linewidth_factor=5e9
        line_color="m"

        n.buses.loc["NO",["x","y"]] = [9.5,61.5]
    
        line_widths_exp = pd.concat(dict(Line=n.lines.s_nom_opt, Link=n.links.p_nom_opt))
        n.plot(bus_sizes=storage/bus_size_factor,
               bus_colors=dic_col,
               line_colors=dict(Line=line_color, Link=line_color),
               line_widths=line_widths_exp/linewidth_factor,
               ax=ax, basemap=True)     
    storage_tech='battery'
    handles = make_legend_circles_for([5e4, 1e5], scale=1e6/dic_scale[storage_tech], facecolor=dic_col[storage_tech])
    labels = ["{} GWh".format(s) for s in (50, 100)] 
    storage_tech='H2'
    handles2 = make_legend_circles_for([5e5, 1e6], scale=1e6/dic_scale[storage_tech], facecolor=dic_col[storage_tech])
    labels2 = ["{} TWh".format(s) for s in (0.5, 1)]  

    
    l1 = ax.legend(handles, labels,
                   loc="upper left", bbox_to_anchor=(0.01, 1.01),
                   labelspacing=1.0,
                   ncol=2,
                   framealpha=1.,
                   title='Battery energy capacity',
                   handler_map=make_handler_map_to_scale_circles_as_in(ax))
    ax.add_artist(l1)
    
    l2 = ax.legend(handles2, labels2,
                   loc="upper left", bbox_to_anchor=(0.01, 0.86),
                   labelspacing=1.0,
                   ncol=2,
                   framealpha=1.,
                   title='Hydrogen energy capacity',
                   handler_map=make_handler_map_to_scale_circles_as_in(ax))
    ax.add_artist(l2)

    #ax.set_title(""))
    fig.tight_layout()
    fig.savefig('figures/spatial_plot_battery_H2_'+flex+'.png',transparent=False, dpi=300)

def plot_CTES_ITES(flex,line_limit,network_name): 
      
    n = pypsa.Network(network_name)
    
    #Drop non-electric buses so they don't clutter the plot
    n.buses.drop(n.buses.index[n.buses.index.str.len() != 2],inplace=True)
    
    fig, ax = plt.subplots(1,1)
    fig.set_size_inches(6,4.3)
    
    dic_storage={'H2':'H2 Store', 'battery':'battery', 'PHS':'PHS', 
                 'CTES':'central water tank', 'ITES': 'water tank'}
    dic_scale={'H2':1., 'battery':10., 'PHS':10., 'CTES': 0.1, 'ITES': 1}
        
    c_gray_alpha=[0., 0., 0.,  0.3]
    dic_col={'CTES':c_gray_alpha, 'ITES': 'black'}
    
    for storage_tech in ['ITES', 'CTES']:
        storage = pd.DataFrame(index=n.buses.index)
    
        if storage_tech=='ITES':    
            storage[storage_tech] = n.stores.e_nom_opt[n.stores.index[n.stores.index.str[3:] == 'water tank']].rename(lambda x : x[:2]) 
            for country in ['BG', 'ES','GR', 'IT', 'PT']:
                storage[storage_tech][country] += n.stores.e_nom_opt[country +  ' urban water tank']
        else:
            # rename change the index from 'AT H2 Store' to 'AT'    
            storage[storage_tech] = n.stores.e_nom_opt[n.stores.index[n.stores.index.str[3:] == dic_storage[storage_tech]]].rename(lambda x : x[:2])
    
        storage[storage < 0.] = 0.
        storage = storage.fillna(0.)
        storage = storage.stack().sort_index()
        
        bus_size_factor =1e6/dic_scale[storage_tech]
        linewidth_factor=5e9
        line_color="m"

        n.buses.loc["NO",["x","y"]] = [9.5,61.5]
    
        line_widths_exp = pd.concat(dict(Line=n.lines.s_nom_opt, Link=n.links.p_nom_opt))
        n.plot(bus_sizes=storage/bus_size_factor,
               bus_colors=dic_col,
               line_colors=dict(Line=line_color, Link=line_color),
               line_widths=line_widths_exp/linewidth_factor,
               ax=ax, basemap=True)     
    
    storage_tech='ITES'
    handles = make_legend_circles_for([5e5, 1e6], scale=1e6/dic_scale[storage_tech], facecolor=dic_col[storage_tech])
    labels = ["{} TWh".format(s) for s in (0.5, 1)] 
    storage_tech='CTES'
    handles2 = make_legend_circles_for([5e6, 1e7], scale=1e6/dic_scale[storage_tech], facecolor=dic_col[storage_tech])
    labels2 = ["{} TWh".format(s) for s in (5, 10)]  
         
    l1 = ax.legend(handles, labels,
                   loc="upper left", bbox_to_anchor=(0.01, 1.01),
                   labelspacing=1.0,
                   ncol=2,
                   framealpha=1.,
                   title='ITES energy capacity',
                   handler_map=make_handler_map_to_scale_circles_as_in(ax))
    ax.add_artist(l1)
    
    l2 = ax.legend(handles2, labels2,
                   loc="upper left", bbox_to_anchor=(0.01, 0.86),
                   labelspacing=1.0,
                   ncol=2,
                   framealpha=1.,
                   title='CTES energy capacity',
                   handler_map=make_handler_map_to_scale_circles_as_in(ax))
    ax.add_artist(l2)

    #ax.set_title(""))
    fig.tight_layout()
    fig.savefig('figures/spatial_plot_ITES_CTES_'+flex+'.png',transparent=False, dpi=300)
    
if __name__ == "__main__":
    # Detect running outside of snakemake and mock snakemake for testing
    if 'snakemake' not in globals():
        from vresutils import Dict
        import yaml
        snakemake = Dict()
        with open('config.yaml') as f:
            snakemake.config = yaml.load(f)
        snakemake.input = Dict()
        snakemake.output = Dict()
   
    snakemake = Dict()
    with open('config.yaml') as f:
        snakemake.config = yaml.load(f)
    
    #version-45  (transmission=2todays, weakly homogeneous, no CO2 price, decreasing CO2 limit)
    path = '/home/marta/Desktop/heavy_data_guest/PyPSA_out/version-86/postnetworks/'
    #flex= 'elec_only'  
    line_limit='opt'#'0.125'
    co2_limit = '0.05'
    flex='elec_only'
    network_name= path+'postnetwork-' +flex+'_'+ line_limit + '_' + co2_limit+ '.h5' 

    #plot_storage(flex,"0", network_name, 'H2')
    #plot_storage(flex,"0", network_name, 'battery')
    #plot_storage(flex,"0", network_name, 'PHS')
    #plot_battery_H2(flex,"0", network_name)   
    #plot_primary_energy(flex,"opt", network_name)
    plot_electricity_generation(flex,"opt", network_name)
    
    #flex= 'elec_central'  
    #network_name= path+'postnetwork-' +flex+'_'+ line_limit + '_' + co2_limit+ '.h5'     
    #plot_storage("elec_only","0", network_name, 'ITES')
    #plot_CTES_ITES("elec_only","0", network_name)
    
    #flex= 'elec_heat_v2g50'  
    #network_name= path+'postnetwork-' +flex+'_'+ line_limit + '_' + co2_limit+ '.h5'     
    #plot_demand("elec_heat_v2g100","opt", network_name)

