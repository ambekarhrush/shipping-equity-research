import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const input = JSON.parse(await fs.readFile(path.join(root, '.cache/workbook-inputs.json'), 'utf8'));
const { company, fleet, financials, assumptions, sources, debt } = input;
const fleetValueLabel = company.fleet_value_label ?? 'Appraisal value';
const output = path.join(root, `outputs/${company.ticker.toLowerCase()}-${company.valuation_date}`);
await fs.mkdir(path.join(output, 'previews'), { recursive: true });
const wb = Workbook.create();
const names = ['Summary', 'Assumptions', 'NAV', 'Cash Flow', 'Debt', 'Fleet', 'Days', 'Historical', 'Sources', 'Checks'];
const sheets = Object.fromEntries(names.map(n => [n, wb.worksheets.add(n)]));
const ink = '#142C46', blue = '#1748A0', green = '#18734A', muted = '#627185';
const money = '#,##0.0,,;(#,##0.0,,);"–"';
const integer = '#,##0;(#,##0);"–"';
const price = '$0.00;($0.00);"–"';
const pct = '0.0%;(0.0%);"–"';
const serial = value => (Date.parse(value + 'T00:00:00Z') - Date.UTC(1899, 11, 30)) / 86400000;
const col = i => { let s=''; for(let n=i+1;n;n=Math.floor((n-1)/26)) s=String.fromCharCode(65+(n-1)%26)+s; return s; };
const val = (s,a,v) => s.getRange(a).values=[[v]];
const fx = (s,a,f) => { s.getRange(a).formulas=[[f]]; s.getRange(a).format.font.color=f.includes('!')?green:'#20252B'; };
const header = (s,a,labels) => {
  const r=s.getRange(a);r.values=[labels];r.format={fill:ink,font:{bold:true,color:'#FFFFFF'},rowHeight:28,verticalAlignment:'center'};
};
const section = (s,row,label,last='H') => { val(s,`C${row}`,label);s.getRange(`C${row}:${last}${row}`).format={fill:'#EAF0F7',font:{bold:true,color:ink},rowHeight:25}; };
const periods=[];
let start=new Date(Date.parse(company.valuation_date)+86400000).toISOString().slice(0,10);
for(let i=0;i<12;i++) {
  const date=new Date(start), y=date.getUTCFullYear(), q=Math.floor(date.getUTCMonth()/3)+1;
  const end=new Date(Date.UTC(y,q*3,0)).toISOString().slice(0,10);
  periods.push({start,end,label:`Q${q}:${String(y).slice(-2)}${i===0?' stub':''}`});
  start=new Date(Date.parse(end)+86400000).toISOString().slice(0,10);
}
while(new Date(start).getUTCFullYear()<company.forecast_end_year || (new Date(start).getUTCFullYear()===company.forecast_end_year && new Date(start).getUTCMonth()===0)) {
  const date=new Date(start);
  const end=new Date(Date.UTC(date.getUTCFullYear()+1,date.getUTCMonth(),date.getUTCDate())-86400000).toISOString().slice(0,10);
  periods.push({start,end,label:new Date(end).toLocaleDateString('en-US',{month:'short',year:'2-digit',timeZone:'UTC'}).replace(' ','-')});
  start=new Date(Date.parse(end)+86400000).toISOString().slice(0,10);
}
const nextYear=Number(company.valuation_date.slice(0,4))+1;
const yearColumns=periods.flatMap((p,i)=>Number(p.start.slice(0,4))===nextYear?[col(i+4)]:[]);
const yearSum=(sheet,row)=>`=SUM(${yearColumns.map(c=>`'${sheet}'!${c}${row}`).join(',')})`;
const lastDebt=30+debt.length;
const endcol=col(4+periods.length-1);
for(const [name,s] of Object.entries(sheets)) {
  s.showGridLines=false;
  const styledEnd=['Cash Flow','Days','Debt'].includes(name)?endcol:name==='Assumptions'?'Q':['Fleet','Summary'].includes(name)?'R':'N';
  s.getRange(`A1:${styledEnd}${name==='Fleet'||name==='Days'?fleet.length+9:name==='Assumptions'?Math.max(170,assumptions.length*5+15):115}`).format={font:{name:'Arial',size:10,color:ink},rowHeight:21,verticalAlignment:'center'};
  s.getRange('A:B').format.columnWidth=2.5;
  s.getRange('C:C').format.columnWidth=38;
  s.getRange('D:D').format.columnWidth=21;
  s.getRange(`E:${['Cash Flow','Days','Debt'].includes(name)?endcol:'N'}`).format.columnWidth=16;
  val(s,'C2',name==='Summary'?`${company.name} valuation`:name);
  s.getRange('C2:H2').format.font={size:16,bold:true,color:ink};
  s.getRange('C3:H3').format.borders={bottom:{style:'thin',color:ink}};
  if(name!=='Assumptions') {val(s,'C4','Case selected');fx(s,'D4',"='Assumptions'!D4");}
  if(name!=='Summary')s.freezePanes.freezeRows(6);
}
sheets.Summary.tabColor=ink;sheets.Assumptions.tabColor='#537598';

