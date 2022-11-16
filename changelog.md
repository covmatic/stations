Covmatic Stations changelog
===========================

## v2.19.4

- [Bioer PCR] Elutes: only columns with controls use single pipetting otherwise are always transferred with 8-channel pipette
              (reverts changes in *v.2.19.3*).

## v2.19.3

- [Bioer PCR] Fixed bug that caused sample transfer for the entire column, even when not needed;
- [Bioer PCR] Added some tests thanks to code refactoring.

## v2.19.2

### Important notes:
- from LocalWebServer v2.11.0 Station C labware is changed ==> Now it is the same as **Bioer PCR** station
- Station C volumes for mastermix tubes are changed: see the documentation.

### Added:

- [Station C Technogenetics] Created class *DistributeMastermixTechnogenetics* to distribute KHB mastermix with Bioer station
- [Bioer PCR] Small fix; fixed volume overhead to match Technogenetics KHB volumes
- [Bioer PCR] Decreased speed exiting from mastermix tubes to avoid bubbles in tip.

## v2.18.6

- [Bioer PCR] Introduced *start at* to restart the run where needed;
- [MultiTubeSource] Added function to retrieve current aspirate tube and fake aspiration (*use_volume_only*) ease *start_at* management

## v2.18.5

- [Bioer PCR] Lowered aspiration height from deepwell; changed labware to Bioer deepwell.
- [covmatic-stations] Fixed *Opentrons* and *typing-extensions* packages version.


## v2.18.4

- [Station A Saliva] Raised lateral point after sample aspiration to avoid touching COPAN collection tube when mixed with saliva ones.

## v2.18.3

- [Station B Technogenetics] Fixed bug caused by duplicated code
- [Station A Saliva] Lower sample aspirate height
- [Station A saliva] Better sample mix and lower contamination
- [Station A] Sample transfer: greater air gap speed


## v2.18.2

- [Station B Technogenetics] Fixed *Pause* and *Delay* commands outside *start_at* 


## v2.18.1

- [Station A Technogenetics Saliva] Fixed bug in rack 2 positions.

## v2.18.0

### Note: the workflow in **Station B** is changed.

### Added

- [Station A, Station B] New protocol for saliva samples with KHB extraction kit;
- [Station B] Reintroduced *second wash A removal*

### Fixed
- [Station B] Better beads resuspension with *mix_walk*

## v2.17.0

### Note: the workflow in **Station B** is changed.

- [Station A Technogenetics] Removed *Add Beads* message
- [Station B Technogenetics] Removed wash A second removal since it is not part of protocol


## v2.16.4

### Fixed
- [Station B Technogenetics] Raised sample mix bottom height to avoid tips clogging.
- [Station B Technogenetics] Diminished after spin wait time on MagDeck;
- [Station B Technogenetics] Diminished after thermomixer time on MagDeck;

## v2.16.3

### Fixed

- [Station A Technogenetics] Better and cleaner sample transfer;
- [Station A Technogenetics] Samples are not mixed in deepwell plate;
- [Station B Technogenetics] Samples are mixed during incubation time.

## v2.16.2

- [Station A Technogenetics] Added message for positive control.

## v2.16.1

### Note

This version modify the analysis workflow **deleting the need for external incubation and thermomixer between station A and B**.
The workflow now is:

>     Station A (Lysis, beads, PK, samples) 
>       |   
>       --> Add Positive Control
>       | 
>     Station B – incubation on Temperature Deck with thermal adapter for deepwell. 
>       |         Place deepwell on Temperature Deck
>       |

### Added
- [Station A] Lysis is dispensed first;
- [Station A] Beads are dispensed first with same tip;
- [Station A] Samples and lysis/beads/PK are mixed with P1000.
- [Station B] Incubation 20 min on TempDeck at 55 °C.

### Fixed

- [Station A] Increased flow rates for lysis and mixing.
- WellWithVolume class now check for negative volume passed.
- mix_top_bottom now supports *last_dispense_rate* to clean tip better.
- fixed github workflow.

## v2.15.0
### Note
- Needs **localwebserver >= v2.9.0**
- Needs **webserver >= v0.9.0**
- Needs **dashboard >= v0.10.0**

