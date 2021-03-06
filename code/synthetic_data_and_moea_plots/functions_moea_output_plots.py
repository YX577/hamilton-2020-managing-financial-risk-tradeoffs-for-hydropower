##############################################################################################################
### functions_moea_output_plots.py - python functions used in analyzing and plotting outputs from multi-objective optimization
###     multi-objective optimization
### Project started May 2017, last update Jan 2020
##############################################################################################################

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
import seaborn as sns


sns.set_style('white')
sns.set_context('paper', font_scale=1.55)

eps = 1e-13

cmap = cm.get_cmap('viridis')
col = [cmap(0),cmap(0.15),cmap(0.6),cmap(0.85)]
# col = [cmap(0.1),cmap(0.3),cmap(0.6),cmap(0.8)]

palette = {'None':col[0], 'Fund':col[3], 'CFD':col[1], 'Fund+CFD':col[2]}
marker = {'None':'<', 'Fund':'o', 'CFD':'*', 'Fund+CFD':'+', 'Infeasible':'$i$'}
alpha = {'None':0.7, 'Fund':0.7, 'CFD':0.7, 'Fund+CFD':0.7, 'Infeasible':0.0}



#########################################################################
######### function to load output from moea. both baseline (p=150) & sensitivity analysis. ####
### returns dataframe. ####
# ##########################################################################
def get_moea_output(dir_generated_inputs, dir_moea_output, p_sfpuc, meanRevenue, minSnowContract, minMaxFund, debt_filter = True):
  param_list = pd.read_csv(dir_generated_inputs + 'param_LHC_sample_withLamPricing.txt', sep=' ')
  param_list['p'] = np.arange(param_list.shape[0])
  opt_2obj = pd.DataFrame(
    {'p': [], 'c': [], 'delta': [], 'Delta_fund': [], 'Delta_debt': [], 'lam': [], 'lam_capX_2': [], 
    'lam_capX_1': [], 'lam_capX_0': [], 'lam_capY_2': [], 'lam_capY_1': [], 'lam_capY_0': [],
     'max_fund': [], 'slope_cfd': [], 'exp_ann_cashflow_borg': [], 'q95_max_debt_borg': [],
     'constraint_borg': [],
     'exp_ann_cashflow_retest': [], 'q95_max_debt_retest': [], 'constraint_retest': []})
  for p in range(p_sfpuc+1):
    if (p == p_sfpuc):
      fil = dir_moea_output + 'baseline/param' + str(p) + '_borg_retest.resultfile'
    else:
      fil = dir_moea_output + 'sensitivity/param' + str(p) + '_borg_retest.resultfile'

    # read solns (retest) from moea output
    dum = pd.read_csv(fil,
                      header=None, sep='\t', index_col=False,
                      names=['max_fund', 'slope_cfd', 'exp_ann_cashflow_borg', 'q95_max_debt_borg',
                             'constraint_borg',
                             'exp_ann_cashflow_retest', 'q95_max_debt_retest', 'constraint_retest'])
    # add sensitivity sample parameter info
    dum['p'] = param_list.p.iloc[p]
    dum['c'] = param_list.c.iloc[p]
    dum['delta'] = param_list.delta.iloc[p]
    dum['Delta_fund'] = param_list.Delta_fund.iloc[p]
    dum['Delta_debt'] = param_list.Delta_debt.iloc[p]
    dum['lam'] = param_list.lam.iloc[p]
    dum['lam_capX_2'] = param_list.lam_capX_2.iloc[p]
    dum['lam_capX_1'] = param_list.lam_capX_1.iloc[p]
    dum['lam_capX_0'] = param_list.lam_capX_0.iloc[p]
    dum['lam_capY_2'] = param_list.lam_capY_2.iloc[p]
    dum['lam_capY_1'] = param_list.lam_capY_1.iloc[p]
    dum['lam_capY_0'] = param_list.lam_capY_0.iloc[p]

    dum['expected_net_revenue'] = meanRevenue * (1 - dum['c'])
    # enforce minimum values for decision variables, as followed in optimization
    dum['slope_cfd'].loc[dum['slope_cfd'] < minSnowContract] = 0
    dum['max_fund'].loc[dum['max_fund'] < minMaxFund] = 0
    # append
    opt_2obj = opt_2obj.append(dum)

  opt_2obj.exp_ann_cashflow_borg = -opt_2obj.exp_ann_cashflow_borg
  opt_2obj.exp_ann_cashflow_retest = -opt_2obj.exp_ann_cashflow_retest
  # del opt_2obj['exp_ann_cashflow_borg'], opt_2obj['q95_max_debt_borg'], opt_2obj['constraint_borg']
  opt_2obj = opt_2obj.reset_index(drop=True)

  ### filter out results that are infeasible or have q95_max_debt > 5
  if (debt_filter):
    opt_2obj = opt_2obj.loc[opt_2obj.q95_max_debt_retest / opt_2obj.expected_net_revenue < 5, :].reset_index(drop=True)

  ### plot based on risk management regime
  regime = np.zeros(opt_2obj.shape[0], dtype=int)
  regime[(opt_2obj.slope_cfd < eps) & (opt_2obj.max_fund > eps)] = 1
  regime[(opt_2obj.slope_cfd > eps) & (opt_2obj.max_fund < eps)] = 2
  regime[(opt_2obj.slope_cfd > eps) & (opt_2obj.max_fund > eps)] = 3
  regime[(opt_2obj.constraint_retest > eps)] = 4
  opt_2obj['Regime'] = 'a'
  opt_2obj.Regime.loc[regime == 0] = 'None'
  opt_2obj.Regime.loc[regime == 1] = 'Fund'
  opt_2obj.Regime.loc[regime == 2] = 'CFD'
  opt_2obj.Regime.loc[regime == 3] = 'Fund+CFD'
  opt_2obj.Regime.loc[regime == 4] = 'Infeasible'
  # opt_2obj = opt_2obj.loc[regime < 4]

  return(opt_2obj)





#########################################################################
######### plot pareto front for sfpuc baseline case (fig 8) ####
### outputs plot, no return. ####
# ##########################################################################
def plot_pareto_baseline(dir_figs, moea_solns, p_sfpuc, cases_sfpuc_index):
  ### plot tradeoff for particular parameter set
  plt.figure()
  plt.plot(moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime=='Fund+CFD')],
                 moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime=='Fund+CFD')],
                marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=2, markerfacecolor='none',
                c=palette['Fund+CFD'],alpha=0.4, ms=10,zorder=2)
  plt.plot(moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')],
                moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')],
                marker=marker['Fund'], linewidth=0, markeredgewidth=2, markerfacecolor='none',
                c=palette['Fund'], alpha=0.4, ms=8,zorder=2)
  m2, = plt.plot(moea_solns.exp_ann_cashflow_retest.iloc[cases_sfpuc_index[0]],
                 moea_solns.q95_max_debt_retest.iloc[cases_sfpuc_index[0]],
                 marker=marker['Fund'], linewidth=0, markeredgewidth=2, markerfacecolor='none',
                 c=palette['Fund'], alpha=1, ms=8)
  plt.annotate('A', xy=(moea_solns.exp_ann_cashflow_retest.iloc[cases_sfpuc_index[0]]+0.03,
                 moea_solns.q95_max_debt_retest.iloc[cases_sfpuc_index[0]]-1.0))
  plt.plot(moea_solns.exp_ann_cashflow_retest.iloc[cases_sfpuc_index[1]],
           moea_solns.q95_max_debt_retest.iloc[cases_sfpuc_index[1]],
           marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=2, markerfacecolor='none',
           c=palette['Fund+CFD'], alpha=1, ms=10, zorder=2)
  plt.annotate('B', xy=(moea_solns.exp_ann_cashflow_retest.iloc[cases_sfpuc_index[1]]+0.015,
                 moea_solns.q95_max_debt_retest.iloc[cases_sfpuc_index[1]]-2.2))
  m1, = plt.plot(moea_solns.exp_ann_cashflow_retest.iloc[cases_sfpuc_index[2]],
                 moea_solns.q95_max_debt_retest.iloc[cases_sfpuc_index[2]],
                 marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=2, markerfacecolor='none',
                 c=palette['Fund+CFD'], alpha=1, ms=10)
  plt.annotate('C', xy=(moea_solns.exp_ann_cashflow_retest.iloc[cases_sfpuc_index[2]]-0.02,
                 moea_solns.q95_max_debt_retest.iloc[cases_sfpuc_index[2]]-2.5))
  dum = moea_solns.loc[(moea_solns.p == p_sfpuc)].copy()
  dum = dum.loc[dum.Regime != 'Infeasible']
  dum.sort_values(by='exp_ann_cashflow_retest', inplace=True) 
  plt.plot(dum.exp_ann_cashflow_retest, dum.q95_max_debt_retest , linewidth=1, c='0.5', alpha=0.5, zorder=1)
  plt.plot([11],[0.2],marker='*',ms=15,c='0.6')
  plt.annotate('Ideal', xy=(10.9,1.5),color='0.6')
  plt.legend([m2,m1], ['Fund','Fund+CFD'], loc='upper left')
  plt.ylabel(r"$\leftarrow$ Q95 Max Debt $\left(J^{debt}\right)$")
  plt.xlabel(r"Expected Annualized Cash Flow $\left(J^{cash}\right)\rightarrow$")
  plt.savefig(dir_figs + 'fig_paretoBaseline.jpg', bbox_inches='tight', dpi=1200)



##########################################################################
######### calculate cash flow after withdrawal (deposit) from (to) reserve fund ####
### returns scalar. ####
# ##########################################################################
def get_cashflow_post_withdrawal(fund_balance, cash_in, cashflow_target, maxFund):
  if (cash_in < cashflow_target):
    if (fund_balance < eps):
      x = cash_in
    else:
      x = min(cash_in + fund_balance, cashflow_target)
  else:
    if (fund_balance > (maxFund - eps)):
      x = cash_in + (fund_balance - maxFund)
    else:
      x = max(cash_in - (maxFund - fund_balance), cashflow_target)
  return(x)



##########################################################################
######### unit payout for cfd function with given params for given swe  ###########
############## Return payout value #########################################
##########################################################################
def cfd_unit_payout(sweWt, cfdCapX, cfdCapY):
  if sweWt >= cfdCapX:
    return cfdCapY
  else:
    return cfdCapY + (cfdCapX - sweWt)



