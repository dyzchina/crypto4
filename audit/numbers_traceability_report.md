# numbers.tex traceability audit

**Total macros**: 51
**CSV-driven**: 43
**Static (documented constants)**: 8
**Untraceable**: 0

## CSV-driven macros

| Macro | Value | Source |
|---|---|---|
| `DELTAFTX` | `-0.247` | `add("DELTAFTX", fmt(f.get("delta_logE")))` |
| `DELTAFTXBLOCK` | `-0.156` | `add("DELTAFTXBLOCK", fmt(d_b))` |
| `DELTAUSDCSVBBLOCK` | `-0.095` | `bootstrap_usdc_svb.csv prefix loop` |
| `DELTAUSDCSVBBLOCKATFTX` | `-0.266` | `add("DELTAUSDCSVBBLOCKATFTX", fmt(r["cross_delta_block"]))` |
| `DELTAUSDCSVBBLOCKHI` | `-0.094` | `bootstrap_usdc_svb.csv prefix loop` |
| `DELTAUSDCSVBBLOCKLO` | `-0.115` | `bootstrap_usdc_svb.csv prefix loop` |
| `DELTAUSDCSVBBLOCKP` | `0.004` | `bootstrap_usdc_svb.csv prefix loop` |
| `DELTAUSDCSVBFULL` | `-0.006` | `bootstrap_usdc_svb.csv prefix loop` |
| `DELTAUSDCSVBFULLHI` | `-0.003` | `bootstrap_usdc_svb.csv prefix loop` |
| `DELTAUSDCSVBFULLLO` | `-0.006` | `bootstrap_usdc_svb.csv prefix loop` |
| `DELTAUSDCSVBFULLP` | `0.004` | `bootstrap_usdc_svb.csv prefix loop` |
| `DELTAUSDCSVBLOGE` | `-0.212` | `bootstrap_usdc_svb.csv prefix loop` |
| `DELTAUSDCSVBLOGEATFTX` | `-0.660` | `add("DELTAUSDCSVBLOGEATFTX",  fmt(r["cross_delta_logE"]))` |
| `DELTAUSDCSVBLOGEHI` | `-0.197` | `bootstrap_usdc_svb.csv prefix loop` |
| `DELTAUSDCSVBLOGELO` | `-0.218` | `bootstrap_usdc_svb.csv prefix loop` |
| `DELTAUSDCSVBLOGEP` | `0.002` | `bootstrap_usdc_svb.csv prefix loop` |
| `ESCOPULA` | `7.7` | `add("ESCOPULA",   f"{r['copula_ES_bp']:.1f}")` |
| `ESCORRCOMP` | `0.4` | `add("ESCORRCOMP", f"{r['corr_component_bp']:.1f}")` |
| `ESCORRSHARE` | `0.1` | `add("ESCORRSHARE", f"{share_c*100:.1f}" if share_c == share_c else "0....` |
| `ESGAP` | `331.5` | `add("ESGAP",      f"{r['gap_bp']:.1f}")` |
| `ESINTERACT` | `13.0` | `add("ESINTERACT", f"{interact_bp:.1f}" if interact_bp == interact_bp e...` |
| `ESINTERACTSHARE` | `3.9` | `add("ESINTERACTSHARE", f"{interact_share*100:.1f}" if interact_share =...` |
| `ESMULT` | `43.9` | `add("ESMULT",     f"{r['multiplier']:.1f}")` |
| `ESVFC` | `339.2` | `add("ESVFC",      f"{r['wall_ES_bp']:.1f}")` |
| `ESVOLCOMP` | `318.1` | `add("ESVOLCOMP",  f"{r['vol_component_bp']:.1f}")` |
| `ESVOLSHARE` | `96.0` | `add("ESVOLSHARE", f"{share*100:.1f}" if share == share else "87.3")` |
| `FDUSDBASKETCOPULA` | `87.8` | `add("FDUSDBASKETCOPULA", f"{r['copula_ES_bp']:.1f}")` |
| `FDUSDBASKETGAP` | `73.1` | `add("FDUSDBASKETGAP",    f"{r['gap_bp']:.1f}")` |
| `FDUSDBASKETVFC` | `160.9` | `add("FDUSDBASKETVFC",    f"{r['wall_ES_bp']:.1f}")` |
| `FTXBASKETCOPULA` | `48.4` | `add("FTXBASKETCOPULA", f"{r['copula_ES_bp']:.1f}")` |
| `FTXBASKETGAP` | `118.8` | `add("FTXBASKETGAP",    f"{r['gap_bp']:.1f}")` |
| `FTXBASKETVFC` | `167.2` | `add("FTXBASKETVFC",    f"{r['wall_ES_bp']:.1f}")` |
| `PLACEBOACONDN` | `6` | `add("PLACEBOACONDN", str(int(ra["n"])))` |
| `PLACEBOACONDP` | `0.667` | `add("PLACEBOACONDP", fmt(ra["p_one_sided"]))` |
| `PLACEBOBCONDMEAN` | `-0.047` | `add("PLACEBOBCONDMEAN", fmt(rb["mean_null"]))` |
| `PLACEBOBCONDN` | `200` | `add("PLACEBOBCONDN", str(int(rb["n"])))` |
| `PLACEBOBCONDP` | `0.430` | `add("PLACEBOBCONDP", fmt(rb["p_one_sided"]))` |
| `PLACEBOBCONDSD` | `0.183` | `add("PLACEBOBCONDSD",   fmt(rb["sd_null"]))` |
| `PLACEBOMEAN` | `-0.013` | `add("PLACEBOMEAN", fmt(p["mean_placebo"]))` |
| `PLACEBOP` | `0.760` | `add("PLACEBOP",    fmt(p["p_one_sided"]))` |
| `PLACEBOREAL` | `-0.108` | `add("PLACEBOREAL", fmt(p["real_sum"]))` |
| `PLACEBOSD` | `0.217` | `add("PLACEBOSD",   fmt(p["std_placebo"]))` |
| `SIGMAFTXHAT` | `0.985` | `add("SIGMAFTXHAT", fmt(r["sigma_hat"]))` |

## Static (documented constants)

| Macro | Value | Rationale |
|---|---|---|
| `DELTAFTXP` | `0.001` | 0.001 (block-bootstrap p-value below MC tail resolution) |
| `FTXMIMBP` | `54.3` | 54.3 (MIM max deviation on FTX event) |
| `FTXUSDDBP` | `249.7` | 249.7 (USDD max deviation on FTX event; from DeFiLlama raw) |
| `FTXUSDPBP` | `59.9` | 59.9 (USDP flight-to-avoidance direction) |
| `NCOINSSUB` | `10` | 10 (typical sub-panel size) |
| `NEVENTS` | `9` | 9 documented episodes (Table 1) |
| `NPANEL` | `35` | 35 stablecoins (Appendix C panel) |
| `SIGMAWHAT` | `0.35` | 0.35 (USDC-SVB calibration, Appendix E) |