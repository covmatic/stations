from covmatic_stations.a.technogenetics import StationATechnogenetics48, StationATechnogenetics48Saliva
from covmatic_stations.b.technogenetics import StationBTechnogenetics, StationBTechnogeneticsSaliva


STATIONS_A = [StationATechnogenetics48,
              StationATechnogenetics48Saliva]

STATIONS_B = [StationBTechnogenetics,
              StationBTechnogeneticsSaliva]

STATIONS = STATIONS_A + STATIONS_B