##########################################################################
######### Run single random simulation with given cfd slope & max fund  ###########
############## Return set of objectives #########################################
##########################################################################
def single_sim(revenue_sample, sweWt_sample, fixedCostFraction, meanRevenue, maxFund, slopeCfd, 
                        interestFund, interestDebt, cfdCapX, cfdCapY, discFactor, discNorm, nYears):

  net_revenue = revenue_sample - meanRevenue * fixedCostFraction
  fund_balance = [0]  # reserve fund balance starts at zero
  debt = [0]  # debt starts at zero
  withdrawal = []  # withdrawal
  net_payout = []
  cash_in = []
  final_cashflow = []  # net_revenue post
  for i in range(0, nYears):
    net_payout.append(slopeCfd * cfd_unit_payout(sweWt_sample[i], cfdCapX, cfdCapY))
    # cash flow after recieving revenues (net of fixed cost), plus net payout cfd, minus debt (plus interest) from last year
    cash_in.append(net_revenue[i] + net_payout[i] - debt[i] * interestDebt)
    # rule for withdrawal (or deposit), after growing fund at interestFund from last year
    final_cashflow.append(get_cashflow_post_withdrawal(fund_balance[i] * interestFund, cash_in[i], 0, maxFund))
    withdrawal.append(final_cashflow[i] - cash_in[i])
    fund_balance.append(fund_balance[i] * interestFund - withdrawal[i])  # adjust reserve based on withdrawal (deposit)
    # if insufficient cash to pay off debt and still be above costs, take on more debt, which grows by interestDebt next year
    if (final_cashflow[i] < -eps):
      debt.append(-final_cashflow[i])
      final_cashflow[i] = 0.0
    else:
      debt.append(0)

  return(net_revenue, net_payout, cash_in, fund_balance, debt, withdrawal, final_cashflow)




##########################################################################
######### Run single random simulation with given cfd slope & max fund  ###########
############## Return set of objectives #########################################
##########################################################################
def single_sim_objectives(revenue_sample, sweWt_sample, fixedCostFraction, meanRevenue, maxFund, slopeCfd, 
                        interestFund, interestDebt, cfdCapX, cfdCapY, discFactor, discNorm, nYears):

  net_revenue, net_payout, cash_in, fund_balance, debt, withdrawal, final_cashflow = single_sim(revenue_sample, sweWt_sample, fixedCostFraction, meanRevenue, 
                                                                            maxFund, slopeCfd, interestFund, interestDebt, cfdCapX, cfdCapY,
                                                                            discFactor, discNorm, nYears)


  # sub-objectives for simulation
  objectives_1sim = []
  # annualized cash flow
  objectives_1sim.append(discNorm * (np.sum((discFactor * final_cashflow)) +
                                     (fund_balance[-1] * interestFund * discFactor[0] -
                                      debt[-1] * interestDebt * discFactor[0]) * discFactor[-1]))

  # max debt
  objectives_1sim.append(np.max(debt))
  # debt constraint
  objectives_1sim.append(debt[-1] - debt[-2])

  return (objectives_1sim)




##########################################################################
######### Run nSamples simulations with given cfd slope & max fund ###########
############## Returns set of objectives #########################################
##########################################################################
def monte_carlo_objectives(synthetic_data, fixedCostFraction, meanRevenue, maxFund, slopeCfd, interestFund, interestDebt,
                         discountRate, cfdCapX, cfdCapY, nYears, nSamples, set_seed, full_output, sample_starts=[0]):

  objectives_1sim = np.array([])
  if (len(sample_starts) == 1):
    if (set_seed > 0):
      np.random.seed(set_seed)
    sample_starts = np.random.choice(range(1, synthetic_data.shape[0] - nYears), size=nSamples)

  discFactor = discountRate ** np.array(range(1,nYears+1))
  discNorm = 1 / np.sum(discFactor)
  for s in range(0, len(sample_starts)):
    objectives_1sim = np.append(objectives_1sim,
                                single_sim_objectives(
                                  synthetic_data.revenue.iloc[sample_starts[s]:(sample_starts[s] + nYears)].values,
                                  synthetic_data.sweWt.iloc[sample_starts[s]:(sample_starts[s] + nYears)].values,
                                  fixedCostFraction, meanRevenue, maxFund, slopeCfd, interestFund, interestDebt,
                                  cfdCapX, cfdCapY, discFactor, discNorm, nYears))
  if (full_output):
    return (objectives_1sim)
  else:
    objectives_mc = [np.mean(objectives_1sim[::3]),
                     np.quantile(objectives_1sim[1::3],0.95),
                     np.mean(objectives_1sim[2::3])]
    return(objectives_mc)




#########################################################################
######### plot distribution of state variables over historical period for 3 cases, baseline params (fig 9) ####
### outputs plot, no return. ####
# ##########################################################################
def plot_example_simulations(dir_figs, moea_solns_filtered, params_sfpuc, cases_sfpuc_index, historical_data, meanRevenue):
  solns = moea_solns_filtered.iloc[cases_sfpuc_index,:]
  fixedCostFraction = params_sfpuc['c']
  historical_data['netrev'] = historical_data['rev'] - meanRevenue * fixedCostFraction
  discountRate = 1 / (params_sfpuc['delta'] / 100 + 1)
  interestFund = (params_sfpuc['Delta_fund'] + params_sfpuc['delta']) / 100 + 1
  interestDebt = (params_sfpuc['Delta_debt'] + params_sfpuc['delta']) / 100 + 1
  cfdWtFeb = 0.311962707367
  cfdCapX = params_sfpuc['lam_capX_2'] * cfdWtFeb**2 + params_sfpuc['lam_capX_1'] * cfdWtFeb + params_sfpuc['lam_capX_0']
  cfdCapY = params_sfpuc['lam_capY_2'] * cfdWtFeb**2 + params_sfpuc['lam_capY_1'] * cfdWtFeb + params_sfpuc['lam_capY_0']
  historical_data['sweWt'] = cfdWtFeb * historical_data['sweFeb'] + (1 - cfdWtFeb) * historical_data['sweApr']
  
  nYears = historical_data.shape[0]
  discFactor = discountRate ** np.array(range(1,nYears+1))
  discNorm = 1 / np.sum(discFactor)

  fig = plt.figure(figsize=(6,10))
  gs1 = fig.add_gridspec(nrows=4, ncols=2, left=0, right=1, wspace=0.05, hspace=0.1)

  ax = fig.add_subplot(gs1[0,0])
  ax.annotate('a)', xy=(0.01, 0.89), xycoords='axes fraction')
  ax.set_ylabel('SWE Index\n(inch)')
  ax.set_xlabel('Year')
  ax.set_yticks([10,25,40])
  # ax.set_xticks(np.arange(0.85, 0.98, 0.04))
  ax.tick_params(axis='y',which='both',labelleft=True,labelright=False)
  ax.tick_params(axis='x',which='both',labelbottom=False,labeltop=True)
  ax.xaxis.set_label_position('top')
  # ax.yaxis.set_label_position('right')
  plt.plot(historical_data['sweWt'], c='k')

  ax0 = fig.add_subplot(gs1[0,1], sharex=ax)
  ax0.annotate('b)', xy=(0.01, 0.89), xycoords='axes fraction')
  ax0.set_ylabel('Generation\n(TWh)', rotation=270, labelpad=35)
  ax0.set_xlabel('Year')
  ax0.set_yticks([1.2, 1.7, 2.2])
  ax0.tick_params(axis='y',which='both',labelleft=False,labelright=True)
  ax0.tick_params(axis='x',which='both',labelbottom=False,labeltop=True)
  ax0.xaxis.set_label_position('top')
  ax0.yaxis.set_label_position('right')
  ax0.plot(historical_data['gen'], c='k')

  ax0 = fig.add_subplot(gs1[1,0], sharex=ax)
  ax0.annotate('c)', xy=(0.01, 0.89), xycoords='axes fraction')
  ax0.set_ylabel('Wholesale Price\n(\$/MWh)')
  # ax0.set_xlabel('Year')
  # ax0.set_xticks(np.arange(0.85, 0.98, 0.04))
  ax0.tick_params(axis='y',which='both',labelleft=True,labelright=False)
  ax0.tick_params(axis='x',which='both',labelbottom=False,labeltop=False)
  # ax0.xaxis.set_label_position('top')
  # ax0.yaxis.set_label_position('right')
  ax0.plot(historical_data['pow'], c='k')

  ax0 = fig.add_subplot(gs1[1,1], sharex=ax)
  ax0.annotate('d)', xy=(0.01, 0.89), xycoords='axes fraction')
  ax0.set_ylabel('Net Revenue\n(\$M)', rotation=270, labelpad=35)
  # ax0.set_xlabel('Year')
  # ax0.set_xticks(np.arange(0.85, 0.98, 0.04))
  ax0.tick_params(axis='y',which='both',labelleft=False,labelright=True)
  ax0.tick_params(axis='x',which='both',labelbottom=False,labeltop=False)
  # ax0.xaxis.set_label_position('top')
  ax0.yaxis.set_label_position('right')
  ax0.axhline(0, color='0.5', ls=':', zorder=1)
  l0, = ax0.plot(historical_data['netrev'], c='k')

  ax1 = fig.add_subplot(gs1[2,0], sharex=ax)
  ax2 = fig.add_subplot(gs1[2,1], sharex=ax)
  ax3 = fig.add_subplot(gs1[3,0], sharex=ax)
  ax4 = fig.add_subplot(gs1[3,1], sharex=ax)

  # ax1 = plt.subplot2grid((4,2),(2,0),sharex=ax)#,rowspan=2,colspan=2)
  # ax2 = plt.subplot2grid((4,2),(2,1),sharex=ax)#,rowspan=2,colspan=2)
  # ax3 = plt.subplot2grid((4,2),(3,0),sharex=ax)#,rowspan=2,colspan=2)
  # ax4 = plt.subplot2grid((4,2),(3,1),sharex=ax)#,rowspan=2,colspan=2)


  for i in range(3):
    vals = single_sim(historical_data['rev'].values, historical_data['sweWt'].values, params_sfpuc['c'], meanRevenue,
                                                  solns['max_fund'].iloc[i], solns['slope_cfd'].iloc[i], 
                                                  interestFund, interestDebt, cfdCapX, cfdCapY, 
                                                  discFactor, discNorm, nYears)

    cfd, fund, debt, wd, cf4 = vals[1], vals[3], vals[4], vals[5], vals[6]

    #     objs = single_sim_objectives(historical_data['rev'].values, historical_data['cfd'].values, params_sfpuc['c'], meanRevenue,