### Added
- [stations] Added *dashboard_input* to make the *dashboard* ask something in the middle of the run;
- [station A technogenetics] Second rack is requested with *dashboard_input*

## v2.14.0
- [station B technogenetics] moved *deepwell incubation* (now *beads drying*) from TempDeck to MagDeck;
- [station B technogenetics] inserted delay of 5 minutes for beads drying on MagDeck;
- [station B technogenetics] removed *check wash A after spin* since it is not needed now.

## v2.13.2
- [station A technogenetics] PK is aspirated with slow movement to avoid bubbles;
- [station A technogenetics] PK deleted touch tip both in aspirate and dispense;
- [station A technogenetics] PK blows out in deepwell to avoid liquid carried back in tip.
- [station A technogenetics] PK increased flow rate.

## v2.13.1
- [stations] Avoided *pause* message when delay is called.

## v2.13.0
- [Station B technogenetics] **Wash B** moved to reservoir in slot 2 same as elution buffer.
- [Station B technogenetics] Using Biofil 1000ul base rack as waste reservoir.

## v2.12.11
- [Station B] Slowed down moving out of wells and reagents to avoid liquid on tip's external surface.

## v2.12.10
- [Station B] Lowered aspirate height in wash reagents.

## v2.12.9
- [Station B technogenetics] Washes volume decreased to 650 to allow dead volume;
- [Station B technogenetics] Disabled touch tip on elute phase.

## v2.12.8
### Fixed
- [Station] Disabled sounds in test mode
- [Station B technogenetics] Added watchdog on tempdeck serial command.

## v2.12.7
- [Station B technogenetics] Reverted wash B moved to slot 2 wrongly inserted for single pipette.

## v2.12.6
- [Station A technogenetics] Beads volume diminished to 9ul to have dead volume.
- [Station A technogenetics] Better beads aspiration with slow movement going up.

## v2.12.5
- [Station B technogenetics] Disabled unuseful mix on elute phase.

## v2.12.4
### Fixed
- [Bioer preparation] Pk volume diminished to 9 to have dead volume.

## v2.12.2
### Fixed
- MultiTubeSource now support a vertical speed to avoid bubbles when aspirating.
- [Bioer mastermix prep] Added support for KHB mastermix
- [Bioer mastermix prep] added slow vertical speed when aspirating from mastermix tube
- [Bioer preparation] revised vertical speed in PK aspiation to avoid bubbles.

## v2.12.0
### Added
- [station] Added watchdog for *start_at* stages and *delays*. Do not support OT-App *pause* command

## v2.11.2
### Fixed
- [stations] Resolved bug that reset every tipracks present upon only one type is finished
- [Bioer preparation] Increased vertical speed to avoid resonance.

## v2.11.1
### Added
- [station A] added protocol to fill Bioer deepwell with samples.

### Fixed
- [Bioer mastermix prep] Added slow movement to avoid drops in mastermix dispense.
- [Bioer mastermix prep] Added air_gap and blow_out to elutes transfer.

## v2.11.0
### Added
- [station A techogenetics] PK volume set to 20ul
- [Bioer mastermix prep] Aspirate from mastermix tube is done at gradual height not to overflow.
- [Bioer mastermix prep] Uses 1 tube for 96 samples to reflect mastermix preparation instruction.

## v2.10.2
### Fixed
- [station A technogenetics] fixed sample aspiration movement speed.
- [station A technogenetics] cleaner sample transfer with delay to avoid bubbles in tip ejecting.

## v2.10.0
### Added
- [Bioer preparation] New protocol to prepare one Bioer deepwell plate
- [station] added MovieWithSpeed class to move at desidered speed to and from wells.

## v2.9.3
### Fixed
- [station B techogenetics] Tempdeck turn on moved before second wash B removal

## v2.9.2
### Fixed
- [station] Changed beep sound.

## v2.9.1
### Fixed
- [station] Force home movement after run even with gantry in near-home position:
  this should mitigate homing problem on next run

## v2.9.0
### Added
- [station] Sounds when pause with blinking, run finish and run error.
- [station B techogenetics] Temperature module is turned on when needed and off when finished.

