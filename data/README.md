# Data provenance

The three source files are public-use SAS transport files from CDC/NCHS NHANES
2017-March 2020 pre-pandemic:

| Local file | NHANES component | Official documentation |
|---|---|---|
| `P_DEMO.xpt` | Demographics and special pre-pandemic sample weights | https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm |
| `P_BPQ.xpt` | Blood pressure awareness and treatment questionnaire | https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_BPQ.htm |
| `P_BPXO.xpt` | Three oscillometric blood pressure measurements | https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_BPXO.htm |

## Re-download

```bash
curl -L -o data/raw/P_DEMO.xpt https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.xpt
curl -L -o data/raw/P_BPQ.xpt https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_BPQ.xpt
curl -L -o data/raw/P_BPXO.xpt https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_BPXO.xpt
```

These files contain de-identified public-use data. They contain no PHI and no
Texas DSHS information.