const a=sheets.Assumptions;
val(a,'C4','Case selected');fx(a,'D4','=CHOOSE(D5,"Bear","Base","Bull")');
val(a,'C5','Case number');val(a,'D5',2);val(a,'F5','1 Bear, 2 Base, 3 Bull');
a.getRange('D5').dataValidation={rule:{type:'whole',operator:'between',formula1:1,formula2:3}};
val(a,'C6','Open-rate multiplier');val(a,'D6',1);
val(a,'F6','Change this to test all open charter rates together.');
val(a,'C7','Discount-rate adjustment');val(a,'D7',0);a.getRange('D7').setNumberFormat(pct);
val(a,'F7','Add to the selected discount rate.');
const ar={};
assumptions.forEach((d,i)=>{
  const r=10+i*5;ar[d.key]=r;
  val(a,`C${r}`,d.label);fx(a,`D${r}`,`=IF(ISNUMBER(CHOOSE($D$5,D${r+1},D${r+2},D${r+3})),CHOOSE($D$5,D${r+1},D${r+2},D${r+3}),NA())`);
  val(a,`E${r}`,d.unit);val(a,`F${r}`,d.rationale);
  a.getRange(`F${r}:J${r+3}`).merge();a.getRange(`F${r}:J${r+3}`).format={wrapText:true,font:{color:muted},verticalAlignment:'top'};
  a.getRange(`C${r}:E${r}`).format.fill='#EDF2F7';a.getRange(`C${r}:E${r}`).format.font.bold=true;
  ['bear','base','bull'].forEach((c,j)=>{val(a,`C${r+1+j}`,c[0].toUpperCase()+c.slice(1));val(a,`D${r+1+j}`,d[c]);});
  a.getRange(`D${r+1}:D${r+3}`).format={font:{color:blue},fill:'#FFF6DF'};
  a.getRange(`D${r}:D${r+3}`).setNumberFormat(d.unit==='fraction'?pct:d.unit==='multiple'?'0.00x':integer);
});
a.getRange('D5:D7').format={fill:'#FFF6DF',font:{color:blue}};
const driver=k=>`'Assumptions'!$D$${ar[k]}`;

const src=sheets.Sources;
header(src,'C6:H6',['Input','Value','Unit','Period','Source ID','Location']);
const sr={};
financials.forEach((f,i)=>{const r=i+7;sr[f.key]=r;src.getRange(`C${r}:H${r}`).values=[[f.key,f.value,f.unit,serial(f.period),f.source_id,f.source_location]];});
src.getRange(`D7:D${financials.length+6}`).format.font.color=blue;
src.getRange(`D7:D${financials.length+6}`).setNumberFormat('#,##0.00;(#,##0.00);"–"');
src.getRange(`F7:F${financials.length+6}`).setNumberFormat('dd-mmm-yy');
src.getRange('H:H').format.columnWidth=55;
src.getRange('G:G').format.columnWidth=24;
const registerRow=financials.length+10;
section(src,registerRow,'Source register','H');
sources.forEach((s,i)=>{let r=registerRow+2+i*3;val(src,`C${r}`,s.id);val(src,`D${r}`,s.title);val(src,`C${r+1}`,s.url);src.getRange(`C${r+1}:H${r+1}`).merge();src.getRange(`C${r+1}:H${r+1}`).format.font={size:9,color:muted};});
val(src,`C${registerRow+sources.length*3+4}`,`Source extracts are dated. ${fleetValueLabel} inputs are not current executable sale prices.`);
const source=k=>`'Sources'!$D$${sr[k]}`;

const f=sheets.Fleet;
header(f,'C6:R6',['Vessel','Class','DWT','Built','Delivery','Value date','Fleet value USD','Remaining capex USD','Scrubber','Source IMO','Source IDs','Delivery basis','Retirement','Scenario value USD','Future capex USD','Notes']);
f.getRange('C:C').format.columnWidth=25;f.getRange('D:D').format.columnWidth=19;
f.getRange('M:M').format.columnWidth=35;f.getRange('R:R').format.columnWidth=70;
f.getRange('J:J').format.columnWidth=23;f.getRange('K:K').format.columnWidth=12;
f.getRange('I:I').format.columnWidth=20;f.getRange('L:L').format.columnWidth=16;
f.getRange('O:O').format.columnWidth=18;f.getRange('P:Q').format.columnWidth=24;
fleet.forEach((v,i)=>{const r=i+7;
  f.getRange(`C${r}:N${r}`).values=[[v.name,v.vessel_class,v.dwt,v.build_year,serial(v.delivery_date),serial(v.appraisal_date),v.appraisal_usd,v.remaining_capex_usd,v.scrubber,v.source_imo,v.source_id,v.delivery_status]];
  fx(f,`O${r}`,`=DATE(F${r}+${driver('retirement_age')},7,1)`);
  fx(f,`P${r}`,`=I${r}*${driver('asset_factor')}`);
  fx(f,`Q${r}`,`=J${r}*${driver('remaining_capex_factor')}`);
  val(f,`R${r}`,v.notes);
});
const lastFleet=fleet.length+6;
f.getRange(`G7:H${lastFleet}`).setNumberFormat('dd-mmm-yy');f.getRange(`O7:O${lastFleet}`).setNumberFormat('dd-mmm-yy');
f.getRange(`I7:K${lastFleet}`).setNumberFormat(integer);f.getRange(`P7:Q${lastFleet}`).setNumberFormat(integer);
f.getRange(`E7:K${lastFleet}`).format.font.color=blue;
f.freezePanes.freezeColumns(4);

