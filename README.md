# Antimony
A lighter Bismuth light wallet, for console use only. Dedicated to command line lovers and automation freaks.

Antimony is a chemical element with properties that are close to Bismuth's, but that is lighter ;)

## Prerequisites

Python3.6+

## Installation

`pip3 install -r requirements.txt`

Antimony needs a `wallet.der` file in the same directory.  
Just copy the wallet.der file you want to use in Antimony's dir. No need for config, local node or anything else.

## Help

`./Antimony.py --help`

(under windows, use `python3 Antimony.py [...]` invocation)

To get detailed help for a specific command, use --help with the command, for instance:

`./Antimony send --help`

## Example commands

Show your balance:  
`./Antimony.py balance`


Send a tip to Antimony devs:  
`./Antimony.py send 437b30a2ea780cffb67cc220428d462cf2bedcbd3aab094aa7d4df9c 10`


Send 100 BIS **only** if the balance is > 200 BIS;  
`./Antimony.py send 437b30a2ea780cffb67cc220428d462cf2bedcbd3aab094aa7d4df9c 100 "" "" 200`  
the two defaults empty parameters are needed since the "Above" condition is the third optional parameter.


## Tip Jar

Show your appreciation, send a few coffees or pizzas to the devs:  
`437b30a2ea780cffb67cc220428d462cf2bedcbd3aab094aa7d4df9c`

Bis Url (10 bis): `bis://pay/437b30a2ea780cffb67cc220428d462cf2bedcbd3aab094aa7d4df9c/10///sLqe+F#1D1pM4>M4N+tb`

Real time balance:  
![TipJar](https://eggpool.net/balance/index.php?address=437b30a2ea780cffb67cc220428d462cf2bedcbd3aab094aa7d4df9c)


## Releases

* 0.0.3 - Added optional "Above" condition to "send" command.
* 0.0.2 - Maintenance
* 0.0.1 - Initial crude version, only balance and send commands


## More

A Stibnite cristal  
![Stibnite](https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Stibnite.jpg/640px-Stibnite.jpg)

Stibnite is an Antimony sulfide.  
This illustrates how complex things (What you will build) can emerge from simple elements (This tool).
