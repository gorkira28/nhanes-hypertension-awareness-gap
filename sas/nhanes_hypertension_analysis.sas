/*
  NHANES 2017-March 2020 pre-pandemic hypertension awareness analysis
  Designed for SAS OnDemand for Academics / SAS 9.4.

  Set ROOT to the project directory containing data/raw.
*/

%let ROOT=/home/your-user/nhanes-hypertension-awareness-gap;

libname xdemo xport "&ROOT./data/raw/P_DEMO.xpt" access=readonly;
libname xbpq  xport "&ROOT./data/raw/P_BPQ.xpt" access=readonly;
libname xbpxo xport "&ROOT./data/raw/P_BPXO.xpt" access=readonly;

proc copy in=xdemo out=work memtype=data; run;
proc copy in=xbpq  out=work memtype=data; run;
proc copy in=xbpxo out=work memtype=data; run;

proc sort data=work.p_demo; by seqn; run;
proc sort data=work.p_bpq;  by seqn; run;
proc sort data=work.p_bpxo; by seqn; run;

proc format;
  value sexfmt 1='Men' 2='Women';
  value agefmt 1='18-39' 2='40-59' 3='60+';
  value racefmt 1='Mexican American' 2='Other Hispanic'
                3='Non-Hispanic White' 4='Non-Hispanic Black'
                6='Non-Hispanic Asian' 7='Other/multiracial';
run;

data work.analysis;
  merge work.p_demo(in=indemo)
        work.p_bpq(in=inbpq)
        work.p_bpxo(in=inbpxo);
  by seqn;
  if indemo and inbpq and inbpxo;

  bp_readings=n(of BPXOSY1-BPXOSY3);
  mean_sbp=mean(of BPXOSY1-BPXOSY3);
  mean_dbp=mean(of BPXODI1-BPXODI3);

  if RIDAGEYR >= 18 and RIDEXPRG ne 1 and WTMECPRP > 0 and
     bp_readings >= 2 and nmiss(mean_sbp,mean_dbp)=0;

  if BPQ020=1 then aware=1;
  else if BPQ020=2 then aware=0;

  treated=(BPQ050A=1);
  high_bp_130=(mean_sbp >= 130 or mean_dbp >= 80);
  high_bp_140=(mean_sbp >= 140 or mean_dbp >= 90);
  htn130=(high_bp_130=1 or treated=1);
  htn140=(high_bp_140=1 or treated=1);

  if htn130=1 and aware in (0,1) then unaware130=1-aware;
  if htn140=1 and aware in (0,1) then unaware140=1-aware;
  if treated=1 then controlled130=(mean_sbp < 130 and mean_dbp < 80);

  if 18 <= RIDAGEYR <= 39 then age_group=1;
  else if 40 <= RIDAGEYR <= 59 then age_group=2;
  else if RIDAGEYR >= 60 then age_group=3;

  format RIAGENDR sexfmt. age_group agefmt. RIDRETH3 racefmt.;
run;

/* Primary national estimates. Missing values define each analytic domain. */
data work.analysis;
  set work.analysis;
  htn_prevalence=htn130;
  if htn130=1 then do;
    unawareness=unaware130;
    treatment=treated;
  end;
  if treated=1 then control=controlled130;
run;

ods csv file="&ROOT./outputs/tables/sas_overall_estimates.csv";
proc surveymeans data=work.analysis mean stderr clm;
  strata SDMVSTRA;
  cluster SDMVPSU;
  weight WTMECPRP;
  var htn_prevalence unawareness treatment control;
run;
ods csv close;

/* Domain estimates retain all PSUs for valid subpopulation variance. */
ods csv file="&ROOT./outputs/tables/sas_subgroup_unawareness.csv";
proc surveymeans data=work.analysis mean stderr clm;
  strata SDMVSTRA;
  cluster SDMVPSU;
  weight WTMECPRP;
  domain RIAGENDR age_group RIDRETH3;
  var unawareness;
run;
ods csv close;

/* Adjusted associations: descriptive, not causal. */
ods csv file="&ROOT./outputs/tables/sas_unawareness_model.csv";
proc surveylogistic data=work.analysis;
  where htn130=1 and unaware130 in (0,1);
  strata SDMVSTRA;
  cluster SDMVPSU;
  weight WTMECPRP;
  class RIAGENDR(ref='2') age_group(ref='3') RIDRETH3(ref='3')
        / param=ref;
  model unaware130(event='1') = RIAGENDR age_group RIDRETH3 INDFMPIR;
  oddsratio RIAGENDR;
  oddsratio age_group;
  oddsratio RIDRETH3;
  oddsratio INDFMPIR;
run;
ods csv close;

/* Sensitivity analysis using the >=140/90 threshold. */
ods csv file="&ROOT./outputs/tables/sas_threshold_sensitivity.csv";
proc surveymeans data=work.analysis mean stderr clm;
  strata SDMVSTRA;
  cluster SDMVPSU;
  weight WTMECPRP;
  var htn130 unaware130 htn140 unaware140;
run;
ods csv close;

title "NHANES hypertension analysis QA";
proc means data=work.analysis n nmiss min p25 median p75 max;
  var mean_sbp mean_dbp WTMECPRP;
run;
proc freq data=work.analysis;
  tables bp_readings*htn130*aware / missing list;
run;
title;