for(const name of ['Days','Cash Flow','Debt']) {
  const s=sheets[name];
  header(s,`E6:${endcol}6`,periods.map(p=>p.label));
  periods.forEach((p,i)=>{const c=col(i+4);val(s,`${c}7`,serial(p.start));val(s,`${c}8`,serial(p.end));});
  s.getRange(`E7:${endcol}8`).setNumberFormat('dd-mmm-yy');
  val(s,'C7','Period starts');val(s,'C8','Period ends');
  s.freezePanes.freezeRows(8);s.freezePanes.freezeColumns(4);
}
const days=sheets.Days;
fleet.forEach((v,i)=>{const r=i+10,fr=i+7;fx(days,`C${r}`,`='Fleet'!C${fr}`);fx(days,`D${r}`,`='Fleet'!D${fr}`);
  periods.forEach((p,j)=>{const c=col(j+4);fx(days,`${c}${r}`,`=MAX(0,MIN(${c}$8+1,'Fleet'!$O${fr})-MAX(${c}$7,'Fleet'!$G${fr}))`);});
});
days.getRange(`E10:${endcol}${fleet.length+9}`).setNumberFormat(integer);

const nav=sheets.NAV;
section(nav,6,'Common-equity NAV (USD millions)');
const navRows={fleet:8,cash_open:11,equity:12,dividends:13,repayments:14,bridge:15,atm:16,cash:17,debt:20,other:21,capex:22,nwc:23,nav:25,shares:27,navps:28,price:29,pnav:30};
const navLines=[
 [8,`Fleet at selected ${fleetValueLabel.toLowerCase()}`,`=SUM('Fleet'!P7:P${lastFleet})`],
 [11,'Reported unrestricted cash',`=${source('cash')}`],
 [12,'Completed equity proceeds',`=${source('equity_proceeds')}`],
 [13,'Disclosed dividend paid',`=-${source('subsequent_dividend')}`],
 [14,'Disclosed debt payments',`=-${source('debt_payments')}`],
 [15,'Estimated other net cash change',`=${driver('bridge_cash')}`],
 [16,'Hypothetical ATM net proceeds',`=${driver('atm_draw')}*(1-${driver('atm_fee')})`],
 [17,'Estimated valuation-date cash','=SUM(D11:D16)'],
 [20,'Gross financial debt',`=${source('bank_debt_gross')}+${source('finance_leases')}-${source('debt_payments')}`],
 [21,'Other net claims',`=${driver('extra_claims')}`],
 [22,'Remaining newbuild payments',`=SUM('Fleet'!Q7:Q${lastFleet})`],
 [23,'Operating working capital proxy',`=${source('operating_working_capital')}`],
 [25,'Common-equity asset NAV','=D8+D17-D20-D21-D22+D23'],
 [27,'Valuation shares (millions)',`=${source('shares')}+${source('equity_issued')}+${driver('additional_shares')}+${driver('atm_draw')}/${source('share_price')}`],
 [28,'Asset NAV per share','=D25/D27'],
 [29,'Market price',`=${source('share_price')}`],
 [30,'Price / asset NAV','=D29/D28']];
navLines.forEach(([r,label,formula])=>{val(nav,`C${r}`,label);fx(nav,`D${r}`,formula);});
nav.getRange('D8:D27').setNumberFormat(money);nav.getRange('D28:D29').setNumberFormat(price);nav.getRange('D30').setNumberFormat('0.00x');
val(nav,'F8',`${fleetValueLabel} multiplier affects vessel values, not cash or debt.`);
val(nav,'F15','Estimated residual includes operations, sales, delivery spending and restricted-cash release.');
val(nav,'F20','Includes finance leases. Adds back June unamortized issuance costs before repayments.');
val(nav,'F22','Full vessel value less remaining payments; deposits are not added a second time.');
val(nav,'F25','Asset NAV excludes future corporate overhead. DCF includes overhead.');
val(nav,'F27','Outstanding shares, not weighted-average EPS shares.');
nav.getRange('F8:J30').format.font.color=muted;