### Fixed
- [package] *requests* dependency version added to fix upgrade on Opentrons v4.6.2

## v2.8.0
### Added
- [station B paired pipette] Paired pickup is done with single pipette to avoid pulled up tiprack

## v2.7.7
### Fixed
- [station A Technogenetics] Disabled drop tip count
- [station A Technogenetics] Disabled mix after beads transfer

## v2.7.6
### Fixed
- [station A] Improper use of filter and *in* keyword in transfer_samples

## v2.7.5
### Fixed
- [station A Techogenetics] Skipped transfer of Negative control from sample A1.
- [station A] Added Negative control well.
- [station A] Added possibility to transfer lysis also to control wells-

## v2.7.4
### Fixed
- [station B] Remove supernatant last step higher to avoid tip clogging.
- [station B] Remove supernatant and final transfer decreased side movement.
- [station B] Remove supernatant max volume limit set to tip volume.
- [station B] Higher Final transfer heights to avoid tips clogging.

## v2.7.3
### Fixed
- [station C] Drop tip after positive control fill.

## v2.7.2
### Fixed 
- [station A Technogenetics] Lysis buffer is dispensed also in H12 in 96-samples run.
- [station B Technogenetics] Magnetic module disengaged before manual intervention.
- [station C Technogenetics] Positive control is not filled twice with 96 samples run.

## v2.7.1
### Fixed
- [paired pipette] Fixed bug in start-at logic when used not at the beginning of the plate.

## v2.7.0
### Fixed
- [station B paired pipette] lowered drop tip position to avoid tip flying around

### Added
- [station] Pause now go to home position without homing motors.


## v2.6.5
### Fixed
- [station A Technogenetics] lowered proteinase K dispense position to avoid drops;
- [station A Technogenetics] proteinase K distribution is done without changing tips.

## v2.6.4
### Fixed
- [paired pipette] reduced remove supernatant side movement to accomplish for mechanical space between pipettes

## v2.6.3
### Fixed
- [paired pipette] Supernatant removal is on the side of the well same as Technogenetics B protocol.
- [opentrons v4.5.0] MagDeck serial is retrieved with *device_info* property instead of accessing internal driver.

## v2.6.2
### Fixed
- [paired pipette] Flow rates are set correctly using the PairedPipette context as needed.

## v2.6.1
### Fixed
- [station] if a wrong start_at value is given throw an error to not complete correctly the protocol.

## v2.6.0
### Added
- Error on protocol execution are saved to file for LWS; requires covmatic-localwebserver >= 2.6.1

## Fixed
- [Tip Log] if Tip Log file is emtpy no error is thrown.
- [Tip Log] if Tip Log is malformed a simple "Reset tiplog" error message is thrown.

## v2.5.2
- [restored] Station C does not change m20 tips for mastermix each column.

## v2.5.1
- Remove supernatant is on the side of the well.

## v2.5.0
### Added
- [*station B*] Higher aspirate and dispense speed;
- WellWithVolume class now calculates the optimal height to aspirate from a well.

### Fixed
- [*station B*] Fixed bug on wash A and B liquid speed;
- [*station B*] Fixed bug on supernatant removal apiration rate;

## v2.4.3
- [*bioer*] added pause before elutes transfer.
- [MultiTubeSource] changed aspirate command to fit *start_at* logic

## v2.4.2
- [*bioer*] fixed height in elution transfer
- minor improvements

## v2.4.1
- [*paired pipette*] minor fixes

## v2.4.0
### Added
- [*station*] now support debug mode to return tip instead of trashing them for debug.
- [*station*] added Paired Pipette support
- [B Techogenetics] added protocol for paired pipette

## v2.3.2
- [station] in file log added date-time info

## v2.3.1
- [B Technogenetics] changed stage names to be unique

## v2.3.0
- [bioer] added Bioer protocol for PK, transfer mastermix, transfer elutes;
- [station] added MultiTubeSource to handle aspirate from a pool of tubes.

## v2.2.1
### Added
- Station for Bioer Mastermix PCR Plate preparation.

### Fixed
- Bioer mastermix prep protocol class and liquid rate fixed
- Logger multiple outputs on Opentrons App on multiple run