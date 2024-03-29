EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L power:GND #PWR?
U 1 1 62E3B183
P 4100 4650
F 0 "#PWR?" H 4100 4400 50  0001 C CNN
F 1 "GND" H 4105 4477 50  0000 C CNN
F 2 "" H 4100 4650 50  0001 C CNN
F 3 "" H 4100 4650 50  0001 C CNN
	1    4100 4650
	1    0    0    -1  
$EndComp
$Comp
L Transistor_BJT:BC337 Q1
U 1 1 62E3D658
P 4000 4250
F 0 "Q1" H 4191 4296 50  0000 L CNN
F 1 "BC337" H 4191 4205 50  0000 L CNN
F 2 "Package_TO_SOT_THT:TO-92_Inline" H 4200 4175 50  0001 L CIN
F 3 "https://diotec.com/tl_files/diotec/files/pdf/datasheets/bc337.pdf" H 4000 4250 50  0001 L CNN
	1    4000 4250
	1    0    0    -1  
$EndComp
Wire Wire Line
	4100 4450 4100 4650
$Comp
L Device:R R1
U 1 1 62E3EE81
P 3450 4250
F 0 "R1" V 3650 4200 50  0000 L CNN
F 1 "12k" V 3550 4200 50  0000 L CNN
F 2 "" V 3380 4250 50  0001 C CNN
F 3 "~" H 3450 4250 50  0001 C CNN
	1    3450 4250
	0    -1   -1   0   
$EndComp
$Comp
L Device:R R2
U 1 1 62E3F5A6
P 4100 3750
F 0 "R2" H 4170 3796 50  0000 L CNN
F 1 "47" H 4170 3705 50  0000 L CNN
F 2 "" V 4030 3750 50  0001 C CNN
F 3 "~" H 4100 3750 50  0001 C CNN
	1    4100 3750
	1    0    0    -1  
$EndComp
$Comp
L LED:CQY99 D1
U 1 1 62E3FC65
P 3550 3000
F 0 "D1" H 3500 3290 50  0000 C CNN
F 1 "CQY99" H 3500 3199 50  0000 C CNN
F 2 "LED_THT:LED_D5.0mm_IRGrey" H 3550 3175 50  0001 C CNN
F 3 "https://www.prtice.info/IMG/pdf/CQY99.pdf" H 3500 3000 50  0001 C CNN
	1    3550 3000
	0    -1   -1   0   
$EndComp
$Comp
L LED:CQY99 D2
U 1 1 62E40254
P 3900 3000
F 0 "D2" H 3850 3290 50  0000 C CNN
F 1 "CQY99" H 3850 3199 50  0000 C CNN
F 2 "LED_THT:LED_D5.0mm_IRGrey" H 3900 3175 50  0001 C CNN
F 3 "https://www.prtice.info/IMG/pdf/CQY99.pdf" H 3850 3000 50  0001 C CNN
	1    3900 3000
	0    -1   -1   0   
$EndComp
$Comp
L LED:CQY99 D3
U 1 1 62E405CC
P 4250 3000
F 0 "D3" H 4200 3290 50  0000 C CNN
F 1 "CQY99" H 4200 3199 50  0000 C CNN
F 2 "LED_THT:LED_D5.0mm_IRGrey" H 4250 3175 50  0001 C CNN
F 3 "https://www.prtice.info/IMG/pdf/CQY99.pdf" H 4200 3000 50  0001 C CNN
	1    4250 3000
	0    -1   -1   0   
$EndComp
$Comp
L LED:CQY99 D4
U 1 1 62E40987
P 4600 3000
F 0 "D4" H 4550 3290 50  0000 C CNN
F 1 "CQY99" H 4550 3199 50  0000 C CNN
F 2 "LED_THT:LED_D5.0mm_IRGrey" H 4600 3175 50  0001 C CNN
F 3 "https://www.prtice.info/IMG/pdf/CQY99.pdf" H 4550 3000 50  0001 C CNN
	1    4600 3000
	0    -1   -1   0   
$EndComp
Wire Wire Line
	3600 4250 3800 4250
Wire Wire Line
	4100 4050 4100 3900
Wire Wire Line
	3550 3200 3550 3400
Wire Wire Line
	3550 3400 3900 3400
Wire Wire Line
	4600 3400 4600 3200
Wire Wire Line
	4250 3200 4250 3400
Connection ~ 4250 3400
Wire Wire Line
	4250 3400 4600 3400