const cf=sheets['Cash Flow'];
const classRows={};
company.class_order.forEach((cls,i)=>{
  const r=11+i*11;classRows[cls]=r;section(cf,r-1,cls,endcol);
  const labels=['Owned days','Available days','Open TCE (USD/day)','Fixed share','Fixed TCE (USD/day)','TCE cash revenue','Vessel operating cost','Management fees','Drydock cash budget','Other maintenance capex'];
  labels.forEach((label,k)=>val(cf,`C${r+k}`,label));
  periods.forEach((p,j)=>{const c=col(j+4),growth=`(1+${driver('inflation')})^(((${c}$7+${c}$8)/2-${serial(company.valuation_date)})/365)`;
    const formulas=[`=SUMIFS('Days'!${c}$10:${c}$${fleet.length+9},'Days'!$D$10:$D$${fleet.length+9},$C${r-1})`,
      `=${c}${r}*(1-${driver('offhire')})`,
      `=${driver('tce_'+cls)}*'Assumptions'!$D$6*${growth}`,
      `=${driver('fixed_share')}`,`=${driver('fixed_tce')}*${growth}`,
      `=${c}${r+1}*((1-${c}${r+3})*${c}${r+2}+${c}${r+3}*${c}${r+4})`,
      `=${c}${r}*${driver('opex')}*${growth}`,`=${c}${r}*${driver('management')}*${growth}`,
      `=${c}${r}/365*${driver('dock_budget')}*${growth}`,`=${c}${r}/365*${driver('maintenance')}*${growth}`];
    formulas.forEach((formula,k)=>fx(cf,`${c}${r+k}`,formula));
    cf.getRange(`${c}${r+5}:${c}${r+9}`).setNumberFormat(money);
    cf.getRange(`${c}${r+3}`).setNumberFormat(pct);
    cf.getRange(`${c}${r+2}`).setNumberFormat(integer);cf.getRange(`${c}${r+4}`).setNumberFormat(integer);
  });
});
section(cf,78,'Unlevered cash flow (USD millions)',endcol);
const cr={owned:80,available:81,revenue:82,opex:83,management:84,ga:85,dock:86,operating:87,tax:88,maintenance:89,newbuild:90,scrap:91,wc:92,delta_wc:93,ufcf:94,discount:95,pv:96,open_pv:97,open_revenue:98,open_wc:99,delta_open_wc:100};
const labels={owned:'Owned days',available:'Available days',revenue:'TCE cash revenue',opex:'Vessel operating cost',management:'Management fees',ga:'Corporate overhead',dock:'Drydock cash budget',operating:'Operating cash before tax and capex',tax:'Cash taxes',maintenance:'Other maintenance capex',newbuild:'Committed newbuild payments',scrap:'Retirement scrap proceeds',wc:'Closing working-capital target',delta_wc:'Increase / (release) in working capital',ufcf:'Unlevered free cash flow',discount:'Discount factor',pv:'Present value of free cash flow',open_pv:'PV of open-rate revenue, after cash tax'};
Object.assign(labels,{open_pv:'PV of rate-sensitive cash incl. working capital',open_revenue:'Open-rate cash revenue',open_wc:'Open-rate working-capital target',delta_open_wc:'Change in rate-sensitive working capital'});
for(const k of Object.keys(cr))val(cf,`C${cr[k]}`,labels[k]);
periods.forEach((p,j)=>{const c=col(j+4),prev=col(j+3),growth=`(1+${driver('inflation')})^(((${c}$7+${c}$8)/2-${serial(company.valuation_date)})/365)`;
  const sum=(offset)=>'=SUM('+Object.values(classRows).map(r=>`${c}${r+offset}`).join(',')+')';
  for(const [k,offset] of [['owned',0],['available',1],['revenue',5],['opex',6],['management',7],['dock',8],['maintenance',9]]) fx(cf,`${c}${cr[k]}`,sum(offset));
  const formulas={ga:`=IF(${c}80=0,0,${driver('ga')}*(${c}$8-${c}$7+1)/365*(${driver('ga_floor')}+(1-${driver('ga_floor')})*${c}80/((${c}$8-${c}$7+1)*${fleet.length}))*${growth})`,
    operating:`=${c}82-SUM(${c}83:${c}86)`,tax:`=${c}82*${driver('tax_on_revenue')}`,
    newbuild:`=SUMIFS('Fleet'!$Q$7:$Q$${lastFleet},'Fleet'!$G$7:$G$${lastFleet},">="&${c}$7,'Fleet'!$G$7:$G$${lastFleet},"<="&${c}$8)`,
    scrap:`=SUMIFS('Fleet'!$E$7:$E$${lastFleet},'Fleet'!$O$7:$O$${lastFleet},">="&${c}$7,'Fleet'!$O$7:$O$${lastFleet},"<="&${c}$8)*${driver('scrap_per_dwt')}`,
    wc:`=${c}82/(${c}$8-${c}$7+1)*365*${driver('working_capital')}`,
    delta_wc:`=${c}92-${j===0?source('operating_working_capital'):prev+'92'}`,
    ufcf:`=${c}87-${c}88-${c}89-${c}90+${c}91-${c}93`,
    discount:`=1/(1+${driver('wacc')}+'Assumptions'!$D$7)^((${c}$8-${serial(company.valuation_date)})/365)`,
    pv:`=${c}94*${c}95`,
    open_revenue:'='+Object.values(classRows).map(r=>`${c}${r+1}*(1-${c}${r+3})*${c}${r+2}`).join('+'),
    open_wc:`=${c}98/(${c}$8-${c}$7+1)*365*${driver('working_capital')}`,
    delta_open_wc:`=${c}99-${j===0?'0':prev+'99'}`,
    open_pv:`=(${c}98*(1-${driver('tax_on_revenue')})-${c}100)*${c}95`};
  Object.entries(formulas).forEach(([k,formula])=>fx(cf,`${c}${cr[k]}`,formula));
  // Unit-rate exposure keeps reverse valuation defined even when D6 is explicitly zero.
  fx(cf,`${c}101`,'='+Object.entries(classRows).map(([cls,r])=>`${c}${r+1}*(1-${c}${r+3})*${driver('tce_'+cls)}*${growth}`).join('+'));
  fx(cf,`${c}102`,`=${c}101/(${c}$8-${c}$7+1)*365*${driver('working_capital')}`);
  fx(cf,`${c}103`,`=${c}102-${j===0?'0':prev+'102'}`);
  fx(cf,`${c}104`,`=(${c}101*(1-${driver('tax_on_revenue')})-${c}103)*${c}95`);
});
['Open revenue at unit rate multiplier','Open working capital at unit multiplier','Change in unit-rate working capital','PV sensitivity to one unit of rate multiplier'].forEach((label,i)=>val(cf,`C${101+i}`,label));
cf.getRange(`E82:${endcol}104`).setNumberFormat(money);cf.getRange(`E95:${endcol}95`).setNumberFormat('0.000x');
cf.getRange(`E80:${endcol}81`).setNumberFormat('#,##0.0');
cf.getRange(`C94:${endcol}94`).format.fill='#EAF0F7';
val(cf,'C108','Cash figures are USD millions; TCE is USD/day. No perpetual terminal value.');
val(cf,'C109','Drydocking uses an annual budget. Charter-in activity is assumed to have zero net value.');