#                                                   solns['max_fund'].iloc[i], solns['slope_cfd'].iloc[i], 
#                                                   interestFund, interestDebt, params_sfpuc['lam_prem_shift'], 
#                                                   discFactor, discNorm, nYears)
    
    if i==0:
      ax1.annotate('e)', xy=(0.01, 0.89), xycoords='axes fraction')
      ax1.set_ylabel('CFD Payout\n(\$M)')
      # ax.set_xlabel('Year')
      # ax.set_xticks(np.arange(0.85, 0.98, 0.04))
      ax1.tick_params(axis='y',which='both',labelleft=True,labelright=False)
      ax1.tick_params(axis='x',which='both',labelbottom=False,labeltop=False)
      # ax.xaxis.set_label_position('top')
      # ax.yaxis.set_label_position('right')
      ax1.set_yticks([-15,0,15])
      ax1.axhline(0, color='0.5', ls=':', zorder=1)
      l1, = ax1.plot(range(1988,2017), cfd, c=col[3-i])
    elif i == 1:
      l2, = ax1.plot(range(1988,2017), cfd, c=col[3-i])
    else:
      l3, = ax1.plot(range(1988,2017), cfd, c=col[3-i])

    if i==0:
      ax2.annotate('f)', xy=(0.01, 0.89), xycoords='axes fraction')
      ax2.set_ylabel('Fund Balance\n(\$M)', rotation=270, labelpad=35)
      # ax.set_xlabel('Year')
      # ax.set_xticks(np.arange(0.85, 0.98, 0.04))
      ax2.tick_params(axis='y',which='both',labelleft=False,labelright=True)
      ax2.tick_params(axis='x',which='both',labelbottom=False,labeltop=False)
      # ax.xaxis.set_label_position('top')
      ax2.yaxis.set_label_position('right')
      ax2.axhline(0, color='0.5', ls=':', zorder=1)
    ax2.plot(range(1988,2018), fund, c=col[3-i])

    if i==0:
      ax3.annotate('g)', xy=(0.01, 0.89), xycoords='axes fraction')
      ax3.set_ylabel('Debt\n(\$M)')
      ax3.set_xlabel('Year')
      # ax3.set_xticks(np.arange(0.85, 0.98, 0.04))
      ax3.tick_params(axis='y',which='both',labelleft=True,labelright=False)
      ax3.tick_params(axis='x',which='both',labelbottom=True,labeltop=False)
      # ax3.xaxis.set_label_position('top')
      # ax3.yaxis.set_label_position('right')
      ax3.axhline(0, color='0.5', ls=':', zorder=1)
    ax3.plot(range(1988,2018), debt, c=col[3-i])

    if i==0:
      ax4.annotate('h)', xy=(0.01, 0.89), xycoords='axes fraction')
      ax4.set_ylabel('Final Cashflow\n(\$M)', rotation=270, labelpad=35)
      ax4.set_xlabel('Year')
      # ax4.set_xticks(np.arange(0.85, 0.98, 0.04))
      ax4.tick_params(axis='y',which='both',labelleft=False,labelright=True)
      ax4.tick_params(axis='x',which='both',labelbottom=True,labeltop=False)
      # ax4.xaxis.set_label_position('top')
      ax4.yaxis.set_label_position('right')
      ax4.axhline(0, color='0.5', ls=':', zorder=1)
    ax4.plot(range(1988,2017), cf4, c=col[3-i])

  ax3.legend([l0, l1, l2, l3],['External Driver','Policy A','Policy B','Policy C'], ncol=4, bbox_to_anchor=(2.26,-0.35))#, fontsize=12)

  plt.savefig(dir_figs + 'fig_historicalSim.jpg', bbox_inches='tight', dpi=1200)

  return



#########################################################################
######### get monte carlo sub-objectives for 3 cases, baseline params ####
###  ####
# ##########################################################################
def get_distribution_objectives(dir_figs, synthetic_data, moea_solns, cases_sfpuc_index, params_sfpuc, meanRevenue, nYears):

  fixedCostFraction = params_sfpuc['c']
  discountRate = 1 / (params_sfpuc['delta'] / 100 + 1)
  interestFund = (params_sfpuc['Delta_fund'] + params_sfpuc['delta']) / 100 + 1
  interestDebt = (params_sfpuc['Delta_debt'] + params_sfpuc['delta']) / 100 + 1
  cfdWtFeb = 0.311962707367
  cfdCapX = params_sfpuc['lam_capX_2'] * cfdWtFeb**2 + params_sfpuc['lam_capX_1'] * cfdWtFeb + params_sfpuc['lam_capX_0']
  cfdCapY = params_sfpuc['lam_capY_2'] * cfdWtFeb**2 + params_sfpuc['lam_capY_1'] * cfdWtFeb + params_sfpuc['lam_capY_0']
  synthetic_data['sweWt'] = cfdWtFeb * synthetic_data['sweFeb'] + (1 - cfdWtFeb) * synthetic_data['sweApr']

  cases_sfpuc_max_fund = moea_solns.max_fund.values[cases_sfpuc_index]
  cases_sfpuc_slope_cfd = moea_solns.slope_cfd.values[cases_sfpuc_index]
  cases_sfpuc_Jcash = moea_solns.exp_ann_cashflow_retest.values[cases_sfpuc_index]
  cases_sfpuc_Jdebt = moea_solns.q95_max_debt_retest.values[cases_sfpuc_index]

  # Run nSamples of nYears each and calculate objectives & constraint
  sample_starts = [0]
  objectivesA = monte_carlo_objectives(synthetic_data, fixedCostFraction, meanRevenue,
                                    cases_sfpuc_max_fund[0], cases_sfpuc_slope_cfd[0], interestFund, interestDebt,
                                    discountRate, cfdCapX, cfdCapY, nYears, 50000, set_seed=6, full_output=True,
                                    sample_starts=sample_starts)
  objectivesB = monte_carlo_objectives(synthetic_data, fixedCostFraction, meanRevenue,
                                    cases_sfpuc_max_fund[1], cases_sfpuc_slope_cfd[1], interestFund, interestDebt,
                                    discountRate, cfdCapX, cfdCapY, nYears, 50000, set_seed=6, full_output=True,
                                    sample_starts=sample_starts)
  objectivesC = monte_carlo_objectives(synthetic_data, fixedCostFraction, meanRevenue,
                                    cases_sfpuc_max_fund[2], cases_sfpuc_slope_cfd[2], interestFund, interestDebt,
                                    discountRate, cfdCapX, cfdCapY, nYears, 50000, set_seed=6, full_output=True,
                                    sample_starts=sample_starts)

  return (objectivesA, objectivesB, objectivesC)


#########################################################################
######### plot distribution of sub-objectives for 3 cases, baseline params (fig 9) ####
### outputs plot, no return. ####
# ##########################################################################

def plot_distribution_objectives(dir_figs, synthetic_data, moea_solns, cases_sfpuc_index, params_sfpuc, meanRevenue, nYears, objectivesA, objectivesB, objectivesC):

  fixedCostFraction = params_sfpuc['c']
  discountRate = 1 / (params_sfpuc['delta'] / 100 + 1)
  interestFund = (params_sfpuc['Delta_fund'] + params_sfpuc['delta']) / 100 + 1
  interestDebt = (params_sfpuc['Delta_debt'] + params_sfpuc['delta']) / 100 + 1
  cfdWtFeb = 0.311962707367
  cfdCapX = params_sfpuc['lam_capX_2'] * cfdWtFeb**2 + params_sfpuc['lam_capX_1'] * cfdWtFeb + params_sfpuc['lam_capX_0']
  cfdCapY = params_sfpuc['lam_capY_2'] * cfdWtFeb**2 + params_sfpuc['lam_capY_1'] * cfdWtFeb + params_sfpuc['lam_capY_0']
  synthetic_data['sweWt'] = cfdWtFeb * synthetic_data['sweFeb'] + (1 - cfdWtFeb) * synthetic_data['sweApr']

  cases_sfpuc_max_fund = moea_solns.max_fund.values[cases_sfpuc_index]
  cases_sfpuc_slope_cfd = moea_solns.slope_cfd.values[cases_sfpuc_index]
  cases_sfpuc_Jcash = moea_solns.exp_ann_cashflow_retest.values[cases_sfpuc_index]
  cases_sfpuc_Jdebt = moea_solns.q95_max_debt_retest.values[cases_sfpuc_index]

  maxxCash = max(max(objectivesA[::3]), max(objectivesB[::3]), max(objectivesC[::3]))
  nbins = 40
  bins = list(np.arange(0.01, maxxCash+0.05, (maxxCash+0.02)/nbins))
  bins.insert(0, -0.01)
  aCash = plt.hist(objectivesA[::3], bins=bins, density=True, alpha=0.6, color=col[0])#, bins=np.arange(0,44)/2)
  bCash = plt.hist(objectivesB[::3], bins=bins, density=True, alpha=0.6, color=col[2])#, bins=np.arange(0,44)/2)
  cCash = plt.hist(objectivesC[::3], bins=bins, density=True, alpha=0.6, color=col[3])#, bins=np.arange(0,44)/2)
  centersCash = (np.array(bins[:-1]) + np.array(bins[1:])) / 2


  maxxDebt = max(max(objectivesA[1::3]), max(objectivesB[1::3]), max(objectivesC[1::3]))
  nbins = 40
  bins = list(np.arange(0.01, maxxDebt+0.05, (maxxDebt+0.02)/nbins))
  bins.insert(0, -0.01)
  aDebt = plt.hist(objectivesA[1::3], bins=bins, density=True, alpha=0.6, color=col[0])#, bins=np.arange(0,44)/2)
  bDebt = plt.hist(objectivesB[1::3], bins=bins, density=True, alpha=0.6, color=col[2])#, bins=np.arange(0,44)/2)
  cDebt = plt.hist(objectivesC[1::3], bins=bins, density=True, alpha=0.6, color=col[3])#, bins=np.arange(0,44)/2)
  centersDebt = (np.array(bins[:-1]) + np.array(bins[1:])) / 2

  plt.figure(figsize=(8,3))
  ax = plt.subplot2grid((1,2), (0, 0))
  ax.annotate('a)', xy=(0.01, 0.89), xycoords='axes fraction')
  ax.set_xlabel('Annualized Cash Flow\n($M/year)')
  ax.set_ylabel('Density')
  ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
  ax.set_ylim([0, 0.28])
  ax.set_xlim([0, 20])
  
  ax.plot(centersCash, aCash[0], color=col[3], linewidth=2)
  ax.plot(centersCash, bCash[0], color=col[2], linewidth=2)
  ax.plot(centersCash, cCash[0], color=col[0], linewidth=2)
  ax.fill_between(centersCash, aCash[0], color=col[3], alpha=0.1)
  ax.fill_between(centersCash, bCash[0], color=col[2], alpha=0.1)
  ax.fill_between(centersCash, cCash[0], color=col[0], alpha=0.1)
  ax.axvline(x=cases_sfpuc_Jcash[0], color=col[3], linewidth=2, linestyle='--')
  ax.axvline(x=cases_sfpuc_Jcash[1], color=col[2], linewidth=2, linestyle='--')
  ax.axvline(x=cases_sfpuc_Jcash[2], color=col[0], linewidth=2, linestyle='--')

  ax.legend(['A','B','C'], loc='lower left', bbox_to_anchor=(0.6, -0.53), ncol=3, borderaxespad=0.)
  
  ax2 = plt.subplot2grid((1,2), (0, 1))
  ax2.annotate('b)', xy=(0.91, 0.89), xycoords='axes fraction')
  ax2.set_xlabel('Max Debt\n($M)')
  ax2.set_ylabel('Density')
  ax2.tick_params(axis='y', which='both', labelleft=False, labelright=False)
  ax2.yaxis.set_label_position('right')
  ax2.set_ylim([0, 0.07])
  ax2.set_xlim([0, 40])
  
  ax2.plot(centersDebt, aDebt[0], color=col[3], linewidth=2)
  ax2.plot(centersDebt, bDebt[0], color=col[2], linewidth=2)
  ax2.plot(centersDebt, cDebt[0], color=col[0], linewidth=2)
  ax2.fill_between(centersDebt, aDebt[0], color=col[3], alpha=0.1)
  ax2.fill_between(centersDebt, bDebt[0], color=col[2], alpha=0.1)
  ax2.fill_between(centersDebt, cDebt[0], color=col[0], alpha=0.1)
  ax2.axvline(x=cases_sfpuc_Jdebt[0], color=col[3], linewidth=2, linestyle='--')
  ax2.axvline(x=cases_sfpuc_Jdebt[1], color=col[2], linewidth=2, linestyle='--')
  ax2.axvline(x=cases_sfpuc_Jdebt[2], color=col[0], linewidth=2, linestyle='--')

  plt.savefig(dir_figs + 'fig_distributionObjectives.jpg', bbox_inches='tight',  dpi=1200)

  return