Wire Wire Line
	3900 3200 3900 3400
Connection ~ 3900 3400
Wire Wire Line
	3900 3400 4100 3400
Wire Wire Line
	4100 3400 4100 3600
Connection ~ 4100 3400
Wire Wire Line
	4100 3400 4250 3400
$Comp
L power:+3V3 #PWR?
U 1 1 62E45ACB
P 4100 2350
F 0 "#PWR?" H 4100 2200 50  0001 C CNN
F 1 "+3V3" H 4115 2523 50  0000 C CNN
F 2 "" H 4100 2350 50  0001 C CNN
F 3 "" H 4100 2350 50  0001 C CNN
	1    4100 2350
	1    0    0    -1  
$EndComp
Wire Wire Line
	3550 2900 3550 2600
Wire Wire Line
	3550 2600 3900 2600
Wire Wire Line
	4600 2600 4600 2900
Wire Wire Line
	4250 2900 4250 2600
Connection ~ 4250 2600
Wire Wire Line
	4250 2600 4600 2600
Wire Wire Line
	3900 2900 3900 2600
Connection ~ 3900 2600
Wire Wire Line
	3900 2600 4100 2600
Wire Wire Line
	4100 2350 4100 2600
Connection ~ 4100 2600
Wire Wire Line
	4100 2600 4250 2600
$Comp
L Interface_Optical:TSOP21xx U1
U 1 1 62E48F22
P 6800 2950
F 0 "U1" V 6742 3238 50  0000 L CNN
F 1 "TSOP21xx" V 6833 3238 50  0000 L CNN
F 2 "OptoDevice:Vishay_MOLD-3Pin" H 6750 2575 50  0001 C CNN
F 3 "http://www.vishay.com/docs/82460/tsop45.pdf" H 7450 3250 50  0001 C CNN
	1    6800 2950
	0    1    1    0   
$EndComp
$Comp
L power:GND #PWR?
U 1 1 62E4CE3D
P 6600 3600
F 0 "#PWR?" H 6600 3350 50  0001 C CNN
F 1 "GND" H 6605 3427 50  0000 C CNN
F 2 "" H 6600 3600 50  0001 C CNN
F 3 "" H 6600 3600 50  0001 C CNN
	1    6600 3600
	1    0    0    -1  
$EndComp
Wire Wire Line
	6600 3600 6600 3350
$Comp
L power:+3V3 #PWR?
U 1 1 62E4E1AC
P 7000 3600
F 0 "#PWR?" H 7000 3450 50  0001 C CNN
F 1 "+3V3" H 7015 3773 50  0000 C CNN
F 2 "" H 7000 3600 50  0001 C CNN
F 3 "" H 7000 3600 50  0001 C CNN
	1    7000 3600
	-1   0    0    1   
$EndComp
Wire Wire Line
	7000 3600 7000 3350
$Comp
L Connector_Generic:Conn_01x01 GPIO17
U 1 1 62E50E69
P 2850 4250
F 0 "GPIO17" H 2800 4350 50  0000 L CNN
F 1 "Conn_01x01" H 2600 4450 50  0000 L CNN
F 2 "" H 2850 4250 50  0001 C CNN
F 3 "~" H 2850 4250 50  0001 C CNN
	1    2850 4250
	-1   0    0    1   
$EndComp
$Comp
L Connector_Generic:Conn_01x01 GPIO18
U 1 1 62E50076
P 6800 4200
F 0 "GPIO18" V 6800 4300 50  0000 L CNN
F 1 "Conn_01x01" V 6900 4100 50  0000 L CNN
F 2 "" H 6800 4200 50  0001 C CNN
F 3 "~" H 6800 4200 50  0001 C CNN
	1    6800 4200
	0    1    1    0   
$EndComp
Wire Wire Line
	6800 3350 6800 4000
Wire Wire Line
	3050 4250 3300 4250
Wire Notes Line
	2500 2000 5000 2000
Wire Notes Line
	5000 2000 5000 5000
Wire Notes Line
	5000 5000 2500 5000
Wire Notes Line
	2500 5000 2500 2000
Wire Notes Line
	6000 2000 8000 2000
Wire Notes Line
	8000 2000 8000 5000
Wire Notes Line
	8000 5000 6000 5000
Wire Notes Line
	6000 5000 6000 2000
Text Notes 7600 4950 0    50   ~ 0
Receptor
Text Notes 4500 4950 0    50   ~ 0
Transmitter
$EndSCHEMATC
