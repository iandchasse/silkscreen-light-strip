# String Vf window calc for silkscreen-light-strip
VF=dict(min=2.70,typ=2.95,max=3.20); VFWIDE=3.50        # per LED @13.9 mA, 25 C
TC=dict(min=0.0015,typ=0.00225,max=0.0030)               # V/K magnitude (Vf rises when cold)
dT_cold=35.0                                              # 25 C -> -10 C
dT_hot=40.0                                               # Tj 65 C (50 C ambient + self-heat)
dim_drop=0.45                                             # per LED, 13.9 mA -> 14 uA (0.1% ADIM), generic 0.15 V/dec
VFB_max=0.206; VQ=0.05                                    # FB ref max, BSS138 drop @14 mA (est.)
DS=dict(cold=0.95,typ=0.75,hotdim=0.45)                   # optional series Si diode drop
OVP_MIN=24.25; OVP_MIN_611=29.6; CEIL=22.0
VIN_MAX=5.5; VBD_uA=0.3; V_LED_1uA_hot=2.1
K=120/(1000+120)
rows=[]
print("| N | String Vf 25 C min / typ / max (V) | VOUT typ 25 C (V) | VOUT max -10 C, no diode / with diode (V) | VOUT max -10 C, 3.5 V wide bin + diode (V) | Margin to OVP min 24.25 V (worst col.) | VOUT min at 0.1 % ADIM, 65 C, min bin (V) | Off-state V per LED at VIN 5.5 V | LED_MONIT typ (V) | Verdict |")
print("|---|---|---|---|---|---|---|---|---|---|")
for N in range(3,8):
    s=[N*VF[k] for k in ('min','typ','max')]
    vtyp=s[1]+0.200+VQ
    vcold=N*(VF['max']+TC['max']*dT_cold)+VFB_max+VQ
    vcold_d=vcold+DS['cold']
    vwide=N*(VFWIDE+TC['max']*dT_cold)+VFB_max+VQ+DS['cold']
    vmin_dim=N*(VF['min']-TC['max']*dT_hot-dim_drop)+0.0002+0.0
    offper=(VIN_MAX-VBD_uA)/N
    marg=OVP_MIN-vwide
    mon=vtyp*K
    if N==3: v="Marginal: deep-dim regulation near VIN (6.4 V vs 6.5 V target); one shorted LED leaves 2 LEDs that conduct when off"
    elif N==7: v="Reject for TPS923610 (worst case at/over OVP); TPS923611 only"
    elif N==6: v="OK only if max bin <= 3.2 V or no series diode"
    else: v="OK"
    print(f"| {N} | {s[0]:.2f} / {s[1]:.2f} / {s[2]:.2f} | {vtyp:.2f} | {vcold:.2f} / {vcold_d:.2f} | {vwide:.2f} | {marg:+.2f} | {vmin_dim:.2f} | {offper:.2f} | {mon:.2f} | {v} |")
print()
print("OVP min->LED_MONIT", OVP_MIN*K, 25.5*K, "611:", 29.6*K, 31.4*K)
print("off-state monit (Vin 3.0..5.5 minus 0.3..0.5):", (3.0-0.5)*K, (4.2-0.4)*K, (5.5-0.3)*K)
# N=5 LED_MONIT range
for lab,v in [("N5 hot min full-I",5*(VF['min']-TC['max']*dT_hot)+0.195+0.03),("N5 typ",5*2.95+0.25),("N5 cold max",5*(3.2+0.105)+0.256),("N5 cold max +Ds",5*(3.2+0.105)+0.256+0.95)]:
    print(lab, round(v,2), round(v*K,3))
# boost duty / power at VIN 3.0, VOUT 22
Vin=3.0; Vo=22.0; I=0.01396; eta=0.8; L=10e-6; fs=1.1e6
Pout=Vo*I; Iin=Pout/(eta*Vin); D=1-Vin/Vo; Deff=1-Vin*eta/Vo
dI=1/(L*(1/(Vo-Vin)+1/Vin)*fs)
print("Pout",Pout,"Iin",Iin,"D ideal",D,"D w/ losses",Deff,"toff ns",(1-D)/fs*1e9,"dIpp",dI,"Ipk",Iin+dI/2)
Vo=24.5; Vin=2.5; print("ROC corner D", 1-Vin/Vo); print("TI ref 6S@2.5V D", 1-2.5/18.5)
# short-circuit estimates
for vin in (4.2,5.5):
    for R in (15+1.5, 15+3.5):
        i=(vin-0.7)/R; print("short vin",vin,"R",R,"I",round(i,3),"P_R37",round(i*i*15,3))
# flipped zener-LED case N=5
for vin in (4.2,5.5):
    i=(vin-0.4-5*0.7)/17; print("flip zener N5 vin",vin,"I",round(i,4), "P_R37", round(i*i*15,4))
# unselected string bleed current through 1M
for N in (5,6):
    for per in (0.6,0.8):
        print("bleed N",N,"excess/LED",per,"I uA",N*per/1e6*1e6)
# C9 decay tau
for c in (2e-6,4.7e-6): print("tau C9",c, c*1.12e6)
