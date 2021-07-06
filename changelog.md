Covmatic Stations changelog
===========================

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