const ds=sheets.Debt;
section(ds,10,'Debt and retained cash (USD millions)',endcol);
const dr={opening_debt:12,repayment:13,closing_debt:14,interest:15,ufcf:17,equity_cash:18,opening_cash:20,closing_cash:21,mincash:22,headroom:23};
const dlabels={opening_debt:'Opening debt',repayment:'Principal paid',closing_debt:'Closing debt',interest:'Cash interest',ufcf:'Unlevered free cash flow',equity_cash:'Cash after financing, before dividends',opening_cash:'Opening retained cash',closing_cash:'Closing retained cash',mincash:'Illustrative minimum cash',headroom:'Cash above / (below) minimum'};
Object.entries(dr).forEach(([k,r])=>val(ds,`C${r}`,dlabels[k]));
section(ds,28,'Repayment inputs (USD millions)');header(ds,'C30:G30',['Assumed pay date','Principal','Source','Basis','Notes']);
debt.forEach((d,i)=>{ds.getRange(`C${i+31}:G${i+31}`).values=[[serial(d.due_date),d.principal_usd,d.source_id,d.status,d.notes]];});
ds.getRange(`C31:C${lastDebt}`).setNumberFormat('dd-mmm-yy');ds.getRange(`D31:D${lastDebt}`).setNumberFormat(money);
periods.forEach((p,j)=>{const c=col(j+4),prev=col(j+3);
  const formulas={opening_debt:j===0?"='NAV'!D20":`=${prev}14`,
    repayment:`=MIN(${c}12,SUMIFS($D$31:$D$${lastDebt},$C$31:$C$${lastDebt},">="&${c}$7,$C$31:$C$${lastDebt},"<="&${c}$8))`,
    closing_debt:`=${c}12-${c}13`,interest:`=AVERAGE(${c}12,${c}14)*${driver('interest')}*(${c}$8-${c}$7+1)/365`,
    ufcf:`='Cash Flow'!${c}94`,equity_cash:`=${c}17-${c}13-${c}15`,
    opening_cash:j===0?"='NAV'!D17":`=${prev}21`,closing_cash:`=${c}20+${c}18`,
    mincash:`=IF('Cash Flow'!${c}80=0,0,${source('minimum_unrestricted_liquidity')})`,headroom:`=${c}21-${c}22`};
  Object.entries(formulas).forEach(([k,formula])=>fx(ds,`${c}${dr[k]}`,formula));
});
ds.getRange(`E12:${endcol}23`).setNumberFormat(money);
ds.getRange(`E23:${endcol}23`).conditionalFormats.add('cellIs',{operator:'lessThan',formula:0,format:{fill:'#FDE9E5',font:{color:'#A12921',bold:true}}});
val(ds,'C39','No refinancing or future dividends assumed; annual maturity buckets paid at endpoint.');
val(ds,'C40','Average-balance interest is an approximation. This is a financing scenario, not a covenant forecast.');