#########################################################################
######### plot tradeoff cloud of pareto fronts for sensitivity analysis (fig 10/S8) ####
### outputs plot, no return. ####
# ##########################################################################
def plot_tradeoff_cloud(dir_figs, moea_solns, meanRevenue, p_sfpuc, debt_filter):
  ### plot tradeoff cloud for sensitivity analysis
  plt.figure()
  m1, = plt.plot(moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.Regime == 'Fund+CFD')] /
                 (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.Regime == 'Fund+CFD')])),
                 moea_solns.q95_max_debt_retest.loc[(moea_solns.Regime == 'Fund+CFD')] /
                 (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.Regime == 'Fund+CFD')])),
                 marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                 c=palette['Fund+CFD'], alpha=0.5,zorder=2)  # , ms=10)
  m2, = plt.plot(moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.Regime == 'Fund')] /
                 (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.Regime == 'Fund')])),
                 moea_solns.q95_max_debt_retest.loc[(moea_solns.Regime == 'Fund')] /
                 (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.Regime == 'Fund')])),
                 marker=marker['Fund'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                 c=palette['Fund'], alpha=0.5,zorder=2)  # , ms=8)
  m3, = plt.plot(moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.Regime == 'CFD')] /
                 (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.Regime == 'CFD')])),
                 moea_solns.q95_max_debt_retest.loc[(moea_solns.Regime == 'CFD')] /
                 (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.Regime == 'CFD')])),
                 marker=marker['CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                 c=palette['CFD'], alpha=0.5,zorder=3)  # , ms=8)
  plt.plot(moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc)].iloc[0])),
           moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc)].iloc[0])),
           marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
           c='k', alpha=0.7,zorder=4)
  plt.plot(moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc)].iloc[0])),
           moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc)].iloc[0])),
           marker=marker['Fund'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
           c='k', alpha=0.7,zorder=4)
  for p in set(moea_solns.p):
    dum = moea_solns.loc[(moea_solns.p == p)].copy()
    dum = dum.loc[dum.Regime != 'Infeasible']
    if (dum.shape[0] > 0):
      dum.sort_values(by='exp_ann_cashflow_retest', inplace=True) 
      if (p==p_sfpuc):
        plt.plot(dum.exp_ann_cashflow_retest / (meanRevenue * (1 - dum.c.iloc[0])),
                dum.q95_max_debt_retest / (meanRevenue * (1 - dum.c.iloc[0])),
                linewidth=1, c='k', alpha=0.7, zorder=1)
      else:
        plt.plot(dum.exp_ann_cashflow_retest / (meanRevenue * (1 - dum.c.iloc[0])),
                dum.q95_max_debt_retest / (meanRevenue * (1 - dum.c.iloc[0])),
                linewidth=1, c='0.5', alpha=0.3, zorder=1)  

  # if (debt_filter):
  plt.plot([1], [0], marker='*', ms=15, c='0.6')
    # plt.annotate('Ideal', xy=(0.975, -0.35), color='0.6')
    # plt.ylim([-0.4, 5.4])
  plt.ylabel(r"$\leftarrow$ Normalized Q95 Max Debt $\left(\hat{J}^{debt}\right)$")
  plt.xlabel(r"Normalized Expected Annualized Cash Flow $\left(\hat{J}^{cash}\right)\rightarrow$")
  if (debt_filter):
    plt.legend([m2, m3, m1], ['Fund', 'CFD', 'Fund+CFD'], loc='lower left', bbox_to_anchor=(0.06, -0.30), ncol=3, borderaxespad=0.)
    plt.savefig(dir_figs + 'fig_cloudFiltered.jpg', bbox_inches='tight', dpi=1200)
  else:
    plt.legend([m2, m3, m1], ['Fund', 'CFD', 'Fund+CFD'], loc='lower left', bbox_to_anchor=(0.06, -0.30), ncol=3, borderaxespad=0.)
    plt.savefig(dir_figs + 'fig_cloudUnfiltered.jpg', bbox_inches='tight', dpi=1200)

  return





