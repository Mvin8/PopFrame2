import geopandas as gpd
from shapely.geometry.base import BaseGeometry
from typing import Dict, Any, Set, List

class InfrastructureAnalyzer:
    def __init__(self, combined_gdf: gpd.GeoDataFrame, spb_hex: gpd.GeoDataFrame) -> None:
        # Convert coordinate systems to metric (EPSG:3857) for calculations
        self.combined_gdf = combined_gdf.to_crs(epsg=3857)
        self.spb_hex = spb_hex.to_crs(epsg=3857)
        
        # Initialize columns and start analysis
        self.spb_hex['score'] = 0
        self.spb_hex['types_in_radius'] = None
        self._analyze_infrastructure()
    
    @staticmethod
    def get_radius(physical_object_type: Dict[str, Any]) -> float:
        """Determines the radius based on the physical object type."""
        name = physical_object_type.get('name', '')
        if "Атомная электростанция" in name:
            return 100000.0  # 100 km in meters for nuclear power plants
        elif "Гидроэлектростанция" in name:
            return 10000.0   # 10 km in meters for hydroelectric power plants
        else:
            return 1000.0    # 1 km in meters for other types
    
    def _analyze_infrastructure(self) -> None:
        """Analyzes infrastructure for each territory and adds assessment attributes."""
        # For each territory, check the presence of unique object types within the radius
        for index, hexagon in self.spb_hex.iterrows():
            # Create a temporary set of unique types for this territory
            unique_types_in_radius: Set[str] = set()
    
            # Check each object in combined_gdf for inclusion in the buffer
            for _, obj in self.combined_gdf.iterrows():
                # Extract `physical_object_type` dictionary to determine the radius
                physical_object_info: Dict[str, Any] = obj['physical_object_type']
                buffer_distance: float = self.get_radius(physical_object_info)
                
                # Create a buffer for the current territory
                hex_buffer: BaseGeometry = hexagon.geometry.buffer(buffer_distance)
                
                # If the object is within the buffer, add its `type` to the set
                if obj.geometry.within(hex_buffer):
                    unique_types_in_radius.add(obj['type'])
    
            # Count unique types and assign them to 'score' and 'types_in_radius' attributes
            self.spb_hex.at[index, 'score'] = len(unique_types_in_radius)
            self.spb_hex.at[index, 'types_in_radius'] = list(unique_types_in_radius)
    
    def get_results(self) -> gpd.GeoDataFrame:
        """Returns the result with columns 'id', 'score', 'types_in_radius', and 'geometry' in CRS 4326."""
        # Convert back to CRS 4326 before returning
        return self.spb_hex[['id', 'score', 'types_in_radius', 'geometry']].to_crs(epsg=4326)


    