const h=sheets.Historical;
section(h,6,`${company.history_label} operating reconciliation`);
const hist=[
 [8,'Voyage revenue',`=${source('voyage_revenue')}`],[9,'Voyage expenses',`=-${source('voyage_cost')}`],
 [10,'Charter-in hire',`=-${source('charter_hire')}`],[11,'Realized derivatives',`=${source('realized_derivatives')}`],
 [12,'Reconstructed TCE revenue','=SUM(D8:D11)'],[13,'Reported TCE revenue',`=${source('tce_revenue')}`],
 [14,'Reconciliation difference','=D12-D13'],[16,'Available days',`=${source('available_days')}`],
 [17,'Reconstructed TCE (USD/day)','=D12/D16'],[18,'Reported rounded TCE',`=${source('reported_tce')}`],
 [20,'Disclosed bunker-sale gain',`=${source('bunker_gain')}`],[21,'TCE excluding bunker gain','=(D12-D20)/D16'],
 [23,'Owned days',`=${source('ownership_days')}`],[24,'Unavailable fraction','=1-D16/D23'],
 [25,'Vessel opex (USD/day)',`=${source('vessel_opex')}/D23`],
 [26,'Management cost (USD/day)',`=${source('management_fees')}/D23`],
 [29,'Opening cash incl. restricted',`=${source('opening_total_cash')}`],
 [30,'Cash from operations',`=${source('cash_from_operations')}`],[31,'Cash from investing',`=${source('cash_from_investing')}`],
 [32,'Cash from financing',`=${source('cash_from_financing')}`],[33,'Reconstructed closing cash','=SUM(D29:D32)'],
 [34,'Reported closing cash',`=${source('closing_total_cash')}`],[35,'Cash reconciliation difference','=D33-D34']];
hist.forEach(([r,label,formula])=>{val(h,`C${r}`,label);fx(h,`D${r}`,formula);});
h.getRange('D8:D14').setNumberFormat(money);h.getRange('D20').setNumberFormat(money);h.getRange('D29:D35').setNumberFormat(money);
h.getRange('D17:D18').setNumberFormat(integer);h.getRange('D21:D26').setNumberFormat(integer);h.getRange('D24').setNumberFormat(pct);
val(h,'F12','Reported TCE already deducts charter-in hire. No second deduction.');
val(h,'F21','Single disclosed normalization, not a fully normalized mid-cycle earnings estimate.');

const sum=sheets.Summary;
val(sum,'C6','Information cutoff');val(sum,'D6',serial(company.information_cutoff));sum.getRange('D6').setNumberFormat('dd-mmm-yyyy');
val(sum,'F6',`USD. Market close: ${company.price_date}.`);
section(sum,8,'What is the fleet worth?','J');
const summary=[
 [10,'Market price',"='NAV'!D29"],[11,'Asset NAV per share',"='NAV'!D28"],[12,'Price / asset NAV',"='NAV'!D30"],
 [16,'Operating enterprise value',`=SUM('Cash Flow'!E96:${endcol}96)`],
 [17,'Cash less debt and other claims',"='NAV'!D17-'NAV'!D20-'NAV'!D21"],
 [18,'DCF equity value','=SUM(D16:D17)'],[19,'DCF equity per share',"=D18/'NAV'!D27"],
 [23,`${nextYear} TCE cash revenue`,yearSum('Cash Flow',82)],
 [24,`${nextYear} unlevered free cash flow`,yearSum('Cash Flow',94)],
 [25,`${nextYear} cash after financing`,yearSum('Debt',18)],
 [29,'PV sensitivity to unit rate change',`=SUM('Cash Flow'!E104:${endcol}104)`],
 [30,'Implied open-rate multiplier',"=IF(D29=0,NA(),('NAV'!D29*'NAV'!D27-D17-D16+D29*'Assumptions'!D6)/D29)"],
 [31,'DCF repricing residual',"=(D16-D29*'Assumptions'!D6+D29*D30+D17)/'NAV'!D27-'NAV'!D29"],
 [34,'Operating vessels',`=COUNTIFS('Fleet'!G7:G${lastFleet},"<="&D6)`],
 [35,'Committed newbuilds',`=COUNTIFS('Fleet'!G7:G${lastFleet},">"&D6)`]];
