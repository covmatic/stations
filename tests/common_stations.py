from covmatic_stations.a.technogenetics import StationATechnogenetics48, StationATechnogenetics48Saliva
from covmatic_stations.b.technogenetics import StationBTechnogenetics, StationBTechnogeneticsSaliva
from covmatic_stations.b.technogenetics_paired_pipette import StationBTechnogeneticsPairedPipette, \
    StationBTechnogeneticsSalivaPairedPipette


STATIONS_A = [StationATechnogenetics48,
              StationATechnogenetics48Saliva]

STATIONS_B = [StationBTechnogenetics,
              StationBTechnogeneticsPairedPipette,
              StationBTechnogeneticsSaliva,
              StationBTechnogeneticsSalivaPairedPipette]

STATIONS = STATIONS_A + STATIONS_B