#########################################################################
######### plot sensitivity analysis for debt objective (fig 11/S9) ####
### outputs plot, no return. ####
# ##########################################################################
def plot_sensitivity_debt(dir_figs, moea_solns, p_sfpuc, debt_filter):
  ### plot regime as function of normalized debt and uncertain params
  plt.figure()
  ax = plt.subplot2grid((2,4),(0,0),rowspan=2,colspan=2)
  ax.annotate('a)', xy=(0.01, 0.95), xycoords='axes fraction')
  ax.set_xlabel('$c$')
  ax.set_ylabel('$\leftarrow\hat{J}^{debt}$')
  ax.set_xticks(np.arange(0.85, 0.98, 0.04))
  if (debt_filter):
    # ax.set_xlim([0.84,0.98])
    ax.set_yticks(np.arange(0, 6))
  else:
    ax.set_yticks(np.arange(0, 36, 5))
  for xp, yp, colp, mp in zip(moea_solns.c.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')],
                              moea_solns.q95_max_debt_retest.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')] /
                              moea_solns.expected_net_revenue.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')],
                              [palette[i] for i in moea_solns.Regime.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')]],
                              [marker[i] for i in moea_solns.Regime.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')]]):
    ax.plot(xp, yp, c=colp, marker=mp, alpha=0.7, linewidth=0, markeredgewidth=1, markerfacecolor='none',zorder=2)

  m1, = ax.plot(moea_solns.c.loc[(moea_solns.Regime=='Fund+CFD')].iloc[0], moea_solns.q95_max_debt_retest.loc[(moea_solns.Regime=='Fund+CFD')].iloc[0] /
                              moea_solns.expected_net_revenue.loc[(moea_solns.Regime=='Fund+CFD')].iloc[0],
                marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1, markerfacecolor='none',
                c=palette['Fund+CFD'],alpha=0.3)
  m2, = ax.plot(moea_solns.c.loc[(moea_solns.Regime == 'Fund')].iloc[0],
                moea_solns.q95_max_debt_retest.loc[(moea_solns.Regime == 'Fund')].iloc[0] /
                              moea_solns.expected_net_revenue.loc[(moea_solns.Regime=='Fund')].iloc[0],
                marker=marker['Fund'], linewidth=0, markeredgewidth=1, markerfacecolor='none',
                c=palette['Fund'], alpha=0.3)
  m3, = ax.plot(moea_solns.c.loc[moea_solns.Regime=='None'],moea_solns.q95_max_debt_retest.loc[moea_solns.Regime=='None'] /
                              moea_solns.expected_net_revenue.loc[(moea_solns.Regime=='None')],
             marker = marker['None'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['None'],alpha=alpha['None'])
  m4, = ax.plot(moea_solns.c.loc[moea_solns.Regime=='CFD'],moea_solns.q95_max_debt_retest.loc[moea_solns.Regime=='CFD'] /
                              moea_solns.expected_net_revenue.loc[(moea_solns.Regime=='CFD')],
             marker = marker['CFD'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['CFD'],alpha=alpha['CFD'])
  plt.plot(moea_solns.c.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')],
                moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')] /
                              moea_solns.expected_net_revenue.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')],
                marker=marker['Fund'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                c='k', alpha=0.7,zorder=3)
  plt.plot(moea_solns.c.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')],
                moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')] /
                              moea_solns.expected_net_revenue.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')],
                marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                c='k', alpha=0.7,zorder=3)
  for p in set(moea_solns.p):
    dum = moea_solns.loc[(moea_solns.p == p)].copy()
    dum = dum.loc[dum.Regime != 'Infeasible']
    dum.sort_values(by='exp_ann_cashflow_retest', inplace=True) 
    if (p==p_sfpuc):
      plt.plot(dum.c , dum.q95_max_debt_retest / dum.expected_net_revenue,
              linewidth=1, c='k', alpha=0.7, zorder=3)
    else:
      plt.plot(dum.c , dum.q95_max_debt_retest / dum.expected_net_revenue,
              linewidth=1, c='0.5', alpha=0.3, zorder=1)  
  ax.legend([(m2,m2,m2,m2,m2,m2,m2,m2,m2,m2,m2,m2,m2,m2,m2,m2,m2),(m4,m4,m4,m4,m4),
             (m1,m1,m1,m1,m1,m1,m1,m1,m1,m1,m1,m1,m1,m1,m1,m1,m1)],['Fund','CFD','Fund+CFD'], 
             loc='lower left', bbox_to_anchor=(0.08, -0.27), ncol=3, borderaxespad=0.)

  ax = plt.subplot2grid((2,4),(0,2))
  ax.annotate('b)', xy=(0.01, 0.89), xycoords='axes fraction')
  ax.set_xlabel('$\delta$')
  ax.xaxis.set_label_position('top')
  ax.set_xticks(np.arange(0,6,5))
  ax.tick_params(axis='y',which='both',labelleft=False)
  ax.tick_params(axis='x',which='both',labelbottom=False,labeltop=True)
  for xp, yp, colp, mp in zip(moea_solns.delta.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')],
                              moea_solns.q95_max_debt_retest.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')] /
                              moea_solns.expected_net_revenue.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')],
                              [palette[i] for i in moea_solns.Regime.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')]],
                              [marker[i] for i in moea_solns.Regime.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')]]):
    ax.plot(xp, yp, c=colp, marker=mp, alpha=0.7, linewidth=0, markeredgewidth=1, markerfacecolor='none',zorder=2)
  m3, = ax.plot(moea_solns.delta.loc[moea_solns.Regime=='None'],moea_solns.q95_max_debt_retest.loc[moea_solns.Regime=='None'] /
                moea_solns.expected_net_revenue.loc[moea_solns.Regime=='None'],
             marker = marker['None'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['None'],alpha=alpha['None'])
  m4, = ax.plot(moea_solns.delta.loc[moea_solns.Regime=='CFD'],moea_solns.q95_max_debt_retest.loc[moea_solns.Regime=='CFD'] /
                moea_solns.expected_net_revenue.loc[moea_solns.Regime=='CFD'],
             marker = marker['CFD'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['CFD'],alpha=alpha['CFD'])
  plt.plot(moea_solns.delta.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')],
                moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')] /
           moea_solns.expected_net_revenue.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')],
                marker=marker['Fund'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                c='k', alpha=0.7,zorder=3)
  plt.plot(moea_solns.delta.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')],
                moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')] /
           moea_solns.expected_net_revenue.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')],
                marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                c='k', alpha=0.7,zorder=3)
  for p in set(moea_solns.p):
    dum = moea_solns.loc[(moea_solns.p == p)].copy()
    dum = dum.loc[dum.Regime != 'Infeasible']
    dum.sort_values(by='exp_ann_cashflow_retest', inplace=True) 
    if (p==p_sfpuc):
      plt.plot(dum.delta , dum.q95_max_debt_retest / dum.expected_net_revenue,
              linewidth=1, c='k', alpha=0.7, zorder=3)
    else:
      plt.plot(dum.delta , dum.q95_max_debt_retest / dum.expected_net_revenue,
              linewidth=1, c='0.5', alpha=0.3, zorder=1)  

  ax = plt.subplot2grid((2,4),(1,2))
  ax.annotate('d)', xy=(0.01, 0.89), xycoords='axes fraction')
  ax.set_xlabel('$\Delta_F$')
  ax.set_xticks(np.arange(-2, 0.5, 2))
  ax.tick_params(axis='y',which='both',labelleft=False)
  ax.tick_params(axis='x',which='both',labelbottom=True,labeltop=False)
  for xp, yp, colp, mp in zip(moea_solns.Delta_fund.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')],
                              moea_solns.q95_max_debt_retest.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')] /
                              moea_solns.expected_net_revenue.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')],
                              [palette[i] for i in moea_solns.Regime.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')]],
                              [marker[i] for i in moea_solns.Regime.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')]]):
    ax.plot(xp, yp, c=colp, marker=mp, alpha=0.7, linewidth=0, markeredgewidth=1, markerfacecolor='none',zorder=2)
  m3, = ax.plot(moea_solns.Delta_fund.loc[moea_solns.Regime=='None'],moea_solns.q95_max_debt_retest.loc[moea_solns.Regime=='None'] /
                moea_solns.expected_net_revenue.loc[moea_solns.Regime=='None'],
             marker = marker['None'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['None'],alpha=alpha['None'])
  m4, = ax.plot(moea_solns.Delta_fund.loc[moea_solns.Regime=='CFD'],moea_solns.q95_max_debt_retest.loc[moea_solns.Regime=='CFD'] /
                moea_solns.expected_net_revenue.loc[moea_solns.Regime=='CFD'],
             marker = marker['CFD'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['CFD'],alpha=alpha['CFD'])
  plt.plot(moea_solns.Delta_fund.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')],
                moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')] /
           moea_solns.expected_net_revenue.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')],
                marker=marker['Fund'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                c='k', alpha=0.7,zorder=3)
  plt.plot(moea_solns.Delta_fund.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')],
                moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')] /
           moea_solns.expected_net_revenue.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')],
                marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                c='k', alpha=0.7,zorder=3)
  for p in set(moea_solns.p):
    dum = moea_solns.loc[(moea_solns.p == p)].copy()
    dum = dum.loc[dum.Regime != 'Infeasible']
    dum.sort_values(by='exp_ann_cashflow_retest', inplace=True) 
    if (p==p_sfpuc):
      plt.plot(dum.Delta_fund , dum.q95_max_debt_retest / dum.expected_net_revenue,
              linewidth=1, c='k', alpha=0.7, zorder=3)
    else:
      plt.plot(dum.Delta_fund , dum.q95_max_debt_retest / dum.expected_net_revenue,
              linewidth=1, c='0.5', alpha=0.3, zorder=1) 

  ax = plt.subplot2grid((2,4),(1,3))
  ax.annotate('e)', xy=(0.01, 0.89), xycoords='axes fraction')
  ax.set_xlabel('$\Delta_D$')
  ax.set_ylabel(r"$\hat{J}^{debt}\rightarrow$",  rotation=270, labelpad=20)
  ax.yaxis.set_label_position('right')
  ax.set_xticks(np.arange(0, 6, 5))
  if (debt_filter):
    ax.set_yticks(np.arange(0, 6, 5))
  else:
    ax.set_yticks(np.arange(0,21,20))
  ax.tick_params(axis='y',which='both',labelleft=False,labelright=True)
  ax.tick_params(axis='x',which='both',labelbottom=True,labeltop=False)
  for xp, yp, colp, mp in zip(moea_solns.Delta_debt.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')],
                              moea_solns.q95_max_debt_retest.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')] /
                              moea_solns.expected_net_revenue.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')],
                              [palette[i] for i in moea_solns.Regime.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')]],
                              [marker[i] for i in moea_solns.Regime.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')]]):
    ax.plot(xp, yp, c=colp, marker=mp, alpha=0.7, linewidth=0, markeredgewidth=1, markerfacecolor='none',zorder=2)
  m3, = ax.plot(moea_solns.Delta_debt.loc[moea_solns.Regime=='None'],moea_solns.q95_max_debt_retest.loc[moea_solns.Regime=='None'] /
                moea_solns.expected_net_revenue.loc[moea_solns.Regime=='None'],
             marker = marker['None'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['None'],alpha=alpha['None'])
  m4, = ax.plot(moea_solns.Delta_debt.loc[moea_solns.Regime=='CFD'],moea_solns.q95_max_debt_retest.loc[moea_solns.Regime=='CFD'] /
                moea_solns.expected_net_revenue.loc[moea_solns.Regime=='CFD'],
             marker = marker['CFD'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['CFD'],alpha=alpha['CFD'])
  plt.plot(moea_solns.Delta_debt.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')],
                moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')] /
           moea_solns.expected_net_revenue.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')],
                marker=marker['Fund'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                c='k', alpha=0.7,zorder=3)
  plt.plot(moea_solns.Delta_debt.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')],
                moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')] /
           moea_solns.expected_net_revenue.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')],
                marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                c='k', alpha=0.7,zorder=3)
  for p in set(moea_solns.p):
    dum = moea_solns.loc[(moea_solns.p == p)].copy()
    dum = dum.loc[dum.Regime != 'Infeasible']
    dum.sort_values(by='exp_ann_cashflow_retest', inplace=True) 
    if (p==p_sfpuc):
      plt.plot(dum.Delta_debt , dum.q95_max_debt_retest / dum.expected_net_revenue,
              linewidth=1, c='k', alpha=0.7, zorder=3)
    else:
      plt.plot(dum.Delta_debt , dum.q95_max_debt_retest / dum.expected_net_revenue,
              linewidth=1, c='0.5', alpha=0.3, zorder=1) 

  ax = plt.subplot2grid((2,4),(0,3))
  ax.annotate('c)', xy=(0.01, 0.89), xycoords='axes fraction')
  ax.set_xlabel('$\lambda$')
  ax.xaxis.set_label_position('top')
  ax.set_ylabel(r"$\hat{J}^{debt}\rightarrow$",  rotation=270, labelpad=20)
  ax.yaxis.set_label_position('right')
  ax.set_xticks(np.arange(0, 0.6, 0.5))
  if (debt_filter):
    ax.set_yticks(np.arange(0, 6, 5))
  else:
    ax.set_yticks(np.arange(0,21,20))
  ax.tick_params(axis='y',which='both',labelleft=False,labelright=True)
  ax.tick_params(axis='x',which='both',labelbottom=False,labeltop=True)
  for xp, yp, colp, mp in zip(moea_solns.lam.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')],
                              moea_solns.q95_max_debt_retest.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')] /
                              moea_solns.expected_net_revenue.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')],
                              [palette[i] for i in moea_solns.Regime.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')]],
                              [marker[i] for i in moea_solns.Regime.loc[(moea_solns.Regime=='Fund')|(moea_solns.Regime=='Fund+CFD')]]):
    ax.plot(xp, yp, c=colp, marker=mp, alpha=0.7, linewidth=0, markeredgewidth=1, markerfacecolor='none',zorder=2)
  m3, = ax.plot(moea_solns.lam.loc[moea_solns.Regime=='None'],moea_solns.q95_max_debt_retest.loc[moea_solns.Regime=='None'] /
                moea_solns.expected_net_revenue.loc[moea_solns.Regime=='None'],
             marker = marker['None'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['None'],alpha=alpha['None'])
  m4, = ax.plot(moea_solns.lam.loc[moea_solns.Regime=='CFD'],moea_solns.q95_max_debt_retest.loc[moea_solns.Regime=='CFD'] /
                moea_solns.expected_net_revenue.loc[moea_solns.Regime=='CFD'],
             marker = marker['CFD'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['CFD'],alpha=alpha['CFD'])
  plt.plot(moea_solns.lam.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')],
                moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')] /
           moea_solns.expected_net_revenue.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund')],
                marker=marker['Fund'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                c='k', alpha=0.7,zorder=3)
  plt.plot(moea_solns.lam.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')],
                moea_solns.q95_max_debt_retest.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')] /
           moea_solns.expected_net_revenue.loc[(moea_solns.p == p_sfpuc)&(moea_solns.Regime == 'Fund+CFD')],
                marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
                c='k', alpha=0.7,zorder=3)
  for p in set(moea_solns.p):
    dum = moea_solns.loc[(moea_solns.p == p)].copy()
    dum = dum.loc[dum.Regime != 'Infeasible']
    dum.sort_values(by='exp_ann_cashflow_retest', inplace=True) 
    if (p==p_sfpuc):
      plt.plot(dum.lam , dum.q95_max_debt_retest / dum.expected_net_revenue,
              linewidth=1, c='k', alpha=0.7, zorder=3)
    else:
      plt.plot(dum.lam , dum.q95_max_debt_retest / dum.expected_net_revenue,
              linewidth=1, c='0.5', alpha=0.3, zorder=1) 
  if (debt_filter):
    plt.savefig(dir_figs + 'fig_sensitivityDebtFiltered.jpg', bbox_inches='tight', dpi=1200)
  else:
    plt.savefig(dir_figs + 'fig_sensitivityDebtUnfiltered.jpg', bbox_inches='tight', dpi=1200)

  return







#########################################################################
######### plot sensitivity analysis for cash flow objective (fig 12/S10) ####
### outputs plot, no return. ####
# ##########################################################################
def plot_sensitivity_cashflow(dir_figs, moea_solns, p_sfpuc, meanRevenue, debt_filter):
  ### plot regime as function of normalized annualized revenue and uncertain params
  plt.figure()
  ax = plt.subplot2grid((2, 4), (0, 0), rowspan=2, colspan=2)
  ax.annotate('a)', xy=(0.01, 0.02), xycoords='axes fraction')
  ax.set_xlabel('$c$')
  ax.set_ylabel(r"$\hat{J}^{cash}\rightarrow$")
  ax.set_xticks(np.arange(0.85, 0.98, 0.04))
  if (debt_filter):
    ax.set_xlim([0.84, 0.98])
  ax.set_yticks(np.arange(0.5, 1.01, 0.1))
  for xp, yp, colp, mp in zip(moea_solns.c.loc[(moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')],
                              moea_solns.exp_ann_cashflow_retest.loc[
                                (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')] /
                              (meanRevenue * (1 - moea_solns.c.loc[
                                (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')])),
                              [palette[i] for i in moea_solns.Regime.loc[
                                (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')]],
                              [marker[i] for i in moea_solns.Regime.loc[
                                (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')]]):
    ax.plot(xp, yp, c=colp, marker=mp, alpha=0.7, linewidth=0, markeredgewidth=1, markerfacecolor='none', zorder=2)

  m1, = ax.plot(moea_solns.c.loc[(moea_solns.Regime == 'Fund+CFD')].iloc[0],
                moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.Regime == 'Fund+CFD')].iloc[0] /
                (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.Regime == 'Fund+CFD')].iloc[0])),
                marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1, markerfacecolor='none',
                c=palette['Fund+CFD'], alpha=0.3)
  m2, = ax.plot(moea_solns.c.loc[(moea_solns.Regime == 'Fund')].iloc[0],
                moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.Regime == 'Fund')].iloc[0] /
                (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.Regime == 'Fund')].iloc[0])),
                marker=marker['Fund'], linewidth=0, markeredgewidth=1, markerfacecolor='none',
                c=palette['Fund'], alpha=0.3)
  m3, = ax.plot(moea_solns.c.loc[moea_solns.Regime == 'None'],
                moea_solns.exp_ann_cashflow_retest.loc[moea_solns.Regime == 'None'] /
                (meanRevenue * (1 - moea_solns.c.loc[moea_solns.Regime == 'None'])),
                marker=marker['None'], linewidth=0, markeredgewidth=1, markerfacecolor='none',
                c=palette['None'], alpha=alpha['None'])
  m4, = ax.plot(moea_solns.c.loc[moea_solns.Regime == 'CFD'],
                moea_solns.exp_ann_cashflow_retest.loc[moea_solns.Regime == 'CFD'] /
                (meanRevenue * (1 - moea_solns.c.loc[moea_solns.Regime == 'CFD'])),
                marker=marker['CFD'], linewidth=0, markeredgewidth=1,
                markerfacecolor='none', c=palette['CFD'], alpha=alpha['CFD'])
  plt.plot(moea_solns.c.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')],
           moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')])),
           marker=marker['Fund'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
           c='k', alpha=0.7, zorder=3)
  plt.plot(moea_solns.c.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')],
           moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')])),
           marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
           c='k', alpha=0.7, zorder=3)
  for p in set(moea_solns.p):
    dum = moea_solns.loc[(moea_solns.p == p)].copy()
    dum = dum.loc[dum.Regime != 'Infeasible']
    dum.sort_values(by='exp_ann_cashflow_retest', inplace=True) 
    if (p==p_sfpuc):
      plt.plot(dum.c , dum.exp_ann_cashflow_retest / dum.expected_net_revenue,
              linewidth=1, c='k', alpha=0.7, zorder=3)
    else:
      plt.plot(dum.c , dum.exp_ann_cashflow_retest / dum.expected_net_revenue,
              linewidth=1, c='0.5', alpha=0.3, zorder=1)  
  ax.legend([(m2, m2, m2, m2, m2, m2, m2, m2, m2, m2, m2, m2, m2, m2, m2, m2, m2), (m4, m4, m4, m4, m4),
             (m1, m1, m1, m1, m1, m1, m1, m1, m1, m1, m1, m1, m1, m1, m1, m1, m1)], ['Fund', 'CFD', 'Fund+CFD'], 
             loc='lower left', bbox_to_anchor=(0.08, -0.27), ncol=3, borderaxespad=0)

  ax = plt.subplot2grid((2, 4), (0, 2))
  ax.annotate('b)', xy=(0.01, 0.04), xycoords='axes fraction')
  ax.set_xlabel('$\delta$')
  ax.xaxis.set_label_position('top')
  ax.set_xticks(np.arange(0, 6, 5))
  ax.tick_params(axis='y', which='both', labelleft=False)
  ax.tick_params(axis='x', which='both', labelbottom=False, labeltop=True)
  for xp, yp, colp, mp in zip(moea_solns.delta.loc[(moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')],
                              moea_solns.exp_ann_cashflow_retest.loc[
                                (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')] /
                              (meanRevenue * (
                                      1 - moea_solns.c.loc[
                                (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')])),
                              [palette[i] for i in moea_solns.Regime.loc[
                                (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')]],
                              [marker[i] for i in moea_solns.Regime.loc[
                                (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')]]):
    ax.plot(xp, yp, c=colp, marker=mp, alpha=0.7, linewidth=0, markeredgewidth=1, markerfacecolor='none', zorder=2)
  m3, = ax.plot(moea_solns.delta.loc[moea_solns.Regime == 'None'],
                moea_solns.exp_ann_cashflow_retest.loc[moea_solns.Regime == 'None'] /
                (meanRevenue * (1 - moea_solns.c.loc[moea_solns.Regime == 'None'])),
                marker=marker['None'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['None'],
                alpha=alpha['None'])
  m4, = ax.plot(moea_solns.delta.loc[moea_solns.Regime == 'CFD'],
                moea_solns.exp_ann_cashflow_retest.loc[moea_solns.Regime == 'CFD'] /
                (meanRevenue * (1 - moea_solns.c.loc[moea_solns.Regime == 'CFD'])),
                marker=marker['CFD'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['CFD'],
                alpha=alpha['CFD'])
  plt.plot(moea_solns.delta.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')],
           moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')])),
           marker=marker['Fund'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
           c='k', alpha=0.7, zorder=3)
  plt.plot(moea_solns.delta.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')],
           moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')])),
           marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
           c='k', alpha=0.7, zorder=3)
  for p in set(moea_solns.p):
    dum = moea_solns.loc[(moea_solns.p == p)].copy()
    dum = dum.loc[dum.Regime != 'Infeasible']
    dum.sort_values(by='exp_ann_cashflow_retest', inplace=True) 
    if (p==p_sfpuc):
      plt.plot(dum.delta , dum.exp_ann_cashflow_retest / dum.expected_net_revenue,
              linewidth=1, c='k', alpha=0.7, zorder=3)
    else:
      plt.plot(dum.delta , dum.exp_ann_cashflow_retest / dum.expected_net_revenue,
              linewidth=1, c='0.5', alpha=0.3, zorder=1)  

  ax = plt.subplot2grid((2, 4), (1, 2))
  ax.annotate('d)', xy=(0.01, 0.04), xycoords='axes fraction')
  ax.set_xlabel('$\Delta_F$')
  ax.set_xticks(np.arange(-2, 1, 2))
  ax.tick_params(axis='y', which='both', labelleft=False)
  ax.tick_params(axis='x', which='both', labelbottom=True, labeltop=False)
  for xp, yp, colp, mp in zip(
          moea_solns.Delta_fund.loc[(moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')],
          moea_solns.exp_ann_cashflow_retest.loc[
            (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')] /
          (meanRevenue * (
                  1 - moea_solns.c.loc[(moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')])),
          [palette[i] for i in
           moea_solns.Regime.loc[(moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')]],
          [marker[i] for i in
           moea_solns.Regime.loc[(moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')]]):
    ax.plot(xp, yp, c=colp, marker=mp, alpha=0.7, linewidth=0, markeredgewidth=1, markerfacecolor='none', zorder=2)
  m3, = ax.plot(moea_solns.Delta_fund.loc[moea_solns.Regime == 'None'],
                moea_solns.exp_ann_cashflow_retest.loc[moea_solns.Regime == 'None'] /
                (meanRevenue * (1 - moea_solns.c.loc[moea_solns.Regime == 'None'])),
                marker=marker['None'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['None'],
                alpha=alpha['None'])
  m4, = ax.plot(moea_solns.Delta_fund.loc[moea_solns.Regime == 'CFD'],
                moea_solns.exp_ann_cashflow_retest.loc[moea_solns.Regime == 'CFD'] /
                (meanRevenue * (1 - moea_solns.c.loc[moea_solns.Regime == 'CFD'])),
                marker=marker['CFD'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['CFD'],
                alpha=alpha['CFD'])
  plt.plot(moea_solns.Delta_fund.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')],
           moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')])),
           marker=marker['Fund'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
           c='k', alpha=0.7, zorder=3)
  plt.plot(moea_solns.Delta_fund.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')],
           moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')])),
           marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
           c='k', alpha=0.7, zorder=3)
  for p in set(moea_solns.p):
    dum = moea_solns.loc[(moea_solns.p == p)].copy()
    dum = dum.loc[dum.Regime != 'Infeasible']
    dum.sort_values(by='exp_ann_cashflow_retest', inplace=True) 
    if (p==p_sfpuc):
      plt.plot(dum.Delta_fund , dum.exp_ann_cashflow_retest / dum.expected_net_revenue,
              linewidth=1, c='k', alpha=0.7, zorder=3)
    else:
      plt.plot(dum.Delta_fund , dum.exp_ann_cashflow_retest / dum.expected_net_revenue,
              linewidth=1, c='0.5', alpha=0.3, zorder=1)  

  ax = plt.subplot2grid((2, 4), (1, 3))
  ax.annotate('e)', xy=(0.01, 0.04), xycoords='axes fraction')
  ax.set_xlabel('$\Delta_D$')
  ax.set_ylabel('$\leftarrow\hat{J}^{cash}$', rotation=270, labelpad=20)
  ax.yaxis.set_label_position('right')
  ax.set_xticks(np.arange(0, 6, 5))
  ax.set_yticks(np.arange(0.6, 1.1, 0.4))
  ax.tick_params(axis='y', which='both', labelleft=False, labelright=True)
  ax.tick_params(axis='x', which='both', labelbottom=True, labeltop=False)
  for xp, yp, colp, mp in zip(
          moea_solns.Delta_debt.loc[(moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')],
          moea_solns.exp_ann_cashflow_retest.loc[
            (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')] /
          (meanRevenue * (
                  1 - moea_solns.c.loc[(moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')])),
          [palette[i] for i in
           moea_solns.Regime.loc[(moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')]],
          [marker[i] for i in
           moea_solns.Regime.loc[(moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')]]):
    ax.plot(xp, yp, c=colp, marker=mp, alpha=0.7, linewidth=0, markeredgewidth=1, markerfacecolor='none', zorder=2)
  m3, = ax.plot(moea_solns.Delta_debt.loc[moea_solns.Regime == 'None'],
                moea_solns.exp_ann_cashflow_retest.loc[moea_solns.Regime == 'None'] /
                (meanRevenue * (1 - moea_solns.c.loc[moea_solns.Regime == 'None'])),
                marker=marker['None'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['None'],
                alpha=alpha['None'])
  m4, = ax.plot(moea_solns.Delta_debt.loc[moea_solns.Regime == 'CFD'],
                moea_solns.exp_ann_cashflow_retest.loc[moea_solns.Regime == 'CFD'] /
                (meanRevenue * (1 - moea_solns.c.loc[moea_solns.Regime == 'CFD'])),
                marker=marker['CFD'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['CFD'],
                alpha=alpha['CFD'])
  plt.plot(moea_solns.Delta_debt.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')],
           moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')])),
           marker=marker['Fund'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
           c='k', alpha=0.7, zorder=3)
  plt.plot(moea_solns.Delta_debt.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')],
           moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')])),
           marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
           c='k', alpha=0.7, zorder=3)
  for p in set(moea_solns.p):
    dum = moea_solns.loc[(moea_solns.p == p)].copy()
    dum = dum.loc[dum.Regime != 'Infeasible']
    dum.sort_values(by='exp_ann_cashflow_retest', inplace=True) 
    if (p==p_sfpuc):
      plt.plot(dum.Delta_debt , dum.exp_ann_cashflow_retest / dum.expected_net_revenue,
              linewidth=1, c='k', alpha=0.7, zorder=3)
    else:
      plt.plot(dum.Delta_debt , dum.exp_ann_cashflow_retest / dum.expected_net_revenue,
              linewidth=1, c='0.5', alpha=0.3, zorder=1)  

  ax = plt.subplot2grid((2, 4), (0, 3))
  ax.annotate('c)', xy=(0.01, 0.04), xycoords='axes fraction')
  ax.set_xlabel('$\lambda$')
  ax.xaxis.set_label_position('top')
  ax.set_ylabel('$\leftarrow\hat{J}^{cash}$', rotation=270, labelpad=20)
  ax.yaxis.set_label_position('right')
  ax.set_xticks(np.arange(0, 0.6, 0.5))
  ax.set_yticks(np.arange(0.6, 1.1, 0.4))
  ax.tick_params(axis='y', which='both', labelleft=False, labelright=True)
  ax.tick_params(axis='x', which='both', labelbottom=False, labeltop=True)
  for xp, yp, colp, mp in zip(moea_solns.lam.loc[(moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')],
                              moea_solns.exp_ann_cashflow_retest.loc[
                                (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')] /
                              (meanRevenue * (
                                      1 - moea_solns.c.loc[
                                (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')])),
                              [palette[i] for i in moea_solns.Regime.loc[
                                (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')]],
                              [marker[i] for i in moea_solns.Regime.loc[
                                (moea_solns.Regime == 'Fund') | (moea_solns.Regime == 'Fund+CFD')]]):
    ax.plot(xp, yp, c=colp, marker=mp, alpha=0.7, linewidth=0, markeredgewidth=1, markerfacecolor='none', zorder=2)
  m3, = ax.plot(moea_solns.lam.loc[moea_solns.Regime == 'None'],
                moea_solns.exp_ann_cashflow_retest.loc[moea_solns.Regime == 'None'] /
                (meanRevenue * (1 - moea_solns.c.loc[moea_solns.Regime == 'None'])),
                marker=marker['None'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['None'],
                alpha=alpha['None'])
  m4, = ax.plot(moea_solns.lam.loc[moea_solns.Regime == 'CFD'],
                moea_solns.exp_ann_cashflow_retest.loc[moea_solns.Regime == 'CFD'] /
                (meanRevenue * (1 - moea_solns.c.loc[moea_solns.Regime == 'CFD'])),
                marker=marker['CFD'], linewidth=0, markeredgewidth=1, markerfacecolor='none', c=palette['CFD'],
                alpha=alpha['CFD'])
  plt.plot(moea_solns.lam.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')],
           moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund')])),
           marker=marker['Fund'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
           c='k', alpha=0.7, zorder=3)
  plt.plot(moea_solns.lam.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')],
           moea_solns.exp_ann_cashflow_retest.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')] /
           (meanRevenue * (1 - moea_solns.c.loc[(moea_solns.p == p_sfpuc) & (moea_solns.Regime == 'Fund+CFD')])),
           marker=marker['Fund+CFD'], linewidth=0, markeredgewidth=1.5, markerfacecolor='none',
           c='k', alpha=0.7, zorder=3)
  for p in set(moea_solns.p):
    dum = moea_solns.loc[(moea_solns.p == p)].copy()
    dum = dum.loc[dum.Regime != 'Infeasible']
    dum.sort_values(by='exp_ann_cashflow_retest', inplace=True) 
    if (p==p_sfpuc):
      plt.plot(dum.lam , dum.exp_ann_cashflow_retest / dum.expected_net_revenue,
              linewidth=1, c='k', alpha=0.7, zorder=3)
    else:
      plt.plot(dum.lam , dum.exp_ann_cashflow_retest / dum.expected_net_revenue,
              linewidth=1, c='0.5', alpha=0.3, zorder=1)  

  if (debt_filter):
    plt.savefig(dir_figs + 'fig_sensitivityCashFiltered.jpg', bbox_inches='tight', dpi=1200)
  else:
    plt.savefig(dir_figs + 'fig_sensitivityCashUnfiltered.jpg', bbox_inches='tight', dpi=1200)

  return








#########################################################################
######### get runtime metrics for single moea run ####
### outputs dataframe ####
# ##########################################################################
def get_metrics_single(metric_file, hv_file, p, s):
  # read data
  df = pd.read_csv(metric_file, sep=' ')
  names = list(df.columns)
  names[0] = names[0].replace('#','')
  df.columns = names
  df['p'] = p
  df['s'] = s
  df = df[['p', 's', 'Hypervolume','GenerationalDistance','EpsilonIndicator']]
  hv = pd.read_csv(hv_file, sep=' ', header=None)
  df['Hypervolume'] /= hv.iloc[0,0]
  df = pd.DataFrame(np.array([[p,s,0,np.nan,np.nan]]), columns=['p','s','Hypervolume','GenerationalDistance','EpsilonIndicator']).append(df, ignore_index=True)
  return df


#########################################################################
######### get runtime metrics for all moea runs, baseline and sensitivity analysis ####
### outputs dataframe ####
# ##########################################################################
def get_metrics_all(dir_moea_output, p_sfpuc, nSeedsBase, nSeedsSensitivity):
  ### first get metrics for sfpuc base case
  metrics_seedsBase = []
  p = p_sfpuc
  for s in range(1, nSeedsBase+1):
    metric_file = dir_moea_output + 'baseline/metrics/param' + str(p) + '_seedS1_seedB' + str(s) + '.metrics'
    hv_file = dir_moea_output + 'baseline/param' + str(p) +'_borg.hypervolume'
    metrics_seedsBase.append(get_metrics_single(metric_file, hv_file, p, s))

  ### now do same for sensitivity analysis samples
  metrics_seedsSensitivity = []
  p_successes = []
  for p in range(p_sfpuc):
    for s in range(1, nSeedsSensitivity+1):
      try:
        metric_file = dir_moea_output + 'sensitivity/metrics/param' + str(p) + '_seedS1_seedB' + str(s) + '.metrics'
        hv_file = dir_moea_output + 'sensitivity/param' + str(p) +'_borg.hypervolume'
        metrics_seedsSensitivity.append(get_metrics_single(metric_file, hv_file, p, s))
        if (s == 1):
          p_successes.append(p)
      except:
        # print(p, ' fail')
        dum = 0

  return(metrics_seedsBase, metrics_seedsSensitivity, p_successes)






#########################################################################
######### plot hypervolume for baseline (50 seeds) + sample of 12 sensitivity analysis runs (10 seeds) ####
### outputs plot, no return. ####
# ##########################################################################
def plot_hypervolume(dir_figs, metrics_seedsBase, metrics_seedsSensitivity, p_successes, nSeedsBase, nSeedsSensitivity, nfe):

  col_scal = np.arange(1,(nSeedsBase+1))/(nSeedsBase+1)
  cmap_vir = cm.get_cmap('viridis')
  function_eval = np.arange(0, nfe+1, 200)
  plt.figure()
  ax = plt.subplot2grid((4,4),(0,0), rowspan=2, colspan=2)
  ax.annotate('a)', xy=(0.9, 0.04), xycoords='axes fraction')
  ax.tick_params(axis='x',which='both',labelbottom=False,labeltop=True)
  for s in range(1, (nSeedsBase+1)):
    hv = metrics_seedsBase[s - 1]['Hypervolume']
    ax.plot(function_eval/1000, hv, c=cmap_vir(col_scal[s - 1]), alpha=0.7)
  ax.set_yticks([0,1])
  ax.set_ylim([-0.1, 1.15])
  ax.set_xticks([0,10])
  nsamp=12
  nrow=2
  ncol=4
  np.random.seed(7)
  param_samps = np.random.choice(p_successes, size=nsamp, replace=False)
  col_scal = np.arange(1,(nSeedsSensitivity+1))/11
  letters = ['b)','c)','d)','e)','f)','g)','h)','i)','j)','k)','l)','m)']
  for j,p in enumerate(param_samps):
    if (j < 4):
      rj = int(j/2)
      cj = 2 + j - 2*rj
      ax = plt.subplot2grid((4,4), (rj, cj))
      ax.annotate(letters[j], xy=(0.8, 0.08), xycoords='axes fraction')
    else:
      rj = 2 + int((j-4)/ncol)
      cj = j+4 - ncol*rj
      ax = plt.subplot2grid((4,4), (rj, cj))
      if (j < 11):
        ax.annotate(letters[j], xy=(0.8, 0.08), xycoords='axes fraction')
      else:
        ax.annotate(letters[j], xy=(0.7, 0.08), xycoords='axes fraction')
    if (rj == 0):
      ax.tick_params(axis='x', which='both', labelbottom=False, labeltop=True)
    elif (rj < ncol-1):
      ax.tick_params(axis='x', which='both', labelbottom=False, labeltop=False)
    if (cj > 0)&(cj < ncol-1):
      ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
    elif (cj == ncol-1):
      ax.tick_params(axis='y', which='both', labelleft=False, labelright=True)
    for s in range(1, 11):
      i = nSeedsSensitivity * np.where(np.array(p_successes)==p)[0][0] + s - 1
      hv = metrics_seedsSensitivity[i]['Hypervolume']
      ax.plot(function_eval / 1000, hv, c=cmap_vir(col_scal[s - 1]), alpha=0.7)
    ax.set_ylim([-0.1, 1.15])
    if (rj == 3)&(cj == 1):
      ax.set_xlabel('Thousands of Function Evaluations')
    if (rj == 2)&(cj == 0):
      ax.set_ylabel('Normalized Hypervolume')
  plt.savefig(dir_figs + 'fig_hypervolume.jpg', bbox_inches='tight', dpi=1200)

  return



#########################################################################
######### plot hypervolume for baseline (50 seeds) + sample of 12 sensitivity analysis runs (10 seeds) ####
### outputs plot, no return. ####
# ##########################################################################
def plot_generational_distance(dir_figs, metrics_seedsBase, metrics_seedsSensitivity, p_successes, nSeedsBase, nSeedsSensitivity, nfe):
  ### combined generational distance plot for sfpuc + sensitivity analysis
  col_scal = np.arange(1,(nSeedsBase+1))/(nSeedsBase+1)
  cmap_vir = cm.get_cmap('viridis')
  function_eval = np.arange(0, nfe+1, 200)
  fig = plt.figure()
  ax = plt.subplot2grid((4,4),(0,0), rowspan=2, colspan=2)
  ax.tick_params(axis='x',which='both',labelbottom=False,labeltop=True)
  for s in range(1, (nSeedsBase+1)):
    hv = metrics_seedsBase[s - 1]['GenerationalDistance']
    ax.plot(function_eval/1000, hv, c=cmap_vir(col_scal[s - 1]), alpha=0.7)
    ax.annotate('a)', xy=(0.88, 0.88), xycoords='axes fraction')
  ax.set_yticks([0,0.1])
  ax.set_ylim([-0.01, 0.15])
  ax.set_xticks([0,10])
  nsamp=12
  nrow=2
  ncol=4
  np.random.seed(7)
  param_samps = np.random.choice(p_successes, size=nsamp, replace=False)
  col_scal = np.arange(1,(nSeedsSensitivity+1))/(nSeedsSensitivity+1)
  letters = ['b)','c)','d)','e)','f)','g)','h)','i)','j)','k)','l)','m)']
  for j,p in enumerate(param_samps):
    if (j < 4):
      rj = int(j/2)
      cj = 2 + j - 2*rj
      ax = plt.subplot2grid((4,4), (rj, cj))
      ax.annotate(letters[j], xy=(0.8, 0.75), xycoords='axes fraction')
    else:
      rj = 2 + int((j-4)/ncol)
      cj = j+4 - ncol*rj
      ax = plt.subplot2grid((4,4), (rj, cj))
      if (j < 11):
        ax.annotate(letters[j], xy=(0.8, 0.75), xycoords='axes fraction')
      else:
        ax.annotate(letters[j], xy=(0.7, 0.75), xycoords='axes fraction')
    if (rj == 0):
      ax.tick_params(axis='x', which='both', labelbottom=False, labeltop=True)
    elif (rj < ncol-1):
      ax.tick_params(axis='x', which='both', labelbottom=False, labeltop=False)
    if (cj > 0)&(cj < ncol-1):
      ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
    elif (cj == ncol-1):
      ax.tick_params(axis='y', which='both', labelleft=False, labelright=True)
    for s in range(1, (nSeedsSensitivity+1)):
      i = nSeedsSensitivity * np.where(np.array(p_successes)==p)[0][0] + s - 1
      hv = metrics_seedsSensitivity[i]['GenerationalDistance']
      ax.plot(function_eval / 1000, hv, c=cmap_vir(col_scal[s - 1]), alpha=0.7)
    ax.set_ylim([-0.01, 0.15])
    if (rj == 3)&(cj == 1):
      ax.set_xlabel('Thousands of Function Evaluations')
    if (rj == 2)&(cj == 0):
      ax.set_ylabel('Generational Distance')
  plt.savefig(dir_figs + 'fig_generationalDistance.jpg', bbox_inches='tight', dpi=1200)

  return


#########################################################################
######### plot epsilon indicator for baseline (50 seeds) + sample of 12 sensitivity analysis runs (10 seeds) ####
### outputs plot, no return. ####
# ##########################################################################
def plot_epsilon_indicator(dir_figs, metrics_seedsBase, metrics_seedsSensitivity, p_successes, nSeedsBase, nSeedsSensitivity, nfe):
  col_scal = np.arange(1,(nSeedsBase+1))/(nSeedsBase+1)
  cmap_vir = cm.get_cmap('viridis')
  function_eval = np.arange(0, nfe+1, 200)
  fig = plt.figure()
  ax = plt.subplot2grid((4,4),(0,0), rowspan=2, colspan=2)
  ax.tick_params(axis='x',which='both',labelbottom=False,labeltop=True)
  for s in range(1, (nSeedsBase+1)):
    hv = metrics_seedsBase[s - 1]['EpsilonIndicator']
    ax.plot(function_eval/1000, hv, c=cmap_vir(col_scal[s - 1]), alpha=0.7)
    ax.annotate('a)', xy=(0.88, 0.88), xycoords='axes fraction')
  ax.set_yticks([0,0.5])
  ax.set_ylim([-0.05, 0.55])
  ax.set_xticks([0,10])
  nsamp=12
  nrow=2
  ncol=4
  np.random.seed(7)
  param_samps = np.random.choice(p_successes, size=nsamp, replace=False)
  col_scal = np.arange(1,(nSeedsSensitivity+1))/(nSeedsSensitivity+1)
  letters = ['b)','c)','d)','e)','f)','g)','h)','i)','j)','k)','l)','m)']
  for j,p in enumerate(param_samps):
    if (j < 4):
      rj = int(j/2)
      cj = 2 + j - 2*rj
      ax = plt.subplot2grid((4,4), (rj, cj))
      ax.annotate(letters[j], xy=(0.8, 0.75), xycoords='axes fraction')
    else:
      rj = 2 + int((j-4)/ncol)
      cj = j+4 - ncol*rj
      ax = plt.subplot2grid((4,4), (rj, cj))
      if (j < 11):
        ax.annotate(letters[j], xy=(0.8, 0.75), xycoords='axes fraction')
      else:
        ax.annotate(letters[j], xy=(0.7, 0.75), xycoords='axes fraction')
    if (rj == 0):
      ax.tick_params(axis='x', which='both', labelbottom=False, labeltop=True)
    elif (rj < ncol-1):
      ax.tick_params(axis='x', which='both', labelbottom=False, labeltop=False)
    if (cj > 0)&(cj < ncol-1):
      ax.tick_params(axis='y', which='both', labelleft=False, labelright=False)
    elif (cj == ncol-1):
      ax.tick_params(axis='y', which='both', labelleft=False, labelright=True)
    for s in range(1, (nSeedsSensitivity+1)):
      i = nSeedsSensitivity * np.where(np.array(p_successes)==p)[0][0] + s - 1
      hv = metrics_seedsSensitivity[i]['EpsilonIndicator']
      ax.plot(function_eval / 1000, hv, c=cmap_vir(col_scal[s - 1]), alpha=0.7)
    ax.set_ylim([-0.05, 0.55])
    if (rj == 3)&(cj == 1):
      ax.set_xlabel('Thousands of Function Evaluations')
    if (rj == 2)&(cj == 0):
      ax.set_ylabel('Epsilon Indicator')
  plt.savefig(dir_figs + 'fig_epsilonIndicator.jpg', bbox_inches='tight', dpi=1200)

  return