summary.forEach(([r,label,formula])=>{val(sum,`C${r}`,label);fx(sum,`D${r}`,formula);});
sum.getRange('D10:D11').setNumberFormat(price);sum.getRange('D19').setNumberFormat(price);
sum.getRange('D12').setNumberFormat('0.00x');sum.getRange('D16:D18').setNumberFormat(money);
sum.getRange('D23:D29').setNumberFormat(money);sum.getRange('D30').setNumberFormat('0.00x');sum.getRange('D31').setNumberFormat('0.000000');
section(sum,14,'What do remaining cash flows support? (USD millions)','J');section(sum,21,'What cash can the business generate? (USD millions)','J');
section(sum,27,'What open freight rates justify the share price?','J');
val(sum,'F10','Edit the blue cells in Assumptions. Keep reported history unchanged.');
val(sum,'F11',`Dated ${fleetValueLabel.toLowerCase()} with the selected asset-value adjustment.`);
val(sum,'F19','Finite fleet life. No perpetual growth or unfinanced replacement fleet.');
val(sum,'F25','Debt maturity timing is estimated; excludes future dividends and refinancing.');
val(sum,'F30','Solves one common class-rate multiplier, with every other input held fixed.');
val(sum,'F31','Zero confirms the affine repricing identity; Python also solves by bisection.');
val(sum,'C38','Research view: conditional valuation, not a final stock recommendation.');
val(sum,'C39',`Cash bridge, charter coverage, remaining commitments and ${fleetValueLabel.toLowerCase()} updates require review.`);
val(sum,'C40','Forecast rates are explicit scenarios. The workbook does not contain a licensed freight curve.');
sum.getRange('C38:J40').format.font={color:muted,size:10};
sum.getRange('D6:D35').format.font.color=ink;sum.getRange('D4').format.font.color=green;

// A native two-input table varies actual model controls on this worksheet.
section(a,6,'', 'J'); // restore compact controls after section styling
val(a,'C6','Open-rate multiplier');a.getRange('D6').format={fill:'#FFF6DF',font:{color:blue}};
val(a,'L4','DCF per share sensitivity');val(a,'L5','Columns: rate multiplier. Rows: discount-rate adjustment.');
fx(a,'L8',"='Summary'!D19");a.getRange('L8').setNumberFormat(';;;');
a.getRange('M8:Q8').values=[[.8,.9,1,1.1,1.2]];
a.getRange('L9:L13').values=[[-.02],[-.01],[0],[.01],[.02]];
a.getRange('M8:Q8').setNumberFormat('0.00x');a.getRange('L9:L13').setNumberFormat(pct);
a.dataTables.add('L8:Q13',{rowInput:'D6',columnInput:'D7'});
a.getRange('M9:Q13').setNumberFormat(price);

const checks=sheets.Checks;
header(checks,'C6:F6',['Reconciliation','Difference','Tolerance','Result']);
const checkRows=[
 ['Historical TCE revenue',"='Historical'!D14",1],['Historical cash flow',"='Historical'!D35",1],
 ['Completed share-count bridge',`='NAV'!D27-${driver('additional_shares')}-${driver('atm_draw')}/${source('share_price')}-${source('adjusted_shares')}`,0],
 ['Debt carrying-value bridge',`='NAV'!D20-${source('debt_issuance_costs')}-${source('adjusted_debt_carrying')}`,1],
 ['Debt schedule ties to gross debt',`=SUM('Debt'!D31:D${lastDebt})-'NAV'!D20`,1],
 ['All newbuild capex forecast once',`=SUM('Cash Flow'!E90:${endcol}90)-'NAV'!D22`,1],
 ['Debt fully repaid',`='Debt'!${endcol}14`,1],['Fleet fully retired',`='Cash Flow'!${endcol}80`,0],
 ['Reverse valuation residual',"='Summary'!D31",.000001],
 ['Operating fleet DWT vs prospectus',`=SUMIFS('Fleet'!E7:E${lastFleet},'Fleet'!G7:G${lastFleet},"<="&'Summary'!D6)-${company.reported_operating_dwt}`,0],
];
checkRows.forEach(([label,formula,tolerance],i)=>{const r=i+7;val(checks,`C${r}`,label);fx(checks,`D${r}`,formula);val(checks,`E${r}`,tolerance);fx(checks,`F${r}`,`=IF(ABS(D${r})<=E${r},"PASS","REVIEW")`);});
checks.getRange('D7:E16').setNumberFormat('0.00');checks.getRange('D7:F16').format.font.color=ink;
checks.getRange('F7:F16').conditionalFormats.add('containsText',{text:'REVIEW',format:{fill:'#FDE9E5',font:{bold:true,color:'#A12921'}}});
val(checks,'C20',company.audit_notes?.[0] ?? 'Review source dates and individual vessel identities before updating.');
val(checks,'C21',company.audit_notes?.[1] ?? 'No appraisal should be counted twice.');
val(checks,'C22','PASS means arithmetic reconciles. It does not validate assumptions or investment suitability.');

const chartData=sheets.Summary;
header(chartData,'F43:G43',['Period','Free cash flow (USD m)']);
periods.slice(0,12).forEach((p,i)=>{val(chartData,`F${i+44}`,p.label);fx(chartData,`G${i+44}`,`='Cash Flow'!${col(i+4)}94/1000000`);});
const chart=chartData.charts.add('bar',chartData.getRange('F43:G55'));
chart.title='Quarterly unlevered cash flow (USD m)';chart.titleTextStyle.typeface='Arial';chart.titleTextStyle.fontSize=12;
chart.hasLegend=false;chart.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10}};
chart.yAxis={numberFormatCode:'0',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};
chart.series.items[0].fill='#537598';chart.setPosition('F43','O58');
// Keep chart sources clear of the chart itself.
chart.setPosition('I43','R59');

wb.recalculate();
console.log((await wb.inspect({kind:'region',sheetId:'Summary',range:'C8:D35',maxChars:2500,tableMaxRows:30})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:20},summary:'Formula error scan'})).ndjson);
const evidence={input_sha256:input.input_sha256,cases:{},periods,layout:{assumptions:ar,source:sr,forecast:cr,debt:dr},checks:checks.getRange('C7:F16').values};
// Change/recalculate/restore verifies the same live build. Comparisons are exported as audit evidence.
for(const [caseName,number] of [['bear',1],['base',2],['bull',3]]) {
  val(a,'D5',number);wb.recalculate();
  evidence.cases[caseName]={summary:Object.fromEntries(summary.map(([r,label])=>[label,sum.getRange(`D${r}`).values[0][0]])),
    nav:nav.getRange('D8:D30').values,forecast:Object.fromEntries(Object.entries(cr).map(([k,r])=>[k,cf.getRange(`E${r}:${endcol}${r}`).values[0]])),
    financing:Object.fromEntries(Object.entries(dr).map(([k,r])=>[k,ds.getRange(`E${r}:${endcol}${r}`).values[0]]))};
}
val(a,'D5',2);wb.recalculate();
const base=sum.getRange('D19').values[0][0];
val(a,'D6',1.1);wb.recalculate();const raised=sum.getRange('D19').values[0][0];
if(!(raised>base))throw Error('Open-rate input did not update DCF');
val(a,'D6',1);wb.recalculate();
evidence.recalculation={base_dcf:base,rate_110_dcf:raised,restored_dcf:sum.getRange('D19').values[0][0],engine:'artifact-tool'};
val(a,'D6',0);wb.recalculate();
if(typeof sum.getRange('D30').values[0][0]!=='number' || Math.abs(sum.getRange('D31').values[0][0])>1e-6)throw Error('Zero freight rates broke reverse valuation');
evidence.recalculation.zero_rate_reverse_multiplier=sum.getRange('D30').values[0][0];
val(a,'D6',1);wb.recalculate();
const testRow=ar['tce_Newcastlemax'];
const savedInput=a.getRange(`D${testRow+1}`).values[0][0];
a.getRange(`D${testRow+1}`).values=[[null]];wb.recalculate();
if(sum.getRange('D19').values[0][0]!==base)throw Error('Unselected blank changed active case');
val(a,'D5',1);wb.recalculate();
const blankResult=a.getRange(`D${testRow}`).values[0][0];
if(typeof blankResult==='number')throw Error('Selected blank was silently converted to zero');
val(a,`D${testRow+1}`,0);wb.recalculate();
if(a.getRange(`D${testRow}`).values[0][0]!==0)throw Error('Explicit zero rate not respected');
val(a,`D${testRow+1}`,savedInput);val(a,'D5',2);wb.recalculate();
evidence.boundary_checks={unselected_blank:'unchanged',selected_blank:blankResult,explicit_zero:'preserved',restored_dcf:sum.getRange('D19').values[0][0]};
await fs.writeFile(path.join(output,'excel-calculation-evidence.json'),JSON.stringify(evidence,null,2));
const workbook=await SpreadsheetFile.exportXlsx(wb);await workbook.save(path.join(output,`${company.ticker}-valuation.xlsx`));
for(const name of names) {
  const range={Summary:'C2:J40',Assumptions:'C2:J24',NAV:'C2:E30','Cash Flow':'C78:J104',Debt:'C10:J23',Fleet:'C2:L17',Days:'C2:J19',Historical:'C2:E35',Sources:'C2:H17',Checks:'C2:F16'}[name];
  const preview=await wb.render({sheetName:name,range,scale:1.5,format:'png'});
  await fs.writeFile(path.join(output,'previews',name.replaceAll(' ','-')+'.png'),new Uint8Array(await preview.arrayBuffer()));
}
for(const [name,range,file] of [['Fleet','M5:R12','Fleet-evidence'],['Assumptions','L4:Q13','Sensitivity']]) {
  const preview=await wb.render({sheetName:name,range,scale:1.5,format:'png'});
  await fs.writeFile(path.join(output,'previews',file+'.png'),new Uint8Array(await preview.arrayBuffer()));
}
console.log('Workbook, calculation evidence and all sheet previews exported.